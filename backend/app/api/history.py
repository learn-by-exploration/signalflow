"""Signal history and stats endpoints."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.signal import Signal
from app.models.signal_history import SignalHistory
from app.schemas.signal import (
    MetaResponse,
    SignalHistoryItem,
    SignalHistoryResponse,
    SignalStatsResponse,
    SignalSummary,
    SymbolTrackRecord,
)

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/history", response_model=SignalHistoryResponse)
async def list_signal_history(
    outcome: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> SignalHistoryResponse:
    """List past signal outcomes with embedded signal details."""
    base_query = select(SignalHistory)
    if outcome:
        base_query = base_query.where(SignalHistory.outcome == outcome)

    # Total count for pagination
    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar() or 0

    # Fetch with joined signal data
    query = (
        base_query.options(joinedload(SignalHistory.signal_rel))
        .order_by(SignalHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    entries = result.unique().scalars().all()

    items = []
    for e in entries:
        item = SignalHistoryItem.model_validate(e)
        if e.signal_rel:
            item.signal = SignalSummary.model_validate(e.signal_rel)
        items.append(item)

    return SignalHistoryResponse(
        data=items,
        meta=MetaResponse(timestamp=datetime.now(timezone.utc), count=len(entries), total=total),
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


@router.get("/{symbol}/track-record", response_model=SymbolTrackRecord)
async def get_symbol_track_record(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> SymbolTrackRecord:
    """Get per-symbol signal performance over the last 30 days."""
    since = datetime.now(timezone.utc) - timedelta(days=30)

    stmt = (
        select(
            func.count(SignalHistory.id).label("total"),
            func.count(SignalHistory.id).filter(SignalHistory.outcome == "hit_target").label("hit_target"),
            func.count(SignalHistory.id).filter(SignalHistory.outcome == "hit_stop").label("hit_stop"),
            func.count(SignalHistory.id).filter(SignalHistory.outcome == "expired").label("expired"),
            func.avg(SignalHistory.return_pct).label("avg_return"),
        )
        .join(Signal, Signal.id == SignalHistory.signal_id)
        .where(Signal.symbol == symbol)
        .where(SignalHistory.created_at >= since)
    )
    result = await db.execute(stmt)
    row = result.one()

    total = row.total or 0
    ht = row.hit_target or 0
    hs = row.hit_stop or 0
    resolved = ht + hs
    win_rate = (ht / resolved * 100) if resolved > 0 else 0.0

    return SymbolTrackRecord(
        symbol=symbol,
        total_signals_30d=total,
        hit_target=ht,
        hit_stop=hs,
        expired=row.expired or 0,
        win_rate=round(win_rate, 1),
        avg_return_pct=round(float(row.avg_return or 0), 2),
    )
