"""SignalHistory model — tracks signal outcomes (hit target, hit stop, expired)."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SignalHistory(Base):
    """Outcome tracking for resolved signals."""

    __tablename__ = "signal_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    signal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("signals.id"), nullable=False
    )
    outcome: Mapped[str | None] = mapped_column(String(20), nullable=True)
    exit_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    return_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    signal_rel = relationship("Signal", lazy="joined")

    __table_args__ = (
        Index("idx_history_outcome", "outcome", created_at.desc()),
        CheckConstraint(
            "outcome IN ('hit_target', 'hit_stop', 'expired', 'pending')",
            name="ck_signal_history_outcome",
        ),
    )
