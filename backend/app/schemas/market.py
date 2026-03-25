"""Market-related Pydantic schemas."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

MarketType = Literal["stock", "crypto", "forex"]


class MarketSnapshot(BaseModel):
    """Snapshot of a single market symbol."""

    symbol: str
    price: Decimal
    change_pct: Decimal
    volume: Decimal | None = None
    market_type: MarketType


class MarketOverviewResponse(BaseModel):
    """Aggregated market overview across all three markets."""

    data: dict[str, list[MarketSnapshot]]
