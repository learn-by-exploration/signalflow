"""Tests for Pydantic schemas — validation, edge cases, serialization."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.alert import AlertConfigCreate, AlertConfigUpdate, WatchlistUpdate
from app.schemas.market import MarketOverviewResponse, MarketSnapshot
from app.schemas.p3 import (
    AskQuestion,
    BacktestCreate,
    PriceAlertCreate,
    PriceAlertData,
    PortfolioSummary,
    TradeCreate,
    TradeData,
)
from app.schemas.signal import (
    MetaResponse,
    SignalHistoryItem,
    SignalListResponse,
    SignalResponse,
    SignalStatsResponse,
    SymbolTrackRecord,
    WeeklyTrendItem,
)


# ─── SignalResponse ─────────────────────────────────────────

class TestSignalResponse:
    def test_valid_signal(self):
        sig = SignalResponse(
            id=uuid4(), symbol="HDFCBANK.NS", market_type="stock",
            signal_type="STRONG_BUY", confidence=92,
            current_price=Decimal("1678.90"), target_price=Decimal("1780.00"),
            stop_loss=Decimal("1630.00"), ai_reasoning="Test reasoning",
            technical_data={"rsi": 62.7}, is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        assert sig.confidence == 92

    def test_confidence_bounds(self):
        base = dict(
            id=uuid4(), symbol="X", market_type="stock", signal_type="BUY",
            current_price=Decimal("100"), target_price=Decimal("110"),
            stop_loss=Decimal("90"), ai_reasoning="ok", technical_data={},
            is_active=True, created_at=datetime.now(timezone.utc),
        )
        with pytest.raises(ValidationError):
            SignalResponse(confidence=-1, **base)
        with pytest.raises(ValidationError):
            SignalResponse(confidence=101, **base)

    def test_optional_fields(self):
        sig = SignalResponse(
            id=uuid4(), symbol="X", market_type="stock", signal_type="BUY",
            confidence=50, current_price=Decimal("100"), target_price=Decimal("110"),
            stop_loss=Decimal("90"), ai_reasoning="ok", technical_data={},
            is_active=True, created_at=datetime.now(timezone.utc),
            # optional fields omitted
        )
        assert sig.timeframe is None
        assert sig.sentiment_data is None
        assert sig.expires_at is None


# ─── SignalStatsResponse ────────────────────────────────────

class TestSignalStatsResponse:
    def test_win_rate_bounds(self):
        with pytest.raises(ValidationError):
            SignalStatsResponse(
                total_signals=10, hit_target=5, hit_stop=5,
                expired=0, pending=0, win_rate=101.0, avg_return_pct=1.0,
            )

    def test_valid_stats(self):
        stats = SignalStatsResponse(
            total_signals=100, hit_target=60, hit_stop=20,
            expired=10, pending=10, win_rate=75.0, avg_return_pct=2.5,
        )
        assert stats.win_rate == 75.0


# ─── MetaResponse ──────────────────────────────────────────

class TestMetaResponse:
    def test_valid_meta(self):
        m = MetaResponse(timestamp=datetime.now(timezone.utc), count=5, total=100)
        assert m.count == 5

    def test_total_optional(self):
        m = MetaResponse(timestamp=datetime.now(timezone.utc), count=5)
        assert m.total is None


# ─── AlertConfigCreate ─────────────────────────────────────

class TestAlertConfigCreate:
    def test_defaults(self):
        config = AlertConfigCreate(telegram_chat_id=12345)
        assert config.markets == ["stock", "crypto", "forex"]
        assert config.min_confidence == 60
        assert config.signal_types == ["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"]

    def test_min_confidence_bounds(self):
        with pytest.raises(ValidationError):
            AlertConfigCreate(telegram_chat_id=1, min_confidence=-1)
        with pytest.raises(ValidationError):
            AlertConfigCreate(telegram_chat_id=1, min_confidence=101)

    def test_custom_values(self):
        config = AlertConfigCreate(
            telegram_chat_id=12345, username="test",
            markets=["crypto"], min_confidence=80,
            signal_types=["STRONG_BUY"],
        )
        assert config.markets == ["crypto"]
        assert config.min_confidence == 80


# ─── AlertConfigUpdate ─────────────────────────────────────

class TestAlertConfigUpdate:
    def test_partial_update(self):
        update = AlertConfigUpdate(min_confidence=75)
        dumped = update.model_dump(exclude_unset=True)
        assert dumped == {"min_confidence": 75}

    def test_all_none_by_default(self):
        update = AlertConfigUpdate()
        dumped = update.model_dump(exclude_unset=True)
        assert dumped == {}


# ─── WatchlistUpdate ───────────────────────────────────────

class TestWatchlistUpdate:
    def test_valid(self):
        w = WatchlistUpdate(symbol="BTCUSDT", action="add")
        assert w.symbol == "BTCUSDT"

    def test_missing_symbol(self):
        with pytest.raises(ValidationError):
            WatchlistUpdate(action="add")


# ─── MarketSnapshot ────────────────────────────────────────

class TestMarketSnapshot:
    def test_valid(self):
        snap = MarketSnapshot(
            symbol="BTC", price=Decimal("97000.00"),
            change_pct=Decimal("3.5"), market_type="crypto",
        )
        assert snap.symbol == "BTC"

    def test_volume_optional(self):
        snap = MarketSnapshot(
            symbol="EUR/USD", price=Decimal("1.08"),
            change_pct=Decimal("-0.2"), market_type="forex",
        )
        assert snap.volume is None


# ─── TradeCreate ────────────────────────────────────────────

class TestTradeCreate:
    def test_valid_trade(self):
        t = TradeCreate(
            telegram_chat_id=12345, symbol="HDFCBANK.NS",
            market_type="stock", side="buy",
            quantity=Decimal("10"), price=Decimal("1650.00"),
        )
        assert t.side == "buy"

    def test_optional_fields(self):
        t = TradeCreate(
            telegram_chat_id=12345, symbol="X", market_type="stock",
            side="sell", quantity=Decimal("1"), price=Decimal("100"),
        )
        assert t.notes is None
        assert t.signal_id is None


# ─── PriceAlertCreate ──────────────────────────────────────

class TestPriceAlertCreate:
    def test_valid(self):
        pa = PriceAlertCreate(
            telegram_chat_id=12345, symbol="BTCUSDT",
            market_type="crypto", condition="above",
            threshold=Decimal("100000"),
        )
        assert pa.condition == "above"

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            PriceAlertCreate(telegram_chat_id=12345)


# ─── BacktestCreate ────────────────────────────────────────

class TestBacktestCreate:
    def test_defaults(self):
        bt = BacktestCreate(symbol="BTCUSDT", market_type="crypto")
        assert bt.days == 90

    def test_days_bounds(self):
        with pytest.raises(ValidationError):
            BacktestCreate(symbol="X", market_type="stock", days=6)
        with pytest.raises(ValidationError):
            BacktestCreate(symbol="X", market_type="stock", days=366)

    def test_custom_days(self):
        bt = BacktestCreate(symbol="INFY.NS", market_type="stock", days=180)
        assert bt.days == 180


# ─── AskQuestion ────────────────────────────────────────────

class TestAskQuestion:
    def test_valid(self):
        q = AskQuestion(symbol="BTC", question="What is the trend?")
        assert q.symbol == "BTC"

    def test_question_max_length(self):
        with pytest.raises(ValidationError):
            AskQuestion(symbol="BTC", question="x" * 501)

    def test_missing_question(self):
        with pytest.raises(ValidationError):
            AskQuestion(symbol="BTC")


# ─── PortfolioSummary ──────────────────────────────────────

class TestPortfolioSummary:
    def test_valid(self):
        ps = PortfolioSummary(
            total_invested=Decimal("100000"),
            current_value=Decimal("110000"),
            total_pnl=Decimal("10000"),
            total_pnl_pct=10.0,
            positions=[],
        )
        assert ps.total_pnl_pct == 10.0


# ─── WeeklyTrendItem ───────────────────────────────────────

class TestWeeklyTrendItem:
    def test_valid(self):
        w = WeeklyTrendItem(
            week="2026-W12", start_date="2026-03-16",
            total=10, hit_target=7, win_rate=70.0,
        )
        assert w.win_rate == 70.0


# ─── SymbolTrackRecord ─────────────────────────────────────

class TestSymbolTrackRecord:
    def test_valid(self):
        tr = SymbolTrackRecord(
            symbol="HDFCBANK.NS", total_signals_30d=20,
            hit_target=12, hit_stop=5, expired=3,
            win_rate=70.6, avg_return_pct=1.85,
        )
        assert tr.symbol == "HDFCBANK.NS"

    def test_win_rate_bounds(self):
        with pytest.raises(ValidationError):
            SymbolTrackRecord(
                symbol="X", total_signals_30d=0,
                hit_target=0, hit_stop=0, expired=0,
                win_rate=101.0, avg_return_pct=0.0,
            )


# ─── SignalHistoryItem ──────────────────────────────────────

class TestSignalHistoryItem:
    def test_valid(self):
        h = SignalHistoryItem(
            id=uuid4(), signal_id=uuid4(), outcome="hit_target",
            exit_price=Decimal("1780.00"), return_pct=Decimal("6.02"),
            created_at=datetime.now(timezone.utc),
        )
        assert h.outcome == "hit_target"

    def test_optional_fields(self):
        h = SignalHistoryItem(
            id=uuid4(), signal_id=uuid4(),
            created_at=datetime.now(timezone.utc),
        )
        assert h.outcome is None
        assert h.exit_price is None
        assert h.signal is None
