"""MarketData model — TimescaleDB hypertable for OHLCV price data."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MarketData(Base):
    """Time-series market data for stocks, crypto, and forex."""

    __tablename__ = "market_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    market_type: Mapped[str] = mapped_column(String(10), nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    volume: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, server_default="1d")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_market_data_symbol_time", "symbol", timestamp.desc()),
        Index(
            "idx_market_data_unique",
            "symbol", "timestamp", "timeframe", "market_type",
            unique=True,
        ),
        CheckConstraint('"open" > 0', name="ck_market_data_open"),
        CheckConstraint('"high" > 0', name="ck_market_data_high"),
        CheckConstraint('"low" > 0', name="ck_market_data_low"),
        CheckConstraint('"close" > 0', name="ck_market_data_close"),
        CheckConstraint('"high" >= "low"', name="ck_market_data_high_gte_low"),
        CheckConstraint(
            "market_type IN ('stock', 'crypto', 'forex')",
            name="ck_market_data_market_type",
        ),
    )
