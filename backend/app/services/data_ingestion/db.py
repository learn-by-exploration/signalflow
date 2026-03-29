"""Shared synchronous database engine for data ingestion tasks.

All data fetchers (stocks, crypto, forex) must use get_sync_engine()
instead of creating their own engines. This prevents connection pool
leaks from Celery tasks that create new fetcher instances every run.
"""

import logging

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import get_settings

logger = logging.getLogger(__name__)

_sync_engine: Engine | None = None


def get_sync_engine() -> Engine:
    """Get or create a shared synchronous database engine.

    Uses module-level singleton to ensure all fetchers share one
    connection pool instead of each creating their own.

    Pool config:
        - pool_size=5: 5 persistent connections
        - max_overflow=5: up to 5 extra under load
        - pool_pre_ping=True: detect stale connections
        - pool_recycle=300: recycle connections every 5 min

    Returns:
        Shared SQLAlchemy Engine instance.
    """
    global _sync_engine
    if _sync_engine is None:
        settings = get_settings()
        _sync_engine = create_engine(
            settings.database_url_sync,
            pool_size=5,
            max_overflow=5,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        logger.info("Created shared sync engine (pool_size=5, max_overflow=5)")
    return _sync_engine


def dispose_sync_engine() -> None:
    """Dispose the shared engine. For testing/shutdown use only."""
    global _sync_engine
    if _sync_engine is not None:
        _sync_engine.dispose()
        _sync_engine = None
        logger.info("Disposed shared sync engine")
