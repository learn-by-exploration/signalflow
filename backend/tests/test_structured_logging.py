"""Tests for structured logging and correlation ID middleware."""

import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app


class TestCorrelationIdMiddleware:
    """Test the correlation ID middleware."""

    @pytest.mark.asyncio
    async def test_response_includes_request_id(self):
        """Every response should include X-Request-ID header."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert "X-Request-ID" in response.headers

    @pytest.mark.asyncio
    async def test_custom_request_id_is_echoed(self):
        """If client sends X-Request-ID, it should be echoed back."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/health",
                headers={"X-Request-ID": "test-123"},
            )
            assert response.headers.get("X-Request-ID") == "test-123"

    @pytest.mark.asyncio
    async def test_auto_generated_request_id_format(self):
        """Auto-generated IDs should be 8-char hex strings."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            request_id = response.headers.get("X-Request-ID", "")
            assert len(request_id) == 8


class TestHealthEndpoint:
    """Test the health endpoint returns structured data."""

    @pytest.mark.asyncio
    async def test_health_returns_status(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "disclaimer" in data
