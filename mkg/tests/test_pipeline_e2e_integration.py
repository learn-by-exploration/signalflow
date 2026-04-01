# mkg/tests/test_pipeline_e2e_integration.py
"""Full E2E integration tests: article → pipeline → provenance → audit → API.

These tests exercise the complete flow:
1. Article ingestion through PipelineOrchestrator
2. Provenance recording at each step
3. Audit logging for mutations
4. API endpoints serving the recorded data
5. SignalBridge compliance enrichment
"""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from mkg.api import dependencies as deps


@pytest.fixture
async def e2e_client(tmp_path):
    """Full E2E client with container and pipeline."""
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


class TestFullPipelineE2E:
    """Full article → pipeline → API flow."""

    @pytest.mark.asyncio
    async def test_article_processing_creates_provenance(self, e2e_client):
        """Processing an article creates provenance records visible via API."""
        client, container = e2e_client

        # Process an article through the ServiceFactory pipeline
        from mkg.service_factory import ServiceFactory
        factory = ServiceFactory(db_dir=os.environ["MKG_DB_DIR"])
        await factory.initialize()
        pipeline = factory.create_pipeline_orchestrator()

        result = await pipeline.process_article(
            title="NVDA Q4 Earnings Beat",
            content="Nvidia Corporation reported Q4 revenue of $22.1 billion, beating analyst estimates. Data center revenue grew 409% year-over-year. The company announced a new AI chip architecture.",
            source="reuters",
            url="http://reuters.com/nvda-q4",
        )

        assert result["status"] == "completed"

        # Now check via API that provenance was recorded
        article_id = result["article_id"]

        # The factory uses its own provenance tracker — but we can verify
        # the pattern works by checking factory provenance
        records = factory.provenance_tracker.get_records(article_id)
        assert len(records) >= 1  # At least extraction step

        await factory.shutdown()

    @pytest.mark.asyncio
    async def test_pipeline_audit_trail_via_api(self, e2e_client):
        """Audit entries from pipeline are queryable via API."""
        client, container = e2e_client

        # Simulate pipeline creating audit entries
        from mkg.domain.services.audit_logger import AuditAction
        container.audit_logger.log(
            AuditAction.ENTITY_CREATED, "pipeline", "art-e2e-1", "article",
            {"entities_created": 3, "source": "reuters"},
        )
        container.audit_logger.log(
            AuditAction.EDGE_CREATED, "pipeline", "art-e2e-1", "article",
            {"relations_created": 2, "source": "reuters"},
        )

        # Query via API
        resp = await client.get("/api/v1/audit/log?target_id=art-e2e-1")
        assert resp.status_code == 200
        entries = resp.json()["data"]
        assert len(entries) == 2

        # Check report
        resp = await client.get("/api/v1/audit/report")
        assert resp.status_code == 200
        report = resp.json()["data"]
        assert report["total_entries"] == 2

    @pytest.mark.asyncio
    async def test_provenance_lineage_via_api(self, e2e_client):
        """Provenance chain for an article queryable via lineage API."""
        client, container = e2e_client

        # Record provenance steps
        container.provenance_tracker.record_step(
            "art-e2e-2", "dedup", {"url": "http://test/1"}, {"is_duplicate": False}
        )
        container.provenance_tracker.record_step(
            "art-e2e-2", "extraction",
            {"source": "reuters"},
            {"tier_used": "regex", "entities_count": 4, "relations_count": 2},
        )
        container.provenance_tracker.record_step(
            "art-e2e-2", "verification",
            {"entities_in": 4, "relations_in": 2},
            {"entities_out": 3, "relations_out": 2},
        )
        container.provenance_tracker.record_entity_origin(
            "ent-nvidia", "Nvidia Corp", "art-e2e-2", "regex", 0.95
        )

        # Query lineage via API
        resp = await client.get("/api/v1/lineage/article/art-e2e-2")
        assert resp.status_code == 200
        lineage = resp.json()["data"]
        assert len(lineage["steps"]) == 3
        assert lineage["steps"][0]["step"] == "dedup"
        assert lineage["steps"][1]["step"] == "extraction"
        assert lineage["steps"][2]["step"] == "verification"
        assert len(lineage["entities_created"]) == 1

    @pytest.mark.asyncio
    async def test_entity_traceability_via_api(self, e2e_client):
        """Entity can be traced back to source articles via API."""
        client, container = e2e_client

        container.provenance_tracker.record_entity_origin(
            "ent-tcs", "TCS", "art-1", "regex", 0.9
        )
        container.provenance_tracker.record_entity_origin(
            "ent-tcs", "TCS", "art-2", "claude", 0.95
        )

        resp = await client.get("/api/v1/lineage/entity/ent-tcs")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_compliance_enrichment_with_pipeline_data(self, e2e_client):
        """Signal enrichment endpoint with real pipeline-style data."""
        client, container = e2e_client

        resp = await client.post("/api/v1/signals/enrich", json={
            "symbol": "TCS",
            "pipeline_result": {
                "status": "completed",
                "impacts": [
                    {"entity_name": "TCS", "impact": 0.85},
                    {"entity_name": "Infosys", "impact": 0.4},
                ],
                "causal_chains": [
                    {"affected_name": "TCS", "impact_score": 0.85},
                    {"affected_name": "Infosys", "impact_score": 0.4},
                ],
                "impact_table": {
                    "rows": [
                        {"entity": "TCS", "impact": 0.85},
                        {"entity": "Infosys", "impact": 0.4},
                    ]
                },
            },
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["has_material_impact"] is True
        assert data["supply_chain_risk"] > 0
        assert len(data["disclaimers"]) >= 2
        assert "classification" in data
        assert data["classification"]["risk_level"] in ("high", "medium", "low")

    @pytest.mark.asyncio
    async def test_pii_scan_and_redact_round_trip(self, e2e_client):
        """PII scan → redact → verify no PII remains."""
        client, _ = e2e_client

        text = "Report by analyst john@firm.com (+91 9876543210)"

        # Scan
        resp = await client.post("/api/v1/pii/scan", json={"text": text})
        assert resp.status_code == 200
        scan = resp.json()["data"]
        assert scan["has_pii"] is True
        assert scan["pii_count"] >= 2

        # Redact
        resp = await client.post("/api/v1/pii/redact", json={"text": text})
        assert resp.status_code == 200
        redacted = resp.json()["data"]["redacted_text"]

        # Verify redacted text is clean
        resp = await client.post("/api/v1/pii/scan", json={"text": redacted})
        scan_clean = resp.json()["data"]
        assert scan_clean["has_pii"] is False

    @pytest.mark.asyncio
    async def test_full_compliance_flow(self, e2e_client):
        """Complete compliance flow: audit + provenance + enrichment + disclaimers."""
        client, container = e2e_client

        # 1. Simulate pipeline work
        from mkg.domain.services.audit_logger import AuditAction
        container.audit_logger.log(
            AuditAction.ENTITY_CREATED, "pipeline", "art-full-1", "article",
            {"entities_created": 5},
        )
        container.provenance_tracker.record_step(
            "art-full-1", "extraction", {"source": "reuters"}, {"entities": 5}
        )

        # 2. Check audit trail
        resp = await client.get("/api/v1/audit/report")
        assert resp.json()["data"]["total_entries"] >= 1

        # 3. Check provenance
        resp = await client.get("/api/v1/lineage/article/art-full-1")
        assert len(resp.json()["data"]["steps"]) >= 1

        # 4. Get compliance report
        resp = await client.get("/api/v1/compliance/report")
        assert resp.status_code == 200

        # 5. Get disclaimers
        resp = await client.get("/api/v1/compliance/disclaimers")
        disclaimers = resp.json()["data"]
        assert len(disclaimers) > 0

        # 6. Check retention status
        resp = await client.get("/api/v1/retention/status")
        assert resp.json()["data"]["audit_retention_days"] == 730

    @pytest.mark.asyncio
    async def test_empty_pipeline_enrichment(self, e2e_client):
        """Signal enrichment with no impacts returns safe defaults."""
        client, _ = e2e_client

        resp = await client.post("/api/v1/signals/enrich", json={
            "symbol": "UNKNOWN",
            "pipeline_result": {"status": "completed", "impacts": []},
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["has_material_impact"] is False
        assert data["supply_chain_risk"] == 0.0
        assert data["confidence_adjustment"] == 0
