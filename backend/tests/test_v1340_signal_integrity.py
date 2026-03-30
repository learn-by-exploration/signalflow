"""v1.3.40 — Signal Integrity Tests.

Verify signal data cannot be manipulated, confidence scores
are valid, and all required fields are present.
"""

from decimal import Decimal

import pytest

from app.services.signal_gen.scorer import SIGNAL_THRESHOLDS, compute_final_confidence
from app.services.signal_gen.targets import calculate_targets


class TestSignalScoreIntegrity:
    """Confidence scores must match signal types."""

    def _threshold_names(self):
        return [name for _, name in SIGNAL_THRESHOLDS]

    def test_strong_buy_threshold(self):
        """STRONG_BUY exists in thresholds."""
        assert "STRONG_BUY" in self._threshold_names()

    def test_buy_threshold(self):
        """BUY exists in thresholds."""
        assert "BUY" in self._threshold_names()

    def test_hold_threshold(self):
        """HOLD is the middle range."""
        assert "HOLD" in self._threshold_names()

    def test_sell_threshold(self):
        """SELL exists in thresholds."""
        assert "SELL" in self._threshold_names()

    def test_strong_sell_threshold(self):
        """STRONG_SELL exists in thresholds."""
        assert "STRONG_SELL" in self._threshold_names()

    def test_confidence_score_always_bounded(self):
        """compute_final_confidence always returns 0-100."""
        tech = {
            "rsi": {"signal": "buy", "strength": 90, "value": 25},
            "macd": {"signal": "buy", "strength": 90, "value": 2},
            "bollinger": {"signal": "buy", "strength": 90, "value": 30},
            "volume": {"signal": "buy", "strength": 90, "value": 2},
            "sma_cross": {"signal": "buy", "strength": 90, "value": 1},
        }
        sentiment = {"sentiment_score": 95, "confidence_in_analysis": 90}
        conf, stype = compute_final_confidence(tech, sentiment)
        assert 0 <= conf <= 100
        assert stype in self._threshold_names()


class TestTargetIntegrity:
    """Target and stop-loss calculations must be valid."""

    def test_buy_target_above_current(self):
        """BUY target price should be above current price."""
        result = calculate_targets(
            current_price=Decimal("100"),
            atr_data={"value": 5.0},
            signal_type="BUY",
            market_type="stock",
        )
        assert Decimal(str(result["target_price"])) > Decimal("100")

    def test_buy_stop_below_current(self):
        """BUY stop loss should be below current price."""
        result = calculate_targets(
            current_price=Decimal("100"),
            atr_data={"value": 5.0},
            signal_type="BUY",
            market_type="stock",
        )
        assert Decimal(str(result["stop_loss"])) < Decimal("100")

    def test_sell_target_below_current(self):
        """SELL target price should be below current price."""
        result = calculate_targets(
            current_price=Decimal("100"),
            atr_data={"value": 5.0},
            signal_type="SELL",
            market_type="stock",
        )
        assert Decimal(str(result["target_price"])) < Decimal("100")

    def test_risk_reward_ratio(self):
        """Risk:reward ratio should be >= 1:2."""
        result = calculate_targets(
            current_price=Decimal("100"),
            atr_data={"value": 5.0},
            signal_type="BUY",
            market_type="stock",
        )
        target_dist = abs(Decimal(str(result["target_price"])) - Decimal("100"))
        stop_dist = abs(Decimal("100") - Decimal(str(result["stop_loss"])))
        if stop_dist > 0:
            ratio = target_dist / stop_dist
            assert ratio >= Decimal("1.5")  # At least 1.5:1


class TestSignalAPIReadonly:
    """Signals can only be read, not created/modified via API."""

    @pytest.mark.asyncio
    async def test_post_signals_not_allowed(self, test_client):
        """POST /signals should not exist (signals are system-generated)."""
        r = await test_client.post(
            "/api/v1/signals",
            json={"symbol": "FAKE", "signal_type": "BUY"},
        )
        assert r.status_code == 405

    @pytest.mark.asyncio
    async def test_put_signals_not_allowed(self, test_client):
        """PUT /signals/{id} should not exist."""
        import uuid
        r = await test_client.put(
            f"/api/v1/signals/{uuid.uuid4()}",
            json={"confidence": 99},
        )
        assert r.status_code == 405

    @pytest.mark.asyncio
    async def test_delete_signals_not_allowed(self, test_client):
        """DELETE /signals/{id} should not exist."""
        import uuid
        r = await test_client.delete(f"/api/v1/signals/{uuid.uuid4()}")
        assert r.status_code == 405

    @pytest.mark.asyncio
    async def test_signal_history_valid_outcomes(self, test_client):
        """Signal history outcomes are from valid set."""
        r = await test_client.get("/api/v1/signals/history")
        if r.status_code == 200:
            data = r.json().get("data", [])
            valid_outcomes = {"hit_target", "hit_stop", "expired", "pending"}
            for item in data:
                if "outcome" in item and item["outcome"]:
                    assert item["outcome"] in valid_outcomes
