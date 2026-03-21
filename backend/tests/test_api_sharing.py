"""Tests for /api/v1/signals/{id}/share and /api/v1/signals/shared/{id} endpoints."""

import pytest


@pytest.mark.asyncio
async def test_share_signal(test_client):
    """POST /api/v1/signals/{id}/share creates a shareable link."""
    # Get a signal id
    signals = await test_client.get("/api/v1/signals")
    sig_id = signals.json()["data"][0]["id"]

    resp = await test_client.post(f"/api/v1/signals/{sig_id}/share")
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert "share_id" in data
    assert data["signal_id"] == sig_id


@pytest.mark.asyncio
async def test_share_signal_not_found(test_client):
    """Sharing a non-existent signal returns 404."""
    resp = await test_client.post(
        "/api/v1/signals/00000000-0000-0000-0000-000000000000/share"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_shared_signal(test_client):
    """GET /api/v1/signals/shared/{share_id} returns shared signal data."""
    # Create a share
    signals = await test_client.get("/api/v1/signals")
    sig_id = signals.json()["data"][0]["id"]
    share_resp = await test_client.post(f"/api/v1/signals/{sig_id}/share")
    share_id = share_resp.json()["data"]["share_id"]

    # Fetch shared signal
    resp = await test_client.get(f"/api/v1/signals/shared/{share_id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "symbol" in data
    assert "signal_type" in data
    assert "confidence" in data
    assert "ai_reasoning" in data
    assert "current_price" in data
    assert "target_price" in data
    assert "stop_loss" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_shared_signal_not_found(test_client):
    """Unknown share_id returns 404."""
    resp = await test_client.get(
        "/api/v1/signals/shared/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_share_multiple_signals(test_client):
    """Can share the same signal multiple times (each gets a unique share_id)."""
    signals = await test_client.get("/api/v1/signals")
    sig_id = signals.json()["data"][0]["id"]

    r1 = await test_client.post(f"/api/v1/signals/{sig_id}/share")
    r2 = await test_client.post(f"/api/v1/signals/{sig_id}/share")
    assert r1.json()["data"]["share_id"] != r2.json()["data"]["share_id"]
