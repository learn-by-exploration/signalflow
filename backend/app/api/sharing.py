"""Signal sharing endpoints — create shareable link, public view."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_user
from app.database import get_db
from app.models.signal import Signal
from app.models.signal_share import SignalShare
from app.rate_limit import limiter

router = APIRouter(prefix="/signals", tags=["sharing"])


@router.post("/{signal_id}/share", response_model=dict, status_code=201)
@limiter.limit("10/minute")
async def share_signal(
    request: Request,
    signal_id: UUID,
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a shareable token for a signal (requires authentication)."""
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    share = SignalShare(signal_id=signal_id, created_by=user.user_id)
    db.add(share)
    await db.flush()
    await db.refresh(share)
    return {"data": {"share_id": str(share.id), "signal_id": str(signal_id)}}


@router.get("/shared/{share_id}", response_model=dict)
@limiter.limit("30/minute")
async def get_shared_signal(
    request: Request,
    share_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Public endpoint — view a shared signal without authentication."""
    result = await db.execute(
        select(SignalShare).where(SignalShare.id == share_id)
    )
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="Shared signal not found")

    # Check share expiration
    if share.expires_at:
        expires = share.expires_at if share.expires_at.tzinfo else share.expires_at.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Share link has expired")

    sig_result = await db.execute(select(Signal).where(Signal.id == share.signal_id))
    signal = sig_result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal no longer exists")

    # Shared signals show directional data (entry, targets) but redact full AI reasoning.
    # This lets Pro users share proof of signals without giving away the full product.
    return {
        "data": {
            "symbol": signal.symbol,
            "market_type": signal.market_type,
            "signal_type": signal.signal_type,
            "confidence": signal.confidence,
            "current_price": str(signal.current_price),
            "target_price": str(signal.target_price),
            "stop_loss": str(signal.stop_loss),
            "timeframe": signal.timeframe,
            "ai_reasoning": (signal.ai_reasoning[:200] + "…") if signal.ai_reasoning and len(signal.ai_reasoning) > 200 else signal.ai_reasoning,
            "created_at": signal.created_at.isoformat(),
            "shared": True,
        }
    }
