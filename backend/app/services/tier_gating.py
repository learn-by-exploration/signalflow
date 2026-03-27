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
