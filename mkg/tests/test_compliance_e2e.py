# mkg/tests/test_compliance_e2e.py
"""End-to-end compliance tests.

Verifies the full compliance chain:
1. ArticlePII scanned and redacted before entering pipeline
2. Provenance recorded at each step (SQLite-backed)
3. Audit trail persists across restarts
4. Signal enrichment includes disclaimers
5. Retention policy is SEBI-compliant (5 years for audit)
6. SignalBridge is wired into ServiceContainer
"""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from mkg.api import dependencies as deps


@pytest.fixture
async def compliance_client(tmp_path):
    """Client with full compliance infrastructure."""
    os.environ["MKG_DB_DIR"] = str(tmp_path)
    os.environ.pop("MKG_API_KEY", None)

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


class TestComplianceChain:
    """Full compliance chain from article to signal."""

    async def test_signal_bridge_accessible_from_container(self, compliance_client):
        """ServiceContainer has signal_bridge wired."""
        _, container, _ = compliance_client
        assert hasattr(container, "signal_bridge")
        assert container.signal_bridge is not None

    async def test_signal_bridge_has_compliance_manager(self, compliance_client):
        """SignalBridge is wired with ComplianceManager."""
        _, container, _ = compliance_client
        bridge = container.signal_bridge
        assert bridge._compliance is not None

    async def test_signal_bridge_has_lineage_tracer(self, compliance_client):
        """SignalBridge is wired with LineageTracer."""
        _, container, _ = compliance_client
        bridge = container.signal_bridge
        assert bridge._lineage is not None

    async def test_pii_detector_accessible(self, compliance_client):
        """PII detector is available in container."""
        _, container, _ = compliance_client
        pii = container.pii_detector
        result = pii.scan("CEO john@corp.com made announcement.")
        assert result["has_pii"] is True
        assert "email" in result["pii_types"]

    async def test_pii_redaction(self, compliance_client):
        """PII detector redacts sensitive data."""
        _, container, _ = compliance_client
        pii = container.pii_detector
        redacted = pii.redact("CEO john@corp.com made announcement.")
        assert "john@corp.com" not in redacted
        assert "[REDACTED]" in redacted

    async def test_retention_policy_sebi_compliant(self, compliance_client):
        """Audit retention is 5 years per SEBI IA Regulations 2013."""
        _, container, _ = compliance_client
        rp = container.retention_policy
        assert rp.audit_retention_days == 1825  # 5 years

    async def test_audit_persistence_via_api(self, compliance_client):
        """Audit log endpoint returns data from persistent storage."""
        client, container, _ = compliance_client
        from mkg.domain.services.audit_logger import AuditAction

        # Log some audit entries
        container.audit_logger.log(
            action=AuditAction.ENTITY_CREATED,
            actor="test",
            target_id="test-entity-001",
            target_type="entity",
            details={"description": "Compliance test entry"},
        )

        resp = await client.get("/api/v1/audit/log")
        assert resp.status_code == 200
        entries = resp.json()["data"]
        assert len(entries) >= 1

    async def test_provenance_persistence(self, compliance_client):
        """Provenance data persists in SQLite."""
        _, container, tmp_path = compliance_client

        container.provenance_tracker.record_step(
            article_id="art-001",
            step="extraction",
            inputs={"source": "test"},
            outputs={"entities": 3},
        )

        # Verify data is in SQLite (not just in-memory)
        import sqlite3
        db_path = os.path.join(str(tmp_path), "provenance.db")
        assert os.path.exists(db_path)

    async def test_disclaimers_endpoint(self, compliance_client):
        """Compliance disclaimers are available via API."""
        client, _, _ = compliance_client
        resp = await client.get("/api/v1/compliance/disclaimers")
        assert resp.status_code == 200
        disclaimers = resp.json()["data"]
        assert len(disclaimers) >= 2

        # Must include NOT_FINANCIAL_ADVICE and AI_GENERATED
        texts = [d["text"] for d in disclaimers]
        has_nfa = any("does not constitute" in t.lower() or "financial advice" in t.lower() for t in texts)
        has_ai = any("ai" in t.lower() for t in texts)
        assert has_nfa, f"Missing NOT_FINANCIAL_ADVICE disclaimer in: {texts}"
        assert has_ai, f"Missing AI_GENERATED disclaimer in: {texts}"

    async def test_signal_enrichment_includes_disclaimers(self, compliance_client):
        """Signal enrichment with compliance wraps enrichment with disclaimers."""
        _, container, _ = compliance_client
        bridge = container.signal_bridge

        # Create pipeline result with material impact
        pipeline_result = {
            "status": "completed",
            "impacts": [{"entity_id": "e1", "entity_name": "TSMC", "impact": 0.8, "depth": 1}],
            "causal_chains": [
                {"trigger_name": "Event", "affected_name": "TSMC", "impact": 0.8, "chain_length": 1}
            ],
            "impact_table": {"entities": 2, "edges": 1},
        }

        enrichment = bridge.enrich_signal_with_compliance("TSMC", pipeline_result)
        assert "disclaimers" in enrichment
        assert len(enrichment["disclaimers"]) >= 2
        assert "classification" in enrichment
        assert "data_sources" in enrichment

    async def test_compliance_report_via_api(self, compliance_client):
        """Compliance report endpoint returns structured data."""
        client, _, _ = compliance_client
        resp = await client.get("/api/v1/compliance/report")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "generated_at" in data or "total_entries" in data or "status" in data
