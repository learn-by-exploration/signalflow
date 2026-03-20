"""Market data ingestion Celery tasks."""

import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app
from app.services.data_ingestion.market_hours import is_nse_open, is_forex_open

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.data_tasks.fetch_indian_stocks")
def fetch_indian_stocks() -> dict:
    """Fetch OHLCV data for tracked Indian stocks (NSE)."""
    if not is_nse_open():
        logger.info("NSE market closed, skipping stock fetch")
        return {"status": "skipped", "reason": "market_closed"}

    from app.services.data_ingestion.indian_stocks import IndianStockFetcher

    fetcher = IndianStockFetcher()
    result = fetcher.fetch_all()
    logger.info("Fetched Indian stocks", extra={"count": result["count"]})
    return result


@celery_app.task(name="app.tasks.data_tasks.fetch_crypto")
def fetch_crypto() -> dict:
    """Fetch real-time crypto prices (24/7)."""
    from app.services.data_ingestion.crypto import CryptoFetcher

    fetcher = CryptoFetcher()
    result = fetcher.fetch_all()
    logger.info("Fetched crypto prices", extra={"count": result["count"]})
    return result


@celery_app.task(name="app.tasks.data_tasks.fetch_forex")
def fetch_forex() -> dict:
    """Fetch forex rates for tracked pairs."""
    if not is_forex_open():
        logger.info("Forex market closed, skipping forex fetch")
        return {"status": "skipped", "reason": "market_closed"}

    from app.services.data_ingestion.forex import ForexFetcher

    fetcher = ForexFetcher()
    result = fetcher.fetch_all()
    logger.info("Fetched forex rates", extra={"count": result["count"]})
    return result


@celery_app.task(name="app.tasks.data_tasks.health_check")
def health_check() -> dict:
    """Periodic health check task."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
