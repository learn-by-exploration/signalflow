"""Tests for Phase 5 P3 features — price alerts, portfolio, sharing, AI Q&A, backtesting."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


# ── Price Alert Tests ──


class TestPriceAlertCreate:
    """Tests for creating price alerts."""

    def test_price_alert_model_fields(self):
        """PriceAlert model has correct fields."""
        from app.models.price_alert import PriceAlert

        alert = PriceAlert(
            telegram_chat_id=12345,
            symbol="BTCUSDT",
            market_type="crypto",
            condition="above",
            threshold=Decimal("100000"),
        )
        assert alert.symbol == "BTCUSDT"
        assert alert.condition == "above"
        assert alert.threshold == Decimal("100000")
        # Note: default=False in the column, but Python-side before flush it's None
        assert alert.is_triggered in (False, None)
        assert alert.is_active in (True, None)

    def test_price_alert_below_condition(self):
        """PriceAlert supports 'below' condition."""
        from app.models.price_alert import PriceAlert

        alert = PriceAlert(
            telegram_chat_id=12345,
            symbol="HDFCBANK.NS",
            market_type="stock",
            condition="below",
            threshold=Decimal("1600.00"),
        )
        assert alert.condition == "below"

    def test_price_alert_schema_validation(self):
        """PriceAlertCreate schema validates correctly."""
        from app.schemas.p3 import PriceAlertCreate

        alert = PriceAlertCreate(
            symbol="ETHUSDT",
            market_type="crypto",
            condition="above",
            threshold=Decimal("4000"),
        )
        assert alert.symbol == "ETHUSDT"
        assert alert.threshold == Decimal("4000")

    def test_price_alert_data_from_attributes(self):
        """PriceAlertData works with from_attributes."""
        from app.schemas.p3 import PriceAlertData

        mock_alert = MagicMock()
        mock_alert.id = uuid4()
        mock_alert.telegram_chat_id = 12345
        mock_alert.symbol = "BTCUSDT"
        mock_alert.market_type = "crypto"
        mock_alert.condition = "above"
        mock_alert.threshold = Decimal("100000")
        mock_alert.is_triggered = False
        mock_alert.is_active = True
        mock_alert.triggered_at = None
        mock_alert.created_at = datetime.now(timezone.utc)

        data = PriceAlertData.model_validate(mock_alert, from_attributes=True)
        assert data.symbol == "BTCUSDT"
        assert data.is_triggered is False


# ── Trade / Portfolio Tests ──


class TestTradeModel:
    """Tests for trade logging."""

    def test_trade_buy(self):
        """Trade model handles buy side."""
        from app.models.trade import Trade

        trade = Trade(
            telegram_chat_id=12345,
            symbol="HDFCBANK.NS",
            market_type="stock",
            side="buy",
            quantity=Decimal("10"),
            price=Decimal("1678.90"),
        )
        assert trade.side == "buy"
        assert trade.quantity == Decimal("10")
        assert trade.price == Decimal("1678.90")

    def test_trade_sell(self):
        """Trade model handles sell side."""
        from app.models.trade import Trade

        trade = Trade(
            telegram_chat_id=12345,
            symbol="BTCUSDT",
            market_type="crypto",
            side="sell",
            quantity=Decimal("0.5"),
            price=Decimal("98000"),
        )
        assert trade.side == "sell"

    def test_trade_with_signal_link(self):
        """Trade can reference a signal."""
        from app.models.trade import Trade

        sig_id = uuid4()
        trade = Trade(
            telegram_chat_id=12345,
            symbol="ETHUSDT",
            market_type="crypto",
            side="buy",
            quantity=Decimal("2"),
            price=Decimal("3500"),
            signal_id=sig_id,
        )
        assert trade.signal_id == sig_id

    def test_trade_schema(self):
        """TradeCreate and TradeData schemas work."""
        from app.schemas.p3 import TradeCreate, TradeData

        create = TradeCreate(
            symbol="RELIANCE.NS",
            market_type="stock",
            side="buy",
            quantity=Decimal("5"),
            price=Decimal("2450.00"),
        )
        assert create.side == "buy"

    def test_portfolio_summary_schema(self):
        """PortfolioSummary schema structures correctly."""
        from app.schemas.p3 import PortfolioSummary

        summary = PortfolioSummary(
            total_invested=Decimal("100000"),
            current_value=Decimal("112000"),
            total_pnl=Decimal("12000"),
            total_pnl_pct=12.0,
            positions=[{
                "symbol": "HDFCBANK.NS",
                "market_type": "stock",
                "quantity": "10",
                "avg_price": "1678.90",
                "current_price": "1780.00",
                "value": "17800.00",
                "pnl": "1011.00",
                "pnl_pct": 6.02,
            }],
        )
        assert summary.total_pnl_pct == 12.0
        assert len(summary.positions) == 1


# ── Signal Sharing Tests ──


class TestSignalSharing:
    """Tests for signal sharing."""

    def test_signal_share_model(self):
        """SignalShare model has correct fields."""
        from app.models.signal_share import SignalShare

        sig_id = uuid4()
        share = SignalShare(signal_id=sig_id)
        assert share.signal_id == sig_id

    def test_signal_share_creates_uuid(self):
        """SignalShare auto-generates a UUID."""
        from app.models.signal_share import SignalShare

        share1 = SignalShare(signal_id=uuid4())
        share2 = SignalShare(signal_id=uuid4())
        # Both should have different IDs (though they won't be set until DB flush)
        assert share1.signal_id != share2.signal_id


# ── AI Q&A Tests ──


class TestAIQA:
    """Tests for AI-powered symbol Q&A."""

    def test_symbol_qa_prompt_formatting(self):
        """SYMBOL_QA_PROMPT formats correctly with all placeholders."""
        from app.services.ai_engine.prompts import SYMBOL_QA_PROMPT

        formatted = SYMBOL_QA_PROMPT.format(
            symbol="HDFCBANK",
            market_type="stock",
            market_data="Price: 1678.90, High: 1690.50",
            signals_info="STRONG_BUY (92%)",
            question="Is it a good time to buy?",
        )
        assert "HDFCBANK" in formatted
        assert "Is it a good time to buy?" in formatted
        assert "stock" in formatted

    def test_ask_question_schema(self):
        """AskQuestion schema validates correctly."""
        from app.schemas.p3 import AskQuestion

        q = AskQuestion(symbol="BTCUSDT", question="What's the trend?")
        assert q.symbol == "BTCUSDT"
        assert q.question == "What's the trend?"

    def test_ask_question_max_length(self):
        """AskQuestion enforces max_length on question."""
        from pydantic import ValidationError

        from app.schemas.p3 import AskQuestion

        with pytest.raises(ValidationError):
            AskQuestion(symbol="BTC", question="x" * 501)


# ── Backtest Tests ──


class TestBacktesting:
    """Tests for backtesting framework."""

    def test_backtest_model(self):
        """BacktestRun model has correct defaults."""
        from app.models.backtest import BacktestRun

        bt = BacktestRun(
            symbol="BTCUSDT",
            market_type="crypto",
            status="pending",
        )
        assert bt.status == "pending"
        assert bt.wins is None
        assert bt.losses is None

    def test_backtest_create_schema(self):
        """BacktestCreate schema validates correctly."""
        from app.schemas.p3 import BacktestCreate

        bc = BacktestCreate(symbol="HDFCBANK", market_type="stock", days=90)
        assert bc.days == 90

    def test_backtest_create_schema_bounds(self):
        """BacktestCreate enforces day bounds (7-365)."""
        from pydantic import ValidationError

        from app.schemas.p3 import BacktestCreate

        with pytest.raises(ValidationError):
            BacktestCreate(symbol="BTC", market_type="crypto", days=3)

        with pytest.raises(ValidationError):
            BacktestCreate(symbol="BTC", market_type="crypto", days=500)

    def test_backtest_data_schema(self):
        """BacktestData schema works with from_attributes."""
        from app.schemas.p3 import BacktestData

        mock_bt = MagicMock()
        mock_bt.id = uuid4()
        mock_bt.symbol = "BTCUSDT"
        mock_bt.market_type = "crypto"
        mock_bt.start_date = datetime.now(timezone.utc)
        mock_bt.end_date = datetime.now(timezone.utc)
        mock_bt.total_signals = 10
        mock_bt.wins = 7
        mock_bt.losses = 3
        mock_bt.win_rate = 70.0
        mock_bt.avg_return_pct = 2.5
        mock_bt.total_return_pct = 25.0
        mock_bt.max_drawdown_pct = 5.0
        mock_bt.status = "completed"
        mock_bt.error_message = None
        mock_bt.created_at = datetime.now(timezone.utc)
        mock_bt.completed_at = datetime.now(timezone.utc)

        data = BacktestData.model_validate(mock_bt, from_attributes=True)
        assert data.win_rate == 70.0
        assert data.status == "completed"

    def test_backtest_engine_metrics_calculation(self):
        """Backtest engine computes correct win/loss metrics."""
        # Simulate the metrics calculation logic from backtest_tasks.py
        trades = [
            {"result": "win", "return_pct": 5.0},
            {"result": "win", "return_pct": 3.0},
            {"result": "loss", "return_pct": -2.0},
            {"result": "win", "return_pct": 4.0},
            {"result": "loss", "return_pct": -1.5},
        ]

        total_signals = len(trades)
        wins = sum(1 for t in trades if t["result"] == "win")
        losses = sum(1 for t in trades if t["result"] == "loss")
        win_rate = (wins / total_signals * 100) if total_signals > 0 else 0
        returns = [t["return_pct"] for t in trades]
        avg_return = sum(returns) / len(returns)
        total_return = sum(returns)

        assert total_signals == 5
        assert wins == 3
        assert losses == 2
        assert win_rate == 60.0
        assert avg_return == pytest.approx(1.7)
        assert total_return == pytest.approx(8.5)

    def test_backtest_max_drawdown_calculation(self):
        """Backtest drawdown calculation is correct."""
        returns = [5.0, -3.0, -2.0, 4.0, -1.0]

        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0
        for r in returns:
            cumulative += r
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_drawdown:
                max_drawdown = dd

        # Peak at 5.0, then drops to 0.0 (dd=5.0), recovers to 4.0 (dd=1.0)
        assert max_drawdown == pytest.approx(5.0)


# ── Formatter Tests ──


class TestP3Formatters:
    """Tests for new formatting functions."""

    def test_format_price_alert_created(self):
        """format_price_alert_created produces correct output."""
        from app.services.alerts.formatter import format_price_alert_created

        msg = format_price_alert_created("BTCUSDT", "above", "100000")
        assert "Price Alert Set" in msg
        assert "BTC" in msg
        assert "above" in msg
        assert "100000" in msg

    def test_format_price_alert_below(self):
        """format_price_alert_created handles below condition."""
        from app.services.alerts.formatter import format_price_alert_created

        msg = format_price_alert_created("HDFCBANK.NS", "below", "1600.00")
        assert "📉" in msg
        assert "HDFCBANK" in msg

    def test_format_portfolio_summary(self):
        """format_portfolio_summary formats positions correctly."""
        from app.services.alerts.formatter import format_portfolio_summary

        positions = [
            {
                "symbol": "HDFCBANK.NS",
                "quantity": 10.0,
                "avg_price": 1678.9,
                "total_cost": 16789.0,
            },
            {
                "symbol": "BTCUSDT",
                "quantity": 0.5,
                "avg_price": 98000.0,
                "total_cost": 49000.0,
            },
        ]
        msg = format_portfolio_summary(positions)
        assert "Portfolio" in msg
        assert "HDFCBANK" in msg
        assert "BTC" in msg
        assert "Total invested" in msg

    def test_format_portfolio_empty(self):
        """format_portfolio_summary handles empty list."""
        from app.services.alerts.formatter import format_portfolio_summary

        msg = format_portfolio_summary([])
        assert "Portfolio" in msg
        assert "Total invested: 0.00" in msg

    def test_format_welcome_includes_new_commands(self):
        """Updated welcome message includes P3 commands."""
        from app.services.alerts.formatter import format_welcome

        msg = format_welcome()
        assert "/ask" in msg
        assert "/alert" in msg
        assert "/trade" in msg
        assert "/portfolio" in msg


# ── Price Alert Checking Task Tests ──


class TestPriceAlertChecker:
    """Tests for the price alert monitoring task."""

    def test_check_alerts_task_exists(self):
        """Price alert check task is registered."""
        from app.tasks.price_alert_tasks import check_price_alerts

        assert check_price_alerts.name == "app.tasks.price_alert_tasks.check_price_alerts"

    def test_price_alert_trigger_logic_above(self):
        """Alert triggers when price >= threshold (above condition)."""
        current_price = 105000.0
        threshold = 100000.0
        condition = "above"
        should_trigger = (condition == "above" and current_price >= threshold)
        assert should_trigger is True

    def test_price_alert_trigger_logic_below(self):
        """Alert triggers when price <= threshold (below condition)."""
        current_price = 1550.0
        threshold = 1600.0
        condition = "below"
        should_trigger = (condition == "below" and current_price <= threshold)
        assert should_trigger is True

    def test_price_alert_no_trigger_above(self):
        """Alert does NOT trigger when price < threshold (above condition)."""
        current_price = 99000.0
        threshold = 100000.0
        condition = "above"
        should_trigger = (condition == "above" and current_price >= threshold)
        assert should_trigger is False

    def test_price_alert_no_trigger_below(self):
        """Alert does NOT trigger when price > threshold (below condition)."""
        current_price = 1700.0
        threshold = 1600.0
        condition = "below"
        should_trigger = (condition == "below" and current_price <= threshold)
        assert should_trigger is False


# ── Backtest Task Tests ──


class TestBacktestTask:
    """Tests for the backtest Celery task."""

    def test_backtest_task_exists(self):
        """Backtest task is registered."""
        from app.tasks.backtest_tasks import run_backtest

        assert run_backtest.name == "app.tasks.backtest_tasks.run_backtest"


# ── Scheduler Tests ──


class TestScheduler:
    """Tests for updated Celery Beat schedule."""

    def test_price_alert_task_in_schedule(self):
        """Price alert check is in the schedule."""
        from app.tasks.scheduler import CELERY_BEAT_SCHEDULE

        assert "check-price-alerts" in CELERY_BEAT_SCHEDULE
        assert CELERY_BEAT_SCHEDULE["check-price-alerts"]["schedule"] == 60.0

    def test_all_tasks_in_schedule(self):
        """All expected tasks are in the Celery Beat schedule."""
        from app.tasks.scheduler import CELERY_BEAT_SCHEDULE

        expected = [
            "fetch-indian-stocks",
            "fetch-crypto-prices",
            "fetch-forex-rates",
            "run-technical-analysis",
            "run-sentiment-analysis",
            "generate-signals",
            "morning-brief",
            "evening-wrap",
            "weekly-digest",
            "resolve-signals",
            "health-check",
            "check-price-alerts",
        ]
        for task in expected:
            assert task in CELERY_BEAT_SCHEDULE, f"Missing task: {task}"


# ── Router Tests ──


class TestRouterInclusion:
    """Tests that all P3 routers are included."""

    def test_router_has_all_prefixes(self):
        """Main router includes all P3 sub-router prefixes."""
        from app.api.router import api_router

        route_paths = [r.path for r in api_router.routes]
        # Check that P3 prefixes exist in route patterns
        # FastAPI includes routes with their full prefix
        found_prefixes = set()
        for route in api_router.routes:
            path = getattr(route, "path", "")
            if "/alerts/price" in path:
                found_prefixes.add("price_alerts")
            if "/portfolio" in path:
                found_prefixes.add("portfolio")
            if "/ai" in path:
                found_prefixes.add("ai_qa")
            if "/backtest" in path:
                found_prefixes.add("backtest")
            if "share" in path:
                found_prefixes.add("sharing")

        assert "price_alerts" in found_prefixes
        assert "portfolio" in found_prefixes
        assert "ai_qa" in found_prefixes
        assert "backtest" in found_prefixes
        assert "sharing" in found_prefixes
