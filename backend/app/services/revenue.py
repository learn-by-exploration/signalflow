"""Revenue tracking and admin metrics.

Provides MRR calculation, subscription metrics, and
re-engagement logic for free users.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Plan prices in INR paise
PLAN_PRICES_INR = {
    "monthly": 49900,  # ₹499/month
    "annual": 499900,  # ₹4999/year (~₹417/month)
    "trial": 0,
}


async def get_revenue_metrics(db: AsyncSession) -> dict[str, Any]:
    """Calculate revenue metrics from subscription data.

    Returns:
        Dict with MRR, active/churned/trial counts, etc.
    """
    from app.models.subscription import Subscription

    now = datetime.now(timezone.utc)

    # Count by status
    status_counts = {}
    for status in ["active", "cancelled", "expired", "past_due"]:
        result = await db.execute(
            select(func.count()).select_from(Subscription).where(Subscription.status == status)
        )
        status_counts[status] = result.scalar() or 0

    # Trial count
    trial_result = await db.execute(
        select(func.count())
        .select_from(Subscription)
        .where(Subscription.plan == "trial", Subscription.status == "active")
    )
    trial_count = trial_result.scalar() or 0

    # MRR calculation (active subscriptions only)
    active_subs = await db.execute(select(Subscription).where(Subscription.status == "active"))
    subs = active_subs.scalars().all()

    mrr_paise = 0
    for sub in subs:
        if sub.plan == "monthly":
            mrr_paise += PLAN_PRICES_INR["monthly"]
        elif sub.plan == "annual":
            mrr_paise += PLAN_PRICES_INR["annual"] // 12  # Monthly equivalent
        # Trial contributes 0

    mrr_inr = mrr_paise / 100

    # Churn: subscriptions cancelled in last 30 days
    thirty_days_ago = now - timedelta(days=30)
    churn_result = await db.execute(
        select(func.count())
        .select_from(Subscription)
        .where(
            Subscription.status == "cancelled",
            Subscription.cancelled_at >= thirty_days_ago,
        )
    )
    recent_churn = churn_result.scalar() or 0

    total_active = status_counts.get("active", 0)
    churn_rate = recent_churn / max(total_active + recent_churn, 1)

    return {
        "mrr_inr": round(mrr_inr, 2),
        "mrr_paise": mrr_paise,
        "active_subscriptions": total_active,
        "trial_count": trial_count,
        "past_due": status_counts.get("past_due", 0),
        "cancelled_last_30d": recent_churn,
        "expired": status_counts.get("expired", 0),
        "churn_rate_30d": round(churn_rate, 4),
        "calculated_at": now.isoformat(),
    }


async def get_free_tier_weekly_digest_data(
    db: AsyncSession,
) -> dict[str, Any]:
    """Get data for the free-tier weekly nudge message.

    Returns signal stats from the past week for the digest.
    """
    from app.models.signal import Signal
    from app.models.signal_history import SignalHistory

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # Signals generated this week
    signal_count_result = await db.execute(
        select(func.count()).select_from(Signal).where(Signal.created_at >= week_ago)
    )
    signals_this_week = signal_count_result.scalar() or 0

    # Resolved signals this week
    resolved = await db.execute(
        select(SignalHistory)
        .where(SignalHistory.created_at >= week_ago)
        .where(SignalHistory.outcome.in_(["hit_target", "hit_stop"]))
    )
    resolved_signals = resolved.scalars().all()

    hits = sum(1 for s in resolved_signals if s.outcome == "hit_target")
    total_resolved = len(resolved_signals)
    win_rate = hits / total_resolved if total_resolved > 0 else 0

    # Best signal this week (highest return)
    best_signal = None
    if resolved_signals:
        best = max(resolved_signals, key=lambda s: s.return_pct or 0)
        if best.return_pct and best.return_pct > 0:
            # Get signal details
            sig_result = await db.execute(select(Signal).where(Signal.id == best.signal_id))
            sig = sig_result.scalars().first()
            if sig:
                best_signal = {
                    "symbol": sig.symbol,
                    "signal_type": sig.signal_type,
                    "return_pct": float(best.return_pct),
                }

    return {
        "signals_this_week": signals_this_week,
        "resolved_this_week": total_resolved,
        "hits": hits,
        "win_rate": round(win_rate * 100, 1),
        "best_signal": best_signal,
    }


def format_free_tier_digest(data: dict[str, Any]) -> str:
    """Format the free-tier weekly digest Telegram message.

    Args:
        data: Output from get_free_tier_weekly_digest_data.

    Returns:
        Formatted Telegram message string.
    """
    msg = "📊 *Your Weekly SignalFlow Digest*\n\n"
    msg += f"This week: {data['signals_this_week']} signals generated\n"

    if data["resolved_this_week"] > 0:
        msg += f"Results: {data['hits']}/{data['resolved_this_week']} hit target "
        msg += f"({data['win_rate']}% win rate)\n\n"
    else:
        msg += "Results: Awaiting resolution\n\n"

    if data.get("best_signal"):
        best = data["best_signal"]
        msg += f"🏆 Best signal: {best['symbol']} ({best['signal_type']}) "
        msg += f"+{best['return_pct']:.1f}%\n\n"

    msg += "🔓 *Upgrade to Pro* for full AI reasoning, "
    msg += "targets, and real-time alerts.\n"
    msg += "/upgrade to see plans"

    return msg


async def get_inactive_users(
    db: AsyncSession,
    days_inactive: int = 7,
) -> list[dict[str, Any]]:
    """Find users who haven't been active for N days.

    Args:
        db: Database session.
        days_inactive: Days of inactivity threshold.

    Returns:
        List of user dicts with chat_id for re-engagement.
    """
    from app.models.user import User

    cutoff = datetime.now(timezone.utc) - timedelta(days=days_inactive)

    result = await db.execute(
        select(User).where(
            User.last_active_at < cutoff,
            User.telegram_chat_id.isnot(None),
        )
    )
    users = result.scalars().all()

    return [
        {
            "user_id": str(u.id),
            "telegram_chat_id": u.telegram_chat_id,
            "last_active": u.last_active_at.isoformat() if u.last_active_at else None,
        }
        for u in users
    ]
