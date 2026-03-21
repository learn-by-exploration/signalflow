"""Tests for /api/v1/signals/history and /api/v1/signals/stats endpoints."""

import pytest


@pytest.mark.asyncio
async def test_list_signal_history(test_client):
    """GET /api/v1/signals/history returns paginated history."""
    resp = await test_client.get("/api/v1/signals/history")
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert "meta" in body
    # Seeded DB has 4 history entries
    assert body["meta"]["total"] == 4


@pytest.mark.asyncio
async def test_list_signal_history_filter_by_outcome(test_client):
    """Filter history by outcome."""
    resp = await test_client.get("/api/v1/signals/history", params={"outcome": "hit_target"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["outcome"] == "hit_target"


@pytest.mark.asyncio
async def test_list_signal_history_pagination(test_client):
    """Test offset/limit on history."""
    resp = await test_client.get("/api/v1/signals/history", params={"limit": 2, "offset": 0})
    body = resp.json()
    assert body["meta"]["count"] == 2
    assert body["meta"]["total"] == 4


@pytest.mark.asyncio
async def test_signal_history_includes_signal_relation(test_client):
    """History items should include nested signal summary."""
    resp = await test_client.get("/api/v1/signals/history")
    body = resp.json()
    for item in body["data"]:
        assert "signal" in item
        if item["signal"] is not None:
            assert "symbol" in item["signal"]
            assert "signal_type" in item["signal"]


@pytest.mark.asyncio
async def test_signal_stats(test_client):
    """GET /api/v1/signals/stats returns aggregate statistics."""
    resp = await test_client.get("/api/v1/signals/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert "total_signals" in body
    assert "hit_target" in body
    assert "hit_stop" in body
    assert "expired" in body
    assert "pending" in body
    assert "win_rate" in body
    assert "avg_return_pct" in body
    assert body["total_signals"] == 4
    assert body["hit_target"] == 1
    assert body["hit_stop"] == 1


@pytest.mark.asyncio
async def test_signal_stats_win_rate_calculation(test_client):
    """Win rate = hit_target / (hit_target + hit_stop) × 100."""
    resp = await test_client.get("/api/v1/signals/stats")
    body = resp.json()
    expected_wr = 1 / (1 + 1) * 100  # 50%
    assert body["win_rate"] == expected_wr


@pytest.mark.asyncio
async def test_symbol_track_record(test_client):
    """GET /api/v1/signals/{symbol}/track-record returns per-symbol stats."""
    resp = await test_client.get("/api/v1/signals/TCS.NS/track-record")
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "TCS.NS"
    assert "total_signals_30d" in body
    assert "win_rate" in body


@pytest.mark.asyncio
async def test_symbol_track_record_unknown_symbol(test_client):
    """Unknown symbol returns zeroed stats."""
    resp = await test_client.get("/api/v1/signals/UNKNOWN/track-record")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_signals_30d"] == 0
    assert body["win_rate"] == 0.0
