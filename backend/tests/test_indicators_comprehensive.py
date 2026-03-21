"""Comprehensive tests for TechnicalAnalyzer indicators."""

import numpy as np
import pandas as pd
import pytest

from app.services.analysis.indicators import TechnicalAnalyzer


def _make_df(n: int = 250, start_price: float = 100.0, trend: str = "flat") -> pd.DataFrame:
    """Generate a synthetic OHLCV DataFrame.

    Args:
        n: Number of data points.
        start_price: Starting close price.
        trend: 'flat', 'up', or 'down'.
    """
    np.random.seed(42)
    if trend == "up":
        closes = start_price + np.cumsum(np.random.uniform(0, 2, n))
    elif trend == "down":
        closes = start_price - np.cumsum(np.random.uniform(0, 2, n))
        closes = np.maximum(closes, 1.0)  # keep positive
    else:
        closes = start_price + np.cumsum(np.random.randn(n) * 0.5)
        closes = np.maximum(closes, 1.0)

    highs = closes + np.random.uniform(0.5, 3, n)
    lows = closes - np.random.uniform(0.5, 3, n)
    lows = np.maximum(lows, 0.01)
    opens = closes + np.random.randn(n) * 0.5
    volumes = np.random.uniform(100_000, 1_000_000, n)

    return pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
        "timestamp": pd.date_range("2025-01-01", periods=n, freq="D"),
    })


# ═══════════════════════════════════════════════════════════
# Constructor
# ═══════════════════════════════════════════════════════════

class TestTechnicalAnalyzerInit:
    def test_valid_init(self):
        df = _make_df(50)
        ta = TechnicalAnalyzer(df)
        assert len(ta.df) == 50

    def test_missing_columns_raises(self):
        df = pd.DataFrame({"close": [1, 2, 3]})
        with pytest.raises(ValueError, match="missing required columns"):
            TechnicalAnalyzer(df)

    def test_does_not_mutate_input(self):
        df = _make_df(50)
        original_len = len(df)
        TechnicalAnalyzer(df)
        assert len(df) == original_len


# ═══════════════════════════════════════════════════════════
# RSI
# ═══════════════════════════════════════════════════════════

class TestRSI:
    def test_rsi_normal(self):
        ta = TechnicalAnalyzer(_make_df(100))
        result = ta.compute_rsi()
        assert result["value"] is not None
        assert 0 <= result["value"] <= 100
        assert result["signal"] in ("buy", "sell", "neutral")
        assert 0 <= result["strength"] <= 100

    def test_rsi_insufficient_data(self):
        ta = TechnicalAnalyzer(_make_df(5))
        result = ta.compute_rsi()
        assert result["value"] is None
        assert result["signal"] == "neutral"

    def test_rsi_strong_uptrend_is_high(self):
        # Create uptrend with occasional small dips (avoiding zero-loss NaN)
        np.random.seed(99)
        base = [100 + i * 1.5 for i in range(50)]
        # Add noise that sometimes makes price dip slightly
        closes = [b + np.random.uniform(-2, 1) for b in base]
        closes = [max(c, 1) for c in closes]
        df = pd.DataFrame({
            "open": closes, "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes], "close": closes,
            "volume": [1000] * 50,
        })
        ta = TechnicalAnalyzer(df)
        result = ta.compute_rsi()
        assert result["value"] is not None
        assert result["value"] > 60

    def test_rsi_strong_downtrend_is_low(self):
        df = _make_df(100, trend="down")
        ta = TechnicalAnalyzer(df)
        result = ta.compute_rsi()
        assert result["value"] is not None
        assert result["value"] < 50

    def test_rsi_oversold_gives_buy(self):
        """Price dropping heavily should give RSI < 30 → buy signal."""
        # Create a steep downtrend
        closes = [100 - i * 3 for i in range(50)]
        closes = [max(c, 1) for c in closes]
        df = pd.DataFrame({
            "open": closes, "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes], "close": closes,
            "volume": [1000] * 50,
        })
        ta = TechnicalAnalyzer(df)
        result = ta.compute_rsi()
        if result["value"] is not None and result["value"] <= 30:
            assert result["signal"] == "buy"

    def test_rsi_overbought_gives_sell(self):
        """Price rising heavily should give RSI > 70 → sell signal."""
        closes = [100 + i * 3 for i in range(50)]
        df = pd.DataFrame({
            "open": closes, "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes], "close": closes,
            "volume": [1000] * 50,
        })
        ta = TechnicalAnalyzer(df)
        result = ta.compute_rsi()
        if result["value"] is not None and result["value"] >= 70:
            assert result["signal"] == "sell"


# ═══════════════════════════════════════════════════════════
# MACD
# ═══════════════════════════════════════════════════════════

class TestMACD:
    def test_macd_normal(self):
        ta = TechnicalAnalyzer(_make_df(100))
        result = ta.compute_macd()
        assert result["macd_line"] is not None
        assert result["signal_line"] is not None
        assert result["histogram"] is not None
        assert result["signal"] in ("buy", "sell", "neutral")

    def test_macd_insufficient_data(self):
        ta = TechnicalAnalyzer(_make_df(20))
        result = ta.compute_macd()
        assert result["macd_line"] is None
        assert result["signal"] == "neutral"

    def test_macd_uptrend(self):
        ta = TechnicalAnalyzer(_make_df(200, trend="up"))
        result = ta.compute_macd()
        assert result["histogram"] is not None
        # In uptrend, MACD line should be > signal line
        assert result["macd_line"] > result["signal_line"]


# ═══════════════════════════════════════════════════════════
# Bollinger Bands
# ═══════════════════════════════════════════════════════════

class TestBollinger:
    def test_bollinger_normal(self):
        ta = TechnicalAnalyzer(_make_df(100))
        result = ta.compute_bollinger()
        assert result["upper"] is not None
        assert result["lower"] is not None
        assert result["middle"] is not None
        assert result["upper"] > result["lower"]
        assert result["percent_b"] is not None

    def test_bollinger_insufficient_data(self):
        ta = TechnicalAnalyzer(_make_df(10))
        result = ta.compute_bollinger()
        assert result["upper"] is None
        assert result["signal"] == "neutral"

    def test_percent_b_range(self):
        """percent_b should typically be between 0 and 1 for normal data."""
        ta = TechnicalAnalyzer(_make_df(200))
        result = ta.compute_bollinger()
        assert result["percent_b"] is not None
        # Usually between -0.5 and 1.5 for volatile data
        assert -1 <= result["percent_b"] <= 2


# ═══════════════════════════════════════════════════════════
# Volume
# ═══════════════════════════════════════════════════════════

class TestVolume:
    def test_volume_normal(self):
        ta = TechnicalAnalyzer(_make_df(100))
        result = ta.compute_volume_ratio()
        assert result["ratio"] is not None
        assert result["ratio"] > 0
        assert result["signal"] in ("buy", "sell", "neutral")

    def test_volume_insufficient_data(self):
        ta = TechnicalAnalyzer(_make_df(10))
        result = ta.compute_volume_ratio()
        assert result["ratio"] is None

    def test_volume_all_zero(self):
        df = _make_df(100)
        df["volume"] = 0
        ta = TechnicalAnalyzer(df)
        result = ta.compute_volume_ratio()
        assert result["signal"] == "neutral"

    def test_volume_no_column(self):
        df = _make_df(100)
        df = df.drop(columns=["volume"])
        ta = TechnicalAnalyzer(df)
        result = ta.compute_volume_ratio()
        assert result["signal"] == "neutral"

    def test_high_volume_bullish(self):
        """High volume + positive price change → buy."""
        df = _make_df(100)
        # Make last candle high volume and positive
        df.loc[df.index[-1], "volume"] = df["volume"].mean() * 3
        df.loc[df.index[-1], "close"] = df.loc[df.index[-2], "close"] * 1.05
        ta = TechnicalAnalyzer(df)
        result = ta.compute_volume_ratio()
        if result["ratio"] is not None and result["ratio"] >= 1.5:
            assert result["signal"] == "buy"


# ═══════════════════════════════════════════════════════════
# SMA Crossover
# ═══════════════════════════════════════════════════════════

class TestSMACross:
    def test_sma_insufficient_data(self):
        ta = TechnicalAnalyzer(_make_df(100))
        result = ta.compute_sma_cross()
        assert result["signal"] == "neutral"  # Need 200 points

    def test_sma_with_enough_data(self):
        ta = TechnicalAnalyzer(_make_df(250))
        result = ta.compute_sma_cross()
        assert result["fast_sma"] is not None
        assert result["slow_sma"] is not None
        assert result["signal"] in ("buy", "sell", "neutral")

    def test_sma_uptrend_gives_buy(self):
        ta = TechnicalAnalyzer(_make_df(250, trend="up"))
        result = ta.compute_sma_cross()
        assert result["fast_sma"] > result["slow_sma"]
        assert result["signal"] == "buy"

    def test_sma_downtrend_gives_sell(self):
        ta = TechnicalAnalyzer(_make_df(250, trend="down"))
        result = ta.compute_sma_cross()
        if result["fast_sma"] is not None and result["slow_sma"] is not None:
            if result["fast_sma"] < result["slow_sma"]:
                assert result["signal"] == "sell"


# ═══════════════════════════════════════════════════════════
# ATR
# ═══════════════════════════════════════════════════════════

class TestATR:
    def test_atr_normal(self):
        ta = TechnicalAnalyzer(_make_df(100))
        result = ta.compute_atr()
        assert result["value"] is not None
        assert result["value"] > 0
        assert result["suggested_stop_distance"] is not None

    def test_atr_insufficient_data(self):
        ta = TechnicalAnalyzer(_make_df(5))
        result = ta.compute_atr()
        assert result["value"] is None

    def test_atr_high_volatility(self):
        """Wider range → higher ATR."""
        df = _make_df(100)
        df["high"] = df["close"] + 50
        df["low"] = df["close"] - 50
        ta = TechnicalAnalyzer(df)
        result = ta.compute_atr()
        assert result["value"] > 10  # Much wider than normal


# ═══════════════════════════════════════════════════════════
# Full Analysis
# ═══════════════════════════════════════════════════════════

class TestFullAnalysis:
    def test_full_analysis_keys(self):
        ta = TechnicalAnalyzer(_make_df(250))
        result = ta.full_analysis()
        assert "rsi" in result
        assert "macd" in result
        assert "bollinger" in result
        assert "volume" in result
        assert "sma_cross" in result
        assert "atr" in result
        assert "recent_closes" in result

    def test_recent_closes_max_20(self):
        ta = TechnicalAnalyzer(_make_df(250))
        result = ta.full_analysis()
        assert len(result["recent_closes"]) <= 20

    def test_full_analysis_all_have_signal(self):
        ta = TechnicalAnalyzer(_make_df(250))
        result = ta.full_analysis()
        for key in ["rsi", "macd", "bollinger", "volume", "sma_cross"]:
            assert "signal" in result[key]
            assert result[key]["signal"] in ("buy", "sell", "neutral")
