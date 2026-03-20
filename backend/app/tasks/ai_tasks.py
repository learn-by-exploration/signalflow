"""AI sentiment analysis Celery tasks.

Runs Claude AI sentiment analysis on news for all tracked symbols.
"""

import asyncio
import logging

import redis.asyncio as aioredis

from app.config import get_settings
from app.services.ai_engine.sentiment import AISentimentEngine
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _detect_market_type(symbol: str) -> str:
    """Detect market type from symbol."""
    if symbol.endswith(".NS"):
        return "stock"
    if symbol.endswith("USDT"):
        return "crypto"
    if "/" in symbol:
        return "forex"
    return "stock"


async def _run_sentiment_async() -> dict:
    """Async sentiment analysis for all symbols."""
    settings = get_settings()
    redis_client = aioredis.from_url(settings.redis_url)

    try:
        engine = AISentimentEngine(redis_client=redis_client)
        all_symbols = settings.tracked_stocks + settings.tracked_crypto + settings.tracked_forex

        analyzed = 0
        errors = 0
        skipped = 0

        for symbol in all_symbols:
            try:
                market_type = _detect_market_type(symbol)
                result = await engine.analyze_sentiment(symbol, market_type)
                if result.get("fallback_reason"):
                    skipped += 1
                else:
                    analyzed += 1
            except Exception:
                logger.exception("Sentiment analysis failed for %s", symbol)
                errors += 1

        return {"status": "ok", "analyzed": analyzed, "skipped": skipped, "errors": errors}
    finally:
        await redis_client.aclose()


@celery_app.task(name="app.tasks.ai_tasks.run_sentiment")
def run_sentiment() -> dict:
    """Run Claude AI sentiment analysis on recent news for all tracked symbols."""
    logger.info("Running sentiment analysis")
    return asyncio.run(_run_sentiment_async())
