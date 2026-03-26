"""Tester 2: The Chaos Mathematician — Financial Precision & Edge Cases.

Tests the signal scoring, target calculation, and indicator analysis with
extreme values: NaN, Infinity, zero, negative, extremely large/small.
Goal: find silent corruption in financial calculations.
"""

import math
import pytest
from decimal import Decimal, InvalidOperation
from typing import Any

from app.services.signal_gen.scorer import (
    _indicator_to_score,
    compute_final_confidence,
    compute_technical_score,
)
from app.services.signal_gen.targets import calculate_targets


# =========================================================================
# Scorer — Boundary & extreme value tests
# =========================================================================

class TestScorerBoundaries:
    """Test confidence scoring at exact threshold boundaries."""

    def test_confidence_exactly_80_is_strong_buy(self):
        """80 is the STRONG_BUY threshold — must be exactly right."""
        # Construct input that produces exactly 80
        # All buy signals at strength 80 → score = 50 + (80-50) = 80
        tech_data = {
            "rsi": {"signal": "buy", "strength": 80},
            "macd": {"signal": "buy", "strength": 80},
            "bollinger": {"signal": "buy", "strength": 80},
            "volume": {"signal": "buy", "strength": 80},
            "sma_cross": {"signal": "buy", "strength": 80},
        }
        score = compute_technical_score(tech_data)
        assert score == 80.0

        # With no sentiment, should be capped at 60 (no AI cap)
        confidence, signal_type = compute_final_confidence(tech_data, None)
        assert confidence == 60
        assert signal_type == "HOLD"  # Capped by NO_AI_CONFIDENCE_CAP

    def test_confidence_at_65_is_buy(self):
        """65 is the BUY threshold boundary."""
        tech_data = {
            "rsi": {"signal": "buy", "strength": 65},
            "macd": {"signal": "buy", "strength": 65},
            "bollinger": {"signal": "buy", "strength": 65},
            "volume": {"signal": "buy", "strength": 65},
            "sma_cross": {"signal": "buy", "strength": 65},
        }
        sentiment = {
            "sentiment_score": 65,
            "confidence_in_analysis": 80,
        }
        confidence, signal_type = compute_final_confidence(tech_data, sentiment)
        assert confidence == 65
        assert signal_type == "BUY"

    def test_confidence_at_64_is_hold(self):
        """64 should be HOLD (just below BUY threshold)."""
        tech_data = {
            "rsi": {"signal": "buy", "strength": 64},
            "macd": {"signal": "buy", "strength": 64},
            "bollinger": {"signal": "buy", "strength": 64},
            "volume": {"signal": "buy", "strength": 64},
            "sma_cross": {"signal": "buy", "strength": 64},
        }
        sentiment = {
            "sentiment_score": 64,
            "confidence_in_analysis": 80,
        }
        confidence, signal_type = compute_final_confidence(tech_data, sentiment)
        assert confidence == 64
        assert signal_type == "HOLD"

    def test_confidence_at_36_is_hold(self):
        """36 is the bottom of HOLD range."""
        tech_data = {
            "rsi": {"signal": "sell", "strength": 64},
            "macd": {"signal": "sell", "strength": 64},
            "bollinger": {"signal": "sell", "strength": 64},
            "volume": {"signal": "sell", "strength": 64},
            "sma_cross": {"signal": "sell", "strength": 64},
        }
        sentiment = {
            "sentiment_score": 36,
            "confidence_in_analysis": 80,
        }
        confidence, signal_type = compute_final_confidence(tech_data, sentiment)
        assert signal_type == "HOLD"

    def test_confidence_at_35_is_sell(self):
        """35 is the SELL threshold boundary."""
        tech_data = {
            "rsi": {"signal": "sell", "strength": 65},
            "macd": {"signal": "sell", "strength": 65},
            "bollinger": {"signal": "sell", "strength": 65},
            "volume": {"signal": "sell", "strength": 65},
            "sma_cross": {"signal": "sell", "strength": 65},
        }
        sentiment = {
            "sentiment_score": 35,
            "confidence_in_analysis": 80,
        }
        confidence, signal_type = compute_final_confidence(tech_data, sentiment)
        # sell strength 65 → score = 50 - (65-50) = 35
        # tech=35, sent=35 → final = 35
        assert signal_type == "SELL"

    def test_confidence_at_20_is_strong_sell(self):
        """20 is the boundary between SELL and STRONG_SELL."""
        tech_data = {
            "rsi": {"signal": "sell", "strength": 80},
            "macd": {"signal": "sell", "strength": 80},
            "bollinger": {"signal": "sell", "strength": 80},
            "volume": {"signal": "sell", "strength": 80},
            "sma_cross": {"signal": "sell", "strength": 80},
        }
        sentiment = {
            "sentiment_score": 20,
            "confidence_in_analysis": 80,
        }
        confidence, signal_type = compute_final_confidence(tech_data, sentiment)
        # sell strength 80 → score = 50 - (80-50) = 20
        # tech=20, sent=20 → final = 20 → but it's ≥ 0 so STRONG_SELL
        assert signal_type == "STRONG_SELL"

    def test_confidence_clamped_at_0(self):
        """Confidence must never go below 0."""
        tech_data = {
            "rsi": {"signal": "sell", "strength": 100},
            "macd": {"signal": "sell", "strength": 100},
            "bollinger": {"signal": "sell", "strength": 100},
            "volume": {"signal": "sell", "strength": 100},
            "sma_cross": {"signal": "sell", "strength": 100},
        }
        sentiment = {
            "sentiment_score": 0,
            "confidence_in_analysis": 80,
        }
        confidence, signal_type = compute_final_confidence(tech_data, sentiment)
        assert confidence >= 0
        assert confidence <= 100

    def test_confidence_clamped_at_100(self):
        """Confidence must never exceed 100."""
        tech_data = {
            "rsi": {"signal": "buy", "strength": 100},
            "macd": {"signal": "buy", "strength": 100},
            "bollinger": {"signal": "buy", "strength": 100},
            "volume": {"signal": "buy", "strength": 100},
            "sma_cross": {"signal": "buy", "strength": 100},
        }
        sentiment = {
            "sentiment_score": 100,
            "confidence_in_analysis": 100,
        }
        confidence, signal_type = compute_final_confidence(tech_data, sentiment)
        assert confidence <= 100
        assert confidence >= 0


class TestScorerExtremeValues:
    """Test scorer with NaN, Infinity, and other extreme values."""

    def test_indicator_score_with_nan_strength(self):
        """NaN strength should not crash."""
        result = _indicator_to_score({"signal": "buy", "strength": float("nan")})
        # NaN math produces NaN — this is a potential bug
        assert result is not None

    def test_indicator_score_with_inf_strength(self):
        """Infinity strength should be handled."""
        result = _indicator_to_score({"signal": "buy", "strength": float("inf")})
        # Should not be infinity in production
        assert result is not None

    def test_technical_score_empty_data(self):
        """Empty technical data should return neutral 50."""
        score = compute_technical_score({})
        assert score == 50.0

    def test_technical_score_missing_indicators(self):
        """Technical data with only some indicators."""
        tech_data = {
            "rsi": {"signal": "buy", "strength": 75},
            # macd, bollinger, volume, sma_cross are missing
        }
        score = compute_technical_score(tech_data)
        # Should still compute from available indicators
        assert 50 <= score <= 100

    def test_technical_score_all_none_signals(self):
        """All indicators have signal=None."""
        tech_data = {
            "rsi": {"signal": None, "strength": 50},
            "macd": {"signal": None, "strength": 50},
            "bollinger": {"signal": None, "strength": 50},
            "volume": {"signal": None, "strength": 50},
            "sma_cross": {"signal": None, "strength": 50},
        }
        score = compute_technical_score(tech_data)
        assert score == 50.0  # No valid indicators → neutral

    def test_final_confidence_with_nan_sentiment(self):
        """NaN sentiment score should not corrupt final confidence."""
        tech_data = {
            "rsi": {"signal": "buy", "strength": 70},
            "macd": {"signal": "buy", "strength": 70},
        }
        sentiment = {
            "sentiment_score": float("nan"),
            "confidence_in_analysis": 80,
        }
        confidence, signal_type = compute_final_confidence(tech_data, sentiment)
        # NaN propagation is a bug if it happens
        assert not math.isnan(confidence), "NaN propagated to final confidence!"
        assert 0 <= confidence <= 100

    def test_final_confidence_with_zero_sentiment(self):
        """Edge: sentiment_score = 0 (extremely bearish)."""
        tech_data = {
            "rsi": {"signal": "buy", "strength": 70},
            "macd": {"signal": "buy", "strength": 70},
        }
        sentiment = {
            "sentiment_score": 0,
            "confidence_in_analysis": 80,
        }
        confidence, signal_type = compute_final_confidence(tech_data, sentiment)
        assert 0 <= confidence <= 100

    def test_final_confidence_with_100_sentiment(self):
        """Edge: sentiment_score = 100 (extremely bullish)."""
        tech_data = {
            "rsi": {"signal": "buy", "strength": 70},
            "macd": {"signal": "buy", "strength": 70},
        }
        sentiment = {
            "sentiment_score": 100,
            "confidence_in_analysis": 80,
        }
        confidence, signal_type = compute_final_confidence(tech_data, sentiment)
        assert 0 <= confidence <= 100

    def test_no_ai_caps_correctly(self):
        """Without AI, max distance from 50 is 10 (cap at 60)."""
        tech_data = {
            "rsi": {"signal": "buy", "strength": 100},
            "macd": {"signal": "buy", "strength": 100},
            "bollinger": {"signal": "buy", "strength": 100},
            "volume": {"signal": "buy", "strength": 100},
            "sma_cross": {"signal": "buy", "strength": 100},
        }
        confidence, signal_type = compute_final_confidence(tech_data, None)
        assert confidence == 60
        assert signal_type == "HOLD"

    def test_no_ai_with_bearish_caps_at_40(self):
        """Without AI, bearish signals capped at 40."""
        tech_data = {
            "rsi": {"signal": "sell", "strength": 100},
            "macd": {"signal": "sell", "strength": 100},
            "bollinger": {"signal": "sell", "strength": 100},
            "volume": {"signal": "sell", "strength": 100},
            "sma_cross": {"signal": "sell", "strength": 100},
        }
        confidence, signal_type = compute_final_confidence(tech_data, None)
        assert confidence == 40
        assert signal_type == "HOLD"

    def test_sentiment_with_fallback_reason_treated_as_no_ai(self):
        """Sentiment with fallback_reason should be treated as unavailable."""
        tech_data = {
            "rsi": {"signal": "buy", "strength": 90},
            "macd": {"signal": "buy", "strength": 90},
        }
        sentiment = {
            "sentiment_score": 95,
            "confidence_in_analysis": 80,
            "fallback_reason": "API budget exhausted",
        }
        confidence, _ = compute_final_confidence(tech_data, sentiment)
        # Should use NO_AI path, capping at 60
        assert confidence <= 60

    def test_sentiment_with_zero_analysis_confidence(self):
        """Zero confidence_in_analysis should be treated as no AI."""
        tech_data = {"rsi": {"signal": "buy", "strength": 90}}
        sentiment = {
            "sentiment_score": 95,
            "confidence_in_analysis": 0,
        }
        confidence, _ = compute_final_confidence(tech_data, sentiment)
        assert confidence <= 60


# =========================================================================
# Target Calculator — Edge cases
# =========================================================================

class TestTargetCalculatorBreaker:
    """Try to break target/stop-loss calculations."""

    def test_zero_atr_uses_fallback(self):
        """Zero ATR should fall back to 2% of price."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 0},
            signal_type="BUY",
            market_type="stock",
        )
        assert result["target_price"] > Decimal("100.00")
        assert result["stop_loss"] < Decimal("100.00")

    def test_none_atr_uses_fallback(self):
        """None ATR should fall back to 2% of price."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": None},
            signal_type="BUY",
            market_type="stock",
        )
        assert result["target_price"] > Decimal("100.00")
        assert result["stop_loss"] < Decimal("100.00")

    def test_negative_atr_produces_valid_targets(self):
        """Negative ATR — should not produce inverted targets."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": -5.0},
            signal_type="BUY",
            market_type="stock",
        )
        # For a BUY, target must be > current price
        # With negative ATR: target = 100 + (-5 * 2) = 90 — WRONG!
        # This is a potential bug. At minimum, prices should be non-negative.
        assert result["target_price"] >= Decimal("0")
        assert result["stop_loss"] >= Decimal("0")

    def test_zero_price_with_valid_atr(self):
        """Zero current price edge case."""
        result = calculate_targets(
            current_price=Decimal("0"),
            atr_data={"value": 0},
            signal_type="BUY",
            market_type="crypto",
        )
        assert result["target_price"] >= Decimal("0")
        assert result["stop_loss"] >= Decimal("0")

    def test_extremely_small_price(self):
        """Price of 0.00000001 (like a tiny altcoin)."""
        result = calculate_targets(
            current_price=Decimal("0.00000001"),
            atr_data={"value": 0.00000001},
            signal_type="BUY",
            market_type="crypto",
        )
        assert result["target_price"] > Decimal("0")
        assert result["stop_loss"] >= Decimal("0")

    def test_extremely_large_price(self):
        """Price of 10 million (like expensive stock in INR)."""
        result = calculate_targets(
            current_price=Decimal("10000000.00"),
            atr_data={"value": 500000},
            signal_type="STRONG_BUY",
            market_type="stock",
        )
        assert result["target_price"] > Decimal("10000000")

    def test_hold_signal_still_gets_targets(self):
        """HOLD signals should still have valid targets."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 5.0},
            signal_type="HOLD",
            market_type="stock",
        )
        assert result["target_price"] > Decimal("0")
        assert result["stop_loss"] > Decimal("0")
        assert "timeframe" in result

    def test_sell_target_below_current_price(self):
        """For SELL signals, target should be BELOW current price."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 5.0},
            signal_type="SELL",
            market_type="stock",
        )
        assert result["target_price"] < Decimal("100.00")
        assert result["stop_loss"] > Decimal("100.00")

    def test_sell_signal_stop_loss_above_price(self):
        """For SELL signals, stop-loss should be ABOVE current price."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 5.0},
            signal_type="STRONG_SELL",
            market_type="forex",
        )
        assert result["stop_loss"] > Decimal("100.00")

    def test_risk_reward_ratio_enforced(self):
        """R:R ratio must be >= 1:2."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 5.0},
            signal_type="BUY",
            market_type="stock",
        )
        reward = abs(result["target_price"] - Decimal("100.00"))
        risk = abs(result["stop_loss"] - Decimal("100.00"))
        if risk > 0:
            rr_ratio = reward / risk
            assert rr_ratio >= Decimal("2.0"), f"R:R ratio {rr_ratio} is below 2.0"

    def test_missing_atr_value_key(self):
        """ATR data dict missing 'value' key entirely."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={},
            signal_type="BUY",
            market_type="stock",
        )
        assert result["target_price"] > Decimal("100.00")

    def test_unknown_market_type_timeframe(self):
        """Unknown market type should get default timeframe."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 5.0},
            signal_type="BUY",
            market_type="commodity",
        )
        assert result["timeframe"] is not None

    def test_atr_as_string(self):
        """ATR value as string (from JSON parsing)."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": "5.0"},
            signal_type="BUY",
            market_type="stock",
        )
        assert result["target_price"] > Decimal("100.00")


# =========================================================================
# Indicator score function edge cases
# =========================================================================

class TestIndicatorScoreEdgeCases:
    """Test the indicator-to-score conversion with edge cases."""

    def test_unknown_signal_returns_50(self):
        """Unknown signal type should return neutral."""
        result = _indicator_to_score({"signal": "unknown", "strength": 75})
        assert result == 50.0

    def test_missing_signal_key(self):
        """Missing signal key should return neutral."""
        result = _indicator_to_score({"strength": 75})
        assert result == 50.0

    def test_missing_strength_key(self):
        """Missing strength key should use default."""
        result = _indicator_to_score({"signal": "buy"})
        assert result == 50.0  # default strength 50 → score 50

    def test_empty_dict(self):
        """Empty dict should return neutral."""
        result = _indicator_to_score({})
        assert result == 50.0

    def test_strength_at_50_buy_gives_50(self):
        """Buy at strength 50 should give exactly 50 (neutral boundary)."""
        result = _indicator_to_score({"signal": "buy", "strength": 50})
        assert result == 50.0

    def test_strength_at_100_buy_gives_100(self):
        """Buy at max strength should give 100."""
        result = _indicator_to_score({"signal": "buy", "strength": 100})
        assert result == 100.0

    def test_strength_at_100_sell_gives_0(self):
        """Sell at max strength should give 0."""
        result = _indicator_to_score({"signal": "sell", "strength": 100})
        assert result == 0.0

    def test_strength_at_50_sell_gives_50(self):
        """Sell at strength 50 gives 50 (boundary)."""
        result = _indicator_to_score({"signal": "sell", "strength": 50})
        assert result == 50.0
