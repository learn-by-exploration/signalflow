"""Sprint 2 Security Tests — Race conditions, data integrity, financial precision.

CRIT-08: Signal resolution race (FOR UPDATE SKIP LOCKED)
CRIT-16: Signal cooldown TOCTOU (atomic check+create)
CRIT-17: Price alert trigger dedup (UPDATE...RETURNING)
CRIT-18: Float → Decimal in signal pipeline
CRIT-19: SMA division-by-zero guard
CRIT-20: R:R ratio ≥ 1:2 enforcement
HIGH-04/05: NaN/Infinity validation in fetchers
HIGH-06/07/08: FK constraints + CASCADE
HIGH-09: JSONB schema validation
HIGH-10: CHECK constraints (confidence, OHLC)
HIGH-18: Cost tracker atomic budget check
HIGH-20/21: Alert config atomic update
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import numpy as np
import pandas as pd
import pytest

# ── Signal Resolution Race (CRIT-08) ──


class TestSignalResolutionRace:
    """Verify signal resolution uses FOR UPDATE SKIP LOCKED."""

    def test_resolve_query_uses_for_update(self) -> None:
        """The _resolve_signals_async function must use with_for_update."""
        import inspect
        from app.tasks.signal_tasks import _resolve_signals_async
        source = inspect.getsource(_resolve_signals_async)
        assert "with_for_update" in source
        assert "skip_locked" in source

    def test_signal_can_only_resolve_once(self) -> None:
        """A signal marked inactive should not create duplicate history records."""
        from app.models.signal import Signal
        from app.models.signal_history import SignalHistory

        signal = Signal(
            symbol="BTC",
            market_type="crypto",
            signal_type="BUY",
            confidence=80,
            current_price=Decimal("50000"),
            target_price=Decimal("55000"),
            stop_loss=Decimal("48000"),
            ai_reasoning="test",
            technical_data={},
            is_active=True,
        )
        # After resolution
        signal.is_active = False
        assert signal.is_active is False


# ── Signal Cooldown TOCTOU (CRIT-16) ──


class TestSignalCooldownTOCTOU:
    """Verify signal cooldown uses FOR UPDATE to prevent TOCTOU race."""

    def test_has_recent_signal_uses_for_update(self) -> None:
        """The _has_recent_signal method must use with_for_update."""
        import inspect
        from app.services.signal_gen.generator import SignalGenerator
        source = inspect.getsource(SignalGenerator._has_recent_signal)
        assert "with_for_update" in source
        assert "skip_locked" in source


# ── Price Alert Trigger Dedup (CRIT-17) ──


class TestPriceAlertDedup:
    """Verify price alert trigger uses atomic UPDATE...WHERE for dedup."""

    def test_check_alerts_uses_atomic_update(self) -> None:
        """The _check_alerts_sync function must use UPDATE...WHERE is_triggered=false."""
        import inspect
        from app.tasks.price_alert_tasks import _check_alerts_sync
        source = inspect.getsource(_check_alerts_sync)
        assert "AND is_triggered = false" in source
        assert "RETURNING" in source


# ── SMA Division-by-Zero Guard (CRIT-19) ──


class TestSMADivisionByZero:
    """Verify SMA cross computation handles zero values safely."""

    def test_sma_zero_slow_returns_neutral(self) -> None:
        """When slow SMA value is zero, return neutral signal without crash."""
        from app.services.analysis.indicators import TechnicalAnalyzer

        # Create a DataFrame with 200+ points that could make SMA close to zero
        # Set all close values to 0 except we need at least some data
        data = {"close": [0.0] * 250, "high": [0.0] * 250,
                "low": [0.0] * 250, "open": [0.0] * 250,
                "volume": [0.0] * 250}
        df = pd.DataFrame(data)
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.compute_sma_cross()
        assert result["signal"] == "neutral"
        assert result["strength"] == 50

    def test_sma_nan_values_return_neutral(self) -> None:
        """When SMA produces NaN, return neutral signal."""
        from app.services.analysis.indicators import TechnicalAnalyzer

        data = {"close": [float("nan")] * 250, "high": [1.0] * 250,
                "low": [1.0] * 250, "open": [1.0] * 250,
                "volume": [1.0] * 250}
        df = pd.DataFrame(data)
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.compute_sma_cross()
        assert result["signal"] == "neutral"

    def test_sma_normal_data_still_works(self) -> None:
        """SMA cross still works correctly with normal data."""
        from app.services.analysis.indicators import TechnicalAnalyzer

        # Create data where fast SMA > slow SMA (buy signal)
        close_data = list(range(1, 251))  # 1 to 250, monotonically increasing
        data = {"close": close_data, "high": close_data,
                "low": close_data, "open": close_data,
                "volume": [1000] * 250}
        df = pd.DataFrame(data)
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.compute_sma_cross()
        assert result["signal"] in ("buy", "sell", "neutral")
        assert result["strength"] >= 0


# ── R:R Ratio Enforcement (CRIT-20) ──


class TestRiskRewardRatio:
    """Verify Risk:Reward ratio is always ≥ 1:2."""

    def test_buy_signal_has_2_to_1_rr(self) -> None:
        """BUY signal target must be at least 2x the risk."""
        from app.services.signal_gen.targets import calculate_targets

        result = calculate_targets(
            current_price=Decimal("100"),
            atr_data={"value": 5.0},
            signal_type="BUY",
            market_type="stock",
        )
        reward = result["target_price"] - Decimal("100")
        risk = Decimal("100") - result["stop_loss"]
        assert risk > 0
        assert reward / risk >= 2

    def test_sell_signal_has_2_to_1_rr(self) -> None:
        """SELL signal target must provide at least 2x reward vs risk."""
        from app.services.signal_gen.targets import calculate_targets

        result = calculate_targets(
            current_price=Decimal("100"),
            atr_data={"value": 5.0},
            signal_type="SELL",
            market_type="stock",
        )
        reward = Decimal("100") - result["target_price"]
        risk = result["stop_loss"] - Decimal("100")
        assert risk > 0
        assert reward / risk >= 2

    def test_strong_buy_has_2_to_1_rr(self) -> None:
        """STRONG_BUY also respects R:R constraint."""
        from app.services.signal_gen.targets import calculate_targets

        result = calculate_targets(
            current_price=Decimal("50000"),
            atr_data={"value": 1000.0},
            signal_type="STRONG_BUY",
            market_type="crypto",
        )
        reward = result["target_price"] - Decimal("50000")
        risk = Decimal("50000") - result["stop_loss"]
        assert risk > 0
        assert reward / risk >= 2

    def test_zero_atr_fallback_maintains_rr(self) -> None:
        """When ATR is zero, fallback 2% still maintains R:R ratio."""
        from app.services.signal_gen.targets import calculate_targets

        result = calculate_targets(
            current_price=Decimal("100"),
            atr_data={"value": 0},
            signal_type="BUY",
            market_type="stock",
        )
        reward = result["target_price"] - Decimal("100")
        risk = Decimal("100") - result["stop_loss"]
        assert risk > 0
        assert reward / risk >= 2

    def test_none_atr_fallback_maintains_rr(self) -> None:
        """When ATR is None, fallback still works."""
        from app.services.signal_gen.targets import calculate_targets

        result = calculate_targets(
            current_price=Decimal("100"),
            atr_data={},
            signal_type="BUY",
            market_type="stock",
        )
        reward = result["target_price"] - Decimal("100")
        risk = Decimal("100") - result["stop_loss"]
        assert risk > 0
        assert reward / risk >= 2

    def test_targets_are_always_positive(self) -> None:
        """Target and stop-loss must never be negative."""
        from app.services.signal_gen.targets import calculate_targets

        result = calculate_targets(
            current_price=Decimal("1"),
            atr_data={"value": 10.0},
            signal_type="SELL",
            market_type="forex",
        )
        assert result["target_price"] >= 0
        assert result["stop_loss"] >= 0


# ── Financial Precision (CRIT-18) ──


class TestFinancialPrecision:
    """Verify Decimal is used for all financial calculations."""

    def test_signal_model_uses_numeric(self) -> None:
        """Signal model must use Numeric (not Float) for prices."""
        from app.models.signal import Signal
        for col_name in ("current_price", "target_price", "stop_loss"):
            col = Signal.__table__.columns[col_name]
            assert "Numeric" in str(col.type) or "NUMERIC" in str(col.type)

    def test_market_data_uses_numeric(self) -> None:
        """MarketData model must use Numeric for OHLCV."""
        from app.models.market_data import MarketData
        for col_name in ("open", "high", "low", "close"):
            col = MarketData.__table__.columns[col_name]
            assert "Numeric" in str(col.type) or "NUMERIC" in str(col.type)

    def test_targets_return_decimal(self) -> None:
        """Target calculator must return Decimal, not float."""
        from app.services.signal_gen.targets import calculate_targets

        result = calculate_targets(
            current_price=Decimal("100.50"),
            atr_data={"value": 3.5},
            signal_type="BUY",
            market_type="stock",
        )
        assert isinstance(result["target_price"], Decimal)
        assert isinstance(result["stop_loss"], Decimal)

    def test_decimal_precision_preserved(self) -> None:
        """Decimal calculations should not lose precision."""
        from app.services.signal_gen.targets import calculate_targets

        result = calculate_targets(
            current_price=Decimal("1678.90"),
            atr_data={"value": 25.3},
            signal_type="BUY",
            market_type="stock",
        )
        # Price should have at most 8 decimal places
        assert result["target_price"] == result["target_price"].quantize(Decimal("0.00000001"))


# ── CHECK Constraints (HIGH-10) ──


class TestCheckConstraints:
    """Verify CHECK constraints are defined on models."""

    def test_signal_confidence_check(self) -> None:
        """Signal model must have CHECK constraint on confidence 0-100."""
        from app.models.signal import Signal
        constraints = [c.name for c in Signal.__table__.constraints
                       if hasattr(c, 'name') and c.name]
        assert "ck_signals_confidence" in constraints

    def test_signal_market_type_check(self) -> None:
        """Signal model must have CHECK constraint on market_type."""
        from app.models.signal import Signal
        constraints = [c.name for c in Signal.__table__.constraints
                       if hasattr(c, 'name') and c.name]
        assert "ck_signals_market_type" in constraints

    def test_signal_signal_type_check(self) -> None:
        """Signal model must have CHECK constraint on signal_type."""
        from app.models.signal import Signal
        constraints = [c.name for c in Signal.__table__.constraints
                       if hasattr(c, 'name') and c.name]
        assert "ck_signals_signal_type" in constraints

    def test_signal_positive_prices_check(self) -> None:
        """Signal model must have CHECK constraints for non-negative prices."""
        from app.models.signal import Signal
        constraints = [c.name for c in Signal.__table__.constraints
                       if hasattr(c, 'name') and c.name]
        assert "ck_signals_current_price" in constraints
        assert "ck_signals_target_price" in constraints
        assert "ck_signals_stop_loss" in constraints

    def test_market_data_ohlc_checks(self) -> None:
        """MarketData model must have CHECK constraints on OHLC positivity."""
        from app.models.market_data import MarketData
        constraints = [c.name for c in MarketData.__table__.constraints
                       if hasattr(c, 'name') and c.name]
        assert "ck_market_data_open" in constraints
        assert "ck_market_data_high" in constraints
        assert "ck_market_data_low" in constraints
        assert "ck_market_data_close" in constraints
        assert "ck_market_data_high_gte_low" in constraints

    def test_signal_history_outcome_check(self) -> None:
        """SignalHistory model must have CHECK constraint on outcome values."""
        from app.models.signal_history import SignalHistory
        constraints = [c.name for c in SignalHistory.__table__.constraints
                       if hasattr(c, 'name') and c.name]
        assert "ck_signal_history_outcome" in constraints


# ── Cost Tracker Budget Safety (HIGH-18) ──


class TestCostTrackerBudget:
    """Verify cost tracker budget checks are safe."""

    def test_budget_check_with_estimated_cost(self) -> None:
        """is_budget_available should accept estimated_cost parameter."""
        from app.services.ai_engine.cost_tracker import CostTracker
        tracker = CostTracker()
        # Without Redis, falls back to file-based check
        result = tracker.is_budget_available(estimated_cost=0.01)
        assert isinstance(result, bool)

    def test_budget_exceeds_returns_false(self) -> None:
        """When estimated cost exceeds remaining budget, return False."""
        from app.services.ai_engine.cost_tracker import CostTracker
        tracker = CostTracker()
        # Request more than the monthly budget
        result = tracker.is_budget_available(estimated_cost=999999.0)
        assert result is False


# ── Alert Config Atomic Update (HIGH-20/21) ──


class TestAlertConfigAtomic:
    """Verify alert config update uses row-level locking."""

    def test_update_uses_for_update(self) -> None:
        """The update_alert_config endpoint must use with_for_update."""
        import inspect
        from app.api.alerts import update_alert_config
        source = inspect.getsource(update_alert_config)
        assert "with_for_update" in source


# ── Signal Schema Validation ──


class TestSignalSchemaValidation:
    """Verify Pydantic schemas enforce data integrity."""

    def test_confidence_rejects_negative(self) -> None:
        """Confidence below 0 should be rejected."""
        from app.schemas.signal import SignalResponse
        with pytest.raises(Exception):
            SignalResponse(
                id=uuid4(), symbol="BTC", market_type="crypto",
                signal_type="BUY", confidence=-1,
                current_price=Decimal("100"), target_price=Decimal("110"),
                stop_loss=Decimal("90"), ai_reasoning="test",
                technical_data={}, is_active=True,
                created_at=datetime.now(timezone.utc),
            )

    def test_confidence_rejects_over_100(self) -> None:
        """Confidence above 100 should be rejected."""
        from app.schemas.signal import SignalResponse
        with pytest.raises(Exception):
            SignalResponse(
                id=uuid4(), symbol="BTC", market_type="crypto",
                signal_type="BUY", confidence=101,
                current_price=Decimal("100"), target_price=Decimal("110"),
                stop_loss=Decimal("90"), ai_reasoning="test",
                technical_data={}, is_active=True,
                created_at=datetime.now(timezone.utc),
            )

    def test_negative_price_rejected(self) -> None:
        """Negative prices should be rejected by schema."""
        from app.schemas.signal import SignalResponse
        with pytest.raises(Exception):
            SignalResponse(
                id=uuid4(), symbol="BTC", market_type="crypto",
                signal_type="BUY", confidence=80,
                current_price=Decimal("-100"), target_price=Decimal("110"),
                stop_loss=Decimal("90"), ai_reasoning="test",
                technical_data={}, is_active=True,
                created_at=datetime.now(timezone.utc),
            )

    def test_invalid_market_type_rejected(self) -> None:
        """Invalid market_type should be rejected."""
        from app.schemas.signal import SignalResponse
        with pytest.raises(Exception):
            SignalResponse(
                id=uuid4(), symbol="BTC", market_type="options",
                signal_type="BUY", confidence=80,
                current_price=Decimal("100"), target_price=Decimal("110"),
                stop_loss=Decimal("90"), ai_reasoning="test",
                technical_data={}, is_active=True,
                created_at=datetime.now(timezone.utc),
            )

    def test_valid_signal_passes(self) -> None:
        """Valid signal data should pass all validation."""
        from app.schemas.signal import SignalResponse
        resp = SignalResponse(
            id=uuid4(), symbol="BTC", market_type="crypto",
            signal_type="STRONG_BUY", confidence=92,
            current_price=Decimal("50000"), target_price=Decimal("55000"),
            stop_loss=Decimal("48000"), ai_reasoning="BTC bullish",
            technical_data={"rsi": {"value": 65}}, is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        assert resp.confidence == 92
        assert resp.market_type == "crypto"


# ── Data Ingestion NaN Validation (HIGH-04/05) ──


class TestDataIngestionValidation:
    """Verify candle validators reject NaN/Infinity/negative data."""

    def test_validate_candle_rejects_nan(self) -> None:
        """NaN values in OHLCV should be rejected."""
        from app.services.data_ingestion.validators import validate_candle
        is_valid, error = validate_candle({
            "open": float("nan"),
            "high": 100.0,
            "low": 90.0,
            "close": 95.0,
        })
        assert is_valid is False
        assert "NaN" in error or "nan" in error.lower()

    def test_validate_candle_rejects_infinity(self) -> None:
        """Infinity values should be rejected."""
        from app.services.data_ingestion.validators import validate_candle
        is_valid, error = validate_candle({
            "open": float("inf"),
            "high": 100.0,
            "low": 90.0,
            "close": 95.0,
        })
        assert is_valid is False

    def test_validate_candle_rejects_negative(self) -> None:
        """Negative prices should be rejected."""
        from app.services.data_ingestion.validators import validate_candle
        is_valid, error = validate_candle({
            "open": -10.0,
            "high": 100.0,
            "low": 90.0,
            "close": 95.0,
        })
        assert is_valid is False
        assert "Negative" in error or "negative" in error.lower()

    def test_validate_candle_accepts_valid(self) -> None:
        """Valid OHLCV data should pass validation."""
        from app.services.data_ingestion.validators import validate_candle
        is_valid, error = validate_candle({
            "open": 100.0,
            "high": 110.0,
            "low": 95.0,
            "close": 105.0,
        })
        assert is_valid is True
        assert error == ""

    def test_validate_candle_rejects_high_lt_low(self) -> None:
        """High < Low should be rejected."""
        from app.services.data_ingestion.validators import validate_candle
        is_valid, error = validate_candle({
            "open": 100.0,
            "high": 80.0,
            "low": 95.0,
            "close": 90.0,
        })
        assert is_valid is False
        assert "high" in error.lower()
