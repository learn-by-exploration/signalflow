"""Technical analysis indicators for market data.

Computes RSI, MACD, Bollinger Bands, Volume analysis, SMA crossovers, and ATR
on OHLCV DataFrames. Each indicator returns a dict with value, signal, and strength.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Minimum data points required per indicator
MIN_PERIODS = {
    "rsi": 15,
    "macd": 35,
    "bollinger": 21,
    "volume": 20,
    "sma": 200,
    "atr": 15,
}


class TechnicalAnalyzer:
    """Computes technical indicators on OHLCV price data.

    Args:
        df: DataFrame with columns: open, high, low, close, volume (lowercase).
            Must be sorted by timestamp ascending.
    """

    def __init__(self, df: pd.DataFrame) -> None:
        required = {"open", "high", "low", "close"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"DataFrame missing required columns: {missing}")
        self.df = df.copy()

    def compute_rsi(self, period: int = 14) -> dict[str, Any]:
        """Compute Relative Strength Index.

        Args:
            period: RSI lookback period.

        Returns:
            Dict with value (float), signal (str), and strength (int 0-100).
        """
        if len(self.df) < period + 1:
            return {"value": None, "signal": "neutral", "strength": 50}

        delta = self.df["close"].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi_value = float(rsi.iloc[-1])

        if np.isnan(rsi_value):
            return {"value": None, "signal": "neutral", "strength": 50}

        # Signal logic
        if rsi_value <= 30:
            signal = "buy"
            strength = int(min(100, (30 - rsi_value) * 3.33 + 70))
        elif rsi_value >= 70:
            signal = "sell"
            strength = int(min(100, (rsi_value - 70) * 3.33 + 70))
        elif rsi_value <= 40:
            signal = "buy"
            strength = int(50 + (40 - rsi_value))
        elif rsi_value >= 60:
            signal = "sell"
            strength = int(50 + (rsi_value - 60))
        else:
            signal = "neutral"
            strength = 50

        return {"value": round(rsi_value, 2), "signal": signal, "strength": strength}

    def compute_macd(
        self, fast: int = 12, slow: int = 26, signal_period: int = 9
    ) -> dict[str, Any]:
        """Compute MACD (Moving Average Convergence Divergence).

        Args:
            fast: Fast EMA period.
            slow: Slow EMA period.
            signal_period: Signal line EMA period.

        Returns:
            Dict with macd_line, signal_line, histogram, signal, and strength.
        """
        if len(self.df) < slow + signal_period:
            return {
                "macd_line": None,
                "signal_line": None,
                "histogram": None,
                "signal": "neutral",
                "strength": 50,
            }

        close = self.df["close"]
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        macd_val = float(macd_line.iloc[-1])
        signal_val = float(signal_line.iloc[-1])
        hist_val = float(histogram.iloc[-1])

        if any(np.isnan(v) for v in [macd_val, signal_val, hist_val]):
            return {
                "macd_line": None,
                "signal_line": None,
                "histogram": None,
                "signal": "neutral",
                "strength": 50,
            }

        # Detect crossover signals
        prev_hist = float(histogram.iloc[-2]) if len(histogram) > 1 else 0

        if hist_val > 0 and prev_hist <= 0:
            signal = "buy"
            strength = min(100, int(70 + abs(hist_val) * 100))
        elif hist_val < 0 and prev_hist >= 0:
            signal = "sell"
            strength = min(100, int(70 + abs(hist_val) * 100))
        elif hist_val > 0:
            signal = "buy"
            strength = min(85, int(55 + abs(hist_val) * 50))
        elif hist_val < 0:
            signal = "sell"
            strength = min(85, int(55 + abs(hist_val) * 50))
        else:
            signal = "neutral"
            strength = 50

        return {
            "macd_line": round(macd_val, 4),
            "signal_line": round(signal_val, 4),
            "histogram": round(hist_val, 4),
            "signal": signal,
            "strength": strength,
        }

    def compute_bollinger(self, period: int = 20, std_dev: float = 2.0) -> dict[str, Any]:
        """Compute Bollinger Bands.

        Args:
            period: Moving average lookback period.
            std_dev: Number of standard deviations for bands.

        Returns:
            Dict with upper, lower, middle, percent_b, signal, and strength.
        """
        if len(self.df) < period:
            return {
                "upper": None,
                "lower": None,
                "middle": None,
                "percent_b": None,
                "signal": "neutral",
                "strength": 50,
            }

        close = self.df["close"]
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()

        upper = sma + std_dev * std
        lower = sma - std_dev * std

        upper_val = float(upper.iloc[-1])
        lower_val = float(lower.iloc[-1])
        middle_val = float(sma.iloc[-1])
        current = float(close.iloc[-1])

        if any(np.isnan(v) for v in [upper_val, lower_val, middle_val]):
            return {
                "upper": None,
                "lower": None,
                "middle": None,
                "percent_b": None,
                "signal": "neutral",
                "strength": 50,
            }

        band_width = upper_val - lower_val
        percent_b = (current - lower_val) / band_width if band_width > 0 else 0.5

        if percent_b <= 0.05:
            signal = "buy"
            strength = int(min(100, 75 + (0.05 - percent_b) * 500))
        elif percent_b >= 0.95:
            signal = "sell"
            strength = int(min(100, 75 + (percent_b - 0.95) * 500))
        elif percent_b <= 0.2:
            signal = "buy"
            strength = int(55 + (0.2 - percent_b) * 100)
        elif percent_b >= 0.8:
            signal = "sell"
            strength = int(55 + (percent_b - 0.8) * 100)
        else:
            signal = "neutral"
            strength = 50

        return {
            "upper": round(upper_val, 4),
            "lower": round(lower_val, 4),
            "middle": round(middle_val, 4),
            "percent_b": round(percent_b, 4),
            "signal": signal,
            "strength": strength,
        }

    def compute_volume_ratio(self, period: int = 20) -> dict[str, Any]:
        """Compute volume ratio vs average.

        Args:
            period: Lookback period for average volume.

        Returns:
            Dict with ratio (float), signal (str), and strength (int).
        """
        if "volume" not in self.df.columns or len(self.df) < period:
            return {"ratio": None, "signal": "neutral", "strength": 50}

        volume = self.df["volume"]
        if volume.isna().all() or (volume == 0).all():
            return {"ratio": None, "signal": "neutral", "strength": 50}

        avg_volume = volume.rolling(window=period).mean()
        current_volume = float(volume.iloc[-1])
        avg_vol_val = float(avg_volume.iloc[-1])

        if avg_vol_val == 0 or np.isnan(avg_vol_val):
            return {"ratio": None, "signal": "neutral", "strength": 50}

        ratio = current_volume / avg_vol_val

        # High volume confirms the current price direction
        price_change = float(self.df["close"].iloc[-1] - self.df["close"].iloc[-2])

        if ratio >= 1.5 and price_change > 0:
            signal = "buy"
            strength = min(100, int(60 + (ratio - 1.5) * 20))
        elif ratio >= 1.5 and price_change < 0:
            signal = "sell"
            strength = min(100, int(60 + (ratio - 1.5) * 20))
        elif ratio >= 1.2:
            signal = "buy" if price_change > 0 else "sell" if price_change < 0 else "neutral"
            strength = 55
        else:
            signal = "neutral"
            strength = 50

        return {"ratio": round(ratio, 2), "signal": signal, "strength": strength}

    def compute_sma_cross(self, fast: int = 50, slow: int = 200) -> dict[str, Any]:
        """Compute SMA crossover (Golden Cross / Death Cross).

        Args:
            fast: Fast moving average period.
            slow: Slow moving average period.

        Returns:
            Dict with fast_sma, slow_sma, golden_cross, death_cross, signal, strength.
        """
        if len(self.df) < slow:
            return {
                "fast_sma": None,
                "slow_sma": None,
                "golden_cross": False,
                "death_cross": False,
                "signal": "neutral",
                "strength": 50,
            }

        close = self.df["close"]
        sma_fast = close.rolling(window=fast).mean()
        sma_slow = close.rolling(window=slow).mean()

        fast_val = float(sma_fast.iloc[-1])
        slow_val = float(sma_slow.iloc[-1])

        if any(np.isnan(v) for v in [fast_val, slow_val]):
            return {
                "fast_sma": None,
                "slow_sma": None,
                "golden_cross": False,
                "death_cross": False,
                "signal": "neutral",
                "strength": 50,
            }

        prev_fast = float(sma_fast.iloc[-2]) if len(sma_fast) > 1 else fast_val
        prev_slow = float(sma_slow.iloc[-2]) if len(sma_slow) > 1 else slow_val

        golden_cross = prev_fast <= prev_slow and fast_val > slow_val
        death_cross = prev_fast >= prev_slow and fast_val < slow_val

        if golden_cross:
            signal = "buy"
            strength = 90
        elif death_cross:
            signal = "sell"
            strength = 90
        elif fast_val > slow_val:
            spread_pct = (fast_val - slow_val) / slow_val * 100
            signal = "buy"
            strength = min(80, int(55 + spread_pct * 5))
        elif fast_val < slow_val:
            spread_pct = (slow_val - fast_val) / slow_val * 100
            signal = "sell"
            strength = min(80, int(55 + spread_pct * 5))
        else:
            signal = "neutral"
            strength = 50

        return {
            "fast_sma": round(fast_val, 4),
            "slow_sma": round(slow_val, 4),
            "golden_cross": golden_cross,
            "death_cross": death_cross,
            "signal": signal,
            "strength": strength,
        }

    def compute_atr(self, period: int = 14) -> dict[str, Any]:
        """Compute Average True Range (volatility measure for stop-loss sizing).

        Args:
            period: ATR lookback period.

        Returns:
            Dict with value (float) and suggested_stop_distance (float).
        """
        if len(self.df) < period + 1:
            return {"value": None, "suggested_stop_distance": None}

        high = self.df["high"]
        low = self.df["low"]
        close = self.df["close"]

        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        atr_value = float(atr.iloc[-1])

        if np.isnan(atr_value):
            return {"value": None, "suggested_stop_distance": None}

        return {
            "value": round(atr_value, 4),
            "suggested_stop_distance": round(atr_value * 1.0, 4),
        }

    def full_analysis(self) -> dict[str, Any]:
        """Run all indicators and return a combined analysis dict.

        Returns:
            Dict with keys: rsi, macd, bollinger, volume, sma_cross, atr.
        """
        return {
            "rsi": self.compute_rsi(),
            "macd": self.compute_macd(),
            "bollinger": self.compute_bollinger(),
            "volume": self.compute_volume_ratio(),
            "sma_cross": self.compute_sma_cross(),
            "atr": self.compute_atr(),
        }
