# mkg/tests/test_pipeline_pii_compliance.py
"""Tests for PII detection in article ingestion and signal compliance enrichment.

Verifies:
1. PII is detected and redacted before articles enter the pipeline
2. Signal enrichment includes compliance metadata (disclaimers, classification)
3. SignalBridge is accessible via API
"""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from mkg.api import dependencies as deps


@pytest.fixture
async def compliance_client(tmp_path):
    """Client with initialized container for compliance tests."""
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


class TestPIIInPipeline:
    """PII detection during article processing."""

    def test_pii_detected_in_article_content(self):
        """PII detector flags emails in article content."""
        from mkg.domain.services.pii_detector import PIIDetector
        detector = PIIDetector()
        text = "Company CEO (john.doe@company.com) announced merger."
        result = detector.scan(text)
        assert result["has_pii"] is True
        assert "email" in result["pii_types"]

    def test_pii_redacted_before_storage(self):
        """PII is redacted from content before graph storage."""
        from mkg.domain.services.pii_detector import PIIDetector
        detector = PIIDetector()
        text = "Contact: john.doe@company.com, +91 9876543210"
        redacted = detector.redact(text)
        assert "john.doe@company.com" not in redacted
        assert "[REDACTED]" in redacted

    def test_pipeline_with_pii_protection(self, tmp_path):
        """PII-sanitized article processes correctly through pipeline."""
        from mkg.domain.services.pii_detector import PIIDetector
        from mkg.tasks.ingestion_tasks import process_article_real

        detector = PIIDetector()
        raw_content = (
            "Nvidia Corp (contact: ir@nvidia.com) reported Q4 revenue of $22.1B. "
            "CEO Jensen Huang's PAN is ABCDE1234F."
        )
        clean_content = detector.redact(raw_content)

        result = process_article_real(
            title="NVDA Q4 Results",
            content=clean_content,
            source="test",
            db_dir=str(tmp_path),
        )
        assert result["status"] == "completed"
        # Verify PII is not in the processed content
        assert "ir@nvidia.com" not in clean_content

    @pytest.mark.asyncio
    async def test_pii_scan_endpoint(self, compliance_client):
        """POST /pii/scan detects PII."""
        client, _ = compliance_client
        resp = await client.post(
            "/api/v1/pii/scan",
            json={"text": "Contact CEO at john@corp.com"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["has_pii"] is True
        assert "email" in data["pii_types"]

    @pytest.mark.asyncio
    async def test_pii_redact_endpoint(self, compliance_client):
        """POST /pii/redact removes PII from text."""
        client, _ = compliance_client
        resp = await client.post(
            "/api/v1/pii/redact",
            json={"text": "Email: ceo@corp.com"},
        )
        assert resp.status_code == 200
        redacted = resp.json()["data"]["redacted_text"]
        assert "ceo@corp.com" not in redacted


class TestSignalEnrichmentCompliance:
    """Signal enrichment with compliance metadata."""

    def test_signal_bridge_enrichment_basic(self):
        """SignalBridge produces enrichment for pipeline result."""
        from mkg.domain.services.signal_bridge import SignalBridge
        from mkg.domain.services.compliance_manager import ComplianceManager

        bridge = SignalBridge(compliance_manager=ComplianceManager())
        result = bridge.enrich_signal("NVDA", {
            "status": "completed",
            "impacts": [
                {"entity_name": "NVDA", "impact": 0.8},
                {"entity_name": "AMD", "impact": 0.3},
            ],
            "causal_chains": [
                {"affected_name": "NVDA", "impact_score": 0.8},
            ],
            "impact_table": {
                "rows": [
                    {"entity": "NVDA", "impact": 0.8, "category": "tech"},
                    {"entity": "AMD", "impact": 0.3, "category": "tech"},
                ]
            },
        })
        assert result["has_material_impact"] is True
        assert result["supply_chain_risk"] > 0
        assert "confidence_adjustment" in result

    def test_signal_bridge_with_compliance(self):
        """enrich_signal_with_compliance includes disclaimers and classification."""
        from mkg.domain.services.signal_bridge import SignalBridge
        from mkg.domain.services.compliance_manager import ComplianceManager
        from mkg.domain.services.lineage_tracer import LineageTracer
        from mkg.domain.services.provenance_tracker import ProvenanceTracker

        bridge = SignalBridge(
            compliance_manager=ComplianceManager(),
            lineage_tracer=LineageTracer(
                provenance_tracker=ProvenanceTracker(),
                compliance_manager=ComplianceManager(),
            ),
        )
        result = bridge.enrich_signal_with_compliance("AAPL", {
            "status": "completed",
            "impacts": [{"entity_name": "AAPL", "impact": 0.6}],
            "causal_chains": [{"affected_name": "AAPL", "impact_score": 0.6}],
            "impact_table": {"rows": [{"entity": "AAPL", "impact": 0.6}]},
        })

        assert "disclaimers" in result
        assert len(result["disclaimers"]) >= 2
        assert "classification" in result
        assert "risk_level" in result["classification"]

    @pytest.mark.asyncio
    async def test_compliance_report_endpoint(self, compliance_client):
        """GET /compliance/report returns compliance data."""
        client, _ = compliance_client
        resp = await client.get("/api/v1/compliance/report")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_disclaimers_endpoint(self, compliance_client):
        """GET /compliance/disclaimers returns all disclaimer texts."""
        client, _ = compliance_client
        resp = await client.get("/api/v1/compliance/disclaimers")
        assert resp.status_code == 200
        disclaimers = resp.json()["data"]
        assert isinstance(disclaimers, list)
        assert len(disclaimers) > 0
        # Each disclaimer should have a type and text
        for d in disclaimers:
            assert "type" in d
            assert "text" in d
            assert len(d["text"]) > 0


class TestSignalEnrichmentAPIEndpoint:
    """Test the signal enrichment endpoint."""

    @pytest.mark.asyncio
    async def test_enrich_signal_endpoint(self, compliance_client):
        """POST /signals/enrich returns compliance-wrapped enrichment."""
        client, _ = compliance_client

        # First process an article to have some data
        from mkg.domain.services.audit_logger import AuditAction
        _, container = compliance_client
        container.audit_logger.log(
            AuditAction.ENTITY_CREATED, "pipeline", "art-1", "article",
            {"entities_created": 2},
        )

        resp = await client.post("/api/v1/signals/enrich", json={
            "symbol": "NVDA",
            "pipeline_result": {
                "status": "completed",
                "impacts": [{"entity_name": "NVDA", "impact": 0.7}],
                "causal_chains": [{"affected_name": "NVDA", "impact_score": 0.7}],
                "impact_table": {},
            },
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "disclaimers" in data
        assert "supply_chain_risk" in data
        assert "classification" in data
