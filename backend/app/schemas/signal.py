"""Signal-related Pydantic schemas for API request/response."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

MarketType = Literal["stock", "crypto", "forex"]
SignalType = Literal["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]


class SignalResponse(BaseModel):
    """Single signal response."""

    id: UUID
    symbol: str
    market_type: MarketType
    signal_type: SignalType
    confidence: int = Field(ge=0, le=100)
    current_price: Decimal = Field(ge=0)
    target_price: Decimal = Field(ge=0)
    stop_loss: Decimal = Field(ge=0)
    timeframe: str | None = None
    ai_reasoning: str
    technical_data: dict
    sentiment_data: dict | None = None
    is_active: bool
    created_at: datetime
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class MetaResponse(BaseModel):
    """Metadata for list responses."""

    timestamp: datetime
    count: int
    total: int | None = None


class SignalListResponse(BaseModel):
    """Paginated list of signals."""

    data: list[SignalResponse]
    meta: MetaResponse
    disclaimer: str = (
        "This is an AI-generated educational analysis tool, not investment advice. "
        "The creator is not a SEBI-registered investment adviser. "
        "Always do your own research before making trading decisions."
    )


class SignalSummary(BaseModel):
    """Minimal signal data embedded in history items."""

    symbol: str
    market_type: str
    signal_type: str
    current_price: Decimal
    target_price: Decimal
    stop_loss: Decimal

    model_config = {"from_attributes": True}


class SignalHistoryItem(BaseModel):
    """Single signal history entry."""

    id: UUID
    signal_id: UUID
    outcome: str | None = None
    exit_price: Decimal | None = None
    return_pct: Decimal | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    signal: SignalSummary | None = None

    model_config = {"from_attributes": True}


class SignalHistoryResponse(BaseModel):
    """List of signal history entries."""

    data: list[SignalHistoryItem]
    meta: MetaResponse


class SignalStatsResponse(BaseModel):
    """Aggregate signal performance statistics."""

    total_signals: int
    hit_target: int
    hit_stop: int
    expired: int
    pending: int
    win_rate: float = Field(ge=0, le=100, description="Win rate percentage")
    avg_return_pct: float
    last_updated: datetime | None = None


class SymbolTrackRecord(BaseModel):
    """Per-symbol signal performance over the last 30 days."""

    symbol: str
    total_signals_30d: int
    hit_target: int
    hit_stop: int
    expired: int
    win_rate: float = Field(ge=0, le=100)
    avg_return_pct: float


class WeeklyTrendItem(BaseModel):
    """Win rate data for a single week."""

    week: str
    start_date: str
    total: int
    hit_target: int
    win_rate: float
