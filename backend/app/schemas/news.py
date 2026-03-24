"""News and event-related Pydantic schemas for API request/response."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── News Events ──

class NewsEventResponse(BaseModel):
    """Single news event/headline response."""

    id: UUID
    headline: str
    source: str | None = None
    source_url: str | None = None
    symbol: str
    market_type: str
    sentiment_direction: str | None = None
    impact_magnitude: int | None = None
    event_category: str | None = None
    published_at: datetime | None = None
    fetched_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class NewsEventListResponse(BaseModel):
    """Paginated list of news events."""

    data: list[NewsEventResponse]
    meta: dict


# ── Event Entities (V2) ──

class EventEntityResponse(BaseModel):
    """Deduplicated real-world event."""

    id: UUID
    title: str
    description: str | None = None
    event_category: str
    source_category: str | None = None
    affected_symbols: list[str] | None = None
    affected_sectors: list[str] | None = None
    affected_markets: list[str] | None = None
    geographic_scope: str | None = None
    impact_magnitude: int = 1
    sentiment_direction: str = "neutral"
    confidence: int = 50
    article_count: int = 1
    occurred_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class EventEntityListResponse(BaseModel):
    """List of event entities."""

    data: list[EventEntityResponse]
    meta: dict


# ── Causal Links (V3) ──

class CausalLinkResponse(BaseModel):
    """A causal relationship between two events."""

    id: UUID
    source_event_id: UUID
    target_event_id: UUID
    relationship_type: str
    propagation_delay: str | None = None
    impact_decay: float | None = None
    confidence: int = 50
    reasoning: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CausalChainResponse(BaseModel):
    """A full causal chain with events and links."""

    root_event: EventEntityResponse
    steps: list[dict]  # [{event, link, depth}]
    affected_symbols: list[dict]  # [{symbol, direction, magnitude}]
    total_depth: int
    net_sentiment: str  # bullish, bearish, neutral


# ── Event Calendar ──

class EventCalendarResponse(BaseModel):
    """Scheduled market event."""

    id: UUID
    title: str
    event_type: str
    description: str | None = None
    scheduled_at: datetime
    affected_symbols: list[str] | None = None
    affected_markets: list[str] | None = None
    impact_magnitude: int = 3
    is_recurring: bool = False
    outcome: str | None = None
    is_completed: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class EventCalendarCreate(BaseModel):
    """Request to create a calendar event."""

    title: str = Field(max_length=200)
    event_type: str = Field(max_length=30)
    description: str | None = None
    scheduled_at: datetime
    affected_symbols: list[str] | None = None
    affected_markets: list[str] | None = None
    impact_magnitude: int = Field(default=3, ge=1, le=5)
    is_recurring: bool = False
    recurrence_rule: str | None = None


class EventCalendarListResponse(BaseModel):
    """List of calendar events."""

    data: list[EventCalendarResponse]
    meta: dict


# ── Signal News Context (embedded in signal responses) ──

class SignalNewsContext(BaseModel):
    """News context attached to a signal response."""

    headlines: list[NewsEventResponse]
    event_chain: CausalChainResponse | None = None
    sentiment_source_count: int = 0
    sentiment_freshness: str | None = None  # "4 articles from last 6 hours"
    is_technical_only: bool = False
