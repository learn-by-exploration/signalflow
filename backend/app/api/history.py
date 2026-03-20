"""Signal history endpoint."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.signal_history import SignalHistory
from app.schemas.signal import MetaResponse, SignalHistoryItem, SignalHistoryResponse

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/history", response_model=SignalHistoryResponse)
async def list_signal_history(
    outcome: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> SignalHistoryResponse:
    """List past signal outcomes."""
    query = select(SignalHistory)

    if outcome:
        query = query.where(SignalHistory.outcome == outcome)

    query = query.order_by(SignalHistory.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    entries = result.scalars().all()

    return SignalHistoryResponse(
        data=[SignalHistoryItem.model_validate(e) for e in entries],
        meta=MetaResponse(timestamp=datetime.now(timezone.utc), count=len(entries)),
    )
