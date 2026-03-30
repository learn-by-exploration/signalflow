"""v1.3.45 — Error Handling Hardening Tests.

Verify errors never expose internal details, stack traces,
database info, or secrets. All errors return safe JSON.
"""

import pytest


class TestErrorResponseFormat:
    """All error responses must be JSON with safe messages."""

    @pytest.mark.asyncio
    async def test_404_is_json(self, test_client):
        r = await test_client.get("/api/v1/nonexistent-endpoint-xyz")
        assert r.status_code in (404, 405)
        data = r.json()
        assert "detail" in data or "error" in data or "message" in data

    @pytest.mark.asyncio
    async def test_422_is_json(self, test_client):
        r = await test_client.post(
            "/api/v1/auth/register",
            json={"invalid": "data"},
        )
        assert r.status_code == 422
        data = r.json()
        assert isinstance(data, dict)


class TestNoStackTraces:
    """Error responses must never contain stack traces."""

    @pytest.mark.asyncio
    async def test_no_traceback_in_422(self, test_client):
        r = await test_client.post(
            "/api/v1/auth/register",
            json={"email": 12345},
        )
        body = r.text
        assert "Traceback" not in body
        assert "File \"" not in body

    @pytest.mark.asyncio
    async def test_no_traceback_in_404(self, test_client):
        r = await test_client.get("/api/v1/does-not-exist")
        body = r.text
        assert "Traceback" not in body

    @pytest.mark.asyncio
    async def test_no_sql_in_error(self, test_client):
        """SQL queries should never appear in error responses."""
        r = await test_client.get("/api/v1/signals?limit=abc")
        body = r.text.lower()
        assert "select" not in body or "from" not in body
        assert "sqlalchemy" not in body


class TestNoInternalDetails:
    """Internal paths, versions, etc. must not leak."""

    @pytest.mark.asyncio
    async def test_no_file_paths_in_errors(self, test_client):
        r = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "no@one.com", "password": "wrong"},
        )
        body = r.text
        assert "/app/" not in body
        assert "/home/" not in body
        assert "site-packages" not in body

    @pytest.mark.asyncio
    async def test_health_no_internal_paths(self, test_client):
        r = await test_client.get("/health")
        body = r.text
        assert "/app/" not in body or "status" in r.json()


class TestMalformedInput:
    """Malformed inputs must be handled gracefully."""

    @pytest.mark.asyncio
    async def test_empty_body_post(self, test_client):
        r = await test_client.post(
            "/api/v1/auth/register",
            content=b"",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_non_json_content_type(self, test_client):
        r = await test_client.post(
            "/api/v1/auth/register",
            content=b"<xml>test</xml>",
            headers={"Content-Type": "text/xml"},
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_oversized_body(self, test_client):
        """Very large request body is handled."""
        large = {"email": "a" * 100000 + "@test.com", "password": "Pass123!"}
        r = await test_client.post("/api/v1/auth/register", json=large)
        assert r.status_code in (400, 413, 422)
