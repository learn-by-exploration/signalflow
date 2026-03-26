"""Tester 5: The Data Poisoner — Ingestion & Pipeline Edge Cases.

Tests data validators, candle integrity, market hours, and the full
analysis pipeline with poisoned, empty, and extreme data.
"""

import math
import pytest
import numpy as np
import pandas as pd
from decimal import Decimal, InvalidOperation
from datetime import datetime, time, timezone

from app.services.data_ingestion.validators import validate_candle
from app.services.data_ingestion.market_hours import is_nse_open, is_forex_open, is_crypto_open
from app.services.analysis.indicators import TechnicalAnalyzer


# =========================================================================
# Candle Validator — Exhaustive edge cases
# =========================================================================

class TestCandleValidatorBreaker:
    """Try every way to get an invalid candle past the validator."""

    def test_valid_candle_passes(self):
        candle = {"open": "100", "high": "110", "low": "95", "close": "105"}
        valid, err = validate_candle(candle, "TEST")
        assert valid, f"Valid candle rejected: {err}"

    def test_negative_open(self):
        candle = {"open": "-100", "high": "110", "low": "95", "close": "105"}
        valid, _ = validate_candle(candle, "TEST")
        assert not valid

    def test_negative_high(self):
        candle = {"open": "100", "high": "-110", "low": "95", "close": "105"}
        valid, _ = validate_candle(candle, "TEST")
        assert not valid

    def test_negative_low(self):
        candle = {"open": "100", "high": "110", "low": "-95", "close": "105"}
        valid, _ = validate_candle(candle, "TEST")
        assert not valid

    def test_negative_close(self):
        candle = {"open": "100", "high": "110", "low": "95", "close": "-105"}
        valid, _ = validate_candle(candle, "TEST")
        assert not valid

    def test_high_less_than_low(self):
        """high < low is invalid."""
        candle = {"open": "100", "high": "90", "low": "95", "close": "100"}
        valid, _ = validate_candle(candle, "TEST")
        assert not valid

    def test_high_less_than_open(self):
        """high < open is invalid."""
        candle = {"open": "100", "high": "99", "low": "95", "close": "98"}
        valid, _ = validate_candle(candle, "TEST")
        assert not valid

    def test_low_greater_than_close(self):
        """low > close is invalid."""
        candle = {"open": "100", "high": "110", "low": "106", "close": "105"}
        valid, _ = validate_candle(candle, "TEST")
        assert not valid

    def test_nan_price(self):
        """NaN price should be rejected."""
        candle = {"open": "NaN", "high": "110", "low": "95", "close": "105"}
        valid, _ = validate_candle(candle, "TEST")
        assert not valid

    def test_infinity_price(self):
        """Infinity price should be rejected."""
        candle = {"open": "Infinity", "high": "110", "low": "95", "close": "105"}
        valid, _ = validate_candle(candle, "TEST")
        assert not valid

    def test_negative_infinity_price(self):
        """Negative infinity should be rejected."""
        candle = {"open": "100", "high": "110", "low": "-Infinity", "close": "105"}
        valid, _ = validate_candle(candle, "TEST")
        assert not valid

    def test_empty_string_price(self):
        """Empty string should be rejected."""
        candle = {"open": "", "high": "110", "low": "95", "close": "105"}
        valid, _ = validate_candle(candle, "TEST")
        assert not valid

    def test_none_price(self):
        """None price should be rejected."""
        candle = {"open": None, "high": "110", "low": "95", "close": "105"}
        valid, _ = validate_candle(candle, "TEST")
        assert not valid

    def test_missing_key(self):
        """Missing 'close' key should be rejected."""
        candle = {"open": "100", "high": "110", "low": "95"}
        valid, _ = validate_candle(candle, "TEST")
        assert not valid

    def test_zero_prices(self):
        """All zero prices — valid but degenerate."""
        candle = {"open": "0", "high": "0", "low": "0", "close": "0"}
        valid, _ = validate_candle(candle, "TEST")
        assert valid  # 0 is a valid number

    def test_very_small_decimal(self):
        """Very small decimal values (altcoin-like)."""
        candle = {
            "open": "0.00000001",
            "high": "0.00000002",
            "low": "0.00000001",
            "close": "0.00000002",
        }
        valid, err = validate_candle(candle, "TEST")
        assert valid, f"Tiny decimals rejected: {err}"

    def test_very_large_values(self):
        """Very large values (like Japanese Yen denominated)."""
        candle = {
            "open": "9999999999.9999",
            "high": "9999999999.9999",
            "low": "9999999999.9998",
            "close": "9999999999.9999",
        }
        valid, err = validate_candle(candle, "TEST")
        assert valid, f"Large values rejected: {err}"

    def test_sql_injection_string(self):
        """SQL injection in price field should fail Decimal parse."""
        candle = {"open": "'; DROP TABLE--", "high": "110", "low": "95", "close": "105"}
        valid, _ = validate_candle(candle, "TEST")
        assert not valid


# =========================================================================
# Market Hours — Edge cases
# =========================================================================

class TestMarketHoursBreaker:
    """Test market hours utility edge cases."""

    def test_crypto_always_open(self):
        """Crypto market is always open."""
        assert is_crypto_open() is True

    def test_market_hours_return_bool(self):
        """All market hours functions return bool."""
        assert isinstance(is_nse_open(), bool)
        assert isinstance(is_forex_open(), bool)
        assert isinstance(is_crypto_open(), bool)


# =========================================================================
# TechnicalAnalyzer — Edge cases
# =========================================================================

class TestTechnicalAnalyzerBreaker:
    """Break the technical analyzer with extreme data."""

    def _make_df(self, n: int = 50, close_val: float = 100.0) -> pd.DataFrame:
        """Create a simple OHLCV DataFrame."""
        dates = pd.date_range("2025-01-01", periods=n, freq="D")
        data = {
            "open": [close_val] * n,
            "high": [close_val + 1] * n,
            "low": [close_val - 1] * n,
            "close": [close_val] * n,
            "volume": [1000000] * n,
        }
        return pd.DataFrame(data, index=dates)

    def test_constructor_missing_columns(self):
        """DataFrame missing required columns should raise ValueError."""
        df = pd.DataFrame({"close": [100, 101, 102]})
        with pytest.raises(ValueError, match="missing required columns"):
            TechnicalAnalyzer(df)

    def test_empty_dataframe(self):
        """Empty DataFrame should not crash."""
        df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.compute_rsi()
        assert result["signal"] == "neutral"
        assert result["strength"] == 50

    def test_single_row_dataframe(self):
        """Single row — not enough data for any indicator."""
        df = self._make_df(n=1)
        analyzer = TechnicalAnalyzer(df)
        rsi = analyzer.compute_rsi()
        assert rsi["value"] is None
        macd = analyzer.compute_macd()
        assert macd["macd_line"] is None

    def test_all_same_prices(self):
        """All prices identical — RSI should be neutral."""
        df = self._make_df(n=50, close_val=100.0)
        analyzer = TechnicalAnalyzer(df)
        rsi = analyzer.compute_rsi()
        # With no change, RSI is undefined (division by zero) — should handle
        assert rsi["signal"] in ("neutral", "buy", "sell")

    def test_monotonically_increasing(self):
        """Steadily increasing prices — RSI should be overbought."""
        n = 50
        dates = pd.date_range("2025-01-01", periods=n, freq="D")
        prices = [100 + i for i in range(n)]
        df = pd.DataFrame({
            "open": prices,
            "high": [p + 1 for p in prices],
            "low": [p - 0.5 for p in prices],
            "close": prices,
            "volume": [1000000] * n,
        }, index=dates)
        analyzer = TechnicalAnalyzer(df)
        rsi = analyzer.compute_rsi()
        if rsi["value"] is not None:
            assert rsi["value"] > 70  # Should be very overbought

    def test_monotonically_decreasing(self):
        """Steadily decreasing prices — RSI should be oversold."""
        n = 50
        dates = pd.date_range("2025-01-01", periods=n, freq="D")
        prices = [200 - i for i in range(n)]
        df = pd.DataFrame({
            "open": prices,
            "high": [p + 0.5 for p in prices],
            "low": [p - 1 for p in prices],
            "close": prices,
            "volume": [1000000] * n,
        }, index=dates)
        analyzer = TechnicalAnalyzer(df)
        rsi = analyzer.compute_rsi()
        if rsi["value"] is not None:
            assert rsi["value"] < 30  # Should be oversold

    def test_nan_in_close_prices(self):
        """NaN in close prices should not crash indicators."""
        df = self._make_df(n=50)
        df.loc[df.index[25], "close"] = np.nan
        analyzer = TechnicalAnalyzer(df)
        rsi = analyzer.compute_rsi()
        assert isinstance(rsi, dict)

    def test_zero_volume(self):
        """Zero volume — volume ratio should handle."""
        df = self._make_df(n=50)
        df["volume"] = 0
        analyzer = TechnicalAnalyzer(df)
        vol = analyzer.compute_volume_ratio()
        assert vol is not None

    def test_negative_volume(self):
        """Negative volume — should not crash."""
        df = self._make_df(n=50)
        df["volume"] = -1000
        analyzer = TechnicalAnalyzer(df)
        vol = analyzer.compute_volume_ratio()
        assert isinstance(vol, dict)

    def test_bollinger_with_zero_std_dev(self):
        """All same prices → std_dev = 0 → band_width = 0."""
        df = self._make_df(n=50, close_val=100.0)
        analyzer = TechnicalAnalyzer(df)
        bb = analyzer.compute_bollinger()
        # band_width == 0 should give percent_b = 0.5 (fallback)
        if bb["percent_b"] is not None:
            assert not math.isnan(bb["percent_b"])

    def test_macd_with_not_enough_data(self):
        """Less than 35 rows (26 + 9) — insufficient for MACD."""
        df = self._make_df(n=20)
        analyzer = TechnicalAnalyzer(df)
        macd = analyzer.compute_macd()
        assert macd["macd_line"] is None
        assert macd["signal"] == "neutral"

    def test_full_analysis_returns_all_keys(self):
        """full_analysis should return all indicator keys."""
        df = self._make_df(n=50)
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.full_analysis()
        expected_keys = {"rsi", "macd", "bollinger", "volume", "sma_cross", "atr"}
        assert expected_keys.issubset(set(result.keys())), \
            f"Missing keys: {expected_keys - set(result.keys())}"

    def test_extremely_volatile_data(self):
        """Data with extreme swings — test numerical stability."""
        n = 50
        dates = pd.date_range("2025-01-01", periods=n, freq="D")
        # Alternating between 1 and 1000
        close_prices = [1 if i % 2 == 0 else 1000 for i in range(n)]
        df = pd.DataFrame({
            "open": close_prices,
            "high": [max(close_prices[i], close_prices[min(i+1, n-1)]) + 1 for i in range(n)],
            "low": [min(close_prices[i], close_prices[max(i-1, 0)]) - 1 for i in range(n)],
            "close": close_prices,
            "volume": [1000000] * n,
        }, index=dates)
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.full_analysis()
        # Should not have NaN or Infinity in any score
        for key in ["rsi", "macd", "bollinger"]:
            indicator = result.get(key, {})
            for field in ["value", "strength"]:
                val = indicator.get(field)
                if val is not None and isinstance(val, (int, float)):
                    assert not math.isnan(val), f"{key}.{field} is NaN"
                    assert not math.isinf(val), f"{key}.{field} is Infinity"
