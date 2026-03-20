"""Signal endpoints — list and detail."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.signal import Signal
from app.schemas.signal import MetaResponse, SignalListResponse, SignalResponse

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("", response_model=SignalListResponse)
async def list_signals(
    market: str | None = None,
    signal_type: str | None = None,
    min_confidence: int = Query(default=0, ge=0, le=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> SignalListResponse:
    """List active trading signals with optional filters."""
    query = select(Signal).where(Signal.is_active.is_(True))

    if market:
        query = query.where(Signal.market_type == market)
    if signal_type:
        query = query.where(Signal.signal_type == signal_type)
    if min_confidence > 0:
        query = query.where(Signal.confidence >= min_confidence)

    query = query.order_by(Signal.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    signals = result.scalars().all()

    return SignalListResponse(
        data=[SignalResponse.model_validate(s) for s in signals],
        meta=MetaResponse(timestamp=datetime.now(timezone.utc), count=len(signals)),
    )


@router.get("/{signal_id}", response_model=dict)
async def get_signal(
    signal_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a single signal by ID."""
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return {"data": SignalResponse.model_validate(signal)}
