"""NewsEvent model — individual news articles/headlines with metadata."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NewsEvent(Base):
    """Persisted news article/headline that fed into sentiment analysis."""

    __tablename__ = "news_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    market_type: Mapped[str] = mapped_column(String(10), nullable=False)
    sentiment_direction: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # bullish, bearish, neutral
    impact_magnitude: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 1-5 scale
    event_category: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # macro_policy, earnings, sector, etc.
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_news_events_symbol_time", "symbol", created_at.desc()),
        Index("idx_news_events_market", "market_type", created_at.desc()),
    )
