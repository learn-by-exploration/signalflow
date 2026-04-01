# mkg/tests/test_performance.py
"""Performance tests for persistent storage and pipeline.

Verifies:
1. 1000+ audit entries write and query within acceptable time
2. Bulk provenance recording performance
3. API endpoint response latency under load
"""

import os
import time

import pytest
from httpx import ASGITransport, AsyncClient

from mkg.api import dependencies as deps
from mkg.domain.services.audit_logger import AuditAction


class TestAuditPerformance:
    """Performance tests for PersistentAuditLogger."""

    def test_1000_audit_writes(self, tmp_path):
        """1000 audit writes should complete in under 5 seconds."""
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger

        db = str(tmp_path / "audit_perf.db")
        logger = PersistentAuditLogger(db_path=db)

        start = time.time()
        for i in range(1000):
            logger.log(
                AuditAction.ENTITY_CREATED,
                "pipeline",
                f"art-{i}",
                "article",
                {"entities_created": i % 10, "source": "test"},
            )
        elapsed = time.time() - start

        assert elapsed < 5.0, f"1000 writes took {elapsed:.2f}s (budget: 5s)"

    def test_query_1000_entries(self, tmp_path):
        """Querying 1000 entries should complete in under 1 second."""
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger

        db = str(tmp_path / "audit_query.db")
        logger = PersistentAuditLogger(db_path=db)

        for i in range(1000):
            logger.log(AuditAction.ENTITY_CREATED, "p", f"a-{i}", "article", {})

        start = time.time()
        entries = logger.get_entries(limit=1000)
        elapsed = time.time() - start

        assert len(entries) == 1000
        assert elapsed < 1.0, f"Query took {elapsed:.2f}s (budget: 1s)"

    def test_filtered_query_performance(self, tmp_path):
        """Filtered query on 1000 entries should be fast."""
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger

        db = str(tmp_path / "audit_filter.db")
        logger = PersistentAuditLogger(db_path=db)

        for i in range(500):
            logger.log(AuditAction.ENTITY_CREATED, "p", f"a-{i}", "article", {})
        for i in range(500):
            logger.log(AuditAction.EDGE_CREATED, "p", f"a-{i}", "article", {})

        start = time.time()
        entries = logger.get_entries(action=AuditAction.ENTITY_CREATED, limit=1000)
        elapsed = time.time() - start

        assert len(entries) == 500
        assert elapsed < 0.5, f"Filtered query took {elapsed:.2f}s (budget: 0.5s)"

    def test_export_report_1000_entries(self, tmp_path):
        """Export report with 1000 entries should complete quickly."""
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger

        db = str(tmp_path / "audit_report.db")
        logger = PersistentAuditLogger(db_path=db)

        for i in range(1000):
            action = AuditAction.ENTITY_CREATED if i % 2 == 0 else AuditAction.EDGE_CREATED
            logger.log(action, "p", f"a-{i}", "article", {})

        start = time.time()
        report = logger.export_report()
        elapsed = time.time() - start

        assert report["total_entries"] == 1000
        assert elapsed < 0.5, f"Report took {elapsed:.2f}s (budget: 0.5s)"


class TestProvenancePerformance:
    """Performance tests for PersistentProvenanceTracker."""

    def test_1000_provenance_steps(self, tmp_path):
        """1000 provenance step writes should complete in under 5 seconds."""
        from mkg.infrastructure.persistent.provenance_tracker import PersistentProvenanceTracker

        db = str(tmp_path / "prov_perf.db")
        tracker = PersistentProvenanceTracker(db_path=db)

        start = time.time()
        for i in range(1000):
            tracker.record_step(
                f"art-{i % 100}",
                "extraction",
                {"source": "test"},
                {"entities": i % 10},
            )
        elapsed = time.time() - start

        assert elapsed < 5.0, f"1000 steps took {elapsed:.2f}s (budget: 5s)"

    def test_article_lineage_query(self, tmp_path):
        """Querying lineage for an article with 20 steps should be fast."""
        from mkg.infrastructure.persistent.provenance_tracker import PersistentProvenanceTracker

        db = str(tmp_path / "prov_lineage.db")
        tracker = PersistentProvenanceTracker(db_path=db)

        for i in range(20):
            tracker.record_step("art-big", f"step_{i}", {"i": i}, {"out": i})
        for i in range(10):
            tracker.record_entity_origin(f"ent-{i}", f"Entity_{i}", "art-big", "regex", 0.9)

        start = time.time()
        lineage = tracker.get_article_lineage("art-big")
        elapsed = time.time() - start

        assert len(lineage["steps"]) == 20
        assert len(lineage["entities_created"]) == 10
        assert elapsed < 0.5, f"Lineage query took {elapsed:.2f}s (budget: 0.5s)"

    def test_summary_performance(self, tmp_path):
        """Summary with 1000+ records should be fast."""
        from mkg.infrastructure.persistent.provenance_tracker import PersistentProvenanceTracker

        db = str(tmp_path / "prov_summary.db")
        tracker = PersistentProvenanceTracker(db_path=db)

        for i in range(500):
            tracker.record_step(f"art-{i}", "extraction", {}, {})
        for i in range(200):
            tracker.record_entity_origin(f"ent-{i}", f"E{i}", f"art-{i}", "regex", 0.8)

        start = time.time()
        summary = tracker.get_summary()
        elapsed = time.time() - start

        assert summary["total_articles_processed"] == 500
        assert summary["total_entities_tracked"] == 200
        assert elapsed < 0.5, f"Summary took {elapsed:.2f}s (budget: 0.5s)"


class TestAPIPerformance:
    """API endpoint performance tests."""

    @pytest.fixture
    async def loaded_client(self, tmp_path):
        """Client with pre-loaded data for performance testing."""
        os.environ["MKG_DB_DIR"] = str(tmp_path)

        from mkg.api.app import create_app

        app = create_app()
        container = deps.init_container()
        await container.startup()

        # Pre-load 100 entries
        for i in range(100):
            container.audit_logger.log(
                AuditAction.ENTITY_CREATED, "pipeline", f"art-{i}", "article",
                {"entities_created": i % 10},
            )
            container.provenance_tracker.record_step(
                f"art-{i}", "extraction", {"source": "test"}, {"entities": i},
            )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client

        await container.shutdown()
        deps._container = None
        os.environ.pop("MKG_DB_DIR", None)

    @pytest.mark.asyncio
    async def test_audit_log_endpoint_latency(self, loaded_client):
        """GET /audit/log with 100 entries should respond under 200ms."""
        start = time.time()
        resp = await loaded_client.get("/api/v1/audit/log?limit=100")
        elapsed = time.time() - start

        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 100
        assert elapsed < 0.2, f"Audit log endpoint took {elapsed:.3f}s (budget: 0.2s)"

    @pytest.mark.asyncio
    async def test_audit_report_endpoint_latency(self, loaded_client):
        """GET /audit/report should respond under 100ms."""
        start = time.time()
        resp = await loaded_client.get("/api/v1/audit/report")
        elapsed = time.time() - start

        assert resp.status_code == 200
        assert elapsed < 0.1, f"Audit report endpoint took {elapsed:.3f}s (budget: 0.1s)"

    @pytest.mark.asyncio
    async def test_compliance_report_endpoint_latency(self, loaded_client):
        """GET /compliance/report should respond under 100ms."""
        start = time.time()
        resp = await loaded_client.get("/api/v1/compliance/report")
        elapsed = time.time() - start

        assert resp.status_code == 200
        assert elapsed < 0.1, f"Compliance report took {elapsed:.3f}s (budget: 0.1s)"
