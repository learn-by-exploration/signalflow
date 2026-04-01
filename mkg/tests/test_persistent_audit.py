# mkg/tests/test_persistent_audit.py
"""Tests for persistent SQLite-backed audit and provenance storage.

Iterations 5-8: Audit and provenance data must survive restarts.
"""

import os
import tempfile
import pytest


class TestSQLiteAuditStorage:
    """AuditLogger backed by SQLite for persistence."""

    @pytest.mark.asyncio
    async def test_create_and_query(self):
        from mkg.infrastructure.sqlite.audit_storage import SQLiteAuditStorage
        from mkg.domain.services.audit_logger import AuditAction

        with tempfile.TemporaryDirectory() as d:
            storage = SQLiteAuditStorage(db_path=os.path.join(d, "audit.db"))
            await storage.initialize()

            await storage.log(
                action=AuditAction.ENTITY_CREATED,
                actor="pipeline",
                target_id="e1",
                target_type="entity",
                details={"name": "TSMC"},
            )

            entries = await storage.get_entries()
            assert len(entries) == 1
            assert entries[0]["action"] == "entity_created"
            assert entries[0]["target_id"] == "e1"
            await storage.close()

    @pytest.mark.asyncio
    async def test_persists_across_reopens(self):
        from mkg.infrastructure.sqlite.audit_storage import SQLiteAuditStorage
        from mkg.domain.services.audit_logger import AuditAction

        with tempfile.TemporaryDirectory() as d:
            db_path = os.path.join(d, "audit.db")

            # Write
            s1 = SQLiteAuditStorage(db_path=db_path)
            await s1.initialize()
            await s1.log(AuditAction.ENTITY_CREATED, "pipeline", "e1", "entity", {"n": "TSMC"})
            await s1.log(AuditAction.EDGE_CREATED, "pipeline", "ed1", "edge", {"r": "SUPPLIES_TO"})
            await s1.close()

            # Reopen and verify
            s2 = SQLiteAuditStorage(db_path=db_path)
            await s2.initialize()
            entries = await s2.get_entries()
            assert len(entries) == 2
            await s2.close()

    @pytest.mark.asyncio
    async def test_filter_by_action(self):
        from mkg.infrastructure.sqlite.audit_storage import SQLiteAuditStorage
        from mkg.domain.services.audit_logger import AuditAction

        with tempfile.TemporaryDirectory() as d:
            s = SQLiteAuditStorage(db_path=os.path.join(d, "audit.db"))
            await s.initialize()
            await s.log(AuditAction.ENTITY_CREATED, "pipeline", "e1", "entity", {})
            await s.log(AuditAction.EDGE_CREATED, "pipeline", "ed1", "edge", {})
            await s.log(AuditAction.ENTITY_UPDATED, "pipeline", "e1", "entity", {})

            entity_entries = await s.get_entries(action=AuditAction.ENTITY_CREATED)
            assert len(entity_entries) == 1
            await s.close()

    @pytest.mark.asyncio
    async def test_filter_by_target_id(self):
        from mkg.infrastructure.sqlite.audit_storage import SQLiteAuditStorage
        from mkg.domain.services.audit_logger import AuditAction

        with tempfile.TemporaryDirectory() as d:
            s = SQLiteAuditStorage(db_path=os.path.join(d, "audit.db"))
            await s.initialize()
            await s.log(AuditAction.ENTITY_CREATED, "pipeline", "e1", "entity", {})
            await s.log(AuditAction.ENTITY_CREATED, "pipeline", "e2", "entity", {})

            entries = await s.get_entries(target_id="e1")
            assert len(entries) == 1
            assert entries[0]["target_id"] == "e1"
            await s.close()

    @pytest.mark.asyncio
    async def test_export_report(self):
        from mkg.infrastructure.sqlite.audit_storage import SQLiteAuditStorage
        from mkg.domain.services.audit_logger import AuditAction

        with tempfile.TemporaryDirectory() as d:
            s = SQLiteAuditStorage(db_path=os.path.join(d, "audit.db"))
            await s.initialize()
            await s.log(AuditAction.ENTITY_CREATED, "pipeline", "e1", "entity", {})
            await s.log(AuditAction.EDGE_CREATED, "pipeline", "ed1", "edge", {})
            await s.log(AuditAction.PROPAGATION_RUN, "pipeline", "p1", "propagation", {})

            report = await s.export_report()
            assert report["total_entries"] == 3
            assert "actions_breakdown" in report
            await s.close()

    @pytest.mark.asyncio
    async def test_limit_entries(self):
        from mkg.infrastructure.sqlite.audit_storage import SQLiteAuditStorage
        from mkg.domain.services.audit_logger import AuditAction

        with tempfile.TemporaryDirectory() as d:
            s = SQLiteAuditStorage(db_path=os.path.join(d, "audit.db"))
            await s.initialize()
            for i in range(50):
                await s.log(AuditAction.ENTITY_CREATED, "pipeline", f"e-{i}", "entity", {})

            entries = await s.get_entries(limit=10)
            assert len(entries) == 10
            await s.close()


class TestSQLiteProvenanceStorage:
    """ProvenanceTracker backed by SQLite for persistence."""

    @pytest.mark.asyncio
    async def test_record_and_retrieve_step(self):
        from mkg.infrastructure.sqlite.provenance_storage import SQLiteProvenanceStorage

        with tempfile.TemporaryDirectory() as d:
            s = SQLiteProvenanceStorage(db_path=os.path.join(d, "prov.db"))
            await s.initialize()

            await s.record_step("art-001", "extraction", {"source": "reuters"}, {"entities": 3})
            records = await s.get_records("art-001")
            assert len(records) == 1
            assert records[0]["step"] == "extraction"
            await s.close()

    @pytest.mark.asyncio
    async def test_persists_across_reopens(self):
        from mkg.infrastructure.sqlite.provenance_storage import SQLiteProvenanceStorage

        with tempfile.TemporaryDirectory() as d:
            db_path = os.path.join(d, "prov.db")

            s1 = SQLiteProvenanceStorage(db_path=db_path)
            await s1.initialize()
            await s1.record_step("art-001", "extraction", {"source": "reuters"}, {"entities": 3})
            await s1.record_entity_origin("e1", "TSMC", "art-001", "tier_1", 0.95)
            await s1.close()

            s2 = SQLiteProvenanceStorage(db_path=db_path)
            await s2.initialize()
            records = await s2.get_records("art-001")
            assert len(records) == 1
            articles = await s2.get_entity_articles("e1")
            assert len(articles) == 1
            await s2.close()

    @pytest.mark.asyncio
    async def test_entity_origin_tracking(self):
        from mkg.infrastructure.sqlite.provenance_storage import SQLiteProvenanceStorage

        with tempfile.TemporaryDirectory() as d:
            s = SQLiteProvenanceStorage(db_path=os.path.join(d, "prov.db"))
            await s.initialize()
            await s.record_entity_origin("e1", "TSMC", "art-001", "tier_1", 0.95)
            await s.record_entity_origin("e1", "TSMC", "art-002", "tier_3", 0.80)

            articles = await s.get_entity_articles("e1")
            assert len(articles) == 2
            await s.close()

    @pytest.mark.asyncio
    async def test_article_lineage(self):
        from mkg.infrastructure.sqlite.provenance_storage import SQLiteProvenanceStorage

        with tempfile.TemporaryDirectory() as d:
            s = SQLiteProvenanceStorage(db_path=os.path.join(d, "prov.db"))
            await s.initialize()
            await s.record_step("art-001", "extraction", {"source": "reuters"}, {"entities": 2})
            await s.record_step("art-001", "verification", {}, {"verified": 2})
            await s.record_entity_origin("e1", "TSMC", "art-001", "tier_1", 0.95)

            lineage = await s.get_article_lineage("art-001")
            assert len(lineage["steps"]) == 2
            assert len(lineage["entities_created"]) == 1
            await s.close()

    @pytest.mark.asyncio
    async def test_summary(self):
        from mkg.infrastructure.sqlite.provenance_storage import SQLiteProvenanceStorage

        with tempfile.TemporaryDirectory() as d:
            s = SQLiteProvenanceStorage(db_path=os.path.join(d, "prov.db"))
            await s.initialize()
            await s.record_step("art-001", "extraction", {}, {})
            await s.record_step("art-002", "extraction", {}, {})
            await s.record_entity_origin("e1", "TSMC", "art-001", "tier_1", 0.95)

            summary = await s.get_summary()
            assert summary["total_articles_processed"] == 2
            assert summary["total_entities_tracked"] == 1
            await s.close()
