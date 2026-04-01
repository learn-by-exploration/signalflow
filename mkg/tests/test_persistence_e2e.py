# mkg/tests/test_persistence_e2e.py
"""End-to-end persistence tests.

Verifies that:
1. Pipeline provenance/audit data is persisted to SQLite
2. API endpoints return persisted data
3. Data survives ServiceContainer recreation (simulates restart)
"""

import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient

from mkg.api import dependencies as deps


@pytest.fixture
async def persisted_client(tmp_path):
    """Create a test client with a temporary SQLite directory for persistence."""
    # Set MKG_DB_DIR to a temp directory so persistence is testable
    os.environ["MKG_DB_DIR"] = str(tmp_path)

    from mkg.api.app import create_app

    app = create_app()
    container = deps.init_container()
    await container.startup()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, container, tmp_path

    await container.shutdown()
    deps._container = None
    os.environ.pop("MKG_DB_DIR", None)


class TestPipelineAuditPersistence:
    """Verify audit data from pipeline is persisted and queryable via API."""

    @pytest.mark.asyncio
    async def test_audit_log_empty_initially(self, persisted_client):
        client, container, _ = persisted_client
        resp = await client.get("/api/v1/audit/log")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_audit_log_from_pipeline(self, persisted_client):
        """Process an article through pipeline, verify audit entries appear in API."""
        client, container, _ = persisted_client

        # Process an article to generate audit entries
        from mkg.domain.services.audit_logger import AuditAction
        container.audit_logger.log(
            action=AuditAction.ENTITY_CREATED,
            actor="pipeline",
            target_id="test-article-1",
            target_type="article",
            details={"entities_created": 5, "source": "test"},
        )

        resp = await client.get("/api/v1/audit/log")
        assert resp.status_code == 200
        entries = resp.json()["data"]
        assert len(entries) >= 1
        assert entries[0]["action"] == "entity_created"
        assert entries[0]["details"]["entities_created"] == 5

    @pytest.mark.asyncio
    async def test_audit_report_includes_entries(self, persisted_client):
        client, container, _ = persisted_client

        from mkg.domain.services.audit_logger import AuditAction
        container.audit_logger.log(AuditAction.ENTITY_CREATED, "p", "a1", "article", {})
        container.audit_logger.log(AuditAction.EDGE_CREATED, "p", "a1", "article", {})

        resp = await client.get("/api/v1/audit/report")
        assert resp.status_code == 200
        report = resp.json()["data"]
        assert report["total_entries"] == 2
        assert "entity_created" in report["actions_breakdown"]

    @pytest.mark.asyncio
    async def test_audit_filter_by_action(self, persisted_client):
        client, container, _ = persisted_client

        from mkg.domain.services.audit_logger import AuditAction
        container.audit_logger.log(AuditAction.ENTITY_CREATED, "p", "a1", "article", {})
        container.audit_logger.log(AuditAction.EDGE_CREATED, "p", "a2", "article", {})

        resp = await client.get("/api/v1/audit/log?action=entity_created")
        assert resp.status_code == 200
        entries = resp.json()["data"]
        assert len(entries) == 1
        assert entries[0]["action"] == "entity_created"


class TestProvenancePersistence:
    """Verify provenance data from pipeline is persisted and queryable."""

    @pytest.mark.asyncio
    async def test_provenance_via_lineage_endpoint(self, persisted_client):
        """Record provenance, check it shows via lineage API."""
        client, container, _ = persisted_client

        container.provenance_tracker.record_step(
            "art-123", "extraction", {"source": "reuters"}, {"entities": 3}
        )
        container.provenance_tracker.record_entity_origin(
            "ent-1", "Apple Inc", "art-123", "regex", 0.92
        )

        resp = await client.get("/api/v1/lineage/article/art-123")
        assert resp.status_code == 200
        lineage = resp.json()["data"]
        assert len(lineage["steps"]) == 1
        assert lineage["steps"][0]["step"] == "extraction"
        assert len(lineage["entities_created"]) == 1

    @pytest.mark.asyncio
    async def test_entity_lineage_endpoint(self, persisted_client):
        client, container, _ = persisted_client

        container.provenance_tracker.record_entity_origin(
            "ent-1", "Test Corp", "art-1", "regex", 0.8
        )

        resp = await client.get("/api/v1/lineage/entity/ent-1")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, dict)


class TestPersistenceAcrossRestarts:
    """Verify data survives container recreation (simulates process restart)."""

    @pytest.mark.asyncio
    async def test_audit_survives_restart(self, tmp_path):
        """Write audit data, destroy container, create new one, verify data."""
        os.environ["MKG_DB_DIR"] = str(tmp_path)

        from mkg.api.app import create_app

        # First container: write data
        app = create_app()
        container1 = deps.init_container()
        await container1.startup()

        from mkg.domain.services.audit_logger import AuditAction
        container1.audit_logger.log(
            AuditAction.ENTITY_CREATED, "pipeline", "art-1", "article",
            {"entities_created": 10},
        )

        await container1.shutdown()
        deps._container = None

        # Second container: read data (simulates restart)
        app2 = create_app()
        container2 = deps.init_container()
        await container2.startup()

        transport = ASGITransport(app=app2)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/api/v1/audit/log")
            assert resp.status_code == 200
            entries = resp.json()["data"]
            assert len(entries) >= 1
            assert entries[0]["details"]["entities_created"] == 10

        await container2.shutdown()
        deps._container = None
        os.environ.pop("MKG_DB_DIR", None)

    @pytest.mark.asyncio
    async def test_provenance_survives_restart(self, tmp_path):
        """Write provenance data, destroy container, create new one, verify data."""
        os.environ["MKG_DB_DIR"] = str(tmp_path)

        from mkg.api.app import create_app

        # First container: write data
        app = create_app()
        container1 = deps.init_container()
        await container1.startup()

        container1.provenance_tracker.record_step(
            "art-persist-1", "extraction", {"src": "test"}, {"entities": 5}
        )

        await container1.shutdown()
        deps._container = None

        # Second container: read data
        app2 = create_app()
        container2 = deps.init_container()
        await container2.startup()

        transport = ASGITransport(app=app2)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/api/v1/lineage/article/art-persist-1")
            assert resp.status_code == 200
            lineage = resp.json()["data"]
            assert len(lineage["steps"]) == 1
            assert lineage["steps"][0]["outputs"]["entities"] == 5

        await container2.shutdown()
        deps._container = None
        os.environ.pop("MKG_DB_DIR", None)
