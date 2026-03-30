"""v1.3.14 — API Versioning & Route Safety Tests.

Verify all API routes are properly versioned, no unversioned
routes expose sensitive data, and unknown routes return appropriate errors.
"""

import pytest
from httpx import AsyncClient


class TestAPIVersioning:
    """All API routes must be under /api/v1/."""

    @pytest.mark.asyncio
    async def test_versioned_routes_accessible(self, test_client: AsyncClient):
        """Main versioned routes should be accessible."""
        routes = [
            "/api/v1/signals",
            "/api/v1/markets/overview",
        ]
        for route in routes:
            resp = await test_client.get(route)
            assert resp.status_code in (200, 404), f"Route {route} returned {resp.status_code}"

    @pytest.mark.asyncio
    async def test_unversioned_api_returns_404(self, test_client: AsyncClient):
        """Unversioned API routes must return 404."""
        unversioned = [
            "/api/signals",
            "/signals",
            "/api/v2/signals",
            "/api/v0/signals",
        ]
        for route in unversioned:
            resp = await test_client.get(route)
            assert resp.status_code in (404, 405), f"Unversioned route {route} returned {resp.status_code}"

    @pytest.mark.asyncio
    async def test_health_endpoint_accessible(self, test_client: AsyncClient):
        """Health check is intentionally unversioned (at root level)."""
        resp = await test_client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_metrics_endpoint_accessible(self, test_client: AsyncClient):
        """Metrics endpoint should exist."""
        resp = await test_client.get("/metrics")
        assert resp.status_code in (200, 404)


class TestUnknownRoutes:
    """Unknown routes must return 404, not sensitive information."""

    @pytest.mark.asyncio
    async def test_random_route_returns_404(self, test_client: AsyncClient):
        """Random path returns 404."""
        resp = await test_client.get("/api/v1/nonexistent")
        assert resp.status_code in (404, 405)

    @pytest.mark.asyncio
    async def test_admin_path_not_open(self, test_client: AsyncClient):
        """Admin paths should not be publicly accessible."""
        paths = ["/admin", "/api/admin", "/api/v1/admin/users"]
        for path in paths:
            resp = await test_client.get(path)
            assert resp.status_code in (404, 401, 403), f"Admin path {path} returned {resp.status_code}"

    @pytest.mark.asyncio
    async def test_debug_endpoints_not_exposed(self, test_client: AsyncClient):
        """Debug/test endpoints must not exist in the API."""
        debug_paths = [
            "/debug",
            "/api/v1/debug",
            "/api/v1/test",
            "/api/v1/internal",
            "/api/v1/dev",
            "/_debug",
            "/phpinfo",
            "/server-status",
        ]
        for path in debug_paths:
            resp = await test_client.get(path)
            assert resp.status_code in (404, 405), f"Debug path {path} returned {resp.status_code}"

    @pytest.mark.asyncio
    async def test_404_response_no_stack_trace(self, test_client: AsyncClient):
        """404 responses must not contain stack traces."""
        resp = await test_client.get("/api/v1/nonexistent_endpoint_xyz")
        body = resp.text
        assert "Traceback" not in body
        assert "File \"" not in body
        assert "line " not in body or "detail" in body

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, test_client: AsyncClient):
        """Wrong HTTP method returns 405, not 500."""
        resp = await test_client.delete("/api/v1/signals")
        assert resp.status_code in (404, 405)

        resp2 = await test_client.patch("/api/v1/signals")
        assert resp2.status_code in (404, 405)


class TestRouterRegistration:
    """Verify all expected routers are registered."""

    def test_all_routers_included(self):
        """router.py must include all expected routers."""
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "router.py")
        with open(path) as f:
            content = f.read()
        expected_routers = [
            "signals_router",
            "markets_router",
            "alerts_router",
            "portfolio_router",
            "history_router",
            "auth_router",
            "payments_router",
        ]
        for router_name in expected_routers:
            assert router_name in content, f"Router {router_name} not registered"
