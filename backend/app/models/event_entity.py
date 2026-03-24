"""EventEntity model — deduplicated real-world events extracted by AI."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EventEntity(Base):
    """A deduplicated real-world event extracted from multiple news articles.

    Example: "RBI holds repo rate at 6.5%" may come from 5 different articles
    but is one EventEntity.
    """

    __tablename__ = "event_entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_category: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # macro_policy, earnings, regulatory, geopolitical, sector, commodity, technical
    source_category: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # central_bank, corporate, government, market
    affected_symbols: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    affected_sectors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    affected_markets: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    geographic_scope: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # india, us, global, emerging_markets
    impact_magnitude: Mapped[int] = mapped_column(
        Integer, default=1
    )  # 1=noise, 3=notable, 5=market-moving
    sentiment_direction: Mapped[str] = mapped_column(
        String(10), default="neutral"
    )  # bullish, bearish, neutral, mixed
    confidence: Mapped[int] = mapped_column(Integer, default=50)  # 0-100
    article_count: Mapped[int] = mapped_column(Integer, default=1)
    news_event_ids: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )  # list of NewsEvent UUIDs that fed into this
    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_event_entities_category", "event_category", created_at.desc()),
        Index("idx_event_entities_active", "is_active", created_at.desc()),
    )
