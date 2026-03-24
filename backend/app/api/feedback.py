"""Feedback loop API — signal accuracy metrics and adaptive weights."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.signal_gen.feedback import (
    compute_adaptive_weights,
    compute_indicator_accuracy,
    get_market_accuracy_summary,
)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get("/accuracy")
async def get_accuracy_summary(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get per-market accuracy summary."""
    summary = await get_market_accuracy_summary(db)
    return {"data": summary}


@router.get("/weights")
async def get_adaptive_weights(
    market_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get current adaptive weights (optionally per market type)."""
    weights = await compute_adaptive_weights(db, market_type)
    return {"data": {"market_type": market_type or "all", "weights": weights}}


@router.get("/indicators")
async def get_indicator_accuracy(
    market_type: str | None = None,
    lookback_days: int = 90,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get per-indicator accuracy metrics."""
    accuracy = await compute_indicator_accuracy(db, market_type, lookback_days)
    return {"data": accuracy}
