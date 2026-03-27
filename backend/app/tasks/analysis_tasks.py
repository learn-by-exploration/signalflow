"""Technical analysis Celery tasks.

Runs TechnicalAnalyzer on recent market data for all tracked symbols
and stores results in Redis cache for signal generation to consume.
"""

import asyncio
import json
import logging

import pandas as pd
import redis
from sqlalchemy import create_engine, select, text

from app.config import get_settings
from app.models.market_data import MarketData
from app.services.analysis.indicators import TechnicalAnalyzer
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_analysis_sync() -> dict:
    """Synchronous implementation that runs technical analysis for all symbols.

    Celery tasks are synchronous, so we use a sync database engine here.
    """
    settings = get_settings()
    redis_client = redis.from_url(settings.redis_url)

    from sqlalchemy.orm import Session

    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)

    all_symbols = settings.tracked_stocks + settings.tracked_crypto + settings.tracked_forex
    analyzed = 0
    errors = 0

    with Session(engine) as session:
        for symbol in all_symbols:
            try:
                # Fetch latest 250 data points
                rows = session.execute(
                    text(
                        "SELECT open, high, low, close, volume, timestamp "
                        "FROM market_data WHERE symbol = :sym "
                        "ORDER BY timestamp DESC LIMIT 250"
                    ),
                    {"sym": symbol},
                ).fetchall()

                if not rows or len(rows) < 15:
                    logger.debug("Skipping %s — only %d data points", symbol, len(rows) if rows else 0)
                    continue

                df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume", "timestamp"])
                for col in ["open", "high", "low", "close", "volume"]:
                    df[col] = df[col].astype(float)
                df = df.sort_values("timestamp").reset_index(drop=True)

                analyzer = TechnicalAnalyzer(df)
                result = analyzer.full_analysis()

                # Cache in Redis for signal generation (TTL 10 minutes)
                redis_client.set(
                    f"analysis:{symbol}",
                    json.dumps(result, default=str),
                    ex=600,
                )
                analyzed += 1

            except Exception:
                logger.exception("Analysis failed for %s", symbol)
                errors += 1

    engine.dispose()
    redis_client.close()
    return {"status": "ok", "analyzed": analyzed, "errors": errors}


@celery_app.task(
    name="app.tasks.analysis_tasks.run_analysis",
    bind=True,
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=2,
)
def run_analysis(self) -> dict:
    """Run technical indicators on latest market data for all tracked symbols."""
    logger.info("Running technical analysis")
    return _run_analysis_sync()
