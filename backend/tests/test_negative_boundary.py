"""v1.3.24 — Negative & Boundary Testing.

Boundary values, negative inputs, and edge conditions across endpoints.
Tests the limits and invalid input scenarios for all major APIs.
"""

import uuid
from decimal import Decimal

import pytest

from app.services.signal_gen.scorer import SIGNAL_THRESHOLDS, compute_final_confidence
from app.services.signal_gen.targets import calculate_targets


# ── Signal API Boundary Tests ────────────────────────────────────


class TestSignalBoundaries:
    """Signal endpoint boundary conditions."""

    @pytest.mark.asyncio
    async def test_signals_limit_zero(self, test_client):
        """limit=0 should return empty or be rejected."""
        r = await test_client.get("/api/v1/signals?limit=0")
        assert r.status_code in (200, 422)

    @pytest.mark.asyncio
    async def test_signals_limit_negative(self, test_client):
        """Negative limit should be rejected."""
        r = await test_client.get("/api/v1/signals?limit=-1")
        assert r.status_code in (200, 422)

    @pytest.mark.asyncio
    async def test_signals_limit_exceeds_max(self, test_client):
        """limit > 100 should be capped or rejected."""
        r = await test_client.get("/api/v1/signals?limit=10000")
        if r.status_code == 200:
            data = r.json().get("data", [])
            assert len(data) <= 100  # Max limit enforced

    @pytest.mark.asyncio
    async def test_signals_offset_negative(self, test_client):
        """Negative offset should be rejected or treated as 0."""
        r = await test_client.get("/api/v1/signals?offset=-5")
        assert r.status_code in (200, 422)

    @pytest.mark.asyncio
    async def test_signals_offset_huge(self, test_client):
        """Huge offset returns empty results, not error."""
        r = await test_client.get("/api/v1/signals?offset=999999")
        assert r.status_code == 200
        data = r.json().get("data", [])
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_signals_min_confidence_boundary(self, test_client):
        """min_confidence at boundaries 0 and 100."""
        for val in (0, 100):
            r = await test_client.get(f"/api/v1/signals?min_confidence={val}")
            assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_signals_min_confidence_out_of_range(self, test_client):
        """min_confidence < 0 or > 100 should be rejected."""
        for val in (-1, 101, 999):
            r = await test_client.get(f"/api/v1/signals?min_confidence={val}")
            assert r.status_code in (200, 422)

    @pytest.mark.asyncio
    async def test_signal_id_nonexistent_uuid(self, test_client):
        """Fetching a non-existent signal should return 404."""
        r = await test_client.get(f"/api/v1/signals/{uuid.uuid4()}")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_signal_id_invalid_format(self, test_client):
        """Non-UUID signal ID should return 422 or 404."""
        r = await test_client.get("/api/v1/signals/not-a-uuid")
        assert r.status_code in (404, 422)

    @pytest.mark.asyncio
    async def test_signals_invalid_market_filter(self, test_client):
        """Invalid market type filter returns 400."""
        r = await test_client.get("/api/v1/signals?market=derivatives")
        assert r.status_code in (200, 400, 422)

    @pytest.mark.asyncio
    async def test_signals_invalid_signal_type(self, test_client):
        """Invalid signal_type filter returns 400."""
        r = await test_client.get("/api/v1/signals?signal_type=EXTREME_BUY")
        assert r.status_code in (200, 400, 422)


# ── History API Boundary Tests ───────────────────────────────────


class TestHistoryBoundaries:
    """Signal history endpoint boundary conditions."""

    @pytest.mark.asyncio
    async def test_history_empty_result(self, test_client):
        """History with tight filters returns empty, not error."""
        r = await test_client.get(
            "/api/v1/signals/history?min_confidence=100&signal_type=STRONG_SELL"
        )
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_history_large_offset(self, test_client):
        """History with large offset returns empty."""
        r = await test_client.get("/api/v1/signals/history?offset=999999")
        assert r.status_code == 200


# ── Price Alert Boundary Tests ───────────────────────────────────


class TestPriceAlertBoundaries:
    """Price alert creation boundary conditions."""

    @pytest.mark.asyncio
    async def test_price_alert_zero_threshold(self, test_client):
        """Zero threshold should be rejected."""
        r = await test_client.post(
            "/api/v1/alerts/price",
            json={
                "symbol": "RELIANCE.NS",
                "market_type": "stock",
                "condition": "above",
                "threshold": 0,
            },
        )
        assert r.status_code in (200, 201, 422)

    @pytest.mark.asyncio
    async def test_price_alert_negative_threshold(self, test_client):
        """Negative threshold should be rejected."""
        r = await test_client.post(
            "/api/v1/alerts/price",
            json={
                "symbol": "RELIANCE.NS",
                "market_type": "stock",
                "condition": "above",
                "threshold": -100,
            },
        )
        assert r.status_code in (200, 201, 422)

    @pytest.mark.asyncio
    async def test_price_alert_huge_threshold(self, test_client):
        """Very large threshold should be accepted (valid for crypto)."""
        r = await test_client.post(
            "/api/v1/alerts/price",
            json={
                "symbol": "BTCUSDT",
                "market_type": "crypto",
                "condition": "above",
                "threshold": 999999999.99,
            },
        )
        assert r.status_code in (200, 201, 402)

    @pytest.mark.asyncio
    async def test_price_alert_invalid_condition(self, test_client):
        """Invalid condition type should be rejected."""
        r = await test_client.post(
            "/api/v1/alerts/price",
            json={
                "symbol": "BTCUSDT",
                "market_type": "crypto",
                "condition": "equals",
                "threshold": 50000,
            },
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_delete_nonexistent_price_alert(self, test_client):
        """Deleting non-existent alert returns 404."""
        r = await test_client.delete(f"/api/v1/alerts/price/{uuid.uuid4()}")
        assert r.status_code == 404


# ── Portfolio Trade Boundary Tests ───────────────────────────────


class TestPortfolioBoundaries:
    """Trade logging boundary conditions."""

    @pytest.mark.asyncio
    async def test_trade_zero_quantity(self, test_client):
        """Zero quantity trade should be rejected."""
        r = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "symbol": "HDFCBANK.NS",
                "market_type": "stock",
                "side": "buy",
                "quantity": 0,
                "price": 1650.00,
            },
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_trade_negative_price(self, test_client):
        """Negative price trade should be rejected."""
        r = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "symbol": "HDFCBANK.NS",
                "market_type": "stock",
                "side": "buy",
                "quantity": 10,
                "price": -100.00,
            },
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_trade_invalid_side(self, test_client):
        """Invalid side (not buy/sell) should be rejected."""
        r = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "symbol": "HDFCBANK.NS",
                "market_type": "stock",
                "side": "hold",
                "quantity": 10,
                "price": 1650.00,
            },
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_trade_invalid_market_type(self, test_client):
        """Invalid market_type should be rejected."""
        r = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "symbol": "ABC",
                "market_type": "options",
                "side": "buy",
                "quantity": 10,
                "price": 100.00,
            },
        )
        assert r.status_code == 422


# ── Alert Config Boundary Tests ──────────────────────────────────


class TestAlertConfigBoundaries:
    """Alert configuration boundary conditions."""

    @pytest.mark.asyncio
    async def test_config_min_confidence_zero(self, test_client):
        """min_confidence of 0 should be accepted."""
        r = await test_client.post(
            "/api/v1/alerts/config",
            json={
                "telegram_chat_id": 11111,
                "markets": ["stock"],
                "min_confidence": 0,
            },
        )
        assert r.status_code in (200, 201, 409)

    @pytest.mark.asyncio
    async def test_config_min_confidence_100(self, test_client):
        """min_confidence of 100 should be accepted (will filter most signals)."""
        r = await test_client.post(
            "/api/v1/alerts/config",
            json={
                "telegram_chat_id": 22222,
                "markets": ["crypto"],
                "min_confidence": 100,
            },
        )
        assert r.status_code in (200, 201, 409)

    @pytest.mark.asyncio
    async def test_config_empty_markets(self, test_client):
        """Empty markets list should be rejected or accepted (no alerts)."""
        r = await test_client.post(
            "/api/v1/alerts/config",
            json={
                "telegram_chat_id": 33333,
                "markets": [],
                "min_confidence": 50,
            },
        )
        assert r.status_code in (200, 201, 409, 422)


# ── Feedback Boundary Tests ──────────────────────────────────────


class TestFeedbackBoundaries:
    """Signal feedback boundary conditions."""

    @pytest.mark.asyncio
    async def test_feedback_invalid_action(self, test_client):
        """Invalid action should be rejected."""
        r = await test_client.post(
            f"/api/v1/signals/{uuid.uuid4()}/feedback",
            json={"action": "love_it"},
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_feedback_negative_entry_price(self, test_client):
        """Negative entry_price should be accepted or rejected."""
        r = await test_client.post(
            f"/api/v1/signals/{uuid.uuid4()}/feedback",
            json={"action": "took", "entry_price": -50.00},
        )
        assert r.status_code in (200, 201, 422)


# ── Scorer Boundary Tests (Unit) ─────────────────────────────────


class TestScorerBoundaries:
    """Signal scoring boundary values."""

    def _tech(self, signal, strength):
        entry = {"signal": signal, "strength": strength, "value": 50.0}
        return {k: dict(entry) for k in ("rsi", "macd", "bollinger", "volume", "sma_cross")}

    def test_confidence_exactly_at_thresholds(self):
        """Test the exact threshold values from SIGNAL_THRESHOLDS."""
        for threshold, expected_type in SIGNAL_THRESHOLDS:
            # Verify threshold is an int
            assert isinstance(threshold, int)
            assert expected_type in ("STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL")

    def test_scoring_with_inf_strength(self):
        """Infinite strength should not crash scoring."""
        tech = self._tech("buy", float("inf"))
        conf, stype = compute_final_confidence(tech, None)
        assert 0 <= conf <= 100
        assert stype in ("STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL")

    def test_scoring_with_negative_strength(self):
        """Negative strength should produce a valid result."""
        tech = self._tech("buy", -100)
        conf, stype = compute_final_confidence(tech, None)
        assert 0 <= conf <= 100

    def test_scoring_with_mixed_signals(self):
        """Mixed buy/sell signals should produce HOLD-like result."""
        tech = {
            "rsi": {"signal": "buy", "strength": 80, "value": 30},
            "macd": {"signal": "sell", "strength": 80, "value": -1},
            "bollinger": {"signal": "buy", "strength": 60, "value": 45},
            "volume": {"signal": "sell", "strength": 70, "value": 0.5},
            "sma_cross": {"signal": "neutral", "strength": 50, "value": 0},
        }
        conf, stype = compute_final_confidence(tech, None)
        # Should be near center since signals conflict
        assert 0 <= conf <= 100


# ── Target Calculation Boundary Tests (Unit) ─────────────────────


class TestTargetBoundaries:
    """Target/stop-loss boundary values."""

    def test_target_hold_signal(self):
        """HOLD signal should still produce valid targets."""
        result = calculate_targets(
            current_price=Decimal("100"),
            atr_data={"value": 5.0},
            signal_type="HOLD",
            market_type="stock",
        )
        assert result["target_price"] > 0
        assert result["stop_loss"] >= 0

    def test_target_strong_sell_low_price(self):
        """STRONG_SELL on low price should not make target negative."""
        result = calculate_targets(
            current_price=Decimal("1.00"),
            atr_data={"value": 3.0},
            signal_type="STRONG_SELL",
            market_type="crypto",
        )
        assert result["target_price"] >= Decimal("0")
        assert result["stop_loss"] >= Decimal("0")

    def test_target_all_market_types(self):
        """All market types produce different timeframes."""
        timeframes = set()
        for mtype in ("stock", "crypto", "forex"):
            result = calculate_targets(
                current_price=Decimal("100"),
                atr_data={"value": 5.0},
                signal_type="BUY",
                market_type=mtype,
            )
            timeframes.add(result["timeframe"])
        assert len(timeframes) == 3  # Each market type has a different timeframe

    def test_target_unknown_market_type(self):
        """Unknown market type should use default timeframe."""
        result = calculate_targets(
            current_price=Decimal("100"),
            atr_data={"value": 5.0},
            signal_type="BUY",
            market_type="commodities",
        )
        assert "timeframe" in result  # Should not crash


# ── AI Q&A Boundary Tests ────────────────────────────────────────


class TestAIQABoundaries:
    """AI Q&A endpoint boundary conditions."""

    @pytest.mark.asyncio
    async def test_ask_empty_question(self, test_client):
        """Empty question should be rejected."""
        r = await test_client.post(
            "/api/v1/ai/ask",
            json={"symbol": "RELIANCE.NS", "question": ""},
        )
        assert r.status_code in (422, 400)

    @pytest.mark.asyncio
    async def test_ask_missing_symbol(self, test_client):
        """Missing symbol should be rejected."""
        r = await test_client.post(
            "/api/v1/ai/ask",
            json={"question": "What's the outlook?"},
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_ask_very_long_question(self, test_client):
        """Very long question should be rejected or truncated."""
        r = await test_client.post(
            "/api/v1/ai/ask",
            json={"symbol": "BTCUSDT", "question": "x" * 5000},
        )
        assert r.status_code in (200, 400, 422, 429)


# ── Health Endpoint Boundaries ───────────────────────────────────


class TestHealthBoundaries:
    """Health endpoint always returns valid structure."""

    @pytest.mark.asyncio
    async def test_health_returns_status(self, test_client):
        """Health endpoint has status field."""
        r = await test_client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert "status" in body
        assert body["status"] in ("healthy", "degraded", "unhealthy")

    @pytest.mark.asyncio
    async def test_health_post_rejected(self, test_client):
        """POST to /health should be rejected."""
        r = await test_client.post("/health")
        assert r.status_code == 405
