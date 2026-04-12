"""Free-tier signal gating.

Implements newspaper-paywall model: free users see signal headline, type,
and direction but AI reasoning, targets, stop-loss, and technical breakdown
are locked after 3 full-detail views per week.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Redis key helpers
_VIEWS_KEY = "tier:free_views:{user_id}"
_VIEWS_TTL_SECONDS = 7 * 24 * 60 * 60  # 1 week

# Free tier limits
FREE_DETAIL_VIEWS_PER_WEEK = 3
FREE_HISTORY_DAYS = 7
FREE_PRICE_ALERTS_PER_DAY = 3
FREE_PORTFOLIO_TRADES_MAX = 10

# Fields to hide from free users who've exhausted their detail views
LOCKED_FIELDS = {
    "ai_reasoning",
    "target_price",
    "stop_loss",
    "technical_data",
    "sentiment_data",
}


async def consume_free_detail_view(user_id: str, redis_client) -> bool:
    """Attempt to consume one free detail view for a user.

    Args:
        user_id: The user's UUID string.
        redis_client: An active aioredis client.

    Returns:
        True if the view was allowed (quota not exhausted), False if locked.
    """
    key = _VIEWS_KEY.format(user_id=user_id)
    count = await redis_client.incr(key)
    if count == 1:
        # First increment — set TTL for 1 week
        await redis_client.expire(key, _VIEWS_TTL_SECONDS)
    return count <= FREE_DETAIL_VIEWS_PER_WEEK


async def get_free_views_remaining(user_id: str, redis_client) -> int:
    """Return how many free detail views remain this week for a user.

    Args:
        user_id: The user's UUID string.
        redis_client: An active aioredis client.

    Returns:
        Number of views remaining (0 means locked).
    """
    key = _VIEWS_KEY.format(user_id=user_id)
    raw = await redis_client.get(key)
    used = int(raw) if raw else 0
    return max(0, FREE_DETAIL_VIEWS_PER_WEEK - used)


def redact_signal_for_free_tier(signal_data: dict) -> dict:
    """Redact premium fields from a signal for free-tier users.

    Args:
        signal_data: Full signal response dict.

    Returns:
        Signal dict with locked fields replaced by placeholder text.
    """
    redacted = dict(signal_data)
    redacted["ai_reasoning"] = "🔒 Upgrade to Pro to see AI reasoning"
    redacted["target_price"] = None
    redacted["stop_loss"] = None
    redacted["technical_data"] = {"locked": True}
    redacted["sentiment_data"] = {"locked": True}
    redacted["is_locked"] = True
    return redacted
