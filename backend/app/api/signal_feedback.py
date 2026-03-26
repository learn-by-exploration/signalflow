"""Signal feedback endpoints — 'Did you take this trade?' tracking."""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_user
from app.database import get_db
from app.models.signal_feedback import SignalFeedback
from app.rate_limit import limiter

router = APIRouter(prefix="/signals", tags=["signal-feedback"])


class SignalFeedbackCreate(BaseModel):
    """Submit feedback on a signal."""

    action: str = Field(pattern=r"^(took|skipped|watching)$")
    entry_price: Decimal | None = None
    notes: str | None = Field(default=None, max_length=500)


class SignalFeedbackData(BaseModel):
    """Signal feedback response."""

    id: UUID
    signal_id: UUID
    action: str
    entry_price: Decimal | None = None
    notes: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


@router.post("/{signal_id}/feedback", response_model=dict, status_code=201)
@limiter.limit("30/minute")
async def submit_feedback(
    request: Request,
    signal_id: UUID,
    payload: SignalFeedbackCreate,
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Record whether the user took, skipped, or is watching a signal."""
    fb = SignalFeedback(
        signal_id=signal_id,
        telegram_chat_id=user.telegram_chat_id,
        action=payload.action,
        entry_price=payload.entry_price,
        notes=payload.notes,
    )
    db.add(fb)
    await db.flush()
    await db.refresh(fb)
    return {"data": SignalFeedbackData.model_validate(fb)}


@router.get("/{signal_id}/feedback", response_model=dict)
async def get_feedback(
    signal_id: UUID,
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the user's feedback for a specific signal."""
    result = await db.execute(
        select(SignalFeedback)
        .where(
            SignalFeedback.signal_id == signal_id,
            SignalFeedback.telegram_chat_id == user.telegram_chat_id,
        )
        .order_by(SignalFeedback.created_at.desc())
        .limit(1)
    )
    fb = result.scalar_one_or_none()
    if fb is None:
        return {"data": None}
    return {"data": SignalFeedbackData.model_validate(fb)}
