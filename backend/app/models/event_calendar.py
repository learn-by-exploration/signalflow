"""EventCalendar model — scheduled known events (RBI MPC, FOMC, earnings dates)."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EventCalendar(Base):
    """Scheduled market events for event-risk awareness.

    Stores upcoming known events like RBI MPC meetings, FOMC dates,
    earnings release dates, etc.
    """

    __tablename__ = "event_calendar"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    event_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # rbi_mpc, fomc, earnings, gdp_release, cpi_release, budget, etc.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    affected_symbols: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    affected_markets: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    impact_magnitude: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # e.g., "bimonthly", "quarterly"
    outcome: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # filled after event occurs
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_event_calendar_scheduled", "scheduled_at"),
        Index("idx_event_calendar_type", "event_type"),
    )
