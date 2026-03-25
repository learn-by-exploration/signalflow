"""Signal model — trading signals with AI reasoning."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Signal(Base):
    """Generated trading signal with confidence, targets, and AI reasoning."""

    __tablename__ = "signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    market_type: Mapped[str] = mapped_column(String(10), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(15), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    target_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    stop_loss: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    timeframe: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    technical_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    sentiment_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_signals_active", "is_active", created_at.desc()),
        Index("idx_signals_symbol", "symbol", created_at.desc()),
        CheckConstraint("confidence >= 0 AND confidence <= 100", name="ck_signals_confidence"),
        CheckConstraint("current_price >= 0", name="ck_signals_current_price"),
        CheckConstraint("target_price >= 0", name="ck_signals_target_price"),
        CheckConstraint("stop_loss >= 0", name="ck_signals_stop_loss"),
        CheckConstraint(
            "market_type IN ('stock', 'crypto', 'forex')",
            name="ck_signals_market_type",
        ),
        CheckConstraint(
            "signal_type IN ('STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL')",
            name="ck_signals_signal_type",
        ),
    )
