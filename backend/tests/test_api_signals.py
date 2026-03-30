"""Tests for /api/v1/signals endpoints."""

import pytest


@pytest.mark.asyncio
async def test_list_signals_returns_active(test_client):
    """GET /api/v1/signals returns only active signals."""
    resp = await test_client.get("/api/v1/signals")
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert "meta" in body
    # Seeded DB has 3 active signals
    assert body["meta"]["total"] == 3
    assert body["meta"]["count"] == 3
    for sig in body["data"]:
        assert sig["is_active"] is True


@pytest.mark.asyncio
async def test_list_signals_filter_by_market(test_client):
    """Filter signals by market type."""
    resp = await test_client.get("/api/v1/signals", params={"market": "stock"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["market_type"] == "stock"


@pytest.mark.asyncio
async def test_list_signals_filter_by_signal_type(test_client):
    """Filter signals by signal_type."""
    resp = await test_client.get("/api/v1/signals", params={"signal_type": "BUY"})
    assert resp.status_code == 200
    body = resp.json()
    assert all(s["signal_type"] == "BUY" for s in body["data"])


@pytest.mark.asyncio
async def test_list_signals_filter_by_symbol(test_client):
    """Filter signals by symbol substring."""
    resp = await test_client.get("/api/v1/signals", params={"symbol": "BTC"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert "BTC" in body["data"][0]["symbol"]


@pytest.mark.asyncio
async def test_list_signals_min_confidence(test_client):
    """Filter signals by minimum confidence."""
    resp = await test_client.get("/api/v1/signals", params={"min_confidence": 90})
    assert resp.status_code == 200
    body = resp.json()
    # Only HDFCBANK (confidence=92) passes
    assert body["meta"]["total"] == 1
    assert body["data"][0]["confidence"] >= 90


@pytest.mark.asyncio
async def test_list_signals_pagination(test_client):
    """Test limit and offset pagination."""
    resp = await test_client.get("/api/v1/signals", params={"limit": 1, "offset": 0})
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["count"] == 1
    assert body["meta"]["total"] == 3

    resp2 = await test_client.get("/api/v1/signals", params={"limit": 1, "offset": 1})
    body2 = resp2.json()
    assert body2["meta"]["count"] == 1
    assert body2["data"][0]["id"] != body["data"][0]["id"]


@pytest.mark.asyncio
async def test_list_signals_empty_for_unknown_market(test_client):
    """Unknown market type is rejected with 400."""
    resp = await test_client.get("/api/v1/signals", params={"market": "commodities"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_signal_by_id(test_client):
    """GET /api/v1/signals/{id} returns correct signal."""
    list_resp = await test_client.get("/api/v1/signals")
    sig_id = list_resp.json()["data"][0]["id"]

    resp = await test_client.get(f"/api/v1/signals/{sig_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["id"] == sig_id


@pytest.mark.asyncio
async def test_get_signal_not_found(test_client):
    """GET /api/v1/signals/{id} returns 404 for unknown ID."""
    resp = await test_client.get("/api/v1/signals/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_signal_invalid_uuid(test_client):
    """GET /api/v1/signals/{id} returns 422 for invalid UUID."""
    resp = await test_client.get("/api/v1/signals/not-a-uuid")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_signals_response_schema(test_client):
    """Validate signal response fields match schema."""
    resp = await test_client.get("/api/v1/signals")
    body = resp.json()
    sig = body["data"][0]
    required_fields = {
        "id", "symbol", "market_type", "signal_type", "confidence",
        "current_price", "target_price", "stop_loss", "ai_reasoning",
        "technical_data", "is_active", "created_at",
    }
    assert required_fields.issubset(sig.keys())


@pytest.mark.asyncio
async def test_list_signals_combined_filters(test_client):
    """Multiple filters applied together."""
    resp = await test_client.get(
        "/api/v1/signals",
        params={"market": "crypto", "min_confidence": 70},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["symbol"] == "BTCUSDT"


@pytest.mark.asyncio
async def test_list_signals_limit_bounds(test_client):
    """limit=0 and limit>100 should fail validation."""
    resp = await test_client.get("/api/v1/signals", params={"limit": 0})
    assert resp.status_code == 422
    resp2 = await test_client.get("/api/v1/signals", params={"limit": 101})
    assert resp2.status_code == 422
