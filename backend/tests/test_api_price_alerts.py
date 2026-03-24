"""Tests for /api/v1/alerts/price endpoints."""

import pytest


@pytest.mark.asyncio
async def test_list_price_alerts_empty(test_client):
    """GET returns empty list when no price alerts exist."""
    resp = await test_client.get("/api/v1/alerts/price", params={"telegram_chat_id": 12345})
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_create_price_alert(test_client):
    """POST /api/v1/alerts/price creates a price alert."""
    payload = {
        "telegram_chat_id": 12345,
        "symbol": "BTCUSDT",
        "market_type": "crypto",
        "condition": "above",
        "threshold": "100000.00",
    }
    resp = await test_client.post("/api/v1/alerts/price", json=payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["symbol"] == "BTCUSDT"
    assert data["condition"] == "above"
    assert data["is_triggered"] is False
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_price_alert_below(test_client):
    """Create a 'below' condition alert."""
    payload = {
        "telegram_chat_id": 12345,
        "symbol": "HDFCBANK.NS",
        "market_type": "stock",
        "condition": "below",
        "threshold": "1600.00",
    }
    resp = await test_client.post("/api/v1/alerts/price", json=payload)
    assert resp.status_code == 201
    assert resp.json()["data"]["condition"] == "below"


@pytest.mark.asyncio
async def test_create_price_alert_invalid_condition(test_client):
    """Invalid condition returns 400."""
    payload = {
        "telegram_chat_id": 12345,
        "symbol": "BTCUSDT",
        "market_type": "crypto",
        "condition": "equals",
        "threshold": "100000.00",
    }
    resp = await test_client.post("/api/v1/alerts/price", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_price_alerts_after_create(test_client):
    """After creating alerts, list returns them."""
    # Create a price alert first
    await test_client.post("/api/v1/alerts/price", json={
        "telegram_chat_id": 12345,
        "symbol": "ETHUSDT",
        "market_type": "crypto",
        "condition": "above",
        "threshold": "5000.00",
    })
    resp = await test_client.get("/api/v1/alerts/price", params={"telegram_chat_id": 12345})
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_delete_price_alert(test_client):
    """DELETE /api/v1/alerts/price/{id} deactivates alert."""
    # Create
    create_resp = await test_client.post("/api/v1/alerts/price", json={
        "telegram_chat_id": 12345,
        "symbol": "SOLUSDT",
        "market_type": "crypto",
        "condition": "below",
        "threshold": "100.00",
    })
    alert_id = create_resp.json()["data"]["id"]

    # Delete
    del_resp = await test_client.delete(f"/api/v1/alerts/price/{alert_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["data"] == "deleted"


@pytest.mark.asyncio
async def test_delete_price_alert_not_found(test_client):
    """DELETE returns 404 for unknown alert ID."""
    resp = await test_client.delete(
        "/api/v1/alerts/price/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_price_alert_schema(test_client):
    """Validate response fields."""
    create_resp = await test_client.post("/api/v1/alerts/price", json={
        "telegram_chat_id": 12345,
        "symbol": "EUR/USD",
        "market_type": "forex",
        "condition": "above",
        "threshold": "1.10",
    })
    data = create_resp.json()["data"]
    required = {"id", "symbol", "market_type", "condition",
                "threshold", "is_triggered", "is_active", "created_at"}
    assert required.issubset(data.keys())
