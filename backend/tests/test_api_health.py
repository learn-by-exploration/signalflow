"""Tests for /health endpoint."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_health_check(test_client):
    """GET /health returns basic health info."""
    resp = await test_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    # Health check always returns these fields even if DB is unreachable
    assert "status" in body
    assert "environment" in body
    assert "disclaimer" in body


@pytest.mark.asyncio
async def test_health_check_has_disclaimer(test_client):
    """Disclaimer about not being financial advice is present."""
    resp = await test_client.get("/health")
    body = resp.json()
    assert "not financial advice" in body.get("disclaimer", "").lower() or \
           "educational" in body.get("disclaimer", "").lower()
