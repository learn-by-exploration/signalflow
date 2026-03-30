"""Price alert endpoints — create, list, delete."""

import re
from uuid import UUID as PyUUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_user
from app.database import get_db
from app.models.price_alert import PriceAlert
from app.rate_limit import limiter
from app.schemas.p3 import PriceAlertCreate, PriceAlertData

router = APIRouter(prefix="/alerts/price", tags=["price-alerts"])

_SYMBOL_RE = re.compile(r"^[A-Z0-9./=_-]{1,20}$")

# Price alert limits per tier
ALERT_LIMITS = {"free": 3, "pro": 50, "admin": 500}


def _user_alert_filter(user: AuthContext):
    """Build a filter for price alerts belonging to the authenticated user."""
    from uuid import UUID as PyUUID
    conditions = []
    if user.user_id:
        uid = PyUUID(user.user_id) if isinstance(user.user_id, str) else user.user_id
        conditions.append(PriceAlert.user_id == uid)
    if user.telegram_chat_id:
        conditions.append(PriceAlert.telegram_chat_id == user.telegram_chat_id)
    if not conditions:
        return PriceAlert.id == None  # noqa: E711
    return or_(*conditions)


@router.get("", response_model=dict)
async def list_price_alerts(
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List active price alerts for the authenticated user."""
    result = await db.execute(
        select(PriceAlert)
        .where(_user_alert_filter(user))
        .where(PriceAlert.is_active.is_(True))
        .order_by(PriceAlert.created_at.desc())
    )
    alerts = result.scalars().all()
    return {"data": [PriceAlertData.model_validate(a) for a in alerts]}


@router.post("", response_model=dict, status_code=201)
@limiter.limit("10/minute")
async def create_price_alert(
    request: Request,
    payload: PriceAlertCreate,
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new price alert for the authenticated user."""
    if payload.condition not in ("above", "below"):
        raise HTTPException(status_code=400, detail="condition must be 'above' or 'below'")

    # Validate symbol format
    safe_symbol = payload.symbol.upper().strip()
    if not _SYMBOL_RE.match(safe_symbol):
        raise HTTPException(status_code=400, detail="Invalid symbol format")

    # Enforce tier-based alert limit
    limit = ALERT_LIMITS.get(user.tier, ALERT_LIMITS["free"])
    count_result = await db.execute(
        select(func.count(PriceAlert.id))
        .where(_user_alert_filter(user))
        .where(PriceAlert.is_active.is_(True))
    )
    current_count = count_result.scalar() or 0
    if current_count >= limit:
        raise HTTPException(
            status_code=402,
            detail=f"Price alert limit reached ({limit} for {user.tier} tier)",
        )

    alert = PriceAlert(
        user_id=PyUUID(user.user_id) if isinstance(user.user_id, str) and user.user_id else user.user_id,
        telegram_chat_id=user.telegram_chat_id,
        symbol=payload.symbol.upper().strip(),
        market_type=payload.market_type,
        condition=payload.condition,
        threshold=payload.threshold,
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)
    return {"data": PriceAlertData.model_validate(alert)}


@router.delete("/{alert_id}", response_model=dict)
@limiter.limit("10/minute")
async def delete_price_alert(
    request: Request,
    alert_id: PyUUID,
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Deactivate a price alert (must belong to user)."""
    result = await db.execute(select(PriceAlert).where(PriceAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Price alert not found")

    # Ownership check
    is_owner = False
    if user.user_id and alert.user_id and str(alert.user_id) == str(user.user_id):
        is_owner = True
    if user.telegram_chat_id and alert.telegram_chat_id == user.telegram_chat_id:
        is_owner = True
    if not is_owner:
        raise HTTPException(status_code=403, detail="Not your price alert")

    alert.is_active = False
    await db.flush()
    return {"data": "deleted"}
