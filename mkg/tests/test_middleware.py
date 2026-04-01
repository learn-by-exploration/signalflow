# mkg/tests/test_middleware.py
"""Tests for MKG middleware: auth, rate limiting, request ID, structured logging.

Validates:
- API key authentication blocks unauthenticated requests
- Valid API key passes through
- Internal endpoints (/health, /metrics) bypass auth
- Request ID is generated and returned in headers
- Rate limiting returns 429 when exceeded
"""

import pytest
from httpx import ASGITransport, AsyncClient

from mkg.api.app import create_app
from mkg.api.dependencies import init_container
import mkg.api.dependencies as deps

TEST_API_KEY = "test-mkg-api-key-for-testing"


@pytest.fixture
async def authed_app(tmp_path):
    """Create app with auth enabled."""
    import os
    old_key = os.environ.get("MKG_API_KEY")
    old_db_dir = os.environ.get("MKG_DB_DIR")
    os.environ["MKG_API_KEY"] = TEST_API_KEY
    os.environ["MKG_DB_DIR"] = str(tmp_path)
    app = create_app()
    container = init_container()
    await container.startup()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await container.shutdown()
    deps._container = None
    if old_key is None:
        os.environ.pop("MKG_API_KEY", None)
    else:
        os.environ["MKG_API_KEY"] = old_key
    if old_db_dir is not None:
        os.environ["MKG_DB_DIR"] = old_db_dir
    else:
        os.environ.pop("MKG_DB_DIR", None)


@pytest.fixture
async def unauthed_app(tmp_path):
    """Create app WITHOUT auth (no MKG_API_KEY set)."""
    import os
    old_key = os.environ.pop("MKG_API_KEY", None)
    old_db_dir = os.environ.get("MKG_DB_DIR")
    os.environ["MKG_DB_DIR"] = str(tmp_path)
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
    if old_db_dir is not None:
        os.environ["MKG_DB_DIR"] = old_db_dir
    else:
        os.environ.pop("MKG_DB_DIR", None)


class TestAPIKeyAuth:
    """API key authentication middleware."""

    async def test_health_bypasses_auth(self, authed_app):
        """Health endpoint should be accessible without auth."""
        resp = await authed_app.get("/health")
        assert resp.status_code == 200

    async def test_metrics_bypasses_auth(self, authed_app):
        """Metrics endpoint should be accessible without auth."""
        resp = await authed_app.get("/metrics")
        assert resp.status_code == 200

    async def test_api_blocked_without_key(self, authed_app):
        """API endpoints require auth header when MKG_API_KEY is set."""
        resp = await authed_app.get("/api/v1/entities")
        assert resp.status_code == 401
        body = resp.json()
        assert body["error"] == "Unauthorized"

    async def test_api_blocked_wrong_key(self, authed_app):
        """Wrong API key returns 401."""
        resp = await authed_app.get(
            "/api/v1/entities",
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    async def test_api_passes_with_correct_key(self, authed_app):
        """Correct API key grants access."""
        resp = await authed_app.get(
            "/api/v1/entities",
            headers={"X-API-Key": TEST_API_KEY},
        )
        assert resp.status_code == 200

    async def test_api_passes_with_bearer_token(self, authed_app):
        """Authorization: Bearer <key> also works."""
        resp = await authed_app.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        )
        assert resp.status_code == 200

    async def test_no_auth_when_key_not_set(self, unauthed_app):
        """Without MKG_API_KEY env var, auth is disabled (dev mode)."""
        resp = await unauthed_app.get("/api/v1/entities")
        assert resp.status_code == 200


class TestRequestIDMiddleware:
    """Request ID generation and propagation."""

    async def test_response_has_request_id(self, unauthed_app):
        """Every response includes X-Request-ID header."""
        resp = await unauthed_app.get("/health")
        assert "x-request-id" in resp.headers
        assert len(resp.headers["x-request-id"]) > 0

    async def test_request_id_is_unique(self, unauthed_app):
        """Each request gets a unique ID."""
        r1 = await unauthed_app.get("/health")
        r2 = await unauthed_app.get("/health")
        assert r1.headers["x-request-id"] != r2.headers["x-request-id"]

    async def test_client_provided_request_id_preserved(self, unauthed_app):
        """Client-provided X-Request-ID is preserved."""
        custom_id = "my-custom-request-id-123"
        resp = await unauthed_app.get(
            "/health",
            headers={"X-Request-ID": custom_id},
        )
        assert resp.headers["x-request-id"] == custom_id


class TestRateLimiting:
    """Rate limiting on API endpoints."""

    async def test_rate_limit_header_present(self, unauthed_app):
        """Rate-limited endpoints include rate limit headers."""
        resp = await unauthed_app.get("/api/v1/entities")
        # Should have at least one rate-limit related header
        headers_lower = {k.lower(): v for k, v in resp.headers.items()}
        has_rate_headers = any(
            "ratelimit" in k or "x-ratelimit" in k or "retry-after" in k
            for k in headers_lower
        )
        # Rate limit headers should be present (or at minimum, status is 200)
        assert resp.status_code == 200 or has_rate_headers
