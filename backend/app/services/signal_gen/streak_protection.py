"""Losing streak protection.

Detects when 3+ consecutive signals hit stop-loss and triggers
alerts with AI summary and position sizing recommendations.
"""

import logging
from typing import Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal
from app.models.signal_history import SignalHistory

logger = logging.getLogger(__name__)

# Number of consecutive stop-losses to trigger protection
STREAK_THRESHOLD = 3


async def check_losing_streak(
    db: AsyncSession,
    market_type: str | None = None,
) -> dict[str, Any]:
    """Check if there's an active losing streak.

    Args:
        db: Async database session.
        market_type: Optional filter by market type.

    Returns:
        Dict with 'is_streak', 'streak_length', 'symbols', 'suggestion'.
    """
    stmt = (
        select(
            SignalHistory.outcome,
            Signal.symbol,
            Signal.market_type,
            Signal.signal_type,
            Signal.confidence,
        )
        .join(Signal, SignalHistory.signal_id == Signal.id)
        .where(SignalHistory.outcome.in_(["hit_target", "hit_stop"]))
        .order_by(desc(SignalHistory.resolved_at))
        .limit(10)
    )

    if market_type:
        stmt = stmt.where(Signal.market_type == market_type)

    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return {"is_streak": False, "streak_length": 0, "symbols": [], "suggestion": None}

    # Count consecutive stop-losses from most recent
    streak_length = 0
    streak_symbols = []
    for row in rows:
        if row[0] == "hit_stop":
            streak_length += 1
            streak_symbols.append(row[1])
        else:
            break

    is_streak = streak_length >= STREAK_THRESHOLD

    suggestion = None
    if is_streak:
        suggestion = (
            f"⚠️ {streak_length} consecutive signals hit stop-loss "
            f"({', '.join(streak_symbols[:5])}). "
            "Consider reducing position sizes by 50% until the streak breaks. "
            "Market conditions may have shifted — review sector allocation."
        )
        logger.warning(
            "Losing streak detected: %d consecutive stops (%s)",
            streak_length, ", ".join(streak_symbols),
        )

    return {
        "is_streak": is_streak,
        "streak_length": streak_length,
        "symbols": streak_symbols,
        "suggestion": suggestion,
    }


def format_streak_alert(streak_data: dict[str, Any]) -> str:
    """Format a losing streak alert message for Telegram.

    Args:
        streak_data: Output from check_losing_streak().

    Returns:
        Formatted Telegram message string.
    """
    n = streak_data["streak_length"]
    symbols = ", ".join(streak_data["symbols"][:5])

    return (
        f"🔴 LOSING STREAK ALERT\n\n"
        f"📉 {n} consecutive signals hit stop-loss\n"
        f"📊 Affected: {symbols}\n\n"
        f"💡 Recommendation:\n"
        f"• Reduce position sizes by 50%\n"
        f"• Review market regime (trending vs ranging)\n"
        f"• Wait for 1 winning signal before resuming full size\n\n"
        f"⚠️ This is risk management, not a stop. "
        f"The system continues generating signals."
    )
