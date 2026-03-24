"""Tests for /api/v1/portfolio endpoints (trades + summary)."""

import pytest


# ─── List Trades ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_trades(test_client):
    """GET /api/v1/portfolio/trades returns trades for a user."""
    resp = await test_client.get("/api/v1/portfolio/trades", params={"telegram_chat_id": 12345})
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert len(body["data"]) == 2  # Two seeded trades


@pytest.mark.asyncio
async def test_list_trades_filter_by_symbol(test_client):
    """Filter trades by symbol substring."""
    resp = await test_client.get(
        "/api/v1/portfolio/trades",
        params={"telegram_chat_id": 12345, "symbol": "BTC"},
    )
    body = resp.json()
    assert len(body["data"]) == 1
    assert "BTC" in body["data"][0]["symbol"]


@pytest.mark.asyncio
async def test_list_trades_unknown_user(test_client):
    """Unknown chat_id returns empty list."""
    resp = await test_client.get("/api/v1/portfolio/trades", params={"telegram_chat_id": 99999})
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_list_trades_schema(test_client):
    """Trade items have required fields."""
    resp = await test_client.get("/api/v1/portfolio/trades", params={"telegram_chat_id": 12345})
    for trade in resp.json()["data"]:
        assert "id" in trade
        assert "symbol" in trade
        assert "side" in trade
        assert "quantity" in trade
        assert "price" in trade
        assert "created_at" in trade


# ─── Log Trade ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_log_trade(test_client):
    """POST /api/v1/portfolio/trades creates a new trade."""
    payload = {
        "telegram_chat_id": 12345,
        "symbol": "ETHUSDT",
        "market_type": "crypto",
        "side": "buy",
        "quantity": "1.5",
        "price": "3200.00",
    }
    resp = await test_client.post("/api/v1/portfolio/trades", json=payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["symbol"] == "ETHUSDT"
    assert data["side"] == "buy"


@pytest.mark.asyncio
async def test_log_trade_normalizes_symbol(test_client):
    """Symbol should be uppercased and trimmed."""
    payload = {
        "telegram_chat_id": 12345,
        "symbol": "infy.ns",
        "market_type": "stock",
        "side": "buy",
        "quantity": "5",
        "price": "1400.00",
    }
    resp = await test_client.post("/api/v1/portfolio/trades", json=payload)
    assert resp.status_code == 201
    assert resp.json()["data"]["symbol"] == "INFY.NS"


@pytest.mark.asyncio
async def test_log_sell_trade(test_client):
    """Log a sell trade."""
    payload = {
        "telegram_chat_id": 12345,
        "symbol": "HDFCBANK.NS",
        "market_type": "stock",
        "side": "sell",
        "quantity": "5",
        "price": "1700.00",
    }
    resp = await test_client.post("/api/v1/portfolio/trades", json=payload)
    assert resp.status_code == 201
    assert resp.json()["data"]["side"] == "sell"


@pytest.mark.asyncio
async def test_log_trade_with_notes_and_signal_id(test_client):
    """Trade can include optional notes and signal_id."""
    # Get a signal id first
    signals = await test_client.get("/api/v1/signals")
    sig_id = signals.json()["data"][0]["id"]

    payload = {
        "telegram_chat_id": 12345,
        "symbol": "TCS.NS",
        "market_type": "stock",
        "side": "buy",
        "quantity": "10",
        "price": "3960.00",
        "notes": "Following AI signal",
        "signal_id": sig_id,
    }
    resp = await test_client.post("/api/v1/portfolio/trades", json=payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["notes"] == "Following AI signal"
    assert data["signal_id"] == sig_id


# ─── Portfolio Summary ──────────────────────────────────────

@pytest.mark.asyncio
async def test_portfolio_summary(test_client):
    """GET /api/v1/portfolio/summary returns aggregated positions."""
    resp = await test_client.get(
        "/api/v1/portfolio/summary", params={"telegram_chat_id": 12345}
    )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert "total_invested" in body
    assert "current_value" in body
    assert "total_pnl" in body
    assert "total_pnl_pct" in body
    assert "positions" in body


@pytest.mark.asyncio
async def test_portfolio_summary_empty(test_client):
    """Unknown user gets empty summary."""
    resp = await test_client.get(
        "/api/v1/portfolio/summary", params={"telegram_chat_id": 99999}
    )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["positions"] == []
    assert float(body["total_invested"]) == 0
