"""Tests for /api/v1/alerts endpoints (config + watchlist)."""

import pytest


# ─── Get Alert Config ───────────────────────────────────────

@pytest.mark.asyncio
async def test_get_alert_config(test_client):
    """GET /api/v1/alerts/config returns config for known chat_id."""
    resp = await test_client.get("/api/v1/alerts/config", params={"telegram_chat_id": 12345})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["telegram_chat_id"] == 12345
    assert data["username"] == "testuser"
    assert data["min_confidence"] == 60


@pytest.mark.asyncio
async def test_get_alert_config_not_found(test_client):
    """404 for unknown chat_id."""
    resp = await test_client.get("/api/v1/alerts/config", params={"telegram_chat_id": 99999})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_alert_config_schema(test_client):
    """Validate response fields."""
    resp = await test_client.get("/api/v1/alerts/config", params={"telegram_chat_id": 12345})
    data = resp.json()["data"]
    required = {"id", "telegram_chat_id", "markets", "min_confidence", "signal_types", "is_active", "created_at", "updated_at"}
    assert required.issubset(data.keys())


# ─── Create Alert Config ───────────────────────────────────

@pytest.mark.asyncio
async def test_create_alert_config(test_client):
    """POST /api/v1/alerts/config creates new config."""
    payload = {
        "telegram_chat_id": 54321,
        "username": "newuser",
        "markets": ["stock"],
        "min_confidence": 75,
        "signal_types": ["STRONG_BUY"],
    }
    resp = await test_client.post("/api/v1/alerts/config", json=payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["telegram_chat_id"] == 54321
    assert data["min_confidence"] == 75
    assert data["markets"] == ["stock"]


# ─── Update Alert Config ───────────────────────────────────

@pytest.mark.asyncio
async def test_update_alert_config(test_client):
    """PUT /api/v1/alerts/config/{id} updates existing config."""
    # Get existing config ID
    get_resp = await test_client.get("/api/v1/alerts/config", params={"telegram_chat_id": 12345})
    config_id = get_resp.json()["data"]["id"]

    payload = {"min_confidence": 80, "is_active": False}
    resp = await test_client.put(f"/api/v1/alerts/config/{config_id}", json=payload)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["min_confidence"] == 80
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_update_alert_config_not_found(test_client):
    """PUT returns 404 for unknown config_id."""
    resp = await test_client.put(
        "/api/v1/alerts/config/00000000-0000-0000-0000-000000000000",
        json={"min_confidence": 50},
    )
    assert resp.status_code == 404


# ─── Watchlist ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_watchlist(test_client):
    """GET /api/v1/alerts/watchlist returns watchlist."""
    resp = await test_client.get("/api/v1/alerts/watchlist", params={"telegram_chat_id": 12345})
    assert resp.status_code == 200
    assert resp.json()["data"] == ["HDFCBANK.NS", "BTCUSDT"]


@pytest.mark.asyncio
async def test_update_watchlist_add(test_client):
    """Add a symbol to watchlist."""
    resp = await test_client.post(
        "/api/v1/alerts/watchlist",
        params={"telegram_chat_id": 12345},
        json={"symbol": "TCS.NS", "action": "add"},
    )
    assert resp.status_code == 200
    assert "TCS.NS" in resp.json()["data"]


@pytest.mark.asyncio
async def test_update_watchlist_no_duplicate(test_client):
    """Adding an existing symbol doesn't duplicate."""
    resp = await test_client.post(
        "/api/v1/alerts/watchlist",
        params={"telegram_chat_id": 12345},
        json={"symbol": "HDFCBANK.NS", "action": "add"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data.count("HDFCBANK.NS") == 1


@pytest.mark.asyncio
async def test_update_watchlist_remove(test_client):
    """Remove a symbol from watchlist."""
    resp = await test_client.post(
        "/api/v1/alerts/watchlist",
        params={"telegram_chat_id": 12345},
        json={"symbol": "BTCUSDT", "action": "remove"},
    )
    assert resp.status_code == 200
    assert "BTCUSDT" not in resp.json()["data"]


@pytest.mark.asyncio
async def test_update_watchlist_invalid_action(test_client):
    """Invalid action returns 400."""
    resp = await test_client.post(
        "/api/v1/alerts/watchlist",
        params={"telegram_chat_id": 12345},
        json={"symbol": "XYZ", "action": "toggle"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_watchlist_unknown_user(test_client):
    """Watchlist for unknown user returns 404."""
    resp = await test_client.get("/api/v1/alerts/watchlist", params={"telegram_chat_id": 99999})
    assert resp.status_code == 404
