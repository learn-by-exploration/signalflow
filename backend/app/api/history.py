"""Signal history and stats endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.signal_history import SignalHistory
from app.schemas.signal import (
    MetaResponse,
    SignalHistoryItem,
    SignalHistoryResponse,
    SignalStatsResponse,
)

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


@router.get("/stats", response_model=SignalStatsResponse)
async def get_signal_stats(
    db: AsyncSession = Depends(get_db),
) -> SignalStatsResponse:
    """Get aggregate signal performance statistics (win rate, avg return, etc.)."""
    result = await db.execute(
        select(
            func.count(SignalHistory.id).label("total"),
            func.count(SignalHistory.id).filter(SignalHistory.outcome == "hit_target").label("hit_target"),
            func.count(SignalHistory.id).filter(SignalHistory.outcome == "hit_stop").label("hit_stop"),
            func.count(SignalHistory.id).filter(SignalHistory.outcome == "expired").label("expired"),
            func.count(SignalHistory.id).filter(SignalHistory.outcome == "pending").label("pending"),
            func.avg(SignalHistory.return_pct).label("avg_return"),
            func.max(SignalHistory.resolved_at).label("last_resolved"),
        )
    )
    row = result.one()

    total = row.total or 0
    hit_target = row.hit_target or 0
    hit_stop = row.hit_stop or 0
    resolved = hit_target + hit_stop
    win_rate = (hit_target / resolved * 100) if resolved > 0 else 0.0

    return SignalStatsResponse(
        total_signals=total,
        hit_target=hit_target,
        hit_stop=hit_stop,
        expired=row.expired or 0,
        pending=row.pending or 0,
        win_rate=round(win_rate, 1),
        avg_return_pct=round(float(row.avg_return or 0), 2),
        last_updated=row.last_resolved,
    )
