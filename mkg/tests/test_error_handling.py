# mkg/tests/test_error_handling.py
"""Error handling and edge case tests for persistent services and API.

Verifies graceful handling of:
1. Corrupted or invalid inputs
2. Missing/unavailable storage
3. Malformed API requests
4. Edge cases in audit/provenance queries
"""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from mkg.api import dependencies as deps
from mkg.domain.services.audit_logger import AuditAction


@pytest.fixture
async def error_client(tmp_path):
    """Client for error-handling tests."""
    os.environ["MKG_DB_DIR"] = str(tmp_path)

    from mkg.api.app import create_app

    app = create_app()
    container = deps.init_container()
    await container.startup()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, container

    await container.shutdown()
    deps._container = None
    os.environ.pop("MKG_DB_DIR", None)


class TestAuditLoggerEdgeCases:
    """Edge cases for PersistentAuditLogger."""

    def test_empty_details(self, tmp_path):
        """Logging with None details should use empty dict."""
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger
        logger = PersistentAuditLogger(db_path=str(tmp_path / "audit.db"))
        logger.log(AuditAction.ENTITY_CREATED, "p", "a1", "article", None)
        entries = logger.get_entries()
        assert len(entries) == 1
        assert entries[0]["details"] == {}

    def test_unicode_in_details(self, tmp_path):
        """Unicode characters in details should be preserved."""
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger
        logger = PersistentAuditLogger(db_path=str(tmp_path / "audit.db"))
        logger.log(AuditAction.ENTITY_CREATED, "p", "a1", "article",
                   {"name": "टाटा कंसल्टेंसी", "symbol": "TCS.NS"})
        entries = logger.get_entries()
        assert entries[0]["details"]["name"] == "टाटा कंसल्टेंसी"

    def test_large_details(self, tmp_path):
        """Large details dict should not cause errors."""
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger
        logger = PersistentAuditLogger(db_path=str(tmp_path / "audit.db"))
        big_details = {f"key_{i}": f"value_{i}" * 100 for i in range(100)}
        logger.log(AuditAction.ENTITY_CREATED, "p", "a1", "article", big_details)
        entries = logger.get_entries()
        assert len(entries) == 1
        assert len(entries[0]["details"]) == 100

    def test_get_entries_no_match(self, tmp_path):
        """Querying with non-existent filters returns empty list."""
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger
        logger = PersistentAuditLogger(db_path=str(tmp_path / "audit.db"))
        entries = logger.get_entries(target_id="nonexistent")
        assert entries == []

    def test_export_report_empty_db(self, tmp_path):
        """Export report on empty DB returns zeros."""
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger
        logger = PersistentAuditLogger(db_path=str(tmp_path / "audit.db"))
        report = logger.export_report()
        assert report["total_entries"] == 0
        assert report["actions_breakdown"] == {}


class TestProvenanceEdgeCases:
    """Edge cases for PersistentProvenanceTracker."""

    def test_empty_inputs_outputs(self, tmp_path):
        """Recording with empty dicts should work."""
        from mkg.infrastructure.persistent.provenance_tracker import PersistentProvenanceTracker
        tracker = PersistentProvenanceTracker(db_path=str(tmp_path / "prov.db"))
        tracker.record_step("art-1", "test", {}, {})
        records = tracker.get_records("art-1")
        assert len(records) == 1

    def test_nonexistent_article_lineage(self, tmp_path):
        """Querying lineage for non-existent article returns empty."""
        from mkg.infrastructure.persistent.provenance_tracker import PersistentProvenanceTracker
        tracker = PersistentProvenanceTracker(db_path=str(tmp_path / "prov.db"))
        lineage = tracker.get_article_lineage("nonexistent")
        assert lineage["steps"] == []
        assert lineage["entities_created"] == []

    def test_nonexistent_entity_articles(self, tmp_path):
        """Querying articles for non-existent entity returns empty."""
        from mkg.infrastructure.persistent.provenance_tracker import PersistentProvenanceTracker
        tracker = PersistentProvenanceTracker(db_path=str(tmp_path / "prov.db"))
        articles = tracker.get_entity_articles("nonexistent")
        assert articles == []

    def test_summary_empty_db(self, tmp_path):
        """Summary on empty DB returns zeros."""
        from mkg.infrastructure.persistent.provenance_tracker import PersistentProvenanceTracker
        tracker = PersistentProvenanceTracker(db_path=str(tmp_path / "prov.db"))
        summary = tracker.get_summary()
        assert summary["total_articles_processed"] == 0
        assert summary["total_steps_recorded"] == 0


class TestAPIErrorHandling:
    """Error handling in API endpoints."""

    @pytest.mark.asyncio
    async def test_invalid_pii_request_body(self, error_client):
        """POST /pii/scan with invalid body returns 422."""
        client, _ = error_client
        resp = await client.post("/api/v1/pii/scan", json={"wrong_field": "text"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_enrich_request_body(self, error_client):
        """POST /signals/enrich with missing symbol returns 422."""
        client, _ = error_client
        resp = await client.post("/api/v1/signals/enrich", json={"pipeline_result": {}})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_audit_action_filter(self, error_client):
        """GET /audit/log with invalid action returns all entries."""
        client, container = error_client
        container.audit_logger.log(AuditAction.ENTITY_CREATED, "p", "a1", "article", {})
        resp = await client.get("/api/v1/audit/log?action=invalid_action")
        assert resp.status_code == 200
        # Invalid action should be ignored, returning all entries
        entries = resp.json()["data"]
        assert len(entries) >= 1

    @pytest.mark.asyncio
    async def test_audit_log_limit_clamped(self, error_client):
        """GET /audit/log with limit=0 should return 422 (min=1)."""
        client, _ = error_client
        resp = await client.get("/api/v1/audit/log?limit=0")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_lineage_nonexistent_entity(self, error_client):
        """GET /lineage/entity/nonexistent returns 200 with empty data."""
        client, _ = error_client
        resp = await client.get("/api/v1/lineage/entity/nonexistent-entity-id")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_lineage_nonexistent_article(self, error_client):
        """GET /lineage/article/nonexistent returns 200 with empty steps."""
        client, _ = error_client
        resp = await client.get("/api/v1/lineage/article/nonexistent-article-id")
        assert resp.status_code == 200
        lineage = resp.json()["data"]
        assert lineage["steps"] == []

    @pytest.mark.asyncio
    async def test_pii_scan_empty_text(self, error_client):
        """POST /pii/scan with empty text returns no PII."""
        client, _ = error_client
        resp = await client.post("/api/v1/pii/scan", json={"text": ""})
        assert resp.status_code == 200
        assert resp.json()["data"]["has_pii"] is False

    @pytest.mark.asyncio
    async def test_enrich_failed_pipeline_result(self, error_client):
        """Enriching a failed pipeline result returns safe defaults."""
        client, _ = error_client
        resp = await client.post("/api/v1/signals/enrich", json={
            "symbol": "TEST",
            "pipeline_result": {"status": "failed", "error": "timeout"},
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["has_material_impact"] is False
        assert data["supply_chain_risk"] == 0.0
