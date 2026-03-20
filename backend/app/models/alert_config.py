"""AlertConfig model — user alert preferences for Telegram delivery."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AlertConfig(Base):
    """Per-user alert configuration for Telegram signal delivery."""

    __tablename__ = "alert_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    markets: Mapped[dict] = mapped_column(JSONB, default=["stock", "crypto", "forex"])
    min_confidence: Mapped[int] = mapped_column(Integer, default=60)
    signal_types: Mapped[dict] = mapped_column(
        JSONB, default=["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"]
    )
    quiet_hours: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    watchlist: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=[])
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
