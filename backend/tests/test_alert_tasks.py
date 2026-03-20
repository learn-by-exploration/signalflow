"""Tests for the alert Celery tasks — morning_brief and evening_wrap."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMorningBriefTask:
    @patch("app.tasks.alert_tasks._get_active_subscribers")
    @patch("app.tasks.alert_tasks._get_active_signals_summary")
    @patch("app.tasks.alert_tasks._get_market_summary")
    @patch("app.services.ai_engine.briefing.BriefingGenerator.morning_brief", new_callable=AsyncMock)
    @patch("app.tasks.alert_tasks.send_telegram_message", new_callable=AsyncMock)
    def test_morning_brief_runs(
        self,
        mock_send: AsyncMock,
        mock_brief: AsyncMock,
        mock_market: MagicMock,
        mock_signals: MagicMock,
        mock_subs: MagicMock,
    ) -> None:
        mock_market.return_value = {"BTCUSDT": {"close": "97000", "timestamp": "2026-03-20T10:00:00"}}
        mock_signals.return_value = "BTC: STRONG_BUY (90%)"
        mock_brief.return_value = "Markets are bullish today."
        mock_subs.return_value = [
            {"telegram_chat_id": 111, "is_active": True},
        ]
        mock_send.return_value = None

        from app.tasks.alert_tasks import morning_brief

        result = morning_brief()
        assert result["status"] == "ok"
        assert result["subscribers"] == 1
        mock_brief.assert_called_once()


class TestEveningWrapTask:
    @patch("app.tasks.alert_tasks._get_active_subscribers")
    @patch("app.tasks.alert_tasks._get_active_signals_summary")
    @patch("app.tasks.alert_tasks._get_market_summary")
    @patch("app.services.ai_engine.briefing.BriefingGenerator.evening_wrap", new_callable=AsyncMock)
    @patch("app.tasks.alert_tasks.send_telegram_message", new_callable=AsyncMock)
    def test_evening_wrap_runs(
        self,
        mock_send: AsyncMock,
        mock_wrap: AsyncMock,
        mock_market: MagicMock,
        mock_signals: MagicMock,
        mock_subs: MagicMock,
    ) -> None:
        mock_market.return_value = {"BTCUSDT": {"close": "97000", "timestamp": "2026-03-20T16:00:00"}}
        mock_signals.return_value = "BTC: STRONG_BUY (90%)"
        mock_wrap.return_value = "Markets closed higher today. Key signals performed well."
        mock_subs.return_value = [
            {"telegram_chat_id": 222, "is_active": True},
        ]
        mock_send.return_value = None

        from app.tasks.alert_tasks import evening_wrap

        result = evening_wrap()
        assert result["status"] == "ok"
        assert result["subscribers"] == 1
        mock_wrap.assert_called_once()
