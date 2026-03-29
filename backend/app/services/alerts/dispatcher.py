"""Alert dispatcher — routes signals and briefs to Telegram subscribers.

Checks each subscriber's alert config (markets, min confidence, signal types,
quiet hours) before dispatching. Enforces a daily alert budget per subscriber.
Uses Redis for daily count persistence across Celery task restarts.
"""

import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import redis

from app.config import get_settings
from app.services.alerts.formatter import format_signal_alert

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")

# Maximum signal alerts per subscriber per day (broadcasts like briefs are exempt)
DAILY_ALERT_BUDGET = 10

# Redis key prefix for daily alert counts (expire at midnight IST)
_DAILY_COUNT_PREFIX = "alert_daily:"


def _get_daily_count_key(chat_id: int) -> str:
    """Get the Redis key for today's alert count for a chat_id."""
    today = datetime.now(IST).strftime("%Y%m%d")
    return f"{_DAILY_COUNT_PREFIX}{today}:{chat_id}"


class AlertDispatcher:
    """Route signal alerts to eligible Telegram subscribers.

    Args:
        bot_send_fn: Async function(chat_id, text) to send a Telegram message.
        daily_counts: Optional dict mapping chat_id → alerts sent today.
                      Kept for backward compatibility. Redis is preferred.
    """

    def __init__(self, bot_send_fn: Any, daily_counts: dict[int, int] | None = None) -> None:
        self.send = bot_send_fn
        self._daily_counts: dict[int, int] = daily_counts if daily_counts is not None else {}
        self._redis: redis.Redis | None = None
        try:
            settings = get_settings()
            if settings.redis_url:
                self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        except Exception:
            logger.debug("Redis unavailable for alert dispatcher, using in-memory counts")

    async def dispatch_signal(
        self, signal: dict, subscribers: list[dict]
    ) -> int:
        """Send a signal alert to all eligible subscribers.

        Signals are ranked by confidence and dispatched respecting the
        daily budget (DAILY_ALERT_BUDGET per subscriber). Broadcasts
        (morning brief, evening wrap, weekly digest) are NOT counted.

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

            chat_id = sub["telegram_chat_id"]
            # Check daily budget via Redis (with in-memory fallback)
            current_count = self._get_daily_count(chat_id)
            if current_count >= DAILY_ALERT_BUDGET:
                logger.debug(
                    "Daily alert budget exhausted for chat_id=%s (%d/%d)",
                    chat_id, current_count, DAILY_ALERT_BUDGET,
                )
                continue

            try:
                await self.send(chat_id, message)
                self._increment_daily_count(chat_id)
                sent += 1
            except Exception:
                logger.exception(
                    "Failed to send signal to chat_id=%s", chat_id
                )

        logger.info(
            "Dispatched signal %s to %d/%d subscribers",
            signal.get("symbol"), sent, len(subscribers),
        )
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
        allowed_types = config.get(
            "signal_types", ["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"]
        )
        return signal.get("signal_type") in allowed_types

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

    def _get_daily_count(self, chat_id: int) -> int:
        """Get today's alert count for a chat_id. Uses Redis with in-memory fallback."""
        if self._redis:
            try:
                key = _get_daily_count_key(chat_id)
                val = self._redis.get(key)
                return int(val) if val else 0
            except (redis.ConnectionError, redis.TimeoutError, OSError):
                pass
        return self._daily_counts.get(chat_id, 0)

    def _increment_daily_count(self, chat_id: int) -> None:
        """Increment today's alert count. Uses Redis with in-memory fallback."""
        if self._redis:
            try:
                key = _get_daily_count_key(chat_id)
                self._redis.incr(key)
                # Expire at end of day (max 24h TTL)
                self._redis.expire(key, 86400)
                return
            except (redis.ConnectionError, redis.TimeoutError, OSError):
                pass
        self._daily_counts[chat_id] = self._daily_counts.get(chat_id, 0) + 1
