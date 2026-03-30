"""News and Events API endpoints — V1 news feed, V2 events, V3 causal chains."""

import re
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.news_event import NewsEvent
from app.models.event_entity import EventEntity
from app.models.causal_link import CausalLink
from app.models.event_calendar import EventCalendar
from app.models.signal_news_link import SignalNewsLink
from app.rate_limit import limiter
from app.schemas.news import (
    CausalChainResponse,
    CausalLinkResponse,
    EventCalendarCreate,
    EventCalendarListResponse,
    EventCalendarResponse,
    EventEntityListResponse,
    EventEntityResponse,
    NewsEventListResponse,
    NewsEventResponse,
)

router = APIRouter(prefix="/news", tags=["news"])

VALID_MARKETS = {"stock", "crypto", "forex"}
_SYMBOL_RE = re.compile(r"^[A-Z0-9./=_-]{1,20}$")


# ── V1: News Headlines ──


@router.get("", response_model=NewsEventListResponse)
async def list_news(
    market: str | None = None,
    symbol: str | None = None,
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> NewsEventListResponse:
    """List recent news headlines with optional filters."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    base_query = select(NewsEvent).where(NewsEvent.created_at >= cutoff)

    if market:
        if market not in VALID_MARKETS:
            raise HTTPException(status_code=400, detail=f"Invalid market: {market}")
        base_query = base_query.where(NewsEvent.market_type == market)
    if symbol:
        safe = symbol.upper().strip()
        if not _SYMBOL_RE.match(safe):
            raise HTTPException(status_code=400, detail="Invalid symbol format")
        base_query = base_query.where(NewsEvent.symbol.ilike(f"%{safe}%"))

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar() or 0

    query = base_query.order_by(NewsEvent.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    events = result.scalars().all()

    return NewsEventListResponse(
        data=[NewsEventResponse.model_validate(e) for e in events],
        meta={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": len(events),
            "total": total,
        },
    )


@router.get("/signal/{signal_id}", response_model=NewsEventListResponse)
async def get_news_for_signal(
    signal_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> NewsEventListResponse:
    """Get news headlines that fed into a specific signal."""
    stmt = (
        select(NewsEvent)
        .join(SignalNewsLink, SignalNewsLink.news_event_id == NewsEvent.id)
        .where(SignalNewsLink.signal_id == signal_id)
        .order_by(NewsEvent.created_at.desc())
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    return NewsEventListResponse(
        data=[NewsEventResponse.model_validate(e) for e in events],
        meta={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": len(events),
            "total": len(events),
        },
    )


# ── V2: Event Entities ──


@router.get("/events", response_model=EventEntityListResponse)
async def list_events(
    category: str | None = None,
    market: str | None = None,
    hours: int = Query(default=72, ge=1, le=720),
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> EventEntityListResponse:
    """List deduplicated real-world events."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    base_query = select(EventEntity).where(
        EventEntity.is_active.is_(True),
        EventEntity.created_at >= cutoff,
    )

    if category:
        base_query = base_query.where(EventEntity.event_category == category)

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar() or 0

    query = base_query.order_by(EventEntity.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    entities = result.scalars().all()

    return EventEntityListResponse(
        data=[EventEntityResponse.model_validate(e) for e in entities],
        meta={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": len(entities),
            "total": total,
        },
    )


@router.get("/events/{event_id}", response_model=dict)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a single event entity with its causal links."""
    result = await db.execute(
        select(EventEntity).where(EventEntity.id == event_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Get causal links where this event is the source
    links_stmt = select(CausalLink).where(CausalLink.source_event_id == event_id)
    links_result = await db.execute(links_stmt)
    links = links_result.scalars().all()

    return {
        "data": {
            "event": EventEntityResponse.model_validate(event),
            "causal_links": [CausalLinkResponse.model_validate(l) for l in links],
        }
    }


# ── V3: Causal Chains ──


@router.get("/chains/{symbol}")
async def get_chains_for_symbol(
    symbol: str,
    hours: int = Query(default=168, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get active causal chains affecting a symbol, with full chain traversal."""
    safe = symbol.upper().strip()
    if not _SYMBOL_RE.match(safe):
        raise HTTPException(status_code=400, detail="Invalid symbol format")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Find events affecting this symbol
    stmt = select(EventEntity).where(
        EventEntity.is_active.is_(True),
        EventEntity.created_at >= cutoff,
    )
    result = await db.execute(stmt)
    all_events = result.scalars().all()

    # Filter to events that affect this symbol
    matching_events = []
    for evt in all_events:
        symbols = evt.affected_symbols or []
        if symbol in symbols or symbol.replace(".NS", "") in [s.replace(".NS", "") for s in symbols]:
            matching_events.append(evt)

    # Build chains by following causal links
    chains = []
    for root_event in matching_events:
        chain_steps = []
        current_ids = [root_event.id]
        visited = {root_event.id}
        depth = 0

        while current_ids and depth < 3:  # Max 3 levels deep
            links_stmt = select(CausalLink).where(
                CausalLink.source_event_id.in_(current_ids)
            )
            links_result = await db.execute(links_stmt)
            links = links_result.scalars().all()

            next_ids = []
            for link in links:
                if link.target_event_id not in visited:
                    visited.add(link.target_event_id)
                    next_ids.append(link.target_event_id)
                    chain_steps.append({
                        "depth": depth + 1,
                        "link": CausalLinkResponse.model_validate(link),
                        "target_event": EventEntityResponse.model_validate(link.target_event),
                    })
            current_ids = next_ids
            depth += 1

        chains.append({
            "root_event": EventEntityResponse.model_validate(root_event),
            "steps": chain_steps,
            "total_depth": depth,
        })

    return {
        "data": chains,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "chain_count": len(chains),
        },
    }


# ── Event Calendar ──


@router.get("/calendar", response_model=EventCalendarListResponse)
async def list_calendar_events(
    days_ahead: int = Query(default=30, ge=1, le=90),
    event_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> EventCalendarListResponse:
    """List upcoming scheduled market events."""
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days_ahead)

    base_query = select(EventCalendar).where(
        EventCalendar.scheduled_at >= now,
        EventCalendar.scheduled_at <= cutoff,
    )

    if event_type:
        base_query = base_query.where(EventCalendar.event_type == event_type)

    query = base_query.order_by(EventCalendar.scheduled_at.asc()).limit(50)
    result = await db.execute(query)
    events = result.scalars().all()

    return EventCalendarListResponse(
        data=[EventCalendarResponse.model_validate(e) for e in events],
        meta={
            "timestamp": now.isoformat(),
            "count": len(events),
        },
    )


@router.post("/calendar", response_model=dict)
@limiter.limit("30/minute")
async def create_calendar_event(
    request: Request,
    data: EventCalendarCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new scheduled calendar event."""
    event = EventCalendar(
        title=data.title,
        event_type=data.event_type,
        description=data.description,
        scheduled_at=data.scheduled_at,
        affected_symbols=data.affected_symbols,
        affected_markets=data.affected_markets,
        impact_magnitude=data.impact_magnitude,
        is_recurring=data.is_recurring,
        recurrence_rule=data.recurrence_rule,
    )
    db.add(event)
    await db.flush()
    return {"data": EventCalendarResponse.model_validate(event)}
