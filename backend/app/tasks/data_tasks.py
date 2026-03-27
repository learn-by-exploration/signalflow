"""Market data ingestion Celery tasks."""

import logging
from datetime import datetime, timezone

import httpx

from app.tasks.celery_app import celery_app
from app.services.data_ingestion.market_hours import is_nse_open, is_forex_open

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.data_tasks.fetch_indian_stocks",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, httpx.HTTPStatusError),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def fetch_indian_stocks(self) -> dict:
    """Fetch OHLCV data for tracked Indian stocks (NSE)."""
    if not is_nse_open():
        logger.info("NSE market closed, skipping stock fetch")
        return {"status": "skipped", "reason": "market_closed"}

    from app.services.data_ingestion.indian_stocks import IndianStockFetcher

    fetcher = IndianStockFetcher()
    result = fetcher.fetch_all()
    logger.info("Fetched Indian stocks", extra={"count": result["count"]})
    return result


@celery_app.task(
    name="app.tasks.data_tasks.fetch_crypto",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, httpx.HTTPStatusError),
    retry_backoff=True,
    retry_backoff_max=30,
    retry_jitter=True,
    max_retries=3,
)
def fetch_crypto(self) -> dict:
    """Fetch real-time crypto prices (24/7)."""
    from app.services.data_ingestion.crypto import CryptoFetcher

    fetcher = CryptoFetcher()
    result = fetcher.fetch_all()
    logger.info("Fetched crypto prices", extra={"count": result["count"]})
    return result


@celery_app.task(
    name="app.tasks.data_tasks.fetch_forex",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, httpx.HTTPStatusError),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def fetch_forex(self) -> dict:
    """Fetch forex rates for tracked pairs."""
    if not is_forex_open():
        logger.info("Forex market closed, skipping forex fetch")
        return {"status": "skipped", "reason": "market_closed"}

    from app.services.data_ingestion.forex import ForexFetcher

    fetcher = ForexFetcher()
    result = fetcher.fetch_all()
    logger.info("Fetched forex rates", extra={"count": result["count"]})
    return result


@celery_app.task(
    name="app.tasks.data_tasks.health_check",
    bind=True,
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_backoff_max=30,
    retry_jitter=True,
    max_retries=1,
)
def health_check(self) -> dict:
    """Periodic health check task."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@celery_app.task(
    name="app.tasks.data_tasks.fetch_crypto_daily",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, httpx.HTTPStatusError),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def fetch_crypto_daily(self) -> dict:
    """Fetch daily (1d) candle data for crypto — confirmation timeframe."""
    from app.services.data_ingestion.crypto import CryptoFetcher

    fetcher = CryptoFetcher(timeframe="1d")
    result = fetcher.fetch_all()
    logger.info("Fetched crypto daily candles", extra={"count": result["count"]})
    return result


@celery_app.task(
    name="app.tasks.data_tasks.fetch_forex_4h",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, httpx.HTTPStatusError),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def fetch_forex_4h(self) -> dict:
    """Fetch 4-hour candle data for forex — confirmation timeframe."""
    if not is_forex_open():
        logger.info("Forex market closed, skipping 4h forex fetch")
        return {"status": "skipped", "reason": "market_closed"}

    from app.services.data_ingestion.forex import ForexFetcher

    fetcher = ForexFetcher(timeframe="4h")
    result = fetcher.fetch_all()
    logger.info("Fetched forex 4h candles", extra={"count": result["count"]})
    return result
