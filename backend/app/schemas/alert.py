"""Alert configuration Pydantic schemas."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

VALID_MARKETS = {"stock", "crypto", "forex"}
VALID_SIGNAL_TYPES = {"STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"}
TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class QuietHours(BaseModel):
    """Validated quiet hours with start/end times in HH:MM format."""

    start: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    end: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


class AlertConfigCreate(BaseModel):
    """Request schema for creating alert config."""

    username: str | None = Field(default=None, max_length=100, pattern=r"^[a-zA-Z0-9_]+$")
    markets: list[str] = ["stock", "crypto", "forex"]
    min_confidence: int = Field(default=60, ge=0, le=100)
    signal_types: list[str] = ["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"]
    quiet_hours: QuietHours | None = None

    @field_validator("markets")
    @classmethod
    def validate_markets(cls, v: list[str]) -> list[str]:
        """Ensure all market values are valid."""
        if len(v) > 3:
            raise ValueError("Maximum 3 markets allowed")
        for m in v:
            if m not in VALID_MARKETS:
                raise ValueError(f"Invalid market: {m}. Must be one of {sorted(VALID_MARKETS)}")
        return v

    @field_validator("signal_types")
    @classmethod
    def validate_signal_types(cls, v: list[str]) -> list[str]:
        """Ensure all signal types are valid."""
        if len(v) > 5:
            raise ValueError("Maximum 5 signal types allowed")
        for st in v:
            if st not in VALID_SIGNAL_TYPES:
                raise ValueError(f"Invalid signal type: {st}. Must be one of {sorted(VALID_SIGNAL_TYPES)}")
        return v


class AlertConfigUpdate(BaseModel):
    """Request schema for updating alert config."""

    markets: list[str] | None = None
    min_confidence: int | None = Field(default=None, ge=0, le=100)
    signal_types: list[str] | None = None
    quiet_hours: QuietHours | dict | None = None
    is_active: bool | None = None
    watchlist: list[str] | None = None

    @field_validator("markets")
    @classmethod
    def validate_markets(cls, v: list[str] | None) -> list[str] | None:
        """Ensure all market values are valid."""
        if v is None:
            return v
        if len(v) > 3:
            raise ValueError("Maximum 3 markets allowed")
        for m in v:
            if m not in VALID_MARKETS:
                raise ValueError(f"Invalid market: {m}. Must be one of {sorted(VALID_MARKETS)}")
        return v

    @field_validator("signal_types")
    @classmethod
    def validate_signal_types(cls, v: list[str] | None) -> list[str] | None:
        """Ensure all signal types are valid."""
        if v is None:
            return v
        if len(v) > 5:
            raise ValueError("Maximum 5 signal types allowed")
        for st in v:
            if st not in VALID_SIGNAL_TYPES:
                raise ValueError(f"Invalid signal type: {st}. Must be one of {sorted(VALID_SIGNAL_TYPES)}")
        return v

    @model_validator(mode="after")
    def validate_quiet_hours_dict(self) -> "AlertConfigUpdate":
        """Convert plain dict quiet_hours to QuietHours model if needed."""
        if isinstance(self.quiet_hours, dict) and not isinstance(self.quiet_hours, QuietHours):
            self.quiet_hours = QuietHours(**self.quiet_hours)
        return self


class WatchlistUpdate(BaseModel):
    """Request schema for adding/removing watchlist symbols."""

    symbol: str = Field(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9/.]+$")
    action: str = Field(description="'add' or 'remove'", pattern=r"^(add|remove)$")


class AlertConfigData(BaseModel):
    """Alert config data."""

    id: UUID
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
