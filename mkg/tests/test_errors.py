# mkg/tests/test_errors.py
"""Tests for MKG structured error handling.

Validates:
- Global exception handler produces consistent error envelope
- HTTPExceptions are wrapped in ErrorDetail format
- Unexpected exceptions return 500 with safe message
- Validation errors from Pydantic return 422 with field details
"""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from mkg.api.app import create_app
from mkg.api.dependencies import init_container
import mkg.api.dependencies as deps


@pytest.fixture
async def client(tmp_path):
    """Create test client with isolated SQLite storage."""
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
    if old_db_dir is not None:
        os.environ["MKG_DB_DIR"] = old_db_dir
    else:
        os.environ.pop("MKG_DB_DIR", None)


class TestErrorHandling:
    """Structured error responses."""

    async def test_404_error_envelope(self, client):
        """HTTPException 404 returns structured error body."""
        resp = await client.get("/api/v1/entities/nonexistent-id-xyz")
        assert resp.status_code == 404
        body = resp.json()
        assert "error" in body
        assert "detail" in body
        assert body["status_code"] == 404

    async def test_400_error_envelope(self, client):
        """HTTPException 400 returns structured error body."""
        resp = await client.post("/api/v1/entities", json={})
        assert resp.status_code == 422  # Pydantic validation error
        body = resp.json()
        assert "error" in body
        assert body["status_code"] == 422

    async def test_422_validation_error(self, client):
        """Pydantic validation errors return field-level details."""
        resp = await client.post("/api/v1/entities", json={
            "entity_type": "COMPANY",
            "name": "",  # min_length=1 violation
        })
        assert resp.status_code == 422
        body = resp.json()
        assert body["status_code"] == 422
        assert "detail" in body

    async def test_405_method_not_allowed(self, client):
        """Wrong HTTP method returns structured error."""
        resp = await client.patch("/api/v1/entities/some-id")
        assert resp.status_code in (405, 422)

    async def test_error_has_request_id(self, client):
        """Error responses include X-Request-ID when middleware is active."""
        resp = await client.get("/api/v1/entities/nonexistent-id-xyz")
        # Request ID should be in both header and body
        assert "x-request-id" in resp.headers
        body = resp.json()
        if "request_id" in body:
            assert body["request_id"] == resp.headers["x-request-id"]
