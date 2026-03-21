"""Tests for /api/v1/markets/overview endpoint."""

import pytest


@pytest.mark.asyncio
async def test_market_overview(test_client):
    """GET /api/v1/markets/overview returns grouped market snapshots."""
    resp = await test_client.get("/api/v1/markets/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    data = body["data"]
    assert "stocks" in data
    assert "crypto" in data
    assert "forex" in data


@pytest.mark.asyncio
async def test_market_overview_stocks(test_client):
    """Stocks section contains seeded HDFCBANK.NS data."""
    resp = await test_client.get("/api/v1/markets/overview")
    stocks = resp.json()["data"]["stocks"]
    assert len(stocks) >= 1
    symbols = [s["symbol"] for s in stocks]
    assert "HDFCBANK.NS" in symbols


@pytest.mark.asyncio
async def test_market_overview_crypto(test_client):
    """Crypto section contains seeded BTCUSDT data."""
    resp = await test_client.get("/api/v1/markets/overview")
    crypto = resp.json()["data"]["crypto"]
    symbols = [c["symbol"] for c in crypto]
    assert "BTCUSDT" in symbols


@pytest.mark.asyncio
async def test_market_overview_forex(test_client):
    """Forex section contains seeded EUR/USD data."""
    resp = await test_client.get("/api/v1/markets/overview")
    forex = resp.json()["data"]["forex"]
    symbols = [f["symbol"] for f in forex]
    assert "EUR/USD" in symbols


@pytest.mark.asyncio
async def test_market_overview_snapshot_schema(test_client):
    """Each snapshot has required fields: symbol, price, change_pct, market_type."""
    resp = await test_client.get("/api/v1/markets/overview")
    for category in resp.json()["data"].values():
        for snap in category:
            assert "symbol" in snap
            assert "price" in snap
            assert "change_pct" in snap
            assert "market_type" in snap


@pytest.mark.asyncio
async def test_market_overview_change_pct_calculation(test_client):
    """change_pct should be (close - open) / open * 100."""
    resp = await test_client.get("/api/v1/markets/overview")
    stocks = resp.json()["data"]["stocks"]
    hdfc = next(s for s in stocks if s["symbol"] == "HDFCBANK.NS")
    # open=1670.00, close=1678.90 → change ~0.533%
    expected_pct = (1678.90 - 1670.00) / 1670.00 * 100
    assert abs(float(hdfc["change_pct"]) - expected_pct) < 0.01
