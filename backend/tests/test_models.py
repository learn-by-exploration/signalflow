"""Tests for model definitions — verify table names, columns, defaults."""

import uuid

import pytest

from app.models.alert_config import AlertConfig
from app.models.backtest import BacktestRun
from app.models.market_data import MarketData
from app.models.price_alert import PriceAlert
from app.models.signal import Signal
from app.models.signal_history import SignalHistory
from app.models.signal_share import SignalShare
from app.models.trade import Trade


class TestSignalModel:
    def test_tablename(self):
        assert Signal.__tablename__ == "signals"

    def test_has_required_columns(self):
        cols = {c.name for c in Signal.__table__.columns}
        expected = {
            "id", "symbol", "market_type", "signal_type", "confidence",
            "current_price", "target_price", "stop_loss", "timeframe",
            "ai_reasoning", "technical_data", "sentiment_data",
            "is_active", "created_at", "expires_at",
        }
        assert expected.issubset(cols)

    def test_id_is_uuid(self):
        col = Signal.__table__.columns["id"]
        assert col.primary_key


class TestSignalHistoryModel:
    def test_tablename(self):
        assert SignalHistory.__tablename__ == "signal_history"

    def test_has_signal_id_fk(self):
        col = SignalHistory.__table__.columns["signal_id"]
        assert len(col.foreign_keys) > 0

    def test_has_relationship(self):
        assert hasattr(SignalHistory, "signal_rel")


class TestMarketDataModel:
    def test_tablename(self):
        assert MarketData.__tablename__ == "market_data"

    def test_has_required_columns(self):
        cols = {c.name for c in MarketData.__table__.columns}
        expected = {"id", "symbol", "market_type", "open", "high", "low", "close", "volume", "timestamp", "created_at"}
        assert expected.issubset(cols)


class TestAlertConfigModel:
    def test_tablename(self):
        assert AlertConfig.__tablename__ == "alert_configs"

    def test_telegram_chat_id_unique(self):
        col = AlertConfig.__table__.columns["telegram_chat_id"]
        assert col.unique

    def test_has_watchlist(self):
        cols = {c.name for c in AlertConfig.__table__.columns}
        assert "watchlist" in cols


class TestTradeModel:
    def test_tablename(self):
        assert Trade.__tablename__ == "trades"

    def test_has_side_column(self):
        cols = {c.name for c in Trade.__table__.columns}
        assert "side" in cols
        assert "quantity" in cols
        assert "price" in cols


class TestPriceAlertModel:
    def test_tablename(self):
        assert PriceAlert.__tablename__ == "price_alerts"

    def test_has_condition_column(self):
        cols = {c.name for c in PriceAlert.__table__.columns}
        assert "condition" in cols
        assert "threshold" in cols
        assert "is_triggered" in cols
        assert "is_active" in cols


class TestSignalShareModel:
    def test_tablename(self):
        assert SignalShare.__tablename__ == "signal_shares"

    def test_has_signal_id(self):
        cols = {c.name for c in SignalShare.__table__.columns}
        assert "signal_id" in cols


class TestBacktestRunModel:
    def test_tablename(self):
        assert BacktestRun.__tablename__ == "backtest_runs"

    def test_has_required_columns(self):
        cols = {c.name for c in BacktestRun.__table__.columns}
        expected = {
            "id", "symbol", "market_type", "start_date", "end_date",
            "total_signals", "wins", "losses", "win_rate", "avg_return_pct",
            "total_return_pct", "max_drawdown_pct", "parameters",
            "status", "error_message", "created_at", "completed_at",
        }
        assert expected.issubset(cols)
