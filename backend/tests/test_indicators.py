"""Unit tests for TechnicalAnalyzer — all 6 indicators."""

import numpy as np
import pandas as pd
import pytest

from app.services.analysis.indicators import TechnicalAnalyzer


def _make_ohlcv(
    n: int = 250,
    start_price: float = 100.0,
    trend: str = "up",
    volatility: float = 0.02,
) -> pd.DataFrame:
    """Generate synthetic OHLCV data for testing.

    Args:
        n: Number of data points.
        start_price: Starting close price.
        trend: 'up', 'down', or 'flat'.
        volatility: Daily price volatility as fraction.
    """
    np.random.seed(42)
    drift = {"up": 0.001, "down": -0.001, "flat": 0.0}[trend]

    closes = [start_price]
    for _ in range(1, n):
        change = drift + np.random.normal(0, volatility)
        closes.append(closes[-1] * (1 + change))

    closes = np.array(closes)
    highs = closes * (1 + np.abs(np.random.normal(0, volatility / 2, n)))
    lows = closes * (1 - np.abs(np.random.normal(0, volatility / 2, n)))
    opens = (closes + np.roll(closes, 1)) / 2
    opens[0] = start_price
    volumes = np.random.randint(100000, 1000000, n).astype(float)

    return pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    })


class TestTechnicalAnalyzerInit:
    """Test analyzer initialization and validation."""

    def test_valid_dataframe(self) -> None:
        df = _make_ohlcv(50)
        analyzer = TechnicalAnalyzer(df)
        assert len(analyzer.df) == 50

    def test_missing_columns_raises(self) -> None:
        df = pd.DataFrame({"close": [1, 2, 3]})
        with pytest.raises(ValueError, match="missing required columns"):
            TechnicalAnalyzer(df)

    def test_does_not_mutate_input(self) -> None:
        df = _make_ohlcv(50)
        original_len = len(df)
        TechnicalAnalyzer(df)
        assert len(df) == original_len


class TestRSI:
    """Test RSI computation."""

    def test_rsi_normal_data(self) -> None:
        df = _make_ohlcv(250, trend="up")
        result = TechnicalAnalyzer(df).compute_rsi()
        assert result["value"] is not None
        assert 0 <= result["value"] <= 100
        assert result["signal"] in ("buy", "sell", "neutral")
        assert 0 <= result["strength"] <= 100

    def test_rsi_insufficient_data(self) -> None:
        df = _make_ohlcv(10)
        result = TechnicalAnalyzer(df).compute_rsi(period=14)
        assert result["value"] is None
        assert result["signal"] == "neutral"

    def test_rsi_oversold(self) -> None:
        # Create a strong downtrend to push RSI below 30
        df = _make_ohlcv(250, trend="down", volatility=0.01)
        result = TechnicalAnalyzer(df).compute_rsi()
        # In a persistent downtrend, RSI should be on the lower side
        if result["value"] is not None and result["value"] < 30:
            assert result["signal"] == "buy"

    def test_rsi_overbought(self) -> None:
        df = _make_ohlcv(250, trend="up", volatility=0.01)
        result = TechnicalAnalyzer(df).compute_rsi()
        if result["value"] is not None and result["value"] > 70:
            assert result["signal"] == "sell"

    def test_rsi_custom_period(self) -> None:
        df = _make_ohlcv(100)
        result = TechnicalAnalyzer(df).compute_rsi(period=7)
        assert result["value"] is not None


class TestMACD:
    """Test MACD computation."""

    def test_macd_normal_data(self) -> None:
        df = _make_ohlcv(250, trend="up")
        result = TechnicalAnalyzer(df).compute_macd()
        assert result["macd_line"] is not None
        assert result["signal_line"] is not None
        assert result["histogram"] is not None
        assert result["signal"] in ("buy", "sell", "neutral")

    def test_macd_insufficient_data(self) -> None:
        df = _make_ohlcv(20)
        result = TechnicalAnalyzer(df).compute_macd()
        assert result["macd_line"] is None

    def test_macd_uptrend_bullish(self) -> None:
        df = _make_ohlcv(250, trend="up")
        result = TechnicalAnalyzer(df).compute_macd()
        # In a strong uptrend, MACD should generally be bullish
        if result["histogram"] is not None and result["histogram"] > 0:
            assert result["signal"] == "buy"

    def test_macd_downtrend_bearish(self) -> None:
        df = _make_ohlcv(250, trend="down")
        result = TechnicalAnalyzer(df).compute_macd()
        if result["histogram"] is not None and result["histogram"] < 0:
            assert result["signal"] == "sell"


class TestBollinger:
    """Test Bollinger Bands computation."""

    def test_bollinger_normal_data(self) -> None:
        df = _make_ohlcv(250)
        result = TechnicalAnalyzer(df).compute_bollinger()
        assert result["upper"] is not None
        assert result["lower"] is not None
        assert result["middle"] is not None
        assert result["percent_b"] is not None
        assert result["lower"] < result["middle"] < result["upper"]

    def test_bollinger_insufficient_data(self) -> None:
        df = _make_ohlcv(15)
        result = TechnicalAnalyzer(df).compute_bollinger()
        assert result["upper"] is None

    def test_bollinger_percent_b_range(self) -> None:
        df = _make_ohlcv(250)
        result = TechnicalAnalyzer(df).compute_bollinger()
        # %B should generally be between -0.5 and 1.5 for normal data
        assert result["percent_b"] is not None
        assert -1.0 <= result["percent_b"] <= 2.0


class TestVolume:
    """Test volume ratio computation."""

    def test_volume_normal_data(self) -> None:
        df = _make_ohlcv(250)
        result = TechnicalAnalyzer(df).compute_volume_ratio()
        assert result["ratio"] is not None
        assert result["ratio"] > 0
        assert result["signal"] in ("buy", "sell", "neutral")

    def test_volume_insufficient_data(self) -> None:
        df = _make_ohlcv(10)
        result = TechnicalAnalyzer(df).compute_volume_ratio()
        assert result["ratio"] is None

    def test_volume_no_volume_column(self) -> None:
        df = _make_ohlcv(50).drop(columns=["volume"])
        result = TechnicalAnalyzer(df).compute_volume_ratio()
        assert result["ratio"] is None
        assert result["signal"] == "neutral"

    def test_volume_zero_volume(self) -> None:
        df = _make_ohlcv(50)
        df["volume"] = 0.0
        result = TechnicalAnalyzer(df).compute_volume_ratio()
        assert result["ratio"] is None


class TestSMACross:
    """Test SMA crossover computation."""

    def test_sma_normal_data(self) -> None:
        df = _make_ohlcv(250, trend="up")
        result = TechnicalAnalyzer(df).compute_sma_cross()
        assert result["fast_sma"] is not None
        assert result["slow_sma"] is not None
        assert isinstance(result["golden_cross"], bool)
        assert isinstance(result["death_cross"], bool)

    def test_sma_insufficient_data(self) -> None:
        df = _make_ohlcv(100)
        result = TechnicalAnalyzer(df).compute_sma_cross(fast=50, slow=200)
        assert result["fast_sma"] is None

    def test_sma_uptrend_bullish(self) -> None:
        df = _make_ohlcv(250, trend="up")
        result = TechnicalAnalyzer(df).compute_sma_cross()
        # In uptrend, fast SMA should be above slow SMA
        if result["fast_sma"] is not None and result["slow_sma"] is not None:
            if result["fast_sma"] > result["slow_sma"]:
                assert result["signal"] == "buy"


class TestATR:
    """Test ATR computation."""

    def test_atr_normal_data(self) -> None:
        df = _make_ohlcv(250)
        result = TechnicalAnalyzer(df).compute_atr()
        assert result["value"] is not None
        assert result["value"] > 0
        assert result["suggested_stop_distance"] is not None

    def test_atr_insufficient_data(self) -> None:
        df = _make_ohlcv(10)
        result = TechnicalAnalyzer(df).compute_atr()
        assert result["value"] is None

    def test_atr_stop_distance(self) -> None:
        df = _make_ohlcv(250)
        result = TechnicalAnalyzer(df).compute_atr()
        # Stop distance should equal 1× ATR
        if result["value"] is not None:
            assert abs(result["suggested_stop_distance"] - result["value"]) < 0.001


class TestFullAnalysis:
    """Test the combined full_analysis method."""

    def test_full_analysis_returns_all_keys(self) -> None:
        df = _make_ohlcv(250)
        result = TechnicalAnalyzer(df).full_analysis()
        assert set(result.keys()) == {"rsi", "macd", "bollinger", "volume", "sma_cross", "atr"}

    def test_full_analysis_with_sufficient_data(self) -> None:
        df = _make_ohlcv(250, trend="up")
        result = TechnicalAnalyzer(df).full_analysis()
        # All indicators should have values with 250 data points
        assert result["rsi"]["value"] is not None
        assert result["macd"]["macd_line"] is not None
        assert result["bollinger"]["upper"] is not None
        assert result["volume"]["ratio"] is not None
        assert result["sma_cross"]["fast_sma"] is not None
        assert result["atr"]["value"] is not None

    def test_full_analysis_with_minimal_data(self) -> None:
        df = _make_ohlcv(10)
        result = TechnicalAnalyzer(df).full_analysis()
        # Most indicators should return None values
        assert result["rsi"]["value"] is None
        assert result["macd"]["macd_line"] is None
