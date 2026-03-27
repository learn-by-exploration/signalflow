"""Subscription model — tracks user payment subscriptions."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Subscription(Base):
    """Tracks user subscription status and payment history."""

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True
    )
    plan: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "monthly", "annual", "trial"
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # "active", "cancelled", "expired", "past_due"
    razorpay_subscription_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, unique=True
    )
    razorpay_customer_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    amount_paise: Mapped[int] = mapped_column(
        Integer, nullable=False, default=49900
    )  # ₹499 in paise
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="INR"
    )
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trial_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
