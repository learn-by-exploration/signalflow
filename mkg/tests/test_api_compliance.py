# mkg/tests/test_api_compliance.py
"""Tests for Compliance, Audit, Lineage, and PII API endpoints.

Iterations 11-20: Expose traceability services via REST API.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from mkg.api.app import create_app
from mkg.api.dependencies import init_container
import mkg.api.dependencies as deps


@pytest.fixture
async def client():
    import os
    old_key = os.environ.pop("MKG_API_KEY", None)
    app = create_app()
    container = init_container()
    await container.startup()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await container.shutdown()
    deps._container = None
    if old_key is not None:
        os.environ["MKG_API_KEY"] = old_key


class TestComplianceEndpoints:
    """GET /compliance/report — aggregate compliance stats."""

    @pytest.mark.asyncio
    async def test_compliance_report_returns_200(self, client):
        response = await client.get("/api/v1/compliance/report")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_compliance_report_has_disclaimers(self, client):
        response = await client.get("/api/v1/compliance/disclaimers")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) >= 4  # At least 4 disclaimer types


class TestAuditEndpoints:
    """GET /audit/log — query audit trail."""

    @pytest.mark.asyncio
    async def test_audit_log_returns_200(self, client):
        response = await client.get("/api/v1/audit/log")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_audit_log_accepts_action_filter(self, client):
        response = await client.get("/api/v1/audit/log?action=entity_created")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_audit_log_accepts_limit(self, client):
        response = await client.get("/api/v1/audit/log?limit=5")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_audit_report_returns_200(self, client):
        response = await client.get("/api/v1/audit/report")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total_entries" in data["data"]


class TestLineageEndpoints:
    """GET /lineage/{entity_id} — entity traceability."""

    @pytest.mark.asyncio
    async def test_lineage_entity_returns_200(self, client):
        response = await client.get("/api/v1/lineage/entity/test-entity-id")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_lineage_article_returns_200(self, client):
        response = await client.get("/api/v1/lineage/article/test-article-id")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestPIIEndpoints:
    """POST /pii/scan — PII detection."""

    @pytest.mark.asyncio
    async def test_pii_scan_clean_text(self, client):
        response = await client.post("/api/v1/pii/scan", json={
            "text": "TSMC reported strong revenue growth"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["has_pii"] is False

    @pytest.mark.asyncio
    async def test_pii_scan_with_email(self, client):
        response = await client.post("/api/v1/pii/scan", json={
            "text": "Contact john@example.com for details"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["has_pii"] is True

    @pytest.mark.asyncio
    async def test_pii_redact(self, client):
        response = await client.post("/api/v1/pii/redact", json={
            "text": "Email: john@example.com, PAN: ABCDE1234F"
        })
        assert response.status_code == 200
        data = response.json()
        assert "john@example.com" not in data["data"]["redacted_text"]
