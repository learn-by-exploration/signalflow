"""Tests for alert dispatcher — filter logic and routing."""

import pytest

from app.services.alerts.dispatcher import AlertDispatcher


@pytest.fixture
def sent_messages() -> list:
    """Accumulate messages sent by the mock bot function."""
    return []


@pytest.fixture
def mock_send(sent_messages: list):
    """Async mock for telegram send function."""
    async def _send(chat_id: int, text: str) -> None:
        sent_messages.append({"chat_id": chat_id, "text": text})
    return _send


@pytest.fixture
def stock_signal() -> dict:
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
def active_subscriber() -> dict:
    return {
        "telegram_chat_id": 12345,
        "markets": ["stock", "crypto", "forex"],
        "min_confidence": 60,
        "signal_types": ["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"],
        "quiet_hours": None,
        "is_active": True,
    }


class TestDispatchSignal:
    @pytest.mark.asyncio
    async def test_send_to_eligible_subscriber(
        self, mock_send, sent_messages: list, stock_signal: dict, active_subscriber: dict
    ) -> None:
        dispatcher = AlertDispatcher(mock_send)
        sent = await dispatcher.dispatch_signal(stock_signal, [active_subscriber])
        assert sent == 1
        assert len(sent_messages) == 1
        assert sent_messages[0]["chat_id"] == 12345

    @pytest.mark.asyncio
    async def test_skip_inactive_subscriber(
        self, mock_send, sent_messages: list, stock_signal: dict, active_subscriber: dict
    ) -> None:
        active_subscriber["is_active"] = False
        dispatcher = AlertDispatcher(mock_send)
        sent = await dispatcher.dispatch_signal(stock_signal, [active_subscriber])
        assert sent == 0
        assert len(sent_messages) == 0

    @pytest.mark.asyncio
    async def test_filter_by_market(
        self, mock_send, sent_messages: list, stock_signal: dict, active_subscriber: dict
    ) -> None:
        active_subscriber["markets"] = ["crypto"]  # only crypto
        dispatcher = AlertDispatcher(mock_send)
        sent = await dispatcher.dispatch_signal(stock_signal, [active_subscriber])
        assert sent == 0

    @pytest.mark.asyncio
    async def test_filter_by_min_confidence(
        self, mock_send, sent_messages: list, stock_signal: dict, active_subscriber: dict
    ) -> None:
        active_subscriber["min_confidence"] = 95  # higher than 92
        dispatcher = AlertDispatcher(mock_send)
        sent = await dispatcher.dispatch_signal(stock_signal, [active_subscriber])
        assert sent == 0

    @pytest.mark.asyncio
    async def test_filter_by_signal_type(
        self, mock_send, sent_messages: list, stock_signal: dict, active_subscriber: dict
    ) -> None:
        active_subscriber["signal_types"] = ["SELL", "STRONG_SELL"]  # no BUY
        dispatcher = AlertDispatcher(mock_send)
        sent = await dispatcher.dispatch_signal(stock_signal, [active_subscriber])
        assert sent == 0

    @pytest.mark.asyncio
    async def test_multiple_subscribers(
        self, mock_send, sent_messages: list, stock_signal: dict
    ) -> None:
        subs = [
            {
                "telegram_chat_id": 111,
                "markets": ["stock"],
                "min_confidence": 60,
                "signal_types": ["STRONG_BUY"],
                "quiet_hours": None,
                "is_active": True,
            },
            {
                "telegram_chat_id": 222,
                "markets": ["stock"],
                "min_confidence": 60,
                "signal_types": ["STRONG_BUY"],
                "quiet_hours": None,
                "is_active": True,
            },
            {
                "telegram_chat_id": 333,
                "markets": ["crypto"],  # won't match
                "min_confidence": 60,
                "signal_types": ["STRONG_BUY"],
                "quiet_hours": None,
                "is_active": True,
            },
        ]
        dispatcher = AlertDispatcher(mock_send)
        sent = await dispatcher.dispatch_signal(stock_signal, subs)
        assert sent == 2

    @pytest.mark.asyncio
    async def test_send_failure_does_not_stop_others(
        self, stock_signal: dict
    ) -> None:
        call_count = {"n": 0}

        async def flaky_send(chat_id: int, text: str) -> None:
            call_count["n"] += 1
            if chat_id == 111:
                raise ConnectionError("Telegram down")

        subs = [
            {
                "telegram_chat_id": 111,
                "markets": ["stock"],
                "min_confidence": 60,
                "signal_types": ["STRONG_BUY"],
                "quiet_hours": None,
                "is_active": True,
            },
            {
                "telegram_chat_id": 222,
                "markets": ["stock"],
                "min_confidence": 60,
                "signal_types": ["STRONG_BUY"],
                "quiet_hours": None,
                "is_active": True,
            },
        ]
        dispatcher = AlertDispatcher(flaky_send)
        sent = await dispatcher.dispatch_signal(stock_signal, subs)
        assert sent == 1  # second subscriber still gets it
        assert call_count["n"] == 2


class TestDispatchBroadcast:
    @pytest.mark.asyncio
    async def test_broadcast_to_all_active(
        self, mock_send, sent_messages: list
    ) -> None:
        subs = [
            {"telegram_chat_id": 111, "is_active": True},
            {"telegram_chat_id": 222, "is_active": True},
            {"telegram_chat_id": 333, "is_active": False},
        ]
        dispatcher = AlertDispatcher(mock_send)
        sent = await dispatcher.dispatch_broadcast("Good morning!", subs)
        assert sent == 2
        assert len(sent_messages) == 2


class TestQuietHours:
    @pytest.mark.asyncio
    async def test_quiet_hours_blocks_dispatch(
        self, mock_send, sent_messages: list, stock_signal: dict
    ) -> None:
        """Quiet hours should block dispatch when current time is within range.

        Note: This test may not block if the current time isn't within the
        configured quiet hours. We test with a 00:00-23:59 range for certainty.
        """
        sub = {
            "telegram_chat_id": 111,
            "markets": ["stock"],
            "min_confidence": 60,
            "signal_types": ["STRONG_BUY"],
            "quiet_hours": {"start": "00:00", "end": "23:59"},
            "is_active": True,
        }
        dispatcher = AlertDispatcher(mock_send)
        sent = await dispatcher.dispatch_signal(stock_signal, [sub])
        assert sent == 0
