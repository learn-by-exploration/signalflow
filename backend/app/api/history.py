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
    WeeklyTrendItem,
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


@router.get("/stats/trend", response_model=list[WeeklyTrendItem])
async def get_accuracy_trend(
    weeks: int = Query(default=8, ge=1, le=52),
    db: AsyncSession = Depends(get_db),
) -> list[WeeklyTrendItem]:
    """Get weekly win rate trend for the last N weeks."""
    since = datetime.now(timezone.utc) - timedelta(weeks=weeks)

    stmt = (
        select(
            func.date_trunc("week", SignalHistory.resolved_at).label("week_start"),
            func.count(SignalHistory.id).label("total"),
            func.count(SignalHistory.id)
            .filter(SignalHistory.outcome == "hit_target")
            .label("hit_target"),
        )
        .where(SignalHistory.resolved_at.isnot(None))
        .where(SignalHistory.resolved_at >= since)
        .group_by(func.date_trunc("week", SignalHistory.resolved_at))
        .order_by(func.date_trunc("week", SignalHistory.resolved_at))
    )
    result = await db.execute(stmt)
    rows = result.all()

    items: list[WeeklyTrendItem] = []
    for row in rows:
        total = row.total or 0
        ht = row.hit_target or 0
        wr = (ht / total * 100) if total > 0 else 0.0
        week_dt = row.week_start
        items.append(
            WeeklyTrendItem(
                week=week_dt.strftime("%G-W%V"),
                start_date=week_dt.strftime("%Y-%m-%d"),
                total=total,
                hit_target=ht,
                win_rate=round(wr, 1),
            )
        )

    return items


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


@router.get("/performance", response_model=dict)
async def get_performance_by_market(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get signal win rates broken down by market type and signal type.

    Returns performance metrics for each market (stock/crypto/forex) and
    each signal type (STRONG_BUY/BUY/SELL/STRONG_SELL).
    """
    since = datetime.now(timezone.utc) - timedelta(days=90)

    stmt = (
        select(
            Signal.market_type,
            Signal.signal_type,
            func.count(SignalHistory.id).label("total"),
            func.count(SignalHistory.id).filter(
                SignalHistory.outcome == "hit_target"
            ).label("hit_target"),
            func.count(SignalHistory.id).filter(
                SignalHistory.outcome == "hit_stop"
            ).label("hit_stop"),
            func.avg(SignalHistory.return_pct).label("avg_return"),
        )
        .join(Signal, Signal.id == SignalHistory.signal_id)
        .where(SignalHistory.outcome.in_(["hit_target", "hit_stop"]))
        .where(SignalHistory.created_at >= since)
        .group_by(Signal.market_type, Signal.signal_type)
    )

    result = await db.execute(stmt)
    rows = result.all()

    performance: dict = {}
    for row in rows:
        market = row.market_type
        if market not in performance:
            performance[market] = {"total": 0, "hit_target": 0, "hit_stop": 0, "by_signal_type": {}}
        ht = row.hit_target or 0
        hs = row.hit_stop or 0
        total = ht + hs
        performance[market]["total"] += total
        performance[market]["hit_target"] += ht
        performance[market]["hit_stop"] += hs
        performance[market]["by_signal_type"][row.signal_type] = {
            "total": total,
            "hit_target": ht,
            "hit_stop": hs,
            "win_rate": round(ht / total * 100, 1) if total > 0 else 0.0,
            "avg_return": round(float(row.avg_return or 0), 2),
        }

    # Calculate overall win rates per market
    for market in performance:
        m = performance[market]
        resolved = m["hit_target"] + m["hit_stop"]
        m["win_rate"] = round(m["hit_target"] / resolved * 100, 1) if resolved > 0 else 0.0

    return {"data": performance}


@router.get("/streak-check", response_model=dict)
async def check_streak(
    market_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Check for losing streak (3+ consecutive stop-losses).

    Returns streak status with recommendation if active.
    """
    from app.services.signal_gen.streak_protection import check_losing_streak

    result = await check_losing_streak(db, market_type=market_type)
    return {"data": result}


@router.get("/calibration", response_model=dict)
async def get_calibration_curve(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the confidence-to-win-rate calibration curve.

    Maps confidence bins to actual historical win probabilities.
    Requires 90+ days of resolved signal data for reliability.
    """
    from app.services.signal_gen.calibration import (
        apply_isotonic_smoothing,
        compute_calibration_curve,
    )

    # Fetch all resolved signals with confidence and outcome
    query = (
        select(SignalHistory, Signal.confidence)
        .join(Signal, SignalHistory.signal_id == Signal.id)
        .where(SignalHistory.outcome.in_(["hit_target", "hit_stop"]))
    )
    result = await db.execute(query)
    rows = result.all()

    resolved_signals = [
        {"confidence": row.confidence, "outcome": row.SignalHistory.outcome}
        for row in rows
    ]

    calibration = compute_calibration_curve(resolved_signals)

    # Apply isotonic smoothing if we have enough data
    if calibration["is_calibrated"]:
        calibration["bins"] = apply_isotonic_smoothing(calibration["bins"])

    return {"data": calibration}
