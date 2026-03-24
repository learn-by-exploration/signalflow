"""Tests for Phase 5 P1 — Trust & Retention features.

Covers: signal stats endpoint, weekly digest, daily alert budget,
tutorial/welcome formatter, weekly digest formatter.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.alerts.dispatcher import AlertDispatcher, DAILY_ALERT_BUDGET
from app.services.alerts.formatter import (
    format_tutorial,
    format_weekly_digest,
    format_welcome,
)


# ── Weekly Digest Formatter ──


class TestWeeklyDigestFormatter:
    def test_empty_digest(self) -> None:
        result = format_weekly_digest({"total": 0})
        assert "Weekly Digest" in result
        assert "No signals were resolved" in result

    def test_full_digest(self) -> None:
        stats = {
            "total": 10,
            "hit_target": 7,
            "hit_stop": 2,
            "expired": 1,
            "win_rate": 77.8,
            "avg_return_pct": 3.45,
            "top_winner": {"symbol": "HDFCBANK", "return_pct": 8.5},
            "top_loser": {"symbol": "BTCUSDT", "return_pct": -2.1},
        }
        result = format_weekly_digest(stats)
        assert "Weekly Digest" in result
        assert "Signals resolved: 10" in result
        assert "Hit target: 7" in result
        assert "Hit stop: 2" in result
        assert "Win rate:" in result
        assert "77.8%" in result
        assert "+3.45%" in result
        assert "HDFCBANK" in result
        assert "BTCUSDT" in result
        assert "+8.50%" in result
        assert "-2.10%" in result

    def test_negative_avg_return(self) -> None:
        stats = {
            "total": 5,
            "hit_target": 1,
            "hit_stop": 3,
            "expired": 1,
            "win_rate": 25.0,
            "avg_return_pct": -1.5,
        }
        result = format_weekly_digest(stats)
        assert "-1.50%" in result

    def test_no_top_winner_loser(self) -> None:
        stats = {
            "total": 2,
            "hit_target": 1,
            "hit_stop": 1,
            "expired": 0,
            "win_rate": 50.0,
            "avg_return_pct": 0.5,
        }
        result = format_weekly_digest(stats)
        assert "Best" not in result
        assert "Worst" not in result


# ── Tutorial Formatter ──


class TestTutorialFormatter:
    def test_tutorial_content(self) -> None:
        result = format_tutorial()
        assert "How to Read" in result
        assert "Analysis Type" in result
        assert "STRONGLY BULLISH" in result
        assert "Analysis Strength" in result
        assert "Key Levels" in result
        assert "support" in result
        assert "AI Reasoning" in result
        assert "RSI" in result
        assert "MACD" in result
        assert "not financial advice" in result

    def test_welcome_includes_tutorial(self) -> None:
        result = format_welcome()
        assert "/tutorial" in result


# ── Daily Alert Budget ──


class TestDailyAlertBudget:
    @pytest.fixture
    def sent_messages(self) -> list:
        return []

    @pytest.fixture
    def mock_send(self, sent_messages: list):
        async def _send(chat_id: int, text: str) -> None:
            sent_messages.append({"chat_id": chat_id, "text": text})
        return _send

    @pytest.fixture
    def stock_signal(self) -> dict:
        return {
            "symbol": "HDFCBANK.NS",
            "market_type": "stock",
            "signal_type": "STRONG_BUY",
            "confidence": 92,
            "current_price": "1678.90",
            "target_price": "1780.00",
            "stop_loss": "1630.00",
            "timeframe": "2-4 weeks",
            "ai_reasoning": "Credit growth accelerating.",
            "technical_data": {"rsi": {"value": 62.7, "signal": "neutral"}},
        }

    @pytest.fixture
    def subscriber(self) -> dict:
        return {
            "telegram_chat_id": 12345,
            "markets": ["stock", "crypto", "forex"],
            "min_confidence": 60,
            "signal_types": ["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"],
            "quiet_hours": None,
            "is_active": True,
        }

    @pytest.mark.asyncio
    async def test_budget_allows_alerts_under_limit(
        self, mock_send, sent_messages: list, stock_signal: dict, subscriber: dict
    ) -> None:
        daily_counts: dict[int, int] = {12345: 5}
        dispatcher = AlertDispatcher(mock_send, daily_counts=daily_counts)
        sent = await dispatcher.dispatch_signal(stock_signal, [subscriber])
        assert sent == 1
        assert daily_counts[12345] == 6

    @pytest.mark.asyncio
    async def test_budget_blocks_after_limit(
        self, mock_send, sent_messages: list, stock_signal: dict, subscriber: dict
    ) -> None:
        daily_counts: dict[int, int] = {12345: DAILY_ALERT_BUDGET}
        dispatcher = AlertDispatcher(mock_send, daily_counts=daily_counts)
        sent = await dispatcher.dispatch_signal(stock_signal, [subscriber])
        assert sent == 0
        assert len(sent_messages) == 0

    @pytest.mark.asyncio
    async def test_budget_increments_count(
        self, mock_send, sent_messages: list, stock_signal: dict, subscriber: dict
    ) -> None:
        daily_counts: dict[int, int] = {}
        dispatcher = AlertDispatcher(mock_send, daily_counts=daily_counts)
        sent = await dispatcher.dispatch_signal(stock_signal, [subscriber])
        assert sent == 1
        assert daily_counts[12345] == 1

    @pytest.mark.asyncio
    async def test_broadcasts_not_budget_limited(
        self, mock_send, sent_messages: list, subscriber: dict
    ) -> None:
        """Broadcasts (morning brief, evening wrap) bypass daily budget."""
        daily_counts: dict[int, int] = {12345: DAILY_ALERT_BUDGET + 5}
        dispatcher = AlertDispatcher(mock_send, daily_counts=daily_counts)
        sent = await dispatcher.dispatch_broadcast("Morning brief text", [subscriber])
        assert sent == 1  # Broadcast should still go through

    @pytest.mark.asyncio
    async def test_budget_per_subscriber(
        self, mock_send, sent_messages: list, stock_signal: dict
    ) -> None:
        """Budget is tracked per subscriber, not globally."""
        sub1 = {
            "telegram_chat_id": 111,
            "markets": ["stock"],
            "min_confidence": 60,
            "signal_types": ["STRONG_BUY"],
            "quiet_hours": None,
            "is_active": True,
        }
        sub2 = {
            "telegram_chat_id": 222,
            "markets": ["stock"],
            "min_confidence": 60,
            "signal_types": ["STRONG_BUY"],
            "quiet_hours": None,
            "is_active": True,
        }
        daily_counts: dict[int, int] = {111: DAILY_ALERT_BUDGET, 222: 0}
        dispatcher = AlertDispatcher(mock_send, daily_counts=daily_counts)
        sent = await dispatcher.dispatch_signal(stock_signal, [sub1, sub2])
        assert sent == 1  # Only sub2 should receive
        assert daily_counts[222] == 1


# ── Weekly Digest Task ──


class TestWeeklyDigestTask:
    @patch("app.tasks.alert_tasks._get_active_subscribers")
    @patch("app.tasks.alert_tasks._get_weekly_stats")
    @patch("app.tasks.alert_tasks.send_telegram_message", new_callable=AsyncMock)
    def test_weekly_digest_runs(
        self,
        mock_send: AsyncMock,
        mock_stats: MagicMock,
        mock_subs: MagicMock,
    ) -> None:
        mock_stats.return_value = {
            "total": 10,
            "hit_target": 7,
            "hit_stop": 2,
            "expired": 1,
            "win_rate": 77.8,
            "avg_return_pct": 3.45,
        }
        mock_subs.return_value = [
            {"telegram_chat_id": 111, "is_active": True},
        ]
        mock_send.return_value = None

        from app.tasks.alert_tasks import weekly_digest

        result = weekly_digest()
        assert result["status"] == "ok"
        assert result["subscribers"] == 1

    @patch("app.tasks.alert_tasks._get_active_subscribers")
    @patch("app.tasks.alert_tasks._get_weekly_stats")
    @patch("app.tasks.alert_tasks.send_telegram_message", new_callable=AsyncMock)
    def test_weekly_digest_empty(
        self,
        mock_send: AsyncMock,
        mock_stats: MagicMock,
        mock_subs: MagicMock,
    ) -> None:
        mock_stats.return_value = {"total": 0}
        mock_subs.return_value = [
            {"telegram_chat_id": 111, "is_active": True},
        ]
        mock_send.return_value = None

        from app.tasks.alert_tasks import weekly_digest

        result = weekly_digest()
        assert result["status"] == "ok"
