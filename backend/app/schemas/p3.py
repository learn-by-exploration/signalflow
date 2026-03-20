"""Price alert Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PriceAlertCreate(BaseModel):
    """Create a new price alert."""

    telegram_chat_id: int
    symbol: str
    market_type: str
    condition: str = Field(description="'above' or 'below'")
    threshold: Decimal


class PriceAlertData(BaseModel):
    """Price alert response data."""

    id: UUID
    telegram_chat_id: int
    symbol: str
    market_type: str
    condition: str
    threshold: Decimal
    is_triggered: bool
    is_active: bool
    triggered_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TradeCreate(BaseModel):
    """Log a new trade."""

    telegram_chat_id: int
    symbol: str
    market_type: str
    side: str = Field(description="'buy' or 'sell'")
    quantity: Decimal
    price: Decimal
    notes: str | None = None
    signal_id: UUID | None = None


class TradeData(BaseModel):
    """Trade response data."""

    id: UUID
    telegram_chat_id: int
    symbol: str
    market_type: str
    side: str
    quantity: Decimal
    price: Decimal
    notes: str | None = None
    signal_id: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PortfolioSummary(BaseModel):
    """Aggregated portfolio summary."""

    total_invested: Decimal
    current_value: Decimal
    total_pnl: Decimal
    total_pnl_pct: float
    positions: list[dict]


class BacktestCreate(BaseModel):
    """Kick off a backtest run."""

    symbol: str
    market_type: str
    days: int = Field(default=90, ge=7, le=365)


class BacktestData(BaseModel):
    """Backtest run response data."""

    id: UUID
    symbol: str
    market_type: str
    start_date: datetime
    end_date: datetime
    total_signals: int
    wins: int
    losses: int
    win_rate: float
    avg_return_pct: float
    total_return_pct: float
    max_drawdown_pct: float
    status: str
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class AskQuestion(BaseModel):
    """Ask a question about a symbol."""

    symbol: str
    question: str = Field(max_length=500)
