"""Signal generation and lifecycle management Celery tasks."""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.config import get_settings
from app.models.market_data import MarketData
from app.models.signal import Signal
from app.models.signal_history import SignalHistory
from app.schemas.signal import SignalResponse
from app.services.pubsub import publish_signal
from app.services.signal_gen.generator import SignalGenerator
from app.tasks._engine import get_task_session_factory
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _generate_signals_async() -> dict:
    """Async signal generation for all tracked symbols."""
    settings = get_settings()

    session_factory = get_task_session_factory()
    redis_client = aioredis.from_url(settings.redis_url)

    try:
        async with session_factory() as db:
            generator = SignalGenerator(db=db, redis_client=redis_client)
            signals = await generator.generate_all()
            await db.commit()

            # Publish new signals to Redis so WebSocket clients get real-time delivery
            for signal in signals:
                try:
                    signal_data = SignalResponse.model_validate(signal).model_dump(mode="json")
                    await publish_signal(redis_client, signal_data)
                except Exception:
                    logger.warning("pubsub_publish_error signal_id=%s", signal.id)

            return {"status": "ok", "signals_generated": len(signals)}
    finally:
        await redis_client.aclose()


async def _resolve_signals_async() -> dict:
    """Check active signals against current prices and resolve them.

    For each active signal:
    - Fetch the latest market price
    - If price >= target_price (for BUY signals) → hit_target
    - If price <= stop_loss (for BUY signals) → hit_stop
    - If price <= target_price (for SELL signals) → hit_target
    - If price >= stop_loss (for SELL signals) → hit_stop
    - If expired → expired
    """
    session_factory = get_task_session_factory()

    now = datetime.now(timezone.utc)
    hit_target = 0
    hit_stop = 0
    expired = 0

    async with session_factory() as db:
        # Fetch all active signals with FOR UPDATE SKIP LOCKED
        # to prevent concurrent workers from resolving the same signal
        stmt = (
            select(Signal)
            .where(Signal.is_active.is_(True))
            .with_for_update(skip_locked=True)
        )
        result = await db.execute(stmt)
        active_signals = result.scalars().all()

        for signal in active_signals:
            # Get the latest price for this symbol
            # Strip .NS suffix — Indian stock fetcher stores without it
            query_symbol = signal.symbol.replace(".NS", "")
            price_stmt = (
                select(MarketData.close)
                .where(MarketData.symbol == query_symbol)
                .order_by(MarketData.timestamp.desc())
                .limit(1)
            )
            price_result = await db.execute(price_stmt)
            latest_price_row = price_result.scalar_one_or_none()

            if latest_price_row is None:
                continue

            current_price = Decimal(str(latest_price_row))
            is_buy = "BUY" in signal.signal_type
            outcome = None

            if is_buy:
                if current_price >= signal.target_price:
                    outcome = "hit_target"
                elif current_price <= signal.stop_loss:
                    outcome = "hit_stop"
            else:
                # SELL signal: target is lower, stop is higher
                if current_price <= signal.target_price:
                    outcome = "hit_target"
                elif current_price >= signal.stop_loss:
                    outcome = "hit_stop"

            # Check expiry
            if outcome is None and signal.expires_at and signal.expires_at <= now:
                outcome = "expired"

            if outcome:
                signal.is_active = False

                # Calculate return percentage
                if signal.current_price and signal.current_price > 0:
                    if is_buy:
                        return_pct = (
                            (current_price - signal.current_price) / signal.current_price * 100
                        )
                    else:
                        return_pct = (
                            (signal.current_price - current_price) / signal.current_price * 100
                        )
                else:
                    return_pct = None

                history = SignalHistory(
                    signal_id=signal.id,
                    outcome=outcome,
                    exit_price=current_price,
                    return_pct=return_pct,
                    resolved_at=now,
                )
                db.add(history)

                if outcome == "hit_target":
                    hit_target += 1
                elif outcome == "hit_stop":
                    hit_stop += 1
                else:
                    expired += 1

                logger.info(
                    "Signal resolved: %s %s → %s (return=%.2f%%)",
                    signal.symbol,
                    signal.signal_type,
                    outcome,
                    float(return_pct) if return_pct else 0,
                )

        await db.commit()

    return {
        "status": "ok",
        "hit_target": hit_target,
        "hit_stop": hit_stop,
        "expired": expired,
        "total_resolved": hit_target + hit_stop + expired,
    }


@celery_app.task(
    name="app.tasks.signal_tasks.generate_signals",
    bind=True,
    autoretry_for=(OperationalError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=2,
    soft_time_limit=300,   # 5 min soft limit (raises SoftTimeLimitExceeded)
    time_limit=600,         # 10 min hard kill
)
def generate_signals(self) -> dict:
    """Generate trading signals from technical + AI analysis."""
    logger.info("Generating signals")
    return asyncio.run(_generate_signals_async())


@celery_app.task(
    name="app.tasks.signal_tasks.resolve_expired",
    bind=True,
    autoretry_for=(OperationalError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=2,
    soft_time_limit=120,   # 2 min soft limit
    time_limit=180,         # 3 min hard kill
)
def resolve_expired(self) -> dict:
    """Check active signals against current prices — resolve hits, stops, and expiries."""
    logger.info("Resolving signals against current prices")
    return asyncio.run(_resolve_signals_async())
