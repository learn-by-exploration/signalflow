"""Market overview endpoint."""

import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.market_data import MarketData
from app.schemas.market import MarketOverviewResponse, MarketSnapshot
from app.services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/markets", tags=["markets"])

MARKET_OVERVIEW_CACHE_KEY = "markets_overview"
MARKET_OVERVIEW_CACHE_TTL = 30  # seconds


async def _get_redis():
    """Get async Redis client, returns None if unavailable."""
    try:
        settings = get_settings()
        if settings.redis_url:
            return aioredis.from_url(settings.redis_url)
    except Exception:
        pass
    return None


@router.get("/overview", response_model=MarketOverviewResponse)
async def market_overview(db: AsyncSession = Depends(get_db)) -> MarketOverviewResponse:
    """Get live market snapshot across all three markets.

    Cached for 30 seconds since data only updates every 30-60s.
    """
    # Check cache first
    redis_client = await _get_redis()
    cached = await get_cached(redis_client, MARKET_OVERVIEW_CACHE_KEY)
    if cached:
        if redis_client:
            await redis_client.aclose()
        return MarketOverviewResponse(**cached)

    result: dict[str, list[MarketSnapshot]] = {"stocks": [], "crypto": [], "forex": []}

    for market_type, key in [("stock", "stocks"), ("crypto", "crypto"), ("forex", "forex")]:
        # Get the latest data point per symbol for this market type using a subquery
        latest_subq = (
            select(
                MarketData.symbol,
                func.max(MarketData.timestamp).label("max_ts"),
            )
            .where(MarketData.market_type == market_type)
            .group_by(MarketData.symbol)
            .subquery()
        )

        query = select(MarketData).join(
            latest_subq,
            (MarketData.symbol == latest_subq.c.symbol)
            & (MarketData.timestamp == latest_subq.c.max_ts),
        )

        rows = await db.execute(query)
        for row in rows.scalars().all():
            result[key].append(
                MarketSnapshot(
                    symbol=row.symbol,
                    price=row.close,
                    change_pct=(row.close - row.open) / row.open * 100 if row.open else 0,
                    volume=row.volume,
                    market_type=row.market_type,
                )
            )

    response = MarketOverviewResponse(data=result)

    # Cache the response for 30 seconds
    try:
        await set_cached(
            redis_client,
            MARKET_OVERVIEW_CACHE_KEY,
            response.model_dump(mode="json"),
            ttl=MARKET_OVERVIEW_CACHE_TTL,
        )
    except Exception:
        logger.debug("Failed to cache market overview")
    finally:
        if redis_client:
            await redis_client.aclose()

    return response
