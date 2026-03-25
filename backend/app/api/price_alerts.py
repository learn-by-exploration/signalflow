"""Price alert endpoints — create, list, delete."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_user
from app.database import get_db
from app.models.price_alert import PriceAlert
from app.schemas.p3 import PriceAlertCreate, PriceAlertData

router = APIRouter(prefix="/alerts/price", tags=["price-alerts"])


@router.get("", response_model=dict)
async def list_price_alerts(
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List active price alerts for the authenticated user."""
    result = await db.execute(
        select(PriceAlert)
        .where(PriceAlert.telegram_chat_id == user.telegram_chat_id)
        .where(PriceAlert.is_active.is_(True))
        .order_by(PriceAlert.created_at.desc())
    )
    alerts = result.scalars().all()
    return {"data": [PriceAlertData.model_validate(a) for a in alerts]}


@router.post("", response_model=dict, status_code=201)
async def create_price_alert(
    payload: PriceAlertCreate,
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new price alert for the authenticated user."""
    if payload.condition not in ("above", "below"):
        raise HTTPException(status_code=400, detail="condition must be 'above' or 'below'")

    alert = PriceAlert(
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
async def delete_price_alert(
    alert_id: UUID,
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Deactivate a price alert (must belong to user)."""
    result = await db.execute(select(PriceAlert).where(PriceAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Price alert not found")

    # Ownership check
    if alert.telegram_chat_id != user.telegram_chat_id:
        raise HTTPException(status_code=403, detail="Not your price alert")

    alert.is_active = False
    await db.flush()
    return {"data": "deleted"}
