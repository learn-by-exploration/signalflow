"""Tests for signal generation — generator, scorer, targets, and market detection."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from app.services.signal_gen.generator import (
    MIN_DATA_POINTS,
    SIGNAL_COOLDOWN_HOURS,
    SignalGenerator,
    detect_market_type,
)
from app.services.signal_gen.scorer import (
    NO_AI_CONFIDENCE_CAP,
    SIGNAL_THRESHOLDS,
    _indicator_to_score,
    compute_final_confidence,
    compute_technical_score,
)
from app.services.signal_gen.targets import (
    DEFAULT_TIMEFRAMES,
    STOP_ATR_MULTIPLIER,
    TARGET_ATR_MULTIPLIER,
    calculate_targets,
)


# ═══════════════════════════════════════════════════════════
# detect_market_type
# ═══════════════════════════════════════════════════════════

class TestDetectMarketType:
    def test_indian_stock(self):
        assert detect_market_type("HDFCBANK.NS") == "stock"

    def test_crypto(self):
        assert detect_market_type("BTCUSDT") == "crypto"

    def test_forex(self):
        assert detect_market_type("EUR/USD") == "forex"

    def test_default_stock(self):
        assert detect_market_type("UNKNOWN") == "stock"


# ═══════════════════════════════════════════════════════════
# _indicator_to_score
# ═══════════════════════════════════════════════════════════

class TestIndicatorToScore:
    def test_buy_high_strength(self):
        score = _indicator_to_score({"signal": "buy", "strength": 100})
        assert score == 100.0

    def test_buy_mid_strength(self):
        score = _indicator_to_score({"signal": "buy", "strength": 75})
        assert score == 75.0

    def test_sell_high_strength(self):
        score = _indicator_to_score({"signal": "sell", "strength": 100})
        assert score == 0.0

    def test_sell_mid_strength(self):
        score = _indicator_to_score({"signal": "sell", "strength": 75})
        assert score == 25.0

    def test_neutral(self):
        score = _indicator_to_score({"signal": "neutral", "strength": 50})
        assert score == 50.0

    def test_missing_signal(self):
        score = _indicator_to_score({})
        assert score == 50.0

    def test_missing_strength_defaults_50(self):
        score = _indicator_to_score({"signal": "neutral"})
        assert score == 50.0


# ═══════════════════════════════════════════════════════════
# compute_technical_score
# ═══════════════════════════════════════════════════════════

class TestComputeTechnicalScore:
    def test_all_buy_signals(self):
        data = {
            "rsi": {"signal": "buy", "strength": 100},
            "macd": {"signal": "buy", "strength": 100},
            "bollinger": {"signal": "buy", "strength": 100},
            "volume": {"signal": "buy", "strength": 100},
            "sma_cross": {"signal": "buy", "strength": 100},
        }
        score = compute_technical_score(data)
        assert score == 100.0

    def test_all_sell_signals(self):
        data = {
            "rsi": {"signal": "sell", "strength": 100},
            "macd": {"signal": "sell", "strength": 100},
            "bollinger": {"signal": "sell", "strength": 100},
            "volume": {"signal": "sell", "strength": 100},
            "sma_cross": {"signal": "sell", "strength": 100},
        }
        score = compute_technical_score(data)
        assert score == 0.0

    def test_all_neutral(self):
        data = {
            "rsi": {"signal": "neutral", "strength": 50},
            "macd": {"signal": "neutral", "strength": 50},
            "bollinger": {"signal": "neutral", "strength": 50},
            "volume": {"signal": "neutral", "strength": 50},
            "sma_cross": {"signal": "neutral", "strength": 50},
        }
        score = compute_technical_score(data)
        assert score == 50.0

    def test_empty_data_returns_50(self):
        score = compute_technical_score({})
        assert score == 50.0

    def test_partial_indicators(self):
        """Only some indicators present — weights adjust."""
        data = {
            "rsi": {"signal": "buy", "strength": 80},
            "macd": {"signal": "buy", "strength": 80},
        }
        score = compute_technical_score(data)
        assert score > 50.0

    def test_missing_signal_key(self):
        """Indicators missing 'signal' key are skipped."""
        data = {
            "rsi": {"value": 30},  # no signal key
            "macd": {"signal": "buy", "strength": 80},
        }
        score = compute_technical_score(data)
        assert score > 50.0  # Only macd contributes


# ═══════════════════════════════════════════════════════════
# compute_final_confidence
# ═══════════════════════════════════════════════════════════

class TestComputeFinalConfidence:
    def test_strong_buy_with_sentiment(self):
        tech_data = {
            "rsi": {"signal": "buy", "strength": 100},
            "macd": {"signal": "buy", "strength": 100},
            "bollinger": {"signal": "buy", "strength": 100},
            "volume": {"signal": "buy", "strength": 100},
            "sma_cross": {"signal": "buy", "strength": 100},
        }
        sentiment = {"sentiment_score": 100, "confidence_in_analysis": 90}
        confidence, signal_type = compute_final_confidence(tech_data, sentiment)
        assert confidence == 100
        assert signal_type == "STRONG_BUY"

    def test_strong_sell_with_sentiment(self):
        tech_data = {
            "rsi": {"signal": "sell", "strength": 100},
            "macd": {"signal": "sell", "strength": 100},
            "bollinger": {"signal": "sell", "strength": 100},
            "volume": {"signal": "sell", "strength": 100},
            "sma_cross": {"signal": "sell", "strength": 100},
        }
        sentiment = {"sentiment_score": 0, "confidence_in_analysis": 90}
        confidence, signal_type = compute_final_confidence(tech_data, sentiment)
        assert confidence == 0
        assert signal_type == "STRONG_SELL"

    def test_hold_range(self):
        tech_data = {
            "rsi": {"signal": "neutral", "strength": 50},
            "macd": {"signal": "neutral", "strength": 50},
            "bollinger": {"signal": "neutral", "strength": 50},
            "volume": {"signal": "neutral", "strength": 50},
            "sma_cross": {"signal": "neutral", "strength": 50},
        }
        sentiment = {"sentiment_score": 50, "confidence_in_analysis": 60}
        confidence, signal_type = compute_final_confidence(tech_data, sentiment)
        assert signal_type == "HOLD"
        assert 36 <= confidence <= 64

    def test_no_sentiment_caps_at_60(self):
        """Without AI sentiment, confidence capped at NO_AI_CONFIDENCE_CAP."""
        tech_data = {
            "rsi": {"signal": "buy", "strength": 100},
            "macd": {"signal": "buy", "strength": 100},
            "bollinger": {"signal": "buy", "strength": 100},
            "volume": {"signal": "buy", "strength": 100},
            "sma_cross": {"signal": "buy", "strength": 100},
        }
        confidence, signal_type = compute_final_confidence(tech_data, None)
        assert confidence <= NO_AI_CONFIDENCE_CAP

    def test_sentiment_with_fallback_reason_treated_as_no_ai(self):
        tech_data = {"rsi": {"signal": "buy", "strength": 90}}
        sentiment = {"sentiment_score": 90, "fallback_reason": "no news", "confidence_in_analysis": 0}
        confidence, _ = compute_final_confidence(tech_data, sentiment)
        assert confidence <= NO_AI_CONFIDENCE_CAP

    def test_signal_threshold_boundaries(self):
        """Verify all threshold boundaries produce correct signal types."""
        tech_all_buy = {
            k: {"signal": "buy", "strength": 100}
            for k in ["rsi", "macd", "bollinger", "volume", "sma_cross"]
        }
        tech_all_sell = {
            k: {"signal": "sell", "strength": 100}
            for k in ["rsi", "macd", "bollinger", "volume", "sma_cross"]
        }

        # 80+ → STRONG_BUY
        conf, sig = compute_final_confidence(
            tech_all_buy, {"sentiment_score": 80, "confidence_in_analysis": 80}
        )
        assert sig in ("STRONG_BUY", "BUY")

        # 0-20 → STRONG_SELL
        conf, sig = compute_final_confidence(
            tech_all_sell, {"sentiment_score": 0, "confidence_in_analysis": 80}
        )
        assert sig in ("STRONG_SELL", "SELL")


# ═══════════════════════════════════════════════════════════
# calculate_targets
# ═══════════════════════════════════════════════════════════

class TestCalculateTargets:
    def test_buy_targets(self):
        result = calculate_targets(
            current_price=Decimal("1000"),
            atr_data={"value": 50},
            signal_type="BUY",
            market_type="stock",
        )
        assert result["target_price"] == Decimal("1000") + Decimal("50") * TARGET_ATR_MULTIPLIER
        assert result["stop_loss"] == Decimal("1000") - Decimal("50") * STOP_ATR_MULTIPLIER
        assert result["timeframe"] == DEFAULT_TIMEFRAMES["stock"]

    def test_sell_targets(self):
        result = calculate_targets(
            current_price=Decimal("1000"),
            atr_data={"value": 50},
            signal_type="SELL",
            market_type="stock",
        )
        expected_target = (Decimal("1000") - Decimal("50") * TARGET_ATR_MULTIPLIER).quantize(Decimal("0.00000001"))
        expected_stop = (Decimal("1000") + Decimal("50") * STOP_ATR_MULTIPLIER).quantize(Decimal("0.00000001"))
        assert result["target_price"] == expected_target
        assert result["stop_loss"] == expected_stop

    def test_strong_buy_same_as_buy(self):
        r1 = calculate_targets(Decimal("100"), {"value": 5}, "BUY", "crypto")
        r2 = calculate_targets(Decimal("100"), {"value": 5}, "STRONG_BUY", "crypto")
        assert r1["target_price"] == r2["target_price"]
        assert r1["stop_loss"] == r2["stop_loss"]

    def test_strong_sell_same_as_sell(self):
        r1 = calculate_targets(Decimal("100"), {"value": 5}, "SELL", "forex")
        r2 = calculate_targets(Decimal("100"), {"value": 5}, "STRONG_SELL", "forex")
        assert r1["target_price"] == r2["target_price"]

    def test_atr_fallback(self):
        """When ATR value is None, uses 2% of price as fallback."""
        result = calculate_targets(
            current_price=Decimal("1000"),
            atr_data={},
            signal_type="BUY",
            market_type="stock",
        )
        fallback_atr = Decimal("1000") * Decimal("0.02")  # 20
        expected_target = (Decimal("1000") + fallback_atr * TARGET_ATR_MULTIPLIER).quantize(Decimal("0.00000001"))
        assert result["target_price"] == expected_target

    def test_atr_zero_uses_fallback(self):
        result = calculate_targets(
            current_price=Decimal("500"),
            atr_data={"value": 0},
            signal_type="BUY",
            market_type="stock",
        )
        # Fallback: 500 * 0.02 = 10 ATR
        expected_target = (Decimal("500") + Decimal("10") * TARGET_ATR_MULTIPLIER).quantize(Decimal("0.00000001"))
        assert result["target_price"] == expected_target

    def test_non_negative_prices(self):
        """Target and stop-loss should never be negative."""
        result = calculate_targets(
            current_price=Decimal("10"),
            atr_data={"value": 100},  # ATR much larger than price
            signal_type="SELL",
            market_type="crypto",
        )
        assert result["target_price"] >= Decimal("0")
        assert result["stop_loss"] >= Decimal("0")

    def test_timeframe_by_market(self):
        for market, expected_tf in DEFAULT_TIMEFRAMES.items():
            result = calculate_targets(Decimal("100"), {"value": 5}, "BUY", market)
            assert result["timeframe"] == expected_tf

    def test_unknown_market_timeframe(self):
        result = calculate_targets(Decimal("100"), {"value": 5}, "BUY", "options")
        assert result["timeframe"] == "1-2 weeks"

    def test_risk_reward_ratio(self):
        """Risk:Reward always >= 1:2 (target distance >= 2x stop distance)."""
        result = calculate_targets(Decimal("1000"), {"value": 50}, "BUY", "stock")
        target_distance = result["target_price"] - Decimal("1000")
        stop_distance = Decimal("1000") - result["stop_loss"]
        assert target_distance >= 2 * stop_distance

    def test_hold_targets(self):
        """HOLD uses equidistant targets (same as BUY)."""
        hold = calculate_targets(Decimal("1000"), {"value": 50}, "HOLD", "stock")
        buy = calculate_targets(Decimal("1000"), {"value": 50}, "BUY", "stock")
        assert hold["target_price"] == buy["target_price"]
        assert hold["stop_loss"] == buy["stop_loss"]


# ═══════════════════════════════════════════════════════════
# SignalGenerator
# ═══════════════════════════════════════════════════════════

class TestSignalGenerator:
    @pytest.mark.asyncio
    async def test_insufficient_data_returns_none(self):
        """If market data < MIN_DATA_POINTS, return None."""
        mock_db = AsyncMock()

        # Mock _fetch_market_data to return too few rows
        gen = SignalGenerator(db=mock_db)
        small_df = pd.DataFrame({
            "open": [100.0] * 10,
            "high": [105.0] * 10,
            "low": [95.0] * 10,
            "close": [102.0] * 10,
            "volume": [1000.0] * 10,
            "timestamp": pd.date_range("2026-01-01", periods=10, freq="D"),
        })
        gen._fetch_market_data = AsyncMock(return_value=small_df)
        gen._has_recent_signal = AsyncMock(return_value=False)

        result = await gen.generate_for_symbol("HDFCBANK.NS", "stock")
        assert result is None

    @pytest.mark.asyncio
    async def test_cooldown_skips_signal(self):
        """If a recent signal exists (within cooldown), skip."""
        mock_db = AsyncMock()
        gen = SignalGenerator(db=mock_db)
        gen._has_recent_signal = AsyncMock(return_value=True)

        result = await gen.generate_for_symbol("BTCUSDT", "crypto")
        assert result is None

    @pytest.mark.asyncio
    async def test_hold_signal_skipped(self):
        """HOLD signals are not persisted."""
        mock_db = AsyncMock()
        gen = SignalGenerator(db=mock_db)

        # Generate enough data
        n = MIN_DATA_POINTS + 200
        df = pd.DataFrame({
            "open": [100.0] * n,
            "high": [101.0] * n,
            "low": [99.0] * n,
            "close": [100.0] * n,  # Flat price → neutral signals
            "volume": [1000.0] * n,
            "timestamp": pd.date_range("2025-01-01", periods=n, freq="D"),
        })

        gen._fetch_market_data = AsyncMock(return_value=df)
        gen._has_recent_signal = AsyncMock(return_value=False)

        # Mock sentiment to return neutral
        gen.sentiment_engine.analyze_sentiment = AsyncMock(return_value={
            "sentiment_score": 50, "confidence_in_analysis": 80,
        })
        gen.reasoner.generate_reasoning = AsyncMock(return_value="Neutral outlook.")

        result = await gen.generate_for_symbol("FLAT.NS", "stock")
        # Flat data → HOLD → should return None
        assert result is None
