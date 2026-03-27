"""Subscription management Celery tasks."""

import logging
from datetime import datetime, timezone

from sqlalchemy.exc import OperationalError

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.subscription_tasks.check_expired_subscriptions",
    bind=True,
    autoretry_for=(OperationalError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=2,
)
def check_expired_subscriptions(self) -> dict:
    """Check for and downgrade expired subscriptions."""
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.config import get_settings
    from app.services.payment.razorpay_service import downgrade_expired_subscriptions

    settings = get_settings()

    async def _check() -> int:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            count = await downgrade_expired_subscriptions(session)
            await session.commit()
        await engine.dispose()
        return count

    try:
        loop = asyncio.new_event_loop()
        count = loop.run_until_complete(_check())
        loop.close()
    except Exception:
        logger.exception("Failed to check expired subscriptions")
        count = 0

    return {"downgraded": count, "timestamp": datetime.now(timezone.utc).isoformat()}
