"""AI sentiment analysis Celery tasks.

Runs Claude AI sentiment analysis on news for tracked symbols.
Budget-optimized: stocks only during market hours, crypto 24/7, forex during market hours.
"""

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import redis.asyncio as aioredis

from app.config import get_settings
from app.services.ai_engine.sentiment import AISentimentEngine
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")


def _detect_market_type(symbol: str) -> str:
    """Detect market type from symbol."""
    if symbol.endswith(".NS"):
        return "stock"
    if symbol.endswith("USDT"):
        return "crypto"
    if "/" in symbol:
        return "forex"
    return "stock"


def _is_stock_market_hours() -> bool:
    """Check if NSE is likely open (Mon-Fri 9:00-16:00 IST with buffer)."""
    now = datetime.now(IST)
    if now.weekday() >= 5:  # Weekend
        return False
    return 9 <= now.hour <= 16


def _is_forex_market_hours() -> bool:
    """Check if forex markets are active (Sun 5:30 PM - Sat 3:30 AM IST, roughly)."""
    now = datetime.now(IST)
    # Forex is closed Sat 3:30 AM IST to Sun 5:30 PM IST
    if now.weekday() == 5 and now.hour >= 4:  # Saturday after 4 AM
        return False
    if now.weekday() == 6 and now.hour < 17:  # Sunday before 5 PM
        return False
    return True


async def _run_sentiment_async() -> dict:
    """Async sentiment analysis — budget-aware with market-hours gating."""
    settings = get_settings()
    redis_client = aioredis.from_url(settings.redis_url)

    try:
        engine = AISentimentEngine(redis_client=redis_client)

        analyzed = 0
        errors = 0
        skipped = 0

        # Always analyze crypto (24/7)
        for symbol in settings.tracked_crypto:
            try:
                result = await engine.analyze_sentiment(symbol, "crypto")
                if result.get("fallback_reason"):
                    skipped += 1
                else:
                    analyzed += 1
            except Exception:
                logger.exception("Sentiment analysis failed for %s", symbol)
                errors += 1

        # Stocks: only during market hours
        if _is_stock_market_hours():
            for symbol in settings.tracked_stocks:
                try:
                    result = await engine.analyze_sentiment(symbol, "stock")
                    if result.get("fallback_reason"):
                        skipped += 1
                    else:
                        analyzed += 1
                except Exception:
                    logger.exception("Sentiment analysis failed for %s", symbol)
                    errors += 1
        else:
            skipped += len(settings.tracked_stocks)
            logger.info("Skipping stock sentiment — market closed")

        # Forex: only during forex hours
        if _is_forex_market_hours():
            for symbol in settings.tracked_forex:
                try:
                    result = await engine.analyze_sentiment(symbol, "forex")
                    if result.get("fallback_reason"):
                        skipped += 1
                    else:
                        analyzed += 1
                except Exception:
                    logger.exception("Sentiment analysis failed for %s", symbol)
                    errors += 1
        else:
            skipped += len(settings.tracked_forex)
            logger.info("Skipping forex sentiment — market closed")

        return {"status": "ok", "analyzed": analyzed, "skipped": skipped, "errors": errors}
    finally:
        await redis_client.aclose()


@celery_app.task(name="app.tasks.ai_tasks.run_sentiment")
def run_sentiment() -> dict:
    """Run Claude AI sentiment analysis on recent news for all tracked symbols."""
    logger.info("Running sentiment analysis")
    return asyncio.run(_run_sentiment_async())


async def _expire_stale_events_async() -> dict:
    """Mark event entities as expired based on their category-specific TTLs."""
    from datetime import timezone as tz
    from sqlalchemy import update
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.config import get_settings
    from app.database import Base
    from app.models.event_entity import EventEntity

    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    now = datetime.now(tz.utc)
    expired = 0

    try:
        async with session_factory() as session:
            # Expire events past their expires_at timestamp
            stmt = (
                update(EventEntity)
                .where(EventEntity.expires_at <= now)
                .values(expires_at=now)
            )
            result = await session.execute(stmt)
            expired = result.rowcount
            await session.commit()
    finally:
        await engine.dispose()

    return {"expired_events": expired}


@celery_app.task(name="app.tasks.ai_tasks.expire_stale_events")
def expire_stale_events() -> dict:
    """Expire event entities that have passed their TTL."""
    logger.info("Expiring stale event entities")
    return asyncio.run(_expire_stale_events_async())
