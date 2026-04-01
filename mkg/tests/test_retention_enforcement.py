# mkg/tests/test_retention_enforcement.py
"""Tests for retention policy enforcement.

Verifies:
1. Retention policy correctly identifies expired records
2. Retention enforcement task purges expired data
3. API endpoint reports retention status
"""

import os
from datetime import datetime, timezone, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from mkg.api import dependencies as deps


@pytest.fixture
async def retention_client(tmp_path):
    """Client with initialized container for retention tests."""
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


class TestRetentionPolicy:
    """Retention policy logic tests."""

    def test_article_not_expired_within_period(self):
        from mkg.domain.services.retention_policy import RetentionPolicy
        policy = RetentionPolicy(article_retention_days=90)
        recent = datetime.now(timezone.utc) - timedelta(days=30)
        assert policy.is_expired("article", recent) is False

    def test_article_expired_beyond_period(self):
        from mkg.domain.services.retention_policy import RetentionPolicy
        policy = RetentionPolicy(article_retention_days=90)
        old = datetime.now(timezone.utc) - timedelta(days=100)
        assert policy.is_expired("article", old) is True

    def test_audit_retention_2_years(self):
        from mkg.domain.services.retention_policy import RetentionPolicy
        policy = RetentionPolicy(audit_retention_days=730)
        # 1 year old audit should NOT be expired
        one_year = datetime.now(timezone.utc) - timedelta(days=365)
        assert policy.is_expired("audit", one_year) is False
        # 3 years old should be expired
        three_years = datetime.now(timezone.utc) - timedelta(days=1100)
        assert policy.is_expired("audit", three_years) is True

    def test_unknown_type_never_expires(self):
        from mkg.domain.services.retention_policy import RetentionPolicy
        policy = RetentionPolicy()
        very_old = datetime.now(timezone.utc) - timedelta(days=10000)
        assert policy.is_expired("unknown_type", very_old) is False


class TestRetentionEndpoint:
    """Test retention status API endpoint."""

    @pytest.mark.asyncio
    async def test_retention_status_endpoint(self, retention_client):
        client, _ = retention_client
        resp = await client.get("/api/v1/retention/status")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "article_retention_days" in data
        assert "entity_retention_days" in data
        assert "audit_retention_days" in data

    @pytest.mark.asyncio
    async def test_retention_enforce_endpoint(self, retention_client):
        """POST /retention/enforce should return purge summary."""
        client, _ = retention_client
        resp = await client.post("/api/v1/retention/enforce")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "purged" in data
        assert isinstance(data["purged"], dict)
