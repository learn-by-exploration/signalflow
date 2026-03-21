"""Tests for /api/v1/backtest endpoints."""

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_start_backtest(test_client):
    """POST /api/v1/backtest/run creates a backtest run."""
    payload = {
        "symbol": "HDFCBANK.NS",
        "market_type": "stock",
        "days": 90,
    }
    with patch("app.tasks.backtest_tasks.run_backtest") as mock_task:
        mock_task.delay.return_value = None
        resp = await test_client.post("/api/v1/backtest/run", json=payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["symbol"] == "HDFCBANK.NS"
    assert data["status"] == "pending"
    assert data["market_type"] == "stock"


@pytest.mark.asyncio
async def test_start_backtest_normalizes_symbol(test_client):
    """Symbol should be uppercased and trimmed."""
    payload = {
        "symbol": "  btcusdt  ",
        "market_type": "crypto",
        "days": 30,
    }
    with patch("app.tasks.backtest_tasks.run_backtest") as mock_task:
        mock_task.delay.return_value = None
        resp = await test_client.post("/api/v1/backtest/run", json=payload)
    assert resp.status_code == 201
    assert resp.json()["data"]["symbol"] == "BTCUSDT"


@pytest.mark.asyncio
async def test_start_backtest_min_days(test_client):
    """days < 7 should fail validation."""
    payload = {
        "symbol": "BTCUSDT",
        "market_type": "crypto",
        "days": 3,
    }
    resp = await test_client.post("/api/v1/backtest/run", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_start_backtest_max_days(test_client):
    """days > 365 should fail validation."""
    payload = {
        "symbol": "BTCUSDT",
        "market_type": "crypto",
        "days": 500,
    }
    resp = await test_client.post("/api/v1/backtest/run", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_backtest_not_found(test_client):
    """GET /api/v1/backtest/{id} returns 404 for unknown ID."""
    resp = await test_client.get(
        "/api/v1/backtest/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_backtest_after_create(test_client):
    """Can retrieve a backtest by its ID after creation."""
    payload = {"symbol": "ETHUSDT", "market_type": "crypto", "days": 30}
    with patch("app.tasks.backtest_tasks.run_backtest") as mock_task:
        mock_task.delay.return_value = None
        create_resp = await test_client.post("/api/v1/backtest/run", json=payload)
    bt_id = create_resp.json()["data"]["id"]

    resp = await test_client.get(f"/api/v1/backtest/{bt_id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == bt_id
    assert data["symbol"] == "ETHUSDT"


@pytest.mark.asyncio
async def test_backtest_schema(test_client):
    """Validate backtest response fields."""
    payload = {"symbol": "SOLUSDT", "market_type": "crypto"}
    with patch("app.tasks.backtest_tasks.run_backtest") as mock_task:
        mock_task.delay.return_value = None
        create_resp = await test_client.post("/api/v1/backtest/run", json=payload)
    data = create_resp.json()["data"]
    required = {
        "id", "symbol", "market_type", "start_date", "end_date",
        "total_signals", "wins", "losses", "win_rate", "avg_return_pct",
        "total_return_pct", "max_drawdown_pct", "status", "created_at",
    }
    assert required.issubset(data.keys())
