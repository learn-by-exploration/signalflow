"""SEO content page model for auto-generated market analysis pages."""

import uuid

from sqlalchemy import String, Text, DateTime, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class SeoPage(Base):
    """Auto-generated SEO page from morning briefs.

    Target keywords: "NIFTY 50 analysis today", "BTC signal today", etc.
    Generated daily from morning brief content.
    """

    __tablename__ = "seo_pages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    market_type: Mapped[str] = mapped_column(String(10), nullable=False)
    meta_description: Mapped[str] = mapped_column(String(300), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    page_date: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_seo_pages_slug", "slug"),
        Index("idx_seo_pages_market_date", "market_type", "page_date"),
    )
