"""API endpoint integration tests.

These tests run against the live backend at localhost:8000.
Requires: backend running (uvicorn) + seeded database.

Skips gracefully if server isn't running.
"""

import pytest
import httpx

BASE_URL = "http://localhost:8000"


def _server_available() -> bool:
    try:
        resp = httpx.get(f"{BASE_URL}/health", timeout=2)
        return resp.status_code == 200
    except httpx.ConnectError:
        return False


pytestmark = pytest.mark.skipif(
    not _server_available(),
    reason="Backend server not running at localhost:8000",
)


class TestHealthEndpoint:
    def test_health_check(self) -> None:
        resp = httpx.get(f"{BASE_URL}/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "uptime" in data
        assert "disclaimer" in data


class TestSignalsEndpoint:
    def test_list_signals_returns_200(self) -> None:
        resp = httpx.get(f"{BASE_URL}/api/v1/signals")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert isinstance(body["data"], list)
        assert body["meta"]["count"] == len(body["data"])

    def test_list_signals_has_expected_fields(self) -> None:
        resp = httpx.get(f"{BASE_URL}/api/v1/signals")
        body = resp.json()
        if body["data"]:
            signal = body["data"][0]
            required_fields = [
                "id", "symbol", "market_type", "signal_type", "confidence",
                "current_price", "target_price", "stop_loss", "ai_reasoning",
                "technical_data", "is_active", "created_at",
            ]
            for field in required_fields:
                assert field in signal, f"Missing field: {field}"

    def test_filter_by_market(self) -> None:
        resp = httpx.get(f"{BASE_URL}/api/v1/signals?market=crypto")
        assert resp.status_code == 200
        body = resp.json()
        for signal in body["data"]:
            assert signal["market_type"] == "crypto"

    def test_filter_by_signal_type(self) -> None:
        resp = httpx.get(f"{BASE_URL}/api/v1/signals?signal_type=STRONG_BUY")
        assert resp.status_code == 200
        body = resp.json()
        for signal in body["data"]:
            assert signal["signal_type"] == "STRONG_BUY"

    def test_filter_by_min_confidence(self) -> None:
        resp = httpx.get(f"{BASE_URL}/api/v1/signals?min_confidence=80")
        assert resp.status_code == 200
        body = resp.json()
        for signal in body["data"]:
            assert signal["confidence"] >= 80

    def test_pagination_limit(self) -> None:
        resp = httpx.get(f"{BASE_URL}/api/v1/signals?limit=2")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) <= 2

    def test_get_signal_by_id(self) -> None:
        resp = httpx.get(f"{BASE_URL}/api/v1/signals?limit=1")
        signals = resp.json()["data"]
        if signals:
            signal_id = signals[0]["id"]
            resp2 = httpx.get(f"{BASE_URL}/api/v1/signals/{signal_id}")
            assert resp2.status_code == 200

    def test_get_nonexistent_signal_returns_404(self) -> None:
        resp = httpx.get(f"{BASE_URL}/api/v1/signals/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestMarketsEndpoint:
    def test_market_overview_returns_200(self) -> None:
        resp = httpx.get(f"{BASE_URL}/api/v1/markets/overview")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        data = body["data"]
        assert "stocks" in data
        assert "crypto" in data
        assert "forex" in data

    def test_market_overview_has_symbols(self) -> None:
        resp = httpx.get(f"{BASE_URL}/api/v1/markets/overview")
        data = resp.json()["data"]
        assert len(data["stocks"]) > 0
        assert len(data["crypto"]) > 0
        assert len(data["forex"]) > 0

    def test_market_snapshot_fields(self) -> None:
        resp = httpx.get(f"{BASE_URL}/api/v1/markets/overview")
        data = resp.json()["data"]
        for market_type in ["stocks", "crypto", "forex"]:
            if data[market_type]:
                item = data[market_type][0]
                assert "symbol" in item
                assert "price" in item
                assert "change_pct" in item
                assert "market_type" in item


class TestHistoryEndpoint:
    def test_history_returns_200(self) -> None:
        resp = httpx.get(f"{BASE_URL}/api/v1/signals/history")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body

    def test_history_has_outcome_fields(self) -> None:
        resp = httpx.get(f"{BASE_URL}/api/v1/signals/history")
        body = resp.json()
        if body["data"]:
            entry = body["data"][0]
            assert "signal_id" in entry
            assert "outcome" in entry
            assert "created_at" in entry
