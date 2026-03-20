"""Signal generation and lifecycle management Celery tasks."""

import asyncio
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models.signal import Signal
from app.models.signal_history import SignalHistory
from app.services.signal_gen.generator import SignalGenerator
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _generate_signals_async() -> dict:
    """Async signal generation for all tracked symbols."""
    settings = get_settings()

    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    redis_client = aioredis.from_url(settings.redis_url)

    try:
        async with session_factory() as db:
            generator = SignalGenerator(db=db, redis_client=redis_client)
            signals = await generator.generate_all()
            await db.commit()
            return {"status": "ok", "signals_generated": len(signals)}
    finally:
        await redis_client.aclose()
        await engine.dispose()


async def _resolve_expired_async() -> dict:
    """Check active signals and resolve expired ones."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    now = datetime.now(timezone.utc)
    resolved = 0

    try:
        async with session_factory() as db:
            # Find expired active signals
            stmt = select(Signal).where(
                Signal.is_active.is_(True),
                Signal.expires_at <= now,
            )
            result = await db.execute(stmt)
            expired_signals = result.scalars().all()

            for signal in expired_signals:
                signal.is_active = False

                # Create history entry
                history = SignalHistory(
                    signal_id=signal.id,
                    outcome="expired",
                    exit_price=signal.current_price,  # Use creation price as placeholder
                    return_pct=None,
                    resolved_at=now,
                )
                db.add(history)
                resolved += 1

            await db.commit()

        return {"status": "ok", "resolved": resolved}
    finally:
        await engine.dispose()


@celery_app.task(name="app.tasks.signal_tasks.generate_signals")
def generate_signals() -> dict:
    """Generate trading signals from technical + AI analysis."""
    logger.info("Generating signals")
    return asyncio.run(_generate_signals_async())


@celery_app.task(name="app.tasks.signal_tasks.resolve_expired")
def resolve_expired() -> dict:
    """Resolve expired signals and update signal history."""
    logger.info("Resolving expired signals")
    return asyncio.run(_resolve_expired_async())
