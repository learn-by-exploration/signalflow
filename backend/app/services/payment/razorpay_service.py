"""Razorpay payment integration service.

Handles subscription creation, webhook processing, and tier management.
"""

import hashlib
import hmac
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import razorpay
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.subscription import Subscription

logger = logging.getLogger(__name__)

# Plan prices in paise (₹1 = 100 paise)
PLAN_PRICES = {
    "monthly": 49900,   # ₹499/mo (GST inclusive)
    "annual": 499900,   # ₹4,999/yr (2 months free)
    "trial": 0,         # Free trial
}


def _get_razorpay_client() -> razorpay.Client:
    """Create and return a Razorpay client instance."""
    settings = get_settings()
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


def _get_plan_id(plan: str) -> str:
    """Get the Razorpay Plan ID for a given plan type."""
    settings = get_settings()
    if plan == "monthly":
        return settings.razorpay_monthly_plan_id
    elif plan == "annual":
        return settings.razorpay_annual_plan_id
    raise ValueError(f"No Razorpay plan ID for: {plan}")


async def create_razorpay_subscription(plan: str) -> dict[str, Any]:
    """Create a subscription on Razorpay and return the subscription details.

    Args:
        plan: "monthly" or "annual".

    Returns:
        Razorpay subscription entity dict with 'id', 'status', etc.

    Raises:
        ValueError: If plan ID is not configured.
        razorpay.errors.BadRequestError: If Razorpay API rejects the request.
    """
    plan_id = _get_plan_id(plan)
    if not plan_id:
        raise ValueError(f"Razorpay plan ID not configured for '{plan}'. "
                         f"Set RAZORPAY_{'MONTHLY' if plan == 'monthly' else 'ANNUAL'}_PLAN_ID.")

    client = _get_razorpay_client()
    rz_sub = client.subscription.create({
        "plan_id": plan_id,
        "total_count": 12 if plan == "monthly" else 1,
        "quantity": 1,
    })
    logger.info("Created Razorpay subscription %s for plan %s", rz_sub.get("id"), plan)
    return rz_sub


def verify_webhook_signature(
    body: bytes,
    signature: str,
    webhook_secret: str,
) -> bool:
    """Verify Razorpay webhook signature (HMAC-SHA256).

    Args:
        body: Raw request body bytes.
        signature: X-Razorpay-Signature header value.
        webhook_secret: Razorpay webhook secret from config.

    Returns:
        True if signature is valid.
    """
    expected = hmac.new(
        webhook_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def create_subscription(
    db: AsyncSession,
    user_id: str,
    plan: str,
) -> Subscription:
    """Create a subscription record for a user.

    Args:
        db: Async database session.
        user_id: UUID of the user.
        plan: "monthly", "annual", or "trial".

    Returns:
        Created Subscription object.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)

    if plan == "trial":
        period_end = now + timedelta(days=settings.pro_trial_days)
        trial_end = period_end
        status = "active"  # Trials are active immediately
    elif plan == "monthly":
        period_end = now + timedelta(days=30)
        trial_end = None
        status = "pending"  # Pending until Razorpay confirms payment
    elif plan == "annual":
        period_end = now + timedelta(days=365)
        trial_end = None
        status = "pending"  # Pending until Razorpay confirms payment
    else:
        raise ValueError(f"Unknown plan: {plan}")

    sub = Subscription(
        user_id=user_id,
        plan=plan,
        status=status,
        amount_paise=PLAN_PRICES.get(plan, 0),
        current_period_start=now,
        current_period_end=period_end,
        trial_end=trial_end,
    )
    db.add(sub)
    await db.flush()

    logger.info("Created %s subscription for user %s", plan, user_id)
    return sub


async def get_active_subscription(
    db: AsyncSession,
    user_id: str,
) -> Subscription | None:
    """Get the user's active subscription, if any.

    Args:
        db: Async database session.
        user_id: UUID of the user.

    Returns:
        Active Subscription or None.
    """
    stmt = (
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .where(Subscription.status.in_(["active", "past_due"]))
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def handle_payment_success(
    db: AsyncSession,
    razorpay_subscription_id: str,
    period_end: datetime,
) -> None:
    """Handle successful payment — activate subscription and upgrade user tier.

    This is the ONLY place where a user's tier gets upgraded to 'pro'
    for paid plans. The subscribe endpoint creates a 'pending' subscription;
    this webhook handler confirms payment and activates it.

    Args:
        db: Async database session.
        razorpay_subscription_id: Razorpay subscription ID.
        period_end: New period end date.
    """
    from app.models.user import User

    # 1. Activate the subscription
    stmt = (
        update(Subscription)
        .where(Subscription.razorpay_subscription_id == razorpay_subscription_id)
        .values(
            status="active",
            current_period_end=period_end,
            updated_at=datetime.now(timezone.utc),
        )
    )
    await db.execute(stmt)

    # 2. Find the subscription to get user_id
    from sqlalchemy import select
    sub_stmt = (
        select(Subscription)
        .where(Subscription.razorpay_subscription_id == razorpay_subscription_id)
    )
    result = await db.execute(sub_stmt)
    sub = result.scalar_one_or_none()

    # 3. Upgrade user tier to 'pro'
    if sub:
        await db.execute(
            update(User)
            .where(User.id == sub.user_id)
            .values(tier="pro")
        )
        logger.info("Payment success — upgraded user %s to pro (sub %s)", sub.user_id, razorpay_subscription_id)
    else:
        logger.warning("Payment success but subscription %s not found", razorpay_subscription_id)


async def handle_payment_failed(
    db: AsyncSession,
    razorpay_subscription_id: str,
) -> None:
    """Handle failed payment — set grace period.

    Args:
        db: Async database session.
        razorpay_subscription_id: Razorpay subscription ID.
    """
    settings = get_settings()
    grace_end = datetime.now(timezone.utc) + timedelta(days=settings.payment_grace_days)

    stmt = (
        update(Subscription)
        .where(Subscription.razorpay_subscription_id == razorpay_subscription_id)
        .values(
            status="past_due",
            current_period_end=grace_end,
            updated_at=datetime.now(timezone.utc),
        )
    )
    await db.execute(stmt)
    logger.warning("Payment failed for subscription %s, grace until %s", razorpay_subscription_id, grace_end)


async def handle_subscription_cancelled(
    db: AsyncSession,
    razorpay_subscription_id: str,
) -> None:
    """Handle subscription cancellation.

    Args:
        db: Async database session.
        razorpay_subscription_id: Razorpay subscription ID.
    """
    stmt = (
        update(Subscription)
        .where(Subscription.razorpay_subscription_id == razorpay_subscription_id)
        .values(
            status="cancelled",
            cancelled_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )
    await db.execute(stmt)
    logger.info("Subscription cancelled: %s", razorpay_subscription_id)


async def downgrade_expired_subscriptions(db: AsyncSession) -> int:
    """Downgrade users whose subscriptions have expired past grace period.

    Called periodically by a Celery task.

    Returns:
        Number of users downgraded.
    """
    now = datetime.now(timezone.utc)
    # Find subscriptions that are past_due and past grace period
    from app.models.user import User

    stmt = (
        select(Subscription)
        .where(Subscription.status.in_(["active", "past_due"]))
        .where(Subscription.current_period_end < now)
    )
    result = await db.execute(stmt)
    expired = result.scalars().all()

    count = 0
    for sub in expired:
        sub.status = "expired"
        sub.updated_at = now
        # Downgrade user tier
        await db.execute(
            update(User)
            .where(User.id == sub.user_id)
            .values(tier="free")
        )
        count += 1

    if count > 0:
        logger.info("Downgraded %d expired subscriptions", count)

    return count
