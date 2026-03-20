"""Alert dispatcher — routes signals and briefs to Telegram subscribers.

Checks each subscriber's alert config (markets, min confidence, signal types,
quiet hours) before dispatching.
"""

import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.services.alerts.formatter import format_signal_alert

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")


class AlertDispatcher:
    """Route signal alerts to eligible Telegram subscribers.

    Args:
        bot_send_fn: Async function(chat_id, text) to send a Telegram message.
    """

    def __init__(self, bot_send_fn: Any) -> None:
        self.send = bot_send_fn

    async def dispatch_signal(
        self, signal: dict, subscribers: list[dict]
    ) -> int:
        """Send a signal alert to all eligible subscribers.

        Args:
            signal: Signal dict with all fields.
            subscribers: List of alert_config dicts.

        Returns:
            Number of messages sent.
        """
        sent = 0
        message = format_signal_alert(signal)

        for sub in subscribers:
            if not sub.get("is_active", True):
                continue
            if not self._passes_filters(signal, sub):
                continue
            if self._in_quiet_hours(sub):
                continue

            try:
                await self.send(sub["telegram_chat_id"], message)
                sent += 1
            except Exception:
                logger.exception(
                    "Failed to send signal to chat_id=%s", sub["telegram_chat_id"]
                )

        logger.info("Dispatched signal %s to %d/%d subscribers", signal.get("symbol"), sent, len(subscribers))
        return sent

    async def dispatch_broadcast(self, text: str, subscribers: list[dict]) -> int:
        """Send a broadcast message (brief/wrap) to all active subscribers.

        Args:
            text: Pre-formatted message text.
            subscribers: List of alert_config dicts.

        Returns:
            Number of messages sent.
        """
        sent = 0
        for sub in subscribers:
            if not sub.get("is_active", True):
                continue
            try:
                await self.send(sub["telegram_chat_id"], text)
                sent += 1
            except Exception:
                logger.exception(
                    "Failed to broadcast to chat_id=%s", sub["telegram_chat_id"]
                )
        return sent

    @staticmethod
    def _passes_filters(signal: dict, config: dict) -> bool:
        """Check if a signal passes the subscriber's filter criteria."""
        # Market filter
        markets = config.get("markets", ["stock", "crypto", "forex"])
        if signal.get("market_type") not in markets:
            return False

        # Confidence filter
        min_conf = config.get("min_confidence", 60)
        if signal.get("confidence", 0) < min_conf:
            return False

        # Signal type filter
        allowed_types = config.get("signal_types", ["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"])
        if signal.get("signal_type") not in allowed_types:
            return False

        return True

    @staticmethod
    def _in_quiet_hours(config: dict) -> bool:
        """Check if current IST time falls within the subscriber's quiet hours."""
        quiet = config.get("quiet_hours")
        if not quiet:
            return False

        now = datetime.now(IST)
        current_mins = now.hour * 60 + now.minute

        start_parts = quiet["start"].split(":")
        end_parts = quiet["end"].split(":")
        start_mins = int(start_parts[0]) * 60 + int(start_parts[1])
        end_mins = int(end_parts[0]) * 60 + int(end_parts[1])

        if start_mins <= end_mins:
            return start_mins <= current_mins <= end_mins
        else:
            # Wraps midnight: e.g. 23:00 – 07:00
            return current_mins >= start_mins or current_mins <= end_mins
