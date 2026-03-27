"""SEO page generation Celery tasks.

Auto-generates daily market analysis pages from morning brief content.
Runs after morning brief task.
"""

import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.seo_tasks.generate_seo_pages",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def generate_seo_pages(self) -> dict:
    """Generate SEO analysis pages for all markets.

    Scheduled to run daily after morning brief (8:30 AM IST).
    Creates one page per market type using the morning brief content.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.config import get_settings
    from app.services.seo import create_seo_page, generate_slug

    settings = get_settings()

    async def _generate():
        engine = create_async_engine(settings.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        today = datetime.now(timezone.utc)
        pages_created = []

        async with async_session() as db:
            for market_type in ["stock", "crypto", "forex"]:
                try:
                    slug = generate_slug(market_type, today)

                    # Check if page already exists for today
                    from app.models.seo_page import SeoPage
                    from sqlalchemy import select

                    existing = await db.execute(select(SeoPage).where(SeoPage.slug == slug))
                    if existing.scalars().first():
                        logger.info("seo_page_exists", slug=slug)
                        continue

                    # Generate content from recent signals and market data
                    content = await _generate_content(db, market_type)
                    if content:
                        page = await create_seo_page(db, market_type, content, today)
                        pages_created.append(page["slug"])
                        logger.info("seo_page_created", slug=page["slug"])

                except Exception:
                    logger.exception("seo_page_generation_failed", market=market_type)

            await db.commit()
        await engine.dispose()
        return pages_created

    pages = asyncio.run(_generate())
    return {"pages_created": pages}


async def _generate_content(db, market_type: str) -> str | None:
    """Generate analysis content from recent signals for a market type.

    Uses actual signal data rather than AI to avoid extra API costs.
    """
    from sqlalchemy import select, func
    from app.models.signal import Signal

    # Get recent active signals for this market
    result = await db.execute(
        select(Signal)
        .where(Signal.market_type == market_type, Signal.is_active.is_(True))
        .order_by(Signal.created_at.desc())
        .limit(5)
    )
    signals = result.scalars().all()

    if not signals:
        return None

    # Build content from signal data
    sections = []
    sections.append(f"## Market Overview\n\n")
    sections.append(f"Today's analysis covers {len(signals)} active signals ")
    sections.append(f"in the {market_type} market.\n\n")

    for sig in signals:
        sections.append(f"### {sig.symbol}\n\n")
        sections.append(f"**Signal**: {sig.signal_type} | ")
        sections.append(f"**Confidence**: {sig.confidence}%\n\n")
        if sig.ai_reasoning:
            sections.append(f"{sig.ai_reasoning}\n\n")
        sections.append(f"- Current Price: {sig.current_price}\n")
        sections.append(f"- Target: {sig.target_price}\n")
        sections.append(f"- Stop Loss: {sig.stop_loss}\n\n")

    sections.append(
        "\n\n*This analysis is AI-generated and should not be considered financial advice.*"
    )

    return "".join(sections)
