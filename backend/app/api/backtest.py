"""Backtesting endpoints — kick off a run, check status/results."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, require_tier
from app.database import get_db
from app.models.backtest import BacktestRun
from app.rate_limit import limiter
from app.schemas.p3 import BacktestCreate, BacktestData

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("/run", response_model=dict, status_code=201)
@limiter.limit("3/hour")
async def start_backtest(
    request: Request,
    payload: BacktestCreate,
    auth: AuthContext = Depends(require_tier("pro")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Kick off a backtest run for a symbol.

    Creates a BacktestRun row with status='pending' and dispatches
    the backtest_runner Celery task.
    """
    # Enforce maximum backtest duration
    MAX_BACKTEST_DAYS = 365
    if payload.days > MAX_BACKTEST_DAYS:
        raise HTTPException(
            status_code=400,
            detail=f"Backtest duration cannot exceed {MAX_BACKTEST_DAYS} days",
        )
    if payload.days < 1:
        raise HTTPException(status_code=400, detail="Backtest duration must be at least 1 day")

    from app.tasks.backtest_tasks import run_backtest

    now = datetime.now(timezone.utc)
    backtest = BacktestRun(
        symbol=payload.symbol.upper().strip(),
        market_type=payload.market_type,
        start_date=now - timedelta(days=payload.days),
        end_date=now,
        status="pending",
    )
    db.add(backtest)
    await db.flush()
    await db.refresh(backtest)

    # Dispatch async Celery task
    run_backtest.delay(str(backtest.id), payload.days)

    return {"data": BacktestData.model_validate(backtest)}


@router.get("/{backtest_id}", response_model=dict)
async def get_backtest(
    backtest_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get backtest results by ID."""
    result = await db.execute(
        select(BacktestRun).where(BacktestRun.id == backtest_id)
    )
    backtest = result.scalar_one_or_none()
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return {"data": BacktestData.model_validate(backtest)}
