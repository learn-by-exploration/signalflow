"""Extensive tests for Phase 3: Signal Quality (v1.4 plan).

Tests cover: ADX indicator, ADX regime weights, risk guard,
confidence calibration model, feedback loop improvements,
multi-timeframe confirmation, timeframe column, backtest parity.
"""

import inspect
import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest


def _make_ohlcv(n: int, trend: str = "neutral") -> pd.DataFrame:
    """Generate sample OHLCV data for testing."""
    np.random.seed(42)
    base = 100.0
    closes = [base]
    for i in range(1, n):
        if trend == "up":
            change = np.random.normal(0.3, 1.0)
        elif trend == "down":
            change = np.random.normal(-0.3, 1.0)
        else:
            change = np.random.normal(0, 1.0)
        closes.append(closes[-1] + change)

    closes = np.array(closes)
    highs = closes + np.abs(np.random.normal(1, 0.5, n))
    lows = closes - np.abs(np.random.normal(1, 0.5, n))
    opens = closes + np.random.normal(0, 0.5, n)
    volumes = np.random.randint(10000, 100000, n).astype(float)

    return pd.DataFrame({
        "open": opens, "high": highs, "low": lows,
        "close": closes, "volume": volumes,
    })


# ═══════════════════════════════════════════════════════════
# Task 3.1: ADX Indicator Tests
# ═══════════════════════════════════════════════════════════
class TestADXIndicator:
    """Verify the ADX indicator implementation."""

    def test_adx_in_full_analysis(self):
        """full_analysis must include an 'adx' key."""
        from app.services.analysis.indicators import TechnicalAnalyzer
        df = _make_ohlcv(250)
        result = TechnicalAnalyzer(df).full_analysis()
        assert "adx" in result

    def test_adx_returns_expected_keys(self):
        """ADX result must include value, plus_di, minus_di, signal, strength."""
        from app.services.analysis.indicators import TechnicalAnalyzer
        df = _make_ohlcv(250)
        adx = TechnicalAnalyzer(df).compute_adx()
        assert "value" in adx
        assert "plus_di" in adx
        assert "minus_di" in adx
        assert "signal" in adx
        assert "strength" in adx

    def test_adx_insufficient_data(self):
        """With insufficient data, ADX should return None values."""
        from app.services.analysis.indicators import TechnicalAnalyzer
        df = _make_ohlcv(10)
        adx = TechnicalAnalyzer(df).compute_adx()
        assert adx["value"] is None
        assert adx["signal"] == "insufficient_data"

    def test_adx_value_range(self):
        """ADX values should be between 0 and 100."""
        from app.services.analysis.indicators import TechnicalAnalyzer
        df = _make_ohlcv(250, trend="up")
        adx = TechnicalAnalyzer(df).compute_adx()
        if adx["value"] is not None:
            assert 0 <= adx["value"] <= 100, f"ADX value {adx['value']} out of range"

    def test_adx_directional_indicators(self):
        """+DI and -DI should be non-negative."""
        from app.services.analysis.indicators import TechnicalAnalyzer
        df = _make_ohlcv(250, trend="up")
        adx = TechnicalAnalyzer(df).compute_adx()
        if adx["plus_di"] is not None:
            assert adx["plus_di"] >= 0
        if adx["minus_di"] is not None:
            assert adx["minus_di"] >= 0

    def test_adx_uptrend_plus_di_higher(self):
        """In a strong uptrend, +DI should generally be higher than -DI."""
        from app.services.analysis.indicators import TechnicalAnalyzer
        # Strong uptrend data
        np.random.seed(123)
        closes = np.cumsum(np.random.normal(1.0, 0.3, 250)) + 100
        df = pd.DataFrame({
            "open": closes - 0.3,
            "high": closes + 1.0,
            "low": closes - 0.5,
            "close": closes,
            "volume": np.random.randint(10000, 100000, 250).astype(float),
        })
        adx = TechnicalAnalyzer(df).compute_adx()
        if adx["plus_di"] is not None and adx["minus_di"] is not None:
            assert adx["plus_di"] > adx["minus_di"], \
                f"+DI ({adx['plus_di']}) should > -DI ({adx['minus_di']}) in uptrend"

    def test_adx_signal_values(self):
        """ADX signal must be one of the defined regime values."""
        from app.services.analysis.indicators import TechnicalAnalyzer
        valid_signals = {"ranging", "transitioning", "trending", "strong_trend", "insufficient_data"}
        df = _make_ohlcv(250)
        adx = TechnicalAnalyzer(df).compute_adx()
        assert adx["signal"] in valid_signals

    def test_adx_min_periods(self):
        """ADX should be in MIN_PERIODS."""
        from app.services.analysis.indicators import MIN_PERIODS
        assert "adx" in MIN_PERIODS


# ═══════════════════════════════════════════════════════════
# ADX Regime Weight Adjustment Tests
# ═══════════════════════════════════════════════════════════
class TestADXRegimeWeights:
    """Verify ADX-based weight adjustments in scorer."""

    def test_ranging_weights_defined(self):
        """RANGING_WEIGHTS must favor RSI and Bollinger."""
        from app.services.signal_gen.scorer import RANGING_WEIGHTS
        assert RANGING_WEIGHTS["rsi"] > 0.25
        assert RANGING_WEIGHTS["bollinger"] > 0.25
        assert RANGING_WEIGHTS["macd"] < 0.10

    def test_trending_weights_defined(self):
        """TRENDING_WEIGHTS must favor MACD and SMA cross."""
        from app.services.signal_gen.scorer import TRENDING_WEIGHTS
        assert TRENDING_WEIGHTS["macd"] > 0.25
        assert TRENDING_WEIGHTS["sma_cross"] > 0.25
        assert TRENDING_WEIGHTS["rsi"] < 0.15

    def test_ranging_weights_sum_to_one(self):
        """RANGING_WEIGHTS must sum to 1.0."""
        from app.services.signal_gen.scorer import RANGING_WEIGHTS
        assert abs(sum(RANGING_WEIGHTS.values()) - 1.0) < 0.001

    def test_trending_weights_sum_to_one(self):
        """TRENDING_WEIGHTS must sum to 1.0."""
        from app.services.signal_gen.scorer import TRENDING_WEIGHTS
        assert abs(sum(TRENDING_WEIGHTS.values()) - 1.0) < 0.001

    def test_adx_adjusted_weights_ranging(self):
        """ADX < 20 should return RANGING_WEIGHTS."""
        from app.services.signal_gen.scorer import _get_adx_adjusted_weights, RANGING_WEIGHTS
        tech_data = {"adx": {"value": 15, "signal": "ranging"}}
        result = _get_adx_adjusted_weights(tech_data)
        assert result == RANGING_WEIGHTS

    def test_adx_adjusted_weights_trending(self):
        """ADX > 25 should return TRENDING_WEIGHTS."""
        from app.services.signal_gen.scorer import _get_adx_adjusted_weights, TRENDING_WEIGHTS
        tech_data = {"adx": {"value": 30, "signal": "trending"}}
        result = _get_adx_adjusted_weights(tech_data)
        assert result == TRENDING_WEIGHTS

    def test_adx_adjusted_weights_transitioning(self):
        """ADX 20-25 should return None (use defaults)."""
        from app.services.signal_gen.scorer import _get_adx_adjusted_weights
        tech_data = {"adx": {"value": 22, "signal": "transitioning"}}
        result = _get_adx_adjusted_weights(tech_data)
        assert result is None

    def test_adx_none_value_returns_none(self):
        """If ADX value is None, return None (use defaults)."""
        from app.services.signal_gen.scorer import _get_adx_adjusted_weights
        tech_data = {"adx": {"value": None}}
        assert _get_adx_adjusted_weights(tech_data) is None

    def test_no_adx_in_data_returns_none(self):
        """If no ADX data, return None."""
        from app.services.signal_gen.scorer import _get_adx_adjusted_weights
        assert _get_adx_adjusted_weights({}) is None

    def test_scoring_uses_adx_weights(self):
        """compute_final_confidence should use ADX-adjusted weights."""
        from app.services.signal_gen.scorer import compute_technical_score, _get_adx_adjusted_weights

        # Strong RSI buy signal + ranging market
        tech_data = {
            "rsi": {"signal": "buy", "strength": 90},
            "macd": {"signal": "neutral", "strength": 50},
            "bollinger": {"signal": "buy", "strength": 85},
            "volume": {"signal": "buy", "strength": 70},
            "sma_cross": {"signal": "neutral", "strength": 50},
            "adx": {"value": 15, "signal": "ranging"},
        }

        # Test at the tech_score level (before NO_AI_CAP)
        ranging_weights = _get_adx_adjusted_weights(tech_data)
        score_ranging = compute_technical_score(tech_data, weights=ranging_weights)

        # Same data but trending market
        tech_data_trend = dict(tech_data)
        tech_data_trend["adx"] = {"value": 35, "signal": "trending"}
        trending_weights = _get_adx_adjusted_weights(tech_data_trend)
        score_trending = compute_technical_score(tech_data_trend, weights=trending_weights)

        # In ranging: RSI+BB weighted heavily → higher tech score
        # In trending: MACD+SMA weighted heavily → RSI signal less impactful
        assert score_ranging > score_trending, \
            f"Ranging score ({score_ranging}) should > trending ({score_trending}) for RSI-driven signal"


# ═══════════════════════════════════════════════════════════
# Task 3.6: Risk Guard Tests
# ═══════════════════════════════════════════════════════════
class TestRiskGuard:
    """Verify portfolio-level risk controls."""

    def test_basic_signal_allowed(self):
        """A signal with no risk violations should be allowed."""
        from app.services.signal_gen.risk_guard import check_risk_limits
        result = check_risk_limits("HDFCBANK.NS", "stock", "BUY", [])
        assert result["allowed"] is True

    def test_sector_limit_blocks_signal(self):
        """Exceeding sector limit should block the signal."""
        from app.services.signal_gen.risk_guard import check_risk_limits
        active = [
            {"symbol": "HDFCBANK.NS", "market_type": "stock", "signal_type": "BUY"},
            {"symbol": "ICICIBANK.NS", "market_type": "stock", "signal_type": "BUY"},
        ]
        result = check_risk_limits("SBIN.NS", "stock", "BUY", active)
        assert result["allowed"] is False
        assert "banking" in result["reason"].lower()

    def test_sector_limit_allows_sell(self):
        """Sector limit should NOT block SELL signals."""
        from app.services.signal_gen.risk_guard import check_risk_limits
        active = [
            {"symbol": "HDFCBANK.NS", "market_type": "stock", "signal_type": "BUY"},
            {"symbol": "ICICIBANK.NS", "market_type": "stock", "signal_type": "BUY"},
        ]
        result = check_risk_limits("SBIN.NS", "stock", "SELL", active)
        assert result["allowed"] is True

    def test_market_limit_blocks_signal(self):
        """Exceeding market-level limit should block."""
        from app.services.signal_gen.risk_guard import check_risk_limits
        active = [
            {"symbol": f"SYM{i}", "market_type": "crypto", "signal_type": "BUY"}
            for i in range(5)
        ]
        result = check_risk_limits("NEWCRYPTO", "crypto", "BUY", active)
        assert result["allowed"] is False
        assert "market limit" in result["reason"].lower()

    def test_cross_market_check(self):
        """3+ BUY in both stocks and crypto should block new BUY."""
        from app.services.signal_gen.risk_guard import check_risk_limits
        active = [
            {"symbol": "S1", "market_type": "stock", "signal_type": "BUY"},
            {"symbol": "S2", "market_type": "stock", "signal_type": "BUY"},
            {"symbol": "S3", "market_type": "stock", "signal_type": "BUY"},
            {"symbol": "C1", "market_type": "crypto", "signal_type": "BUY"},
            {"symbol": "C2", "market_type": "crypto", "signal_type": "BUY"},
            {"symbol": "C3", "market_type": "crypto", "signal_type": "BUY"},
        ]
        result = check_risk_limits("NEW", "forex", "BUY", active)
        assert result["allowed"] is False
        assert "cross-market" in result["reason"].lower()

    def test_adx_downtrend_blocks_buy(self):
        """Strong downtrend (ADX>25, -DI > +DI) should block BUY."""
        from app.services.signal_gen.risk_guard import check_risk_limits
        adx_data = {"value": 35, "plus_di": 15, "minus_di": 30}
        result = check_risk_limits("HDFCBANK.NS", "stock", "BUY", [], adx_data=adx_data)
        assert result["allowed"] is False
        assert "downtrend" in result["reason"].lower()

    def test_adx_downtrend_allows_sell(self):
        """Strong downtrend should NOT block SELL signals."""
        from app.services.signal_gen.risk_guard import check_risk_limits
        adx_data = {"value": 35, "plus_di": 15, "minus_di": 30}
        result = check_risk_limits("HDFCBANK.NS", "stock", "SELL", [], adx_data=adx_data)
        assert result["allowed"] is True

    def test_position_size_warning(self):
        """4+ active positions should generate a warning."""
        from app.services.signal_gen.risk_guard import check_risk_limits
        active = [
            {"symbol": f"S{i}", "market_type": "stock", "signal_type": "BUY"}
            for i in range(4)
        ]
        result = check_risk_limits("NEW", "crypto", "BUY", active)
        assert len(result["warnings"]) > 0
        assert "position size" in result["warnings"][0].lower()

    def test_config_risk_limits(self):
        """Risk limit configuration should exist in settings."""
        from app.config import get_settings
        settings = get_settings()
        assert hasattr(settings, "max_concurrent_per_sector")
        assert hasattr(settings, "max_concurrent_per_market")
        assert hasattr(settings, "sector_map")
        assert settings.max_concurrent_per_sector == 2
        assert settings.max_concurrent_per_market == 5

    def test_sector_map_covers_tracked_stocks(self):
        """Sector map should cover most tracked stocks."""
        from app.config import get_settings
        settings = get_settings()
        mapped = set(settings.sector_map.keys())
        tracked = set(settings.tracked_stocks)
        coverage = len(mapped & tracked) / len(tracked)
        assert coverage >= 0.8, f"Sector map covers only {coverage:.0%} of tracked stocks"


# ═══════════════════════════════════════════════════════════
# Task 3.5: Confidence Calibration Model Tests
# ═══════════════════════════════════════════════════════════
class TestConfidenceCalibration:
    """Verify calibration model exists and has correct schema."""

    def test_model_importable(self):
        """ConfidenceCalibration model should be importable."""
        from app.models.confidence_calibration import ConfidenceCalibration
        assert hasattr(ConfidenceCalibration, "score_bucket")
        assert hasattr(ConfidenceCalibration, "total_signals")
        assert hasattr(ConfidenceCalibration, "successful_signals")
        assert hasattr(ConfidenceCalibration, "calibrated_probability")
        assert hasattr(ConfidenceCalibration, "market_type")

    def test_table_name(self):
        """Table name should be confidence_calibration."""
        from app.models.confidence_calibration import ConfidenceCalibration
        assert ConfidenceCalibration.__tablename__ == "confidence_calibration"


# ═══════════════════════════════════════════════════════════
# Task 3.7: Feedback Loop Improvement Tests
# ═══════════════════════════════════════════════════════════
class TestFeedbackLoopImprovements:
    """Verify feedback loop parameter changes."""

    def test_min_signals_increased(self):
        """MIN_SIGNALS_FOR_ADJUSTMENT should be 50 (was 20)."""
        from app.services.signal_gen.feedback import MIN_SIGNALS_FOR_ADJUSTMENT
        assert MIN_SIGNALS_FOR_ADJUSTMENT == 50

    def test_learning_rate_increased(self):
        """LEARNING_RATE should be 0.4 (was 0.3)."""
        from app.services.signal_gen.feedback import LEARNING_RATE
        assert LEARNING_RATE == 0.4

    def test_weight_bounds_defined(self):
        """MIN_WEIGHT and MAX_WEIGHT must be defined."""
        from app.services.signal_gen.feedback import MIN_WEIGHT, MAX_WEIGHT
        assert MIN_WEIGHT == 0.05
        assert MAX_WEIGHT == 0.40

    def test_weight_bounds_in_compute_adaptive(self):
        """compute_adaptive_weights source must reference weight clamping."""
        source = inspect.getsource(
            __import__("app.services.signal_gen.feedback", fromlist=["compute_adaptive_weights"])
        )
        assert "MIN_WEIGHT" in source
        assert "MAX_WEIGHT" in source
        assert "clamp" in source.lower() or "clamped" in source.lower()

    def test_default_weights_within_bounds(self):
        """Default weights should be within [MIN_WEIGHT, MAX_WEIGHT]."""
        from app.services.signal_gen.feedback import DEFAULT_WEIGHTS, MIN_WEIGHT, MAX_WEIGHT
        for key, weight in DEFAULT_WEIGHTS.items():
            assert MIN_WEIGHT <= weight <= MAX_WEIGHT, \
                f"Default weight {key}={weight} outside bounds [{MIN_WEIGHT}, {MAX_WEIGHT}]"


# ═══════════════════════════════════════════════════════════
# Task 3.2: Timeframe Column in MarketData
# ═══════════════════════════════════════════════════════════
class TestTimeframeColumn:
    """Verify the timeframe column in MarketData model."""

    def test_market_data_has_timeframe_column(self):
        """MarketData model should have a timeframe column."""
        from app.models.market_data import MarketData
        assert hasattr(MarketData, "timeframe")

    def test_timeframe_default_is_1d(self):
        """The timeframe column should default to '1d'."""
        from app.models.market_data import MarketData
        col = MarketData.__table__.c.timeframe
        assert col.server_default is not None
        assert "1d" in str(col.server_default.arg)

    def test_unique_index_includes_timeframe(self):
        """Unique index should include symbol, timestamp, timeframe, market_type."""
        from app.models.market_data import MarketData
        indexes = MarketData.__table__.indexes
        unique_idx = [i for i in indexes if "unique" in i.name.lower()]
        assert len(unique_idx) >= 1, "Must have unique index including timeframe"
        idx_cols = {c.name for c in unique_idx[0].columns}
        assert "timeframe" in idx_cols
        assert "symbol" in idx_cols
        assert "market_type" in idx_cols

    def test_migration_file_exists(self):
        """Alembic migration for timeframe column should exist."""
        import os
        migration_dir = os.path.join(
            os.path.dirname(__file__), "..", "migrations", "versions",
        )
        files = os.listdir(migration_dir)
        timeframe_files = [f for f in files if "timeframe" in f.lower()]
        assert len(timeframe_files) >= 1


# ═══════════════════════════════════════════════════════════
# Task 3.3: Multi-Timeframe Data Ingestion
# ═══════════════════════════════════════════════════════════
class TestMultiTimeframeIngestion:
    """Verify multi-timeframe data fetchers."""

    def test_crypto_fetcher_accepts_timeframe(self):
        """CryptoFetcher should accept a timeframe parameter."""
        from app.services.data_ingestion.crypto import CryptoFetcher
        fetcher = CryptoFetcher(timeframe="1d")
        assert fetcher.timeframe == "1d"

    def test_crypto_fetcher_default_timeframe(self):
        """CryptoFetcher default timeframe should be '1d'."""
        from app.services.data_ingestion.crypto import CryptoFetcher
        fetcher = CryptoFetcher()
        assert fetcher.timeframe == "1d"

    def test_crypto_fetcher_binance_interval_map(self):
        """CryptoFetcher should map timeframes to Binance intervals."""
        from app.services.data_ingestion.crypto import CryptoFetcher
        fetcher = CryptoFetcher(timeframe="4h")
        assert fetcher._binance_interval_map["4h"] == "4h"
        assert fetcher._binance_interval_map["1d"] == "1d"

    def test_forex_fetcher_accepts_timeframe(self):
        """ForexFetcher should accept a timeframe parameter."""
        from app.services.data_ingestion.forex import ForexFetcher
        fetcher = ForexFetcher(timeframe="4h")
        assert fetcher.timeframe == "4h"

    def test_forex_fetcher_default_timeframe(self):
        """ForexFetcher default timeframe should be '1d'."""
        from app.services.data_ingestion.forex import ForexFetcher
        fetcher = ForexFetcher()
        assert fetcher.timeframe == "1d"

    def test_higher_tf_tasks_registered(self):
        """Celery tasks for higher-TF fetch should exist."""
        from app.tasks.data_tasks import fetch_crypto_daily, fetch_forex_4h
        assert callable(fetch_crypto_daily)
        assert callable(fetch_forex_4h)

    def test_scheduler_has_higher_tf_tasks(self):
        """Beat schedule should include higher-TF fetch tasks."""
        from app.tasks.scheduler import CELERY_BEAT_SCHEDULE
        assert "fetch-crypto-daily" in CELERY_BEAT_SCHEDULE
        assert "fetch-forex-4h" in CELERY_BEAT_SCHEDULE


# ═══════════════════════════════════════════════════════════
# Task 3.4: Multi-Timeframe Signal Confirmation
# ═══════════════════════════════════════════════════════════
class TestMultiTimeframeConfirmation:
    """Verify multi-TF confirmation logic."""

    def test_mtf_module_importable(self):
        """mtf_confirmation module should be importable."""
        from app.services.signal_gen.mtf_confirmation import (
            apply_mtf_confirmation,
            compute_confirmation_score,
            CONFIRMATION_TIMEFRAMES,
        )
        assert callable(apply_mtf_confirmation)
        assert callable(compute_confirmation_score)
        assert "stock" in CONFIRMATION_TIMEFRAMES

    def test_confirmation_timeframes_defined(self):
        """All 3 markets should have confirmation timeframes."""
        from app.services.signal_gen.mtf_confirmation import CONFIRMATION_TIMEFRAMES
        assert "stock" in CONFIRMATION_TIMEFRAMES
        assert "crypto" in CONFIRMATION_TIMEFRAMES
        assert "forex" in CONFIRMATION_TIMEFRAMES

    def test_bullish_confirmed(self):
        """Bullish primary + bullish confirmation → keep signal."""
        from app.services.signal_gen.mtf_confirmation import apply_mtf_confirmation
        conf, sig = apply_mtf_confirmation(85, "STRONG_BUY", 65.0)
        assert sig == "STRONG_BUY"
        assert conf == 85

    def test_bullish_neutral_confirmation(self):
        """Bullish primary + neutral confirmation → downgrade."""
        from app.services.signal_gen.mtf_confirmation import apply_mtf_confirmation
        conf, sig = apply_mtf_confirmation(85, "STRONG_BUY", 45.0)
        assert sig == "BUY"  # Downgraded from STRONG_BUY
        assert conf < 85     # Confidence reduced

    def test_bullish_conflicting(self):
        """Bullish primary + bearish confirmation → HOLD."""
        from app.services.signal_gen.mtf_confirmation import apply_mtf_confirmation
        conf, sig = apply_mtf_confirmation(85, "STRONG_BUY", 30.0)
        assert sig == "HOLD"
        assert conf == 50

    def test_bearish_confirmed(self):
        """Bearish primary + bearish confirmation → keep signal."""
        from app.services.signal_gen.mtf_confirmation import apply_mtf_confirmation
        conf, sig = apply_mtf_confirmation(25, "SELL", 35.0)
        assert sig == "SELL"
        assert conf == 25

    def test_bearish_conflicting(self):
        """Bearish primary + bullish confirmation → HOLD."""
        from app.services.signal_gen.mtf_confirmation import apply_mtf_confirmation
        conf, sig = apply_mtf_confirmation(25, "SELL", 75.0)
        assert sig == "HOLD"

    def test_hold_signal_passthrough(self):
        """HOLD signals should pass through without modification."""
        from app.services.signal_gen.mtf_confirmation import apply_mtf_confirmation
        conf, sig = apply_mtf_confirmation(50, "HOLD", 80.0)
        assert sig == "HOLD"
        assert conf == 50

    def test_neutral_confirmation_no_change(self):
        """Neutral confirmation score (50) should not modify signal."""
        from app.services.signal_gen.mtf_confirmation import apply_mtf_confirmation
        conf, sig = apply_mtf_confirmation(85, "STRONG_BUY", 50.0)
        assert sig == "STRONG_BUY"
        assert conf == 85

    def test_confirmation_score_from_data(self):
        """compute_confirmation_score should return 0-100 from real data."""
        from app.services.signal_gen.mtf_confirmation import compute_confirmation_score
        df = _make_ohlcv(100, trend="up")
        score = compute_confirmation_score(df)
        assert 0 <= score <= 100

    def test_confirmation_score_insufficient_data(self):
        """Insufficient data should return neutral (50)."""
        from app.services.signal_gen.mtf_confirmation import compute_confirmation_score
        df = _make_ohlcv(5)
        score = compute_confirmation_score(df)
        assert score == 50.0


# ═══════════════════════════════════════════════════════════
# Task 3.8: Backtest Parity Tests
# ═══════════════════════════════════════════════════════════
class TestBacktestParity:
    """Verify backtest uses production pipeline."""

    def test_backtest_imports_technical_analyzer(self):
        """Backtest should import TechnicalAnalyzer (production parity)."""
        source = inspect.getsource(
            __import__("app.tasks.backtest_tasks", fromlist=["_run_backtest_sync"])
        )
        assert "TechnicalAnalyzer" in source

    def test_backtest_imports_scorer(self):
        """Backtest should import compute_final_confidence."""
        source = inspect.getsource(
            __import__("app.tasks.backtest_tasks", fromlist=["_run_backtest_sync"])
        )
        assert "compute_final_confidence" in source

    def test_backtest_has_slippage(self):
        """Backtest should apply slippage."""
        source = inspect.getsource(
            __import__("app.tasks.backtest_tasks", fromlist=["_run_backtest_sync"])
        )
        assert "slippage" in source.lower()

    def test_backtest_has_walk_forward(self):
        """Backtest should use walk-forward windows."""
        from app.tasks.backtest_tasks import TRAIN_DAYS, TEST_DAYS
        assert TRAIN_DAYS == 60
        assert TEST_DAYS == 30

    def test_simulate_trades_returns_list(self):
        """_simulate_trades should return a list of trade dicts."""
        from app.tasks.backtest_tasks import _simulate_trades
        df = _make_ohlcv(100)
        df["timestamp"] = pd.date_range("2025-01-01", periods=100, freq="D")
        trades = _simulate_trades(df, "TEST", "stock", 10)
        assert isinstance(trades, list)

    def test_sharpe_ratio_computed(self):
        """_compute_sharpe should return a float."""
        from app.tasks.backtest_tasks import _compute_sharpe
        result = _compute_sharpe([2.0, -1.0, 3.0, -0.5, 1.5])
        assert isinstance(result, float)

    def test_sharpe_zero_returns(self):
        """_compute_sharpe with empty returns should be 0."""
        from app.tasks.backtest_tasks import _compute_sharpe
        assert _compute_sharpe([]) == 0.0

    def test_profit_factor_computed(self):
        """_compute_profit_factor should calculate correctly."""
        from app.tasks.backtest_tasks import _compute_profit_factor
        trades = [
            {"return_pct": 5.0},
            {"return_pct": -2.0},
            {"return_pct": 3.0},
            {"return_pct": -1.0},
        ]
        pf = _compute_profit_factor(trades)
        assert pf == (5.0 + 3.0) / (2.0 + 1.0)  # 8/3 ≈ 2.67

    def test_profit_factor_no_losses(self):
        """Profit factor with no losses should be inf."""
        from app.tasks.backtest_tasks import _compute_profit_factor
        trades = [{"return_pct": 5.0}, {"return_pct": 3.0}]
        pf = _compute_profit_factor(trades)
        assert pf == float("inf")

    def test_resolve_trades_win(self):
        """_resolve_trades should detect target hit."""
        from app.tasks.backtest_tasks import _resolve_trades
        trades = [{"signal_type": "BUY", "entry": 100.0, "target": 110.0, "stop": 95.0, "timestamp": None}]
        df_future = pd.DataFrame({
            "close": [101, 105, 110, 112],
            "high": [102, 106, 111, 113],
            "low": [100, 104, 109, 111],
        })
        resolved = _resolve_trades(trades, df_future)
        assert len(resolved) == 1
        assert resolved[0]["result"] == "win"

    def test_resolve_trades_loss(self):
        """_resolve_trades should detect stop-loss hit."""
        from app.tasks.backtest_tasks import _resolve_trades
        trades = [{"signal_type": "BUY", "entry": 100.0, "target": 110.0, "stop": 95.0, "timestamp": None}]
        df_future = pd.DataFrame({
            "close": [99, 97, 94, 92],
            "high": [100, 98, 95, 93],
            "low": [98, 96, 93, 91],
        })
        resolved = _resolve_trades(trades, df_future)
        assert len(resolved) == 1
        assert resolved[0]["result"] == "loss"
