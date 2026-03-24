"""CausalLink model — directed edges between events showing causal chains."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CausalLink(Base):
    """A causal relationship between two EventEntities.

    Example: "RBI holds rate" --causes--> "Bank margins stable"
    """

    __tablename__ = "causal_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("event_entities.id"), nullable=False
    )
    target_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("event_entities.id"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="causes"
    )  # causes, amplifies, dampens, contradicts, precedes
    propagation_delay: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # minutes, hours, days, weeks
    impact_decay: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # 0.0-1.0, how much effect diminishes
    confidence: Mapped[int] = mapped_column(Integer, default=50)  # 0-100
    reasoning: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # brief explanation of the causal mechanism
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    source_event = relationship(
        "EventEntity", foreign_keys=[source_event_id], lazy="joined"
    )
    target_event = relationship(
        "EventEntity", foreign_keys=[target_event_id], lazy="joined"
    )

    __table_args__ = (
        Index("idx_causal_links_source", "source_event_id"),
        Index("idx_causal_links_target", "target_event_id"),
    )
