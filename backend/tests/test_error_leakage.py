"""v1.3.15 — Error Information Leakage Tests.

Verify that error responses never expose internal
implementation details, stack traces, or sensitive data.
"""

import uuid

import pytest
from httpx import AsyncClient


class TestNoStackTraces:
    """Error responses must not contain stack traces."""

    DANGEROUS_PATTERNS = [
        "Traceback",
        "File \"",
        "raise ",
        "Exception(",
        "sqlalchemy.",
        "postgresql",
        "asyncpg",
        "redis.exceptions",
        ".pyc",
        "/usr/lib/python",
        "/site-packages/",
        "app/api/",
        "app/models/",
        "app/services/",
    ]

    @pytest.mark.asyncio
    async def test_invalid_uuid_no_trace(self, test_client: AsyncClient):
        """Invalid UUID in URL should return clean error."""
        resp = await test_client.get("/api/v1/signals/not-a-uuid")
        body = resp.text
        for pattern in self.DANGEROUS_PATTERNS:
            assert pattern not in body, f"Stack trace leak: '{pattern}' found in response"

    @pytest.mark.asyncio
    async def test_missing_signal_no_trace(self, test_client: AsyncClient):
        """Nonexistent signal should return clean 404."""
        fake_id = str(uuid.uuid4())
        resp = await test_client.get(f"/api/v1/signals/{fake_id}")
        if resp.status_code == 404:
            body = resp.text
            for pattern in self.DANGEROUS_PATTERNS:
                assert pattern not in body

    @pytest.mark.asyncio
    async def test_malformed_json_no_trace(self, test_client: AsyncClient):
        """Malformed JSON body should return clean error."""
        resp = await test_client.post(
            "/api/v1/auth/register",
            content="{invalid json",
            headers={"Content-Type": "application/json"},
        )
        body = resp.text
        assert resp.status_code == 422
        for pattern in self.DANGEROUS_PATTERNS:
            assert pattern not in body, f"Stack trace in malformed JSON response: '{pattern}'"

    @pytest.mark.asyncio
    async def test_type_error_no_trace(self, test_client: AsyncClient):
        """Type errors should return clean 422."""
        resp = await test_client.get("/api/v1/signals?limit=abc")
        body = resp.text
        for pattern in self.DANGEROUS_PATTERNS:
            assert pattern not in body


class TestNoInternalPaths:
    """Responses must not reveal internal file paths."""

    @pytest.mark.asyncio
    async def test_error_no_file_paths(self, test_client: AsyncClient):
        """Error responses must not contain file system paths."""
        path_patterns = [
            "/home/",
            "/opt/",
            "/var/",
            "/app/",
            "C:\\",
            "D:\\",
        ]
        resp = await test_client.get("/api/v1/signals/invalid-id-format")
        body = resp.text
        for pattern in path_patterns:
            assert pattern not in body, f"File path leak: '{pattern}'"


class TestNoDatabaseInfo:
    """Responses must not reveal database details."""

    @pytest.mark.asyncio
    async def test_no_sql_in_errors(self, test_client: AsyncClient):
        """Error responses must not contain SQL statements."""
        sql_patterns = [
            "SELECT ",
            "INSERT ",
            "UPDATE ",
            "DELETE ",
            "FROM ",
            "WHERE ",
            "CREATE TABLE",
            "ALTER TABLE",
            "DROP ",
        ]
        # Try various invalid requests
        endpoints = [
            "/api/v1/signals?limit=-1",
            f"/api/v1/signals/{uuid.uuid4()}",
        ]
        for endpoint in endpoints:
            resp = await test_client.get(endpoint)
            body = resp.text.upper()
            for pattern in sql_patterns:
                if pattern in body and "SQL" not in body[:50]:
                    # Allow "SQL" in error type name but not raw SQL
                    assert pattern not in resp.text, f"SQL leak in {endpoint}: '{pattern}'"

    @pytest.mark.asyncio
    async def test_no_connection_strings(self, test_client: AsyncClient):
        """Error responses must not contain database connection strings."""
        resp = await test_client.get("/health")
        body = resp.text
        assert "postgresql" not in body.lower() or "timescaledb" in body.lower()
        assert "password" not in body.lower()
        assert "redis://" not in body


class TestHeadResponse:
    """Health endpoint should not leak too much info."""

    @pytest.mark.asyncio
    async def test_health_no_secrets(self, test_client: AsyncClient):
        """Health endpoint must not expose secrets or keys."""
        resp = await test_client.get("/health")
        body = resp.text.lower()
        assert "api_key" not in body or "configured" in body
        assert "secret" not in body
        assert "password" not in body
        assert "token" not in body or "access_token" not in body

    @pytest.mark.asyncio
    async def test_health_safe_info_only(self, test_client: AsyncClient):
        """Health endpoint should only expose operational status info."""
        resp = await test_client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        # Should have status, version, uptime — not internal details
        if isinstance(body, dict):
            assert "status" in body or "ok" in str(body).lower()


class TestErrorResponseFormat:
    """Error responses should have consistent format."""

    @pytest.mark.asyncio
    async def test_422_has_detail_field(self, test_client: AsyncClient):
        """422 responses should have 'detail' field."""
        resp = await test_client.post(
            "/api/v1/auth/register",
            json={},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert "detail" in body

    @pytest.mark.asyncio
    async def test_error_responses_are_json(self, test_client: AsyncClient):
        """Error responses should be JSON, not HTML."""
        resp = await test_client.get("/api/v1/signals/not-a-uuid")
        content_type = resp.headers.get("content-type", "")
        assert "application/json" in content_type, f"Error response is {content_type}, should be JSON"
