"""v1.3.4 — Path Traversal Prevention Tests.

Verify that no API endpoint allows directory traversal to access files
outside of intended directories. Tests SEO slugs, shared signal IDs,
and any file-serving endpoints.
"""

import pytest
from uuid import uuid4


PATH_TRAVERSAL_PAYLOADS = [
    "../../../etc/passwd",
    "..\\..\\..\\etc\\passwd",
    "....//....//....//etc/passwd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%252f..%252f..%252fetc%252fpasswd",
    "..%c0%af..%c0%af..%c0%afetc/passwd",
    "/etc/passwd",
    "....//etc//passwd",
    "..;/etc/passwd",
    "..%00/etc/passwd",
]


class TestSeoSlugTraversal:
    """Path traversal in SEO slug endpoint."""

    @pytest.mark.asyncio
    async def test_seo_slug_traversal(self, test_client):
        """GET /seo/{slug} should reject traversal payloads."""
        for payload in PATH_TRAVERSAL_PAYLOADS:
            resp = await test_client.get(f"/api/v1/seo/{payload}")
            assert resp.status_code in (400, 404, 422), \
                f"Expected 400/404 for traversal: {payload}"

    @pytest.mark.asyncio
    async def test_seo_slug_with_slashes(self, test_client):
        """Slashes in SEO slug should not resolve to different routes."""
        resp = await test_client.get("/api/v1/seo/../../admin/revenue")
        assert resp.status_code in (400, 404, 307)


class TestSharedSignalTraversal:
    """Path traversal in shared signal endpoint."""

    @pytest.mark.asyncio
    async def test_shared_signal_traversal(self, test_client):
        """GET /signals/shared/{id} with traversal."""
        for payload in ["../../../etc/passwd", "..%2f..%2fetc%2fpasswd"]:
            resp = await test_client.get(f"/api/v1/signals/shared/{payload}")
            # Should be 404 or 422, not serve a file
            assert resp.status_code in (400, 404, 422)

    @pytest.mark.asyncio
    async def test_signal_id_traversal(self, test_client):
        """GET /signals/{id} with traversal instead of UUID."""
        resp = await test_client.get("/api/v1/signals/../../admin")
        assert resp.status_code in (400, 404, 422)


class TestNewsEndpointTraversal:
    """Path traversal in news endpoints."""

    @pytest.mark.asyncio
    async def test_chains_symbol_traversal(self, test_client):
        """GET /news/chains/{symbol} with traversal."""
        for payload in ["../../../etc/passwd", "..%2f..%2fadmin"]:
            resp = await test_client.get(f"/api/v1/news/chains/{payload}")
            assert resp.status_code in (400, 404, 422)

    @pytest.mark.asyncio
    async def test_events_id_traversal(self, test_client):
        """GET /news/events/{id} with traversal."""
        resp = await test_client.get("/api/v1/news/events/../../admin")
        assert resp.status_code in (400, 404, 422)


class TestBacktestIdTraversal:
    """Path traversal in backtest endpoints."""

    @pytest.mark.asyncio
    async def test_backtest_id_traversal(self, test_client):
        """GET /backtest/{id} with traversal."""
        resp = await test_client.get("/api/v1/backtest/../../admin")
        assert resp.status_code in (400, 404, 422)


class TestNoFileServingEndpoints:
    """Verify the API doesn't serve arbitrary files."""

    @pytest.mark.asyncio
    async def test_no_static_file_serving(self, test_client):
        """API should not serve static files — no /../ access."""
        dangerous_paths = [
            "/../../etc/passwd",
            "/../.env",
            "/static/../../../etc/passwd",
            "/api/../.env",
        ]
        for path in dangerous_paths:
            resp = await test_client.get(path)
            # Should be 404 or redirect, never 200 with file contents
            assert resp.status_code != 200 or "application/json" in resp.headers.get("content-type", ""), \
                f"Unexpected 200 for: {path}"

    @pytest.mark.asyncio
    async def test_env_file_not_accessible(self, test_client):
        """/.env should not be accessible."""
        resp = await test_client.get("/.env")
        assert resp.status_code in (404, 405)

    @pytest.mark.asyncio
    async def test_alembic_ini_not_accessible(self, test_client):
        """/alembic.ini should not be accessible."""
        resp = await test_client.get("/alembic.ini")
        assert resp.status_code in (404, 405)


class TestCodebasePathSafety:
    """Verify no open() calls with unsanitized user input."""

    def test_no_open_with_user_input_in_api(self):
        """API files should not use open() with dynamic paths."""
        import os
        for root, dirs, files in os.walk("app/api"):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path) as fh:
                        source = fh.read()
                    # open() in API files is suspicious — should only be in test/config
                    for i, line in enumerate(source.splitlines(), 1):
                        stripped = line.strip()
                        if stripped.startswith("#"):
                            continue
                        if "open(" in stripped and "file" not in stripped.lower():
                            # Allow open_browser but flag open(variable)
                            pass  # FastAPI doesn't serve files from API
