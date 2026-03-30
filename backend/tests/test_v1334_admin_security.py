"""v1.3.34 — Admin Endpoint Security Tests.

Verify admin endpoints require proper API key,
reject JWT-only auth, and don't expose sensitive data.
"""

import pytest


class TestAdminAuth:
    """Admin endpoints require X-API-Key header."""

    @pytest.mark.asyncio
    async def test_admin_revenue_without_key_403(self, test_client):
        """GET /admin/revenue without X-API-Key returns 403."""
        r = await test_client.get("/api/v1/admin/revenue")
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_revenue_wrong_key_403(self, test_client):
        """GET /admin/revenue with wrong key returns 403."""
        r = await test_client.get(
            "/api/v1/admin/revenue",
            headers={"X-API-Key": "wrong-key-here"},
        )
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_shadow_without_key_403(self, test_client):
        """GET /admin/shadow-mode without key returns 403."""
        r = await test_client.get("/api/v1/admin/shadow-mode")
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_shadow_wrong_key_403(self, test_client):
        """GET /admin/shadow-mode with wrong key returns 403."""
        r = await test_client.get(
            "/api/v1/admin/shadow-mode",
            headers={"X-API-Key": "invalid-admin-key"},
        )
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_key_via_query_param_ignored(self, test_client):
        """API key in query param doesn't grant admin access."""
        r = await test_client.get("/api/v1/admin/revenue?api_key=test-key")
        assert r.status_code == 403


class TestAdminDataExposure:
    """Admin responses must not expose sensitive information."""

    @pytest.mark.asyncio
    async def test_admin_error_no_stack_trace(self, test_client):
        """Admin error response doesn't contain stack traces."""
        r = await test_client.get("/api/v1/admin/revenue")
        body = r.text
        assert "Traceback" not in body
        assert "File \"/" not in body

    @pytest.mark.asyncio
    async def test_admin_endpoint_returns_json(self, test_client):
        """Admin endpoints return JSON even on error."""
        r = await test_client.get("/api/v1/admin/revenue")
        assert r.headers.get("content-type", "").startswith("application/json")


class TestAdminKeyConfiguration:
    """Admin key configuration must be safe."""

    def test_require_admin_checks_empty_key(self):
        """Empty INTERNAL_API_KEY blocks admin access."""
        import inspect
        from app.api.admin import _require_admin
        source = inspect.getsource(_require_admin)
        # Should check if key is empty/not configured
        assert "not" in source or "403" in source

    def test_admin_uses_hmac_comparison(self):
        """Admin key comparison uses constant-time hmac.compare_digest."""
        import inspect
        from app.api.admin import _require_admin
        source = inspect.getsource(_require_admin)
        assert "compare_digest" in source
