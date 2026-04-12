"""Signal endpoints — list and detail."""

import re
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_optional_auth
from app.config import get_settings
from app.database import get_db
from app.models.signal import Signal
from app.models.signal_news_link import SignalNewsLink
from app.models.news_event import NewsEvent
from app.schemas.signal import MetaResponse, SignalListResponse, SignalResponse
from app.services.tier_gating import consume_free_detail_view, redact_signal_for_free_tier

router = APIRouter(prefix="/signals", tags=["signals"])

VALID_MARKETS = {"stock", "crypto", "forex"}
VALID_SIGNAL_TYPES = {"STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"}
_SYMBOL_RE = re.compile(r"^[A-Z0-9./=_-]{1,20}$")


@router.get("", response_model=SignalListResponse)
async def list_signals(
    market: str | None = None,
    signal_type: str | None = None,
    symbol: str | None = None,
    min_confidence: int = Query(default=0, ge=0, le=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> SignalListResponse:
    """List active trading signals with optional filters."""
    if market and market not in VALID_MARKETS:
        raise HTTPException(status_code=400, detail=f"Invalid market. Must be one of {sorted(VALID_MARKETS)}")
    if signal_type and signal_type not in VALID_SIGNAL_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid signal_type. Must be one of {sorted(VALID_SIGNAL_TYPES)}")

    base_query = select(Signal).where(Signal.is_active.is_(True))

    if market:
        base_query = base_query.where(Signal.market_type == market)
    if signal_type:
        base_query = base_query.where(Signal.signal_type == signal_type)
    if symbol:
        safe = symbol.upper().strip()
        if not _SYMBOL_RE.match(safe):
            raise HTTPException(status_code=400, detail="Invalid symbol format")
        base_query = base_query.where(Signal.symbol.ilike(f"%{safe}%"))
    if min_confidence > 0:
        base_query = base_query.where(Signal.confidence >= min_confidence)

    # Total count for pagination
    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar() or 0

    query = base_query.order_by(Signal.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    signals = result.scalars().all()

    return SignalListResponse(
        data=[SignalResponse.model_validate(s) for s in signals],
        meta=MetaResponse(timestamp=datetime.now(timezone.utc), count=len(signals), total=total),
    )


@router.get("/{signal_id}", response_model=dict)
async def get_signal(
    signal_id: UUID,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth),
) -> dict:
    """Get a single signal by ID, including linked news events.

    Free users get 3 full-detail views per week; subsequent views are redacted.
    Pro users always receive full data.
    """
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    # Fetch linked news events
    news_items: list[dict] = []
    link_result = await db.execute(
        select(SignalNewsLink.news_event_id)
        .where(SignalNewsLink.signal_id == signal_id)
    )
    news_event_ids = [row[0] for row in link_result.all()]
    if news_event_ids:
        news_result = await db.execute(
            select(NewsEvent)
            .where(NewsEvent.id.in_(news_event_ids))
            .order_by(NewsEvent.fetched_at.desc())
            .limit(10)
        )
        for ne in news_result.scalars().all():
            news_items.append({
                "id": str(ne.id),
                "headline": ne.headline,
                "source": ne.source,
                "source_url": ne.source_url,
                "sentiment_direction": ne.sentiment_direction,
                "impact_magnitude": ne.impact_magnitude,
                "event_category": ne.event_category,
                "published_at": ne.published_at.isoformat() if ne.published_at else None,
            })

    signal_data = SignalResponse.model_validate(signal).model_dump(mode="json")

    # Apply tier gating: pro users always get full data;
    # free/anonymous users get 3 views/week then redacted.
    is_pro = auth is not None and auth.tier == "pro"
    if not is_pro and auth is not None and auth.user_id:
        settings = get_settings()
        redis_client = aioredis.from_url(settings.redis_url)
        allowed = True  # Fail-open: if Redis is down, grant the view
        try:
            allowed = await consume_free_detail_view(auth.user_id, redis_client)
        except Exception:
            logger.warning("redis_unavailable tier_gating user_id=%s — granting view", auth.user_id)
        finally:
            try:
                await redis_client.aclose()
            except Exception:
                pass
        if not allowed:
            signal_data = redact_signal_for_free_tier(signal_data)
    elif not is_pro and auth is None:
        # Unauthenticated requests always get redacted detail
        signal_data = redact_signal_for_free_tier(signal_data)

    return {
        "data": signal_data,
        "news": news_items,
    }
