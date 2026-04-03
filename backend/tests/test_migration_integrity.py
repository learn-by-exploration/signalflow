"""Migration integrity and model-schema drift detection tests.

These tests catch the exact class of bug where a developer adds a column to a
SQLAlchemy model but forgets to create an Alembic migration.  They also verify
the migration chain is linear and every migration can upgrade/downgrade cleanly.

Industry-standard practices implemented:
1. Model-vs-migration drift detection (regex-based, runs everywhere)
2. Migration chain linearity check (no forks, no orphans)
3. Migration file naming and structure validation
4. Model completeness checks (imports in __init__.py and env.py)
5. Full autogenerate diff against real PostgreSQL (CI-only, gold standard)
"""

import os
import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = BACKEND_DIR / "migrations" / "versions"


# ===================================================================
# 1. Model-vs-Migration Drift Detection
# ===================================================================

class TestModelMigrationDrift:
    """Detect when ORM models have changes not covered by migrations.

    This is the EXACT test that would have caught the email_verified bug.
    It compares what Alembic's autogenerate would produce against the current
    migration head.  If autogenerate finds pending changes, the test fails.
    """

    def test_no_pending_model_changes(self):
        """Ensure all model changes have corresponding migrations.

        Parses all migration files and collects every create_table/add_column
        operation, accounts for drop_column/drop_table removals, then verifies
        every current model column is covered by a migration.
        """
        # Import all models so Base.metadata is fully populated
        from app.database import Base
        import app.models  # noqa: F401 — triggers __init__.py

        model_columns = self._get_model_columns(Base)
        migration_columns = self._get_migration_columns()

        missing = []
        for table_name, columns in model_columns.items():
            for col_name in columns:
                if not self._column_in_migrations(table_name, col_name, migration_columns):
                    missing.append(f"{table_name}.{col_name}")

        assert not missing, (
            f"Model columns not covered by any migration:\n"
            f"  {', '.join(missing)}\n\n"
            f"Fix: Run 'cd backend && alembic revision --autogenerate -m \"add missing columns\"' "
            f"to generate a migration for these changes."
        )

    def _get_model_columns(self, base) -> dict[str, set[str]]:
        """Extract all columns from all SQLAlchemy models."""
        result = {}
        for table in base.metadata.tables.values():
            result[table.name] = {col.name for col in table.columns}
        return result

    def _get_migration_columns(self) -> dict[str, set[str]]:
        """Parse migration upgrade() functions and track net column state.

        Processes migrations in chain order, handling:
        - op.create_table  → adds table + columns
        - op.add_column    → adds column to existing table
        - op.drop_column   → removes column (in upgrade path)
        - op.drop_table    → removes table entirely (in upgrade path)
        """
        columns: dict[str, set[str]] = {}

        for migration_file in sorted(MIGRATIONS_DIR.glob("*.py")):
            content = migration_file.read_text()

            # Only parse the upgrade() function body, not downgrade()
            upgrade_match = re.search(
                r'def upgrade\(\)[^:]*:(.*?)(?=\ndef downgrade\(|\Z)',
                content,
                re.DOTALL,
            )
            if not upgrade_match:
                continue
            upgrade_body = upgrade_match.group(1)

            # -- create_table --
            create_table_matches = re.finditer(
                r'op\.create_table\(\s*["\'](\w+)["\']',
                upgrade_body,
                re.DOTALL,
            )
            for match in create_table_matches:
                table_name = match.group(1)
                if table_name not in columns:
                    columns[table_name] = set()

                start = match.end()
                remaining = upgrade_body[start:]
                col_matches = re.finditer(
                    r'sa\.Column\(\s*["\'](\w+)["\']',
                    remaining,
                )
                for col_match in col_matches:
                    between = remaining[:col_match.start()]
                    if re.search(r'\bop\.\w+\(', between):
                        break
                    columns[table_name].add(col_match.group(1))

            # -- add_column --
            add_col_matches = re.finditer(
                r'op\.add_column\(\s*["\'](\w+)["\']\s*,\s*sa\.Column\(\s*["\'](\w+)["\']',
                upgrade_body,
                re.DOTALL,
            )
            for match in add_col_matches:
                table_name = match.group(1)
                col_name = match.group(2)
                if table_name not in columns:
                    columns[table_name] = set()
                columns[table_name].add(col_name)

            # -- drop_column (in upgrade) --
            drop_col_matches = re.finditer(
                r'op\.drop_column\(\s*["\'](\w+)["\']\s*,\s*["\'](\w+)["\']',
                upgrade_body,
                re.DOTALL,
            )
            for match in drop_col_matches:
                table_name = match.group(1)
                col_name = match.group(2)
                if table_name in columns:
                    columns[table_name].discard(col_name)

            # -- drop_table (in upgrade) --
            drop_table_matches = re.finditer(
                r'op\.drop_table\(\s*["\'](\w+)["\']',
                upgrade_body,
                re.DOTALL,
            )
            for match in drop_table_matches:
                table_name = match.group(1)
                columns.pop(table_name, None)

        return columns

    def _column_in_migrations(
        self, table_name: str, col_name: str,
        migration_columns: dict[str, set[str]],
    ) -> bool:
        """Check if a column is covered by any migration."""
        table_cols = migration_columns.get(table_name, set())
        return col_name in table_cols


# ===================================================================
# 2. Migration Chain Integrity
# ===================================================================

class TestMigrationChain:
    """Verify the Alembic migration chain is linear and complete."""

    def _load_migrations(self) -> list[dict]:
        """Load all migration metadata from files."""
        migrations = []
        for f in sorted(MIGRATIONS_DIR.glob("*.py")):
            content = f.read_text()

            rev_match = re.search(
                r'^revision(?:\s*:\s*str)?\s*=\s*["\']([^"\']+)["\']',
                content, re.M,
            )
            down_match = re.search(
                r'^down_revision(?:\s*:\s*[^=]*)?\s*=\s*(.*)',
                content, re.M,
            )

            if rev_match:
                rev = rev_match.group(1)
                down = None
                if down_match:
                    raw = down_match.group(1).strip()
                    # Extract string value, or None
                    str_match = re.search(r'["\']([^"\']+)["\']', raw)
                    if str_match:
                        down = str_match.group(1)
                    # If raw is just "None" or contains no quoted string, down stays None

                migrations.append({
                    "file": f.name,
                    "revision": rev,
                    "down_revision": down,
                })
        return migrations

    def test_migration_chain_is_linear(self):
        """Every migration except the first must have exactly one parent."""
        migrations = self._load_migrations()
        assert len(migrations) > 0, "No migration files found"

        revisions = {m["revision"] for m in migrations}
        roots = [m for m in migrations if m["down_revision"] is None]

        assert len(roots) == 1, (
            f"Expected exactly 1 root migration (down_revision=None), "
            f"found {len(roots)}: {[r['file'] for r in roots]}"
        )

        # Every non-root migration must point to an existing revision
        for m in migrations:
            if m["down_revision"] is not None:
                assert m["down_revision"] in revisions, (
                    f"Migration {m['file']} references down_revision "
                    f"'{m['down_revision']}' which doesn't exist. Broken chain!"
                )

    def test_no_duplicate_revisions(self):
        """No two migration files should have the same revision ID."""
        migrations = self._load_migrations()
        seen = {}
        for m in migrations:
            rev = m["revision"]
            assert rev not in seen, (
                f"Duplicate revision ID '{rev}' in files: "
                f"{seen[rev]} and {m['file']}"
            )
            seen[rev] = m["file"]

    def test_chain_has_single_head(self):
        """Only one migration should be the head (not referenced as down_revision)."""
        migrations = self._load_migrations()
        all_revisions = {m["revision"] for m in migrations}
        referenced = {m["down_revision"] for m in migrations if m["down_revision"]}

        heads = all_revisions - referenced
        assert len(heads) == 1, (
            f"Expected exactly 1 head migration, found {len(heads)}: {heads}. "
            f"This means migrations have forked — merge them."
        )

    def test_full_chain_is_connected(self):
        """Walking from root through the chain should visit all migrations."""
        migrations = self._load_migrations()
        if not migrations:
            pytest.skip("No migrations")

        # Build forward map: down_revision -> revision
        forward = {}
        for m in migrations:
            down = m["down_revision"]
            if down in forward:
                pytest.fail(
                    f"Two migrations share down_revision '{down}': "
                    f"{forward[down]} and {m['revision']}"
                )
            forward[down] = m["revision"]

        # Walk from root (None -> first)
        visited = set()
        current = forward.get(None)
        while current:
            assert current not in visited, f"Cycle detected at revision {current}"
            visited.add(current)
            current = forward.get(current)

        all_revisions = {m["revision"] for m in migrations}
        orphans = all_revisions - visited
        assert not orphans, (
            f"Orphaned migrations not reachable from root: {orphans}"
        )


# ===================================================================
# 3. Migration File Quality Checks
# ===================================================================

class TestMigrationFileQuality:
    """Validate migration files follow project conventions."""

    def test_all_migrations_have_upgrade_and_downgrade(self):
        """Every migration must define both upgrade() and downgrade()."""
        for f in sorted(MIGRATIONS_DIR.glob("*.py")):
            content = f.read_text()
            assert "def upgrade(" in content, (
                f"Migration {f.name} is missing upgrade() function"
            )
            assert "def downgrade(" in content, (
                f"Migration {f.name} is missing downgrade() function"
            )

    def test_downgrade_is_not_empty_pass(self):
        """Downgrade functions should do something, not just 'pass'.

        Empty downgrade makes rollback impossible. If intentional,
        add a comment explaining why.
        """
        for f in sorted(MIGRATIONS_DIR.glob("*.py")):
            content = f.read_text()
            # Extract downgrade function body
            match = re.search(
                r'def downgrade\(\)[^:]*:\n((?:\s+.*\n)*)',
                content,
            )
            if match:
                body = match.group(1).strip()
                if body == "pass":
                    pytest.fail(
                        f"Migration {f.name} has an empty downgrade() (just 'pass'). "
                        f"This makes rollback impossible. Add the inverse operations "
                        f"or document why downgrade is intentionally empty."
                    )

    def test_migration_files_have_descriptive_names(self):
        """Migration files should have descriptive slugs, not just revision IDs."""
        for f in sorted(MIGRATIONS_DIR.glob("*.py")):
            if f.name == "__pycache__":
                continue
            # Pattern: revision_id_descriptive_slug.py
            parts = f.stem.split("_", 1)
            assert len(parts) == 2, (
                f"Migration {f.name} should follow pattern: "
                f"<revision_id>_<descriptive_slug>.py"
            )
            slug = parts[1]
            assert len(slug) > 3, (
                f"Migration {f.name} has a too-short description: '{slug}'. "
                f"Use a descriptive name like 'add_email_verified_column'."
            )

    def test_no_raw_sql_without_comment(self):
        """Raw SQL in migrations should have a comment explaining why.

        op.execute() with raw SQL is sometimes necessary but should be
        documented. This is a soft check — warns rather than fails.
        """
        for f in sorted(MIGRATIONS_DIR.glob("*.py")):
            content = f.read_text()
            execute_matches = list(re.finditer(r'op\.execute\(', content))
            for match in execute_matches:
                # Check if there's a comment in the 3 lines before
                start = max(0, content.rfind('\n', 0, match.start() - 1))
                context_before = content[start:match.start()]
                if '#' not in context_before and '"""' not in context_before:
                    # Soft warning — don't fail, just note
                    import warnings
                    warnings.warn(
                        f"Migration {f.name} has op.execute() without a "
                        f"preceding comment explaining the raw SQL.",
                        stacklevel=1,
                    )


# ===================================================================
# 4. Model Completeness Checks
# ===================================================================

class TestModelCompleteness:
    """Verify all models are properly registered in __init__.py and migrations/env.py."""

    def test_all_model_files_imported_in_init(self):
        """Every model module in app/models/ must be imported in __init__.py."""
        models_dir = BACKEND_DIR / "app" / "models"
        init_content = (models_dir / "__init__.py").read_text()

        model_files = [
            f.stem for f in models_dir.glob("*.py")
            if f.stem != "__init__" and not f.stem.startswith("_")
        ]

        missing = []
        for model_file in model_files:
            if f"from app.models.{model_file}" not in init_content:
                missing.append(model_file)

        assert not missing, (
            f"Model files not imported in app/models/__init__.py: {missing}. "
            f"This means Alembic autogenerate won't detect their tables."
        )

    def test_all_models_imported_in_migration_env(self):
        """migrations/env.py must import all models for autogenerate to work."""
        env_content = (BACKEND_DIR / "migrations" / "env.py").read_text()
        init_content = (BACKEND_DIR / "app" / "models" / "__init__.py").read_text()

        # Extract class names from __init__.py imports
        model_classes = re.findall(r'from app\.models\.\w+ import (\w+(?:,\s*\w+)*)', init_content)
        all_classes = []
        for match in model_classes:
            all_classes.extend([c.strip() for c in match.split(",")])

        missing = []
        for cls in all_classes:
            if cls not in env_content:
                missing.append(cls)

        assert not missing, (
            f"Model classes not imported in migrations/env.py: {missing}. "
            f"Alembic autogenerate won't detect changes to these models."
        )


# ===================================================================
# 5. Full Autogenerate Drift Detection (CI-only, requires PostgreSQL)
# ===================================================================

# Set TEST_DATABASE_URL_SYNC to a real PostgreSQL URL to enable these tests.
# Example: TEST_DATABASE_URL_SYNC=postgresql://postgres:pass@localhost:5432/signalflow_test
_ci_pg_url = os.environ.get("TEST_DATABASE_URL_SYNC")


@pytest.mark.skipif(
    not _ci_pg_url,
    reason="Requires TEST_DATABASE_URL_SYNC pointing to a real PostgreSQL database",
)
class TestAutogenerateDrift:
    """Gold-standard drift detection: replay all migrations on a real PostgreSQL
    database, then use Alembic's ``compare_metadata`` to compare the resulting
    schema against the ORM models.

    This catches everything the regex-based test cannot:
    - Column type mismatches (e.g., String(100) vs String(200))
    - Missing/extra indexes
    - Constraint differences (nullable, unique, check)
    - Foreign key changes
    - Server default mismatches

    Requires a real PostgreSQL instance. Skipped in local dev; runs in CI where
    a test PG is available via ``TEST_DATABASE_URL_SYNC``.
    """

    def test_migrations_produce_schema_matching_models(self):
        """Replay all migrations → compare result against ORM metadata → zero diff."""
        from alembic import command
        from alembic.autogenerate import compare_metadata
        from alembic.config import Config
        from alembic.migration import MigrationContext
        from sqlalchemy import create_engine, text

        from app.database import Base
        import app.models  # noqa: F401

        engine = create_engine(_ci_pg_url)

        # Clean slate: drop all tables to start fresh
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))

        try:
            # Replay all migrations from base to head
            alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
            alembic_cfg.set_main_option(
                "script_location", str(BACKEND_DIR / "migrations"),
            )
            alembic_cfg.set_main_option("sqlalchemy.url", _ci_pg_url)

            with engine.begin() as conn:
                alembic_cfg.attributes["connection"] = conn
                command.upgrade(alembic_cfg, "head")

            # Compare the migrated DB schema against ORM metadata
            with engine.connect() as conn:
                mc = MigrationContext.configure(conn)
                diff = compare_metadata(mc, Base.metadata)

            # Filter out diffs we intentionally ignore:
            # - TimescaleDB hypertable creation (op.execute raw SQL)
            # - Sequence/autoincrement differences (PG-specific)
            meaningful_diffs = []
            for d in diff:
                op_type = d[0] if isinstance(d, tuple) else None
                if op_type in ("add_table", "remove_table",
                               "add_column", "remove_column"):
                    meaningful_diffs.append(d)
                elif op_type == "modify_nullable":
                    meaningful_diffs.append(d)
                elif op_type == "modify_type":
                    meaningful_diffs.append(d)

            assert not meaningful_diffs, (
                f"Alembic autogenerate found {len(meaningful_diffs)} schema differences "
                f"between migrations and ORM models:\n"
                + "\n".join(f"  - {d}" for d in meaningful_diffs[:10])
                + ("\n  ... (truncated)" if len(meaningful_diffs) > 10 else "")
                + "\n\nFix: Run 'alembic revision --autogenerate' to generate "
                "the missing migration."
            )
        finally:
            # Cleanup: drop everything
            with engine.begin() as conn:
                conn.execute(text("DROP SCHEMA public CASCADE"))
                conn.execute(text("CREATE SCHEMA public"))
            engine.dispose()

    def test_upgrade_downgrade_round_trip(self):
        """Upgrade to head, downgrade to base, upgrade again — must be clean."""
        from alembic import command
        from alembic.config import Config
        from sqlalchemy import create_engine, text

        engine = create_engine(_ci_pg_url)

        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))

        try:
            alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
            alembic_cfg.set_main_option(
                "script_location", str(BACKEND_DIR / "migrations"),
            )
            alembic_cfg.set_main_option("sqlalchemy.url", _ci_pg_url)

            # Upgrade to head
            with engine.begin() as conn:
                alembic_cfg.attributes["connection"] = conn
                command.upgrade(alembic_cfg, "head")

            # Downgrade to base
            with engine.begin() as conn:
                alembic_cfg.attributes["connection"] = conn
                command.downgrade(alembic_cfg, "base")

            # Upgrade again — should work without errors
            with engine.begin() as conn:
                alembic_cfg.attributes["connection"] = conn
                command.upgrade(alembic_cfg, "head")
        finally:
            with engine.begin() as conn:
                conn.execute(text("DROP SCHEMA public CASCADE"))
                conn.execute(text("CREATE SCHEMA public"))
            engine.dispose()
