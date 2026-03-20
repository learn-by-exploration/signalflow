"""Market-related Pydantic schemas."""

from decimal import Decimal

from pydantic import BaseModel


class MarketSnapshot(BaseModel):
    """Snapshot of a single market symbol."""

    symbol: str
    price: Decimal
    change_pct: Decimal
    volume: Decimal | None = None
    market_type: str


class MarketOverviewResponse(BaseModel):
    """Aggregated market overview across all three markets."""

    data: dict[str, list[MarketSnapshot]]
