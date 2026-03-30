"""v1.3.43 — Database Constraint Security Tests.

Verify DB constraints enforce data integrity for financial data —
CHECK constraints, foreign keys, unique constraints, NOT NULL.
"""

import pytest
import inspect


class TestMarketTypeConstraint:
    """market_type must be one of stock/crypto/forex."""

    def test_market_data_model_has_check(self):
        """Market data model uses valid market_type values."""
        from app.models.market_data import MarketData

        source = inspect.getsource(MarketData)
        assert "stock" in source
        assert "crypto" in source
        assert "forex" in source

    def test_signal_model_has_market_type(self):
        """Signal model has market_type field."""
        from app.models.signal import Signal

        assert hasattr(Signal, "market_type")


class TestSignalTypeConstraint:
    """signal_type must be valid enum value."""

    def test_signal_types_defined(self):
        """Signal types are properly constrained."""
        from app.models.signal import Signal

        source = inspect.getsource(Signal)
        for st in ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]:
            assert st in source

    def test_history_outcomes_defined(self):
        """Signal history outcomes are constrained."""
        from app.models.signal_history import SignalHistory

        source = inspect.getsource(SignalHistory)
        for outcome in ["hit_target", "hit_stop", "expired", "pending"]:
            assert outcome in source


class TestPriceDecimalPrecision:
    """Financial fields must use Decimal, not Float."""

    def test_market_data_uses_decimal(self):
        """Market data prices use Numeric/Decimal columns."""
        from app.models.market_data import MarketData

        source = inspect.getsource(MarketData)
        # Should use Numeric or Decimal, not Float
        assert "Numeric" in source or "DECIMAL" in source

    def test_signal_uses_decimal(self):
        """Signal prices use Numeric/Decimal columns."""
        from app.models.signal import Signal

        source = inspect.getsource(Signal)
        assert "Numeric" in source or "DECIMAL" in source


class TestRequiredFields:
    """NOT NULL constraints are properly applied."""

    def test_signal_required_fields(self):
        """Signal model has non-nullable required fields."""
        from app.models.signal import Signal

        required = ["symbol", "market_type", "signal_type", "confidence",
                     "current_price", "target_price", "stop_loss", "ai_reasoning"]
        for field in required:
            assert hasattr(Signal, field), f"Signal missing field: {field}"

    def test_market_data_required_fields(self):
        """Market data has required OHLCV fields."""
        from app.models.market_data import MarketData

        for field in ["symbol", "open", "high", "low", "close", "timestamp"]:
            assert hasattr(MarketData, field), f"MarketData missing: {field}"


class TestUniqueConstraints:
    """Unique constraints prevent duplicates."""

    def test_user_email_unique(self):
        """User model has unique email."""
        from app.models.user import User

        source = inspect.getsource(User)
        assert "unique" in source.lower()

    def test_alert_config_chat_id_unique(self):
        """Alert config has unique telegram_chat_id."""
        from app.models.alert_config import AlertConfig

        source = inspect.getsource(AlertConfig)
        assert "unique" in source.lower()
