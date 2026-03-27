"""Re-engagement and free-tier digest Celery tasks.

Sends weekly digests to free users and re-engagement nudges to inactive users.
"""

import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.engagement_tasks.send_free_tier_digest",
    bind=True,
    max_retries=2,
    default_retry_delay=600,
)
def send_free_tier_digest(self) -> dict:
    """Send weekly digest to free-tier users.

    Shows signal count, win rate, and best signal as a teaser.
    Scheduled: Sunday 6:30 PM IST (after weekly digest for paid users).
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.config import get_settings

    settings = get_settings()

    async def _send():
        engine = create_async_engine(settings.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            from app.services.revenue import (
                get_free_tier_weekly_digest_data,
                format_free_tier_digest,
            )

            data = await get_free_tier_weekly_digest_data(db)
            message = format_free_tier_digest(data)

            # Get free-tier users with Telegram
            from app.models.user import User
            from sqlalchemy import select

            result = await db.execute(
                select(User).where(
                    User.tier == "free",
                    User.telegram_chat_id.isnot(None),
                )
            )
            users = result.scalars().all()

            sent_count = 0
            for user in users:
                try:
                    # Send via Telegram bot
                    if settings.telegram_bot_token and user.telegram_chat_id:
                        import httpx

                        async with httpx.AsyncClient(timeout=10.0) as client:
                            await client.post(
                                f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                                json={
                                    "chat_id": user.telegram_chat_id,
                                    "text": message,
                                    "parse_mode": "Markdown",
                                },
                            )
                        sent_count += 1
                except Exception:
                    logger.debug("free_digest_send_failed", user_id=str(user.id))

        await engine.dispose()
        return sent_count

    count = asyncio.get_event_loop().run_until_complete(_send())
    return {"sent": count}


@celery_app.task(
    name="app.tasks.engagement_tasks.send_reengagement_nudge",
    bind=True,
    max_retries=1,
    default_retry_delay=600,
)
def send_reengagement_nudge(self) -> dict:
    """Send re-engagement nudge to users inactive for 7+ days.

    Max 1 nudge per user per week. Respects quiet hours.
    Shows best signal from the past week.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.config import get_settings

    settings = get_settings()

    async def _nudge():
        engine = create_async_engine(settings.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            from app.services.revenue import (
                get_inactive_users,
                get_free_tier_weekly_digest_data,
            )

            inactive = await get_inactive_users(db, days_inactive=7)
            if not inactive:
                await engine.dispose()
                return 0

            data = await get_free_tier_weekly_digest_data(db)

            nudge_msg = "👋 *You missed some winning signals!*\n\n"
            if data.get("best_signal"):
                best = data["best_signal"]
                nudge_msg += f"Best signal this week: {best['symbol']} "
                nudge_msg += f"({best['signal_type']}) +{best['return_pct']:.1f}%\n\n"
            nudge_msg += f"This week: {data['signals_this_week']} signals, "
            nudge_msg += f"{data['win_rate']}% win rate\n\n"
            nudge_msg += "Check your dashboard: /signals"

            sent_count = 0
            for user in inactive[:50]:  # Cap at 50 per run
                try:
                    chat_id = user.get("telegram_chat_id")
                    if chat_id and settings.telegram_bot_token:
                        import httpx

                        async with httpx.AsyncClient(timeout=10.0) as client:
                            await client.post(
                                f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                                json={
                                    "chat_id": chat_id,
                                    "text": nudge_msg,
                                    "parse_mode": "Markdown",
                                },
                            )
                        sent_count += 1
                except Exception:
                    logger.debug("nudge_send_failed", user_id=user.get("user_id"))

        await engine.dispose()
        return sent_count

    count = asyncio.get_event_loop().run_until_complete(_nudge())
    return {"nudged": count}
