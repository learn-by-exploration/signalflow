"""SignalFeedback model — captures user actions on signals (took/skipped/watching)."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SignalFeedback(Base):
    """User feedback on a signal — did they take the trade?"""

    __tablename__ = "signal_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    signal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    telegram_chat_id: Mapped[int] = mapped_column(nullable=False)
    action: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # took, skipped, watching
    entry_price: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 8), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_signal_feedback_signal", "signal_id"),
        Index("idx_signal_feedback_user", "telegram_chat_id"),
    )
