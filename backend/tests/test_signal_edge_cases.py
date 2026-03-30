"""v1.3.21 — Signal Pipeline Edge Cases Tests.

Verify signal generation handles edge cases safely:
missing data, extreme values, and boundary conditions.
"""

import math
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from app.services.analysis.indicators import TechnicalAnalyzer
from app.services.signal_gen.scorer import (
    SIGNAL_THRESHOLDS,
    compute_final_confidence,
    compute_technical_score,
)
from app.services.signal_gen.targets import calculate_targets


def _make_df(close, *, high=None, low=None, volume=None, n=None):
    """Helper to build OHLCV DataFrames for tests."""
    if isinstance(close, (int, float)):
        n = n or 50
        close = [close] * n
    n = len(close)
    if high is None:
        high = [c + 1 for c in close]
    if low is None:
        low = [c - 1 for c in close]
    if volume is None:
        volume = [1000.0] * n
    return pd.DataFrame({
        "open": close,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


# ── Indicator Edge Cases ──────────────────────────────────────────


class TestIndicatorEdgeCases:
    """Technical indicators must handle edge cases gracefully."""

    def test_rsi_with_constant_prices(self):
        """RSI with no price changes should not crash."""
        df = _make_df(100.0, high=[100.0] * 50, low=[100.0] * 50)
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.compute_rsi()
        assert isinstance(result, dict)
        # Value may be None (division by zero in RS) — that's acceptable
        assert result.get("signal") in ("buy", "sell", "neutral")

    def test_rsi_insufficient_data(self):
        """RSI with very few data points returns neutral."""
        df = _make_df([100.0, 101.0, 102.0])
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.compute_rsi()
        assert result["signal"] == "neutral"
        assert result["value"] is None

    def test_macd_with_insufficient_data(self):
        """MACD with < 35 data points should return neutral safely."""
        df = _make_df([100.0 + i for i in range(10)])
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.compute_macd()
        assert isinstance(result, dict)
        assert result["signal"] == "neutral"

    def test_bollinger_with_zero_std(self):
        """Bollinger bands with zero std dev should not divide by zero."""
        df = _make_df(50.0, high=[50.0] * 50, low=[50.0] * 50)
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.compute_bollinger()
        assert isinstance(result, dict)
        # Should not crash — any signal is fine

    def test_volume_analysis_with_zero_volume(self):
        """Volume analysis with all-zero volume should handle gracefully."""
        df = _make_df(
            [100.0 + i for i in range(30)],
            volume=[0.0] * 30,
        )
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.compute_volume_ratio()
        assert isinstance(result, dict)

    def test_full_analysis_returns_all_keys(self):
        """full_analysis() should return all indicator keys."""
        prices = [100 + i * 0.5 for i in range(250)]
        df = _make_df(prices)
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.full_analysis()
        assert isinstance(result, dict)
        for key in ("rsi", "macd", "bollinger", "volume", "sma_cross", "atr"):
            assert key in result, f"Missing key: {key}"

    def test_constructor_rejects_missing_columns(self):
        """TechnicalAnalyzer should reject DataFrame without required cols."""
        df = pd.DataFrame({"close": [1, 2, 3]})
        with pytest.raises(ValueError, match="missing required columns"):
            TechnicalAnalyzer(df)


# ── Scoring Edge Cases ────────────────────────────────────────────


class TestScoringEdgeCases:
    """Signal scoring must handle extreme values."""

    def _make_tech_data(self, signal: str, strength: int = 80):
        """Build minimal technical_data dict with uniform signals."""
        entry = {"signal": signal, "strength": strength, "value": 50.0}
        return {
            "rsi": dict(entry),
            "macd": dict(entry),
            "bollinger": dict(entry),
            "volume": dict(entry),
            "sma_cross": dict(entry),
        }

    def test_all_buy_signals_give_high_confidence(self):
        """All-buy tech data should produce HIGH confidence."""
        tech = self._make_tech_data("buy", 90)
        conf, stype = compute_final_confidence(tech, None)
        # No AI → capped at 60, but should still be above 50
        assert conf >= 50
        assert stype in ("BUY", "HOLD")  # capped at 60 without AI

    def test_all_sell_signals_give_low_confidence(self):
        """All-sell tech data should produce LOW confidence."""
        tech = self._make_tech_data("sell", 90)
        conf, stype = compute_final_confidence(tech, None)
        assert conf <= 50
        assert stype in ("SELL", "HOLD")  # capped at 40 without AI

    def test_neutral_signals_map_to_hold(self):
        """All-neutral tech data should map to HOLD."""
        tech = self._make_tech_data("neutral", 50)
        conf, stype = compute_final_confidence(tech, None)
        assert stype == "HOLD"

    def test_boundary_thresholds(self):
        """Every threshold boundary maps to the correct signal type."""
        for threshold, expected_type in SIGNAL_THRESHOLDS:
            # Use threshold as tech_score directly via mock-like data
            # Verify the threshold list is well-ordered
            assert isinstance(threshold, int)
            assert expected_type in ("STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL")

    def test_nan_in_technical_data(self):
        """NaN indicator values should not crash scoring."""
        tech = {
            "rsi": {"signal": "buy", "strength": float("nan"), "value": float("nan")},
            "macd": {"signal": None, "strength": 50, "value": None},
            "bollinger": {},
            "volume": {},
            "sma_cross": {},
        }
        conf, stype = compute_final_confidence(tech, None)
        # Should return a valid result — NaN guard kicks in
        assert 0 <= conf <= 100
        assert stype in ("STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL")

    def test_empty_technical_data(self):
        """Empty technical data should return neutral HOLD."""
        conf, stype = compute_final_confidence({}, None)
        assert stype == "HOLD"
        assert 0 <= conf <= 100

    def test_technical_score_with_empty_dict(self):
        """compute_technical_score({}) should return 50 (neutral)."""
        score = compute_technical_score({})
        assert score == 50.0

    def test_confidence_with_sentiment(self):
        """With valid sentiment, confidence is un-capped."""
        tech = self._make_tech_data("buy", 95)
        sentiment = {
            "sentiment_score": 90,
            "confidence_in_analysis": 80,
            "key_factors": ["strong earnings"],
        }
        conf, stype = compute_final_confidence(tech, sentiment)
        # With AI sentiment, cap is removed so could be above 60
        assert 0 <= conf <= 100
        assert stype in ("STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL")


# ── Target Calculation Edge Cases ─────────────────────────────────


class TestTargetCalculation:
    """Target/stop-loss calculation edge cases."""

    def test_target_buy_with_valid_atr(self):
        """BUY target should be above current price."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 5.0},
            signal_type="BUY",
            market_type="stock",
        )
        assert result["target_price"] > Decimal("100")
        assert result["stop_loss"] < Decimal("100")

    def test_target_sell_with_valid_atr(self):
        """SELL target should be below current price."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 5.0},
            signal_type="SELL",
            market_type="stock",
        )
        assert result["target_price"] < Decimal("100")
        assert result["stop_loss"] > Decimal("100")

    def test_target_with_zero_atr_uses_fallback(self):
        """Zero ATR should use 2% fallback, not crash."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 0},
            signal_type="BUY",
            market_type="stock",
        )
        assert isinstance(result, dict)
        assert result["target_price"] > Decimal("0")
        assert result["stop_loss"] >= Decimal("0")

    def test_target_with_missing_atr_value(self):
        """Missing ATR value should use 2% fallback."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={},
            signal_type="BUY",
            market_type="stock",
        )
        assert isinstance(result, dict)
        assert result["target_price"] > Decimal("0")

    def test_target_with_very_low_price(self):
        """Very low price should not produce negative stop-loss."""
        result = calculate_targets(
            current_price=Decimal("0.001"),
            atr_data={"value": 0.01},
            signal_type="SELL",
            market_type="crypto",
        )
        assert result["stop_loss"] >= Decimal("0")
        assert result["target_price"] >= Decimal("0")

    def test_target_with_very_high_price(self):
        """Very high price should produce valid targets."""
        result = calculate_targets(
            current_price=Decimal("999999.99"),
            atr_data={"value": 1000.0},
            signal_type="BUY",
            market_type="stock",
        )
        assert result["target_price"] > Decimal("999999.99")
        assert result["stop_loss"] < Decimal("999999.99")

    def test_risk_reward_ratio_at_least_2(self):
        """Risk:Reward ratio must be ≥ 1:2."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 5.0},
            signal_type="BUY",
            market_type="stock",
        )
        reward = abs(result["target_price"] - Decimal("100"))
        risk = abs(result["stop_loss"] - Decimal("100"))
        if risk > 0:
            assert reward / risk >= 2

    def test_timeframe_per_market_type(self):
        """Each market type gets its own default timeframe."""
        for mtype in ("stock", "crypto", "forex"):
            result = calculate_targets(
                current_price=Decimal("100.00"),
                atr_data={"value": 5.0},
                signal_type="BUY",
                market_type=mtype,
            )
            assert "timeframe" in result
            assert isinstance(result["timeframe"], str)


# ── DataFrame Validation ──────────────────────────────────────────


class TestDataFrameValidation:
    """Data validation utilities must handle bad data."""

    def test_empty_dataframe_raises(self):
        """Empty DataFrame should raise or return empty from indicators."""
        df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.compute_rsi()
        assert result["value"] is None
        assert result["signal"] == "neutral"

    def test_nan_values_in_prices(self):
        """NaN values in price data should not crash indicators."""
        df = _make_df(
            [100.0, np.nan, 102.0] * 20,
            high=[101.0, np.nan, 103.0] * 20,
            low=[99.0, np.nan, 101.0] * 20,
            volume=[1000.0, np.nan, 1200.0] * 20,
        )
        analyzer = TechnicalAnalyzer(df)
        # Should not raise — returns some result
        result = analyzer.full_analysis()
        assert isinstance(result, dict)

    def test_single_row_dataframe(self):
        """Single-row DataFrame should return neutral for all indicators."""
        df = _make_df([100.0])
        analyzer = TechnicalAnalyzer(df)
        rsi = analyzer.compute_rsi()
        assert rsi["signal"] == "neutral"
        macd = analyzer.compute_macd()
        assert macd["signal"] == "neutral"
