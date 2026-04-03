# mkg/tests/test_deployment_readiness.py
"""Deployment readiness tests — catches missing dependencies, broken imports,
Dockerfile errors, and app startup failures BEFORE they hit production.

Industry patterns implemented:
1. Deep import smoke test — imports every module in the package tree
2. Dependency completeness audit — scans source imports vs requirements.txt
3. Dockerfile validation — checks COPY paths and required files exist
4. App startup smoke test — boots FastAPI app and hits /health
5. Requirements parsability — ensures requirements.txt is valid
"""

import ast
import importlib
import os
import pkgutil
import re
import sys
from pathlib import Path

import pytest

# ── Paths ──
MKG_ROOT = Path(__file__).resolve().parent.parent  # mkg/
PROJECT_ROOT = MKG_ROOT.parent                      # signalflow/
REQUIREMENTS_FILE = MKG_ROOT / "requirements.txt"
DOCKERFILE = MKG_ROOT / "Dockerfile"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. DEEP IMPORT SMOKE TEST
#    Recursively imports every .py module in mkg/ (excluding tests).
#    If any import fails, a dependency is missing from requirements.txt.
# ═══════════════════════════════════════════════════════════════════════════════

def _discover_all_modules(package_name: str, package_path: str) -> list[str]:
    """Recursively discover all importable modules in a package."""
    modules = []
    for importer, modname, ispkg in pkgutil.walk_packages(
        path=[package_path],
        prefix=f"{package_name}.",
    ):
        # Skip test modules and __pycache__
        if ".tests." in modname or modname.endswith(".tests"):
            continue
        if "conftest" in modname:
            continue
        modules.append(modname)
    return modules


def _get_all_mkg_modules() -> list[str]:
    """Get all importable modules in the mkg package."""
    return _discover_all_modules("mkg", str(MKG_ROOT))


class TestDeepImportSmoke:
    """Every module in mkg/ must be importable without errors.

    This catches:
    - Missing pip dependencies (the aiosqlite bug)
    - Broken relative imports
    - Syntax errors in production code
    - Import-time side effects that crash
    """

    @pytest.fixture(autouse=True)
    def _set_env(self, monkeypatch, tmp_path):
        """Set required env vars so modules don't fail on config."""
        monkeypatch.setenv("MKG_ENV", "test")
        monkeypatch.setenv("MKG_DB_DIR", str(tmp_path))

    @pytest.mark.parametrize("module_name", _get_all_mkg_modules())
    def test_module_imports(self, module_name: str):
        """Each module must import without raising ImportError or ModuleNotFoundError."""
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            pytest.fail(
                f"Module '{module_name}' failed to import: {e}\n"
                f"This likely means a dependency is missing from mkg/requirements.txt"
            )

    def test_at_least_20_modules_discovered(self):
        """Sanity check: we should discover a meaningful number of modules."""
        modules = _get_all_mkg_modules()
        assert len(modules) >= 20, (
            f"Only discovered {len(modules)} modules — expected 20+. "
            f"Check if package __init__.py files are missing."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DEPENDENCY COMPLETENESS AUDIT
#    Scans all source files for import statements and checks each third-party
#    import is satisfied by requirements.txt (directly or transitively).
# ═══════════════════════════════════════════════════════════════════════════════

# Known transitive deps that don't need explicit listing
KNOWN_TRANSITIVE = {
    "starlette",     # via fastapi
    "anyio",         # via starlette
    "typing_extensions",  # via pydantic/fastapi
    "annotated_types",    # via pydantic
    "pluggy",        # via pytest (dev only)
    "sniffio",       # via anyio
    "h11",           # via uvicorn
    "click",         # via uvicorn/celery
    "idna",          # via anyio
    "certifi",       # via httpx
    "httpcore",      # via httpx
}


def _parse_requirements(req_file: Path) -> set[str]:
    """Parse package names from a requirements.txt file."""
    packages = set()
    for line in req_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Extract package name before any version specifier
        match = re.match(r"^([a-zA-Z0-9_-]+)", line)
        if match:
            # Normalize: hyphens → underscores, lowercase
            packages.add(match.group(1).lower().replace("-", "_"))
    return packages


def _scan_imports(source_dir: Path) -> set[str]:
    """Scan all .py files for third-party import names."""
    stdlib_modules = set(sys.stdlib_module_names)
    third_party = set()

    for py_file in source_dir.rglob("*.py"):
        if "tests" in py_file.parts or "__pycache__" in py_file.parts:
            continue
        try:
            tree = ast.parse(py_file.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in stdlib_modules and top != "mkg":
                        third_party.add(top)
            elif isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".")[0]
                if top not in stdlib_modules and top != "mkg":
                    third_party.add(top)

    return third_party


class TestDependencyCompleteness:
    """Every third-party import in source must be in requirements.txt.

    This catches:
    - Adding 'import newlib' without updating requirements.txt
    - Works on fresh installs, not just dev machines with extra packages
    """

    def test_all_imports_covered(self):
        """Every third-party import must map to a requirements.txt entry."""
        required = _parse_requirements(REQUIREMENTS_FILE)
        imported = _scan_imports(MKG_ROOT)

        # Remove known transitive deps
        imported -= KNOWN_TRANSITIVE

        # Check each import is satisfied
        # Map common import-name → package-name mismatches
        import_to_package = {
            "lxml": "lxml",
            "yaml": "pyyaml",
            "cv2": "opencv_python",
            "PIL": "pillow",
            "sklearn": "scikit_learn",
            "bs4": "beautifulsoup4",
            "dotenv": "python_dotenv",
        }

        missing = set()
        for imp in imported:
            pkg_name = import_to_package.get(imp, imp).lower().replace("-", "_")
            if pkg_name not in required:
                missing.add(f"{imp} (expected '{pkg_name}' in requirements.txt)")

        assert not missing, (
            f"Third-party imports NOT covered by mkg/requirements.txt:\n"
            + "\n".join(f"  - {m}" for m in sorted(missing))
            + "\n\nFix: add these packages to mkg/requirements.txt"
        )

    def test_requirements_file_exists(self):
        """requirements.txt must exist."""
        assert REQUIREMENTS_FILE.exists(), f"Missing {REQUIREMENTS_FILE}"

    def test_requirements_file_parseable(self):
        """requirements.txt must contain at least one valid package."""
        packages = _parse_requirements(REQUIREMENTS_FILE)
        assert len(packages) >= 5, (
            f"Only {len(packages)} packages found in requirements.txt — "
            f"expected at least 5"
        )

    def test_no_duplicate_requirements(self):
        """No package should be listed twice."""
        seen = {}
        for line in REQUIREMENTS_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            match = re.match(r"^([a-zA-Z0-9_-]+)", line)
            if match:
                name = match.group(1).lower()
                if name in seen:
                    pytest.fail(
                        f"Duplicate requirement: '{name}' at lines "
                        f"{seen[name]} and {line}"
                    )
                seen[name] = line


# ═══════════════════════════════════════════════════════════════════════════════
# 3. DOCKERFILE VALIDATION
#    Checks that Dockerfile references valid paths and copies required files.
# ═══════════════════════════════════════════════════════════════════════════════

class TestDockerfileValidation:
    """Dockerfile must reference files that actually exist.

    This catches:
    - COPY paths pointing to wrong locations (the requirements.txt bug)
    - Missing directories in COPY commands
    - Dockerfile syntax issues detectable statically
    """

    def test_dockerfile_exists(self):
        """Dockerfile must exist."""
        assert DOCKERFILE.exists(), f"Missing {DOCKERFILE}"

    def test_copy_sources_exist(self):
        """Every COPY source path in the Dockerfile must exist in the project.

        The Dockerfile build context is the project root (.), so paths
        are relative to PROJECT_ROOT.
        """
        content = DOCKERFILE.read_text()
        # Match COPY <source> <dest> (skip multi-stage --from= or --chown)
        copy_pattern = re.compile(
            r"^COPY\s+(?:--[a-z]+=\S+\s+)*(\S+)\s+\S+",
            re.MULTILINE,
        )
        for match in copy_pattern.finditer(content):
            source = match.group(1)
            # Skip build arg references like $VAR
            if source.startswith("$"):
                continue
            source_path = PROJECT_ROOT / source
            assert source_path.exists(), (
                f"Dockerfile COPY source '{source}' does not exist at "
                f"{source_path}\n"
                f"Build context is project root: {PROJECT_ROOT}\n"
                f"Line: {match.group(0)}"
            )

    def test_exposes_port_8001(self):
        """MKG Dockerfile should expose port 8001."""
        content = DOCKERFILE.read_text()
        assert "EXPOSE 8001" in content, "Dockerfile must EXPOSE 8001"

    def test_uses_python_3_11_plus(self):
        """Base image should use Python 3.11+."""
        content = DOCKERFILE.read_text()
        # Match python:3.XX
        py_match = re.search(r"python:3\.(\d+)", content)
        assert py_match, "Dockerfile must use a python:3.x base image"
        minor = int(py_match.group(1))
        assert minor >= 11, f"Python 3.{minor} found, need 3.11+"

    def test_pythonpath_set(self):
        """PYTHONPATH must be set to /app for mkg imports to work."""
        content = DOCKERFILE.read_text()
        assert "PYTHONPATH" in content, "Dockerfile must set PYTHONPATH"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. APP STARTUP SMOKE TEST
#    Actually creates the FastAPI app and tests /health endpoint.
# ═══════════════════════════════════════════════════════════════════════════════

class TestAppStartupSmoke:
    """The FastAPI app must boot and serve /health.

    This catches:
    - Broken service wiring in dependencies.py
    - Missing router registrations
    - Import errors in route modules
    - Bad middleware configuration
    """

    @pytest.fixture
    async def client(self, tmp_path, monkeypatch):
        """Create a test client with the real app, triggering lifespan."""
        monkeypatch.setenv("MKG_ENV", "test")
        monkeypatch.setenv("MKG_DB_DIR", str(tmp_path))
        monkeypatch.setenv("MKG_API_KEY", "test-key")

        from contextlib import asynccontextmanager

        from httpx import ASGITransport, AsyncClient
        from mkg.api.app import create_app
        from mkg.api.dependencies import init_container

        app = create_app()
        # Manually trigger lifespan since ASGITransport doesn't
        container = init_container()
        await container.startup()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

        await container.shutdown()

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_200(self, client):
        """GET /health must return 200 with status=healthy."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_has_version(self, client):
        """Health response must include version."""
        resp = await client.get("/health")
        data = resp.json()
        assert "version" in data

    @pytest.mark.asyncio
    async def test_docs_endpoint_available(self, client):
        """OpenAPI docs must be accessible."""
        resp = await client.get("/docs")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_openapi_schema(self, client):
        """OpenAPI schema must be valid JSON."""
        resp = await client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert "paths" in schema
        assert len(schema["paths"]) > 0, "No API routes registered"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. DOCKER-COMPOSE VALIDATION
#    Checks the docker-compose.mkg.yml references valid Dockerfiles and paths.
# ═══════════════════════════════════════════════════════════════════════════════

class TestDockerComposeValidation:
    """docker-compose.mkg.yml must reference valid files and paths."""

    @pytest.fixture
    def compose_content(self) -> str:
        compose_file = PROJECT_ROOT / "docker-compose.mkg.yml"
        assert compose_file.exists(), "docker-compose.mkg.yml missing"
        return compose_file.read_text()

    def test_dockerfile_path_valid(self, compose_content: str):
        """The dockerfile path in compose must point to a real file."""
        # Find all dockerfile references
        for match in re.finditer(r"dockerfile:\s*(\S+)", compose_content):
            df_path = match.group(1)
            full_path = PROJECT_ROOT / df_path
            assert full_path.exists(), (
                f"docker-compose.mkg.yml references '{df_path}' "
                f"but {full_path} does not exist"
            )

    def test_volume_source_dirs_exist(self, compose_content: str):
        """Volume mount source directories must exist."""
        # Match ./path:/container/path patterns
        for match in re.finditer(r"-\s*\./([^:]+):", compose_content):
            host_path = match.group(1)
            full_path = PROJECT_ROOT / host_path
            assert full_path.exists(), (
                f"Volume mount source './{host_path}' does not exist "
                f"at {full_path}"
            )

    def test_mkg_api_exposes_8001(self, compose_content: str):
        """MKG API service should map port 8001."""
        assert "8001:8001" in compose_content, "MKG API must expose port 8001"


# ═══════════════════════════════════════════════════════════════════════════════
# 6. RESEARCH LIBRARY VALIDATION
#    Ensures the core/ research documents are complete, linked, and servable.
# ═══════════════════════════════════════════════════════════════════════════════

# The 7 research documents that form MKG's intellectual moat
REQUIRED_RESEARCH_DOCS = [
    "MKG_Problem_Definition.html",
    "MKG_Problem_Research-2.html",
    "MKG_Market_Research.html",
    "MKG_Competitor_Deep_Dive.html",
    "MKG_Niche_Definition_FINAL.html",
    "MKG_SupplyChain_Application.html",
    "MKG_Tribal_Knowledge_Gap.html",
    "MKG_Complete_Thesis.html",
]

RESEARCH_DIR = PROJECT_ROOT / "core"


class TestResearchLibrary:
    """The research intelligence library must be complete and servable.

    These documents are the intellectual moat of MKG. Every one must:
    - Exist on disk
    - Be valid HTML
    - Be referenced from the index page
    - Be copied into the Docker image
    """

    def test_core_directory_exists(self):
        """core/ directory must exist."""
        assert RESEARCH_DIR.is_dir(), f"Missing {RESEARCH_DIR}"

    def test_index_page_exists(self):
        """core/index.html must exist as the research hub landing page."""
        index = RESEARCH_DIR / "index.html"
        assert index.exists(), (
            "Missing core/index.html — the research library needs a landing page"
        )

    @pytest.mark.parametrize("doc_name", REQUIRED_RESEARCH_DOCS)
    def test_research_doc_exists(self, doc_name: str):
        """Each required research document must exist."""
        doc_path = RESEARCH_DIR / doc_name
        assert doc_path.exists(), (
            f"Missing research document: {doc_path}\n"
            f"This is a core moat document — it must not be deleted."
        )

    @pytest.mark.parametrize("doc_name", REQUIRED_RESEARCH_DOCS)
    def test_research_doc_is_valid_html(self, doc_name: str):
        """Each research document must be valid HTML (has DOCTYPE and title)."""
        content = (RESEARCH_DIR / doc_name).read_text()
        assert "<!DOCTYPE html>" in content, f"{doc_name} missing DOCTYPE"
        assert "<title>" in content, f"{doc_name} missing <title> tag"

    @pytest.mark.parametrize("doc_name", REQUIRED_RESEARCH_DOCS)
    def test_research_doc_linked_from_index(self, doc_name: str):
        """Each research document must be linked from index.html."""
        index_content = (RESEARCH_DIR / "index.html").read_text()
        assert doc_name in index_content, (
            f"index.html does not link to {doc_name}\n"
            f"All research documents must be discoverable from the index."
        )

    def test_index_has_all_docs(self):
        """Index page must reference every required research document."""
        index_content = (RESEARCH_DIR / "index.html").read_text()
        missing = [
            doc for doc in REQUIRED_RESEARCH_DOCS
            if doc not in index_content
        ]
        assert not missing, (
            f"Index page missing links to: {missing}"
        )

    def test_dockerfile_copies_core(self):
        """Dockerfile must COPY core/ into the image."""
        content = DOCKERFILE.read_text()
        assert "core/" in content, (
            "Dockerfile does not COPY core/ — research docs won't be "
            "available in the container"
        )

    def test_research_docs_not_empty(self):
        """No research document should be empty or trivially small."""
        for doc_name in REQUIRED_RESEARCH_DOCS:
            doc_path = RESEARCH_DIR / doc_name
            size = doc_path.stat().st_size
            assert size > 10000, (
                f"{doc_name} is only {size} bytes — expected substantial "
                f"research content (>10KB)"
            )

    @pytest.mark.asyncio
    async def test_research_endpoint_serves_index(self, tmp_path, monkeypatch):
        """GET /research/ must serve the index page."""
        monkeypatch.setenv("MKG_ENV", "test")
        monkeypatch.setenv("MKG_DB_DIR", str(tmp_path))
        monkeypatch.setenv("MKG_API_KEY", "test-key")

        from httpx import ASGITransport, AsyncClient
        from mkg.api.app import create_app
        from mkg.api.dependencies import init_container

        app = create_app()
        container = init_container()
        await container.startup()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/research/")
            assert resp.status_code == 200, (
                f"GET /research/ returned {resp.status_code} — "
                f"static file mount may be broken"
            )
            assert "MKG" in resp.text, "Research index page should mention MKG"
            assert "Research" in resp.text

        await container.shutdown()
