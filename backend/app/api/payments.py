"""Payment and subscription endpoints.

Handles Razorpay checkout, webhook verification, and subscription management.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, require_auth
from app.config import get_settings
from app.database import get_db
from app.rate_limit import limiter
from app.services.payment.razorpay_service import (
    create_subscription,
    get_active_subscription,
    handle_payment_failed,
    handle_payment_success,
    handle_subscription_cancelled,
    verify_webhook_signature,
    PLAN_PRICES,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


class StartTrialRequest(BaseModel):
    """Request to start a free Pro trial."""
    pass


class SubscribeRequest(BaseModel):
    """Request to create a paid subscription."""
    plan: str = Field(..., pattern="^(monthly|annual)$")


class SubscriptionResponse(BaseModel):
    """Subscription status response."""
    id: str
    plan: str
    status: str
    amount_paise: int
    current_period_end: datetime | None
    trial_end: datetime | None


@router.get("/subscription", response_model=dict)
async def get_subscription(
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get current user's subscription status."""
    sub = await get_active_subscription(db, auth.user_id)
    if not sub:
        return {"data": None, "meta": {"tier": auth.tier}}

    return {
        "data": {
            "id": sub.id,
            "plan": sub.plan,
            "status": sub.status,
            "amount_paise": sub.amount_paise,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
            "trial_end": sub.trial_end.isoformat() if sub.trial_end else None,
        },
        "meta": {"tier": auth.tier},
    }


@router.post("/trial", response_model=dict)
@limiter.limit("3/day")
async def start_trial(
    request: Request,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Start a 7-day free Pro trial (no card required).

    Can only be used once per user.
    """
    # Check if user already had a trial or active subscription
    existing = await get_active_subscription(db, auth.user_id)
    if existing:
        raise HTTPException(400, "You already have an active subscription or trial")

    # Check for any past trial
    from sqlalchemy import select
    from app.models.subscription import Subscription
    past_trial = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == auth.user_id)
        .where(Subscription.plan == "trial")
        .limit(1)
    )
    if past_trial.scalar_one_or_none():
        raise HTTPException(400, "Free trial already used. Subscribe to Pro for full access.")

    sub = await create_subscription(db, auth.user_id, "trial")

    # Upgrade user tier
    from sqlalchemy import update
    from app.models.user import User
    await db.execute(
        update(User).where(User.id == auth.user_id).values(tier="pro")
    )
    await db.commit()

    return {
        "data": {
            "id": sub.id,
            "plan": "trial",
            "status": "active",
            "trial_end": sub.trial_end.isoformat() if sub.trial_end else None,
        },
        "message": "Pro trial started! You have 7 days of full access.",
    }


@router.post("/subscribe", response_model=dict)
@limiter.limit("5/hour")
async def create_paid_subscription(
    request: Request,
    body: SubscribeRequest,
    auth: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a Razorpay subscription checkout.

    Returns the subscription ID and checkout URL for the frontend.
    """
    settings = get_settings()

    if not settings.razorpay_key_id:
        raise HTTPException(503, "Payment system not configured")

    sub = await create_subscription(db, auth.user_id, body.plan)

    # Upgrade user tier immediately (verify via webhook later)
    from sqlalchemy import update
    from app.models.user import User
    await db.execute(
        update(User).where(User.id == auth.user_id).values(tier="pro")
    )
    await db.commit()

    return {
        "data": {
            "subscription_id": sub.id,
            "plan": body.plan,
            "amount_paise": PLAN_PRICES[body.plan],
            "razorpay_key_id": settings.razorpay_key_id,
        },
    }


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle Razorpay webhook events.

    Verifies webhook signature and processes payment events.
    """
    settings = get_settings()

    if not settings.razorpay_webhook_secret:
        raise HTTPException(503, "Webhook not configured")

    # Verify signature
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not verify_webhook_signature(body, signature, settings.razorpay_webhook_secret):
        logger.warning("Invalid Razorpay webhook signature")
        raise HTTPException(400, "Invalid signature")

    import json
    payload = json.loads(body)
    event = payload.get("event", "")

    logger.info("Razorpay webhook: %s", event)

    if event == "subscription.charged":
        # Payment successful
        sub_id = payload["payload"]["subscription"]["entity"]["id"]
        period_end_ts = payload["payload"]["subscription"]["entity"].get("current_end")
        if period_end_ts:
            period_end = datetime.fromtimestamp(period_end_ts, tz=timezone.utc)
        else:
            period_end = datetime.now(timezone.utc)
        await handle_payment_success(db, sub_id, period_end)

    elif event == "subscription.payment_failed":
        sub_id = payload["payload"]["subscription"]["entity"]["id"]
        await handle_payment_failed(db, sub_id)

    elif event in ("subscription.cancelled", "subscription.completed"):
        sub_id = payload["payload"]["subscription"]["entity"]["id"]
        await handle_subscription_cancelled(db, sub_id)

    await db.commit()
    return {"status": "ok"}


@router.get("/plans", response_model=dict)
async def list_plans() -> dict:
    """List available subscription plans."""
    settings = get_settings()
    return {
        "data": [
            {
                "plan": "trial",
                "name": "Free Trial",
                "price_display": "Free for 7 days",
                "amount_paise": 0,
                "duration_days": settings.pro_trial_days,
                "features": [
                    "Full AI reasoning on all signals",
                    "Target & stop-loss levels",
                    "Technical breakdown",
                    "Telegram alerts",
                ],
            },
            {
                "plan": "monthly",
                "name": "Pro Monthly",
                "price_display": "₹499/month",
                "amount_paise": PLAN_PRICES["monthly"],
                "duration_days": 30,
                "features": [
                    "Everything in Trial",
                    "Unlimited signal views",
                    "AI Q&A",
                    "Backtesting",
                    "Full history",
                ],
            },
            {
                "plan": "annual",
                "name": "Pro Annual",
                "price_display": "₹4,999/year (save ₹989)",
                "amount_paise": PLAN_PRICES["annual"],
                "duration_days": 365,
                "features": [
                    "Everything in Monthly",
                    "2 months free",
                    "Priority support",
                ],
            },
        ],
    }
