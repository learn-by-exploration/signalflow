"""Alert configuration Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AlertConfigCreate(BaseModel):
    """Request schema for creating alert config."""

    telegram_chat_id: int
    username: str | None = None
    markets: list[str] = ["stock", "crypto", "forex"]
    min_confidence: int = Field(default=60, ge=0, le=100)
    signal_types: list[str] = ["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"]
    quiet_hours: dict | None = None


class AlertConfigUpdate(BaseModel):
    """Request schema for updating alert config."""

    markets: list[str] | None = None
    min_confidence: int | None = Field(default=None, ge=0, le=100)
    signal_types: list[str] | None = None
    quiet_hours: dict | None = None
    is_active: bool | None = None
    watchlist: list[str] | None = None


class WatchlistUpdate(BaseModel):
    """Request schema for adding/removing watchlist symbols."""

    symbol: str
    action: str = Field(description="'add' or 'remove'")


class AlertConfigData(BaseModel):
    """Alert config data."""

    id: UUID
    telegram_chat_id: int
    username: str | None = None
    markets: list[str]
    min_confidence: int
    signal_types: list[str]
    quiet_hours: dict | None = None
    watchlist: list[str] | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertConfigResponse(BaseModel):
    """Response schema for alert config."""

    data: AlertConfigData
