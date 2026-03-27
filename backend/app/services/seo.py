"""SEO content generation and serving.

Auto-generates daily market analysis pages from AI morning briefs.
Serves them via public API endpoints for search engine indexing.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Slug generation config
MARKET_SLUG_PREFIX = {
    "stock": "nifty-50-analysis",
    "crypto": "crypto-analysis",
    "forex": "forex-analysis",
}


def generate_slug(market_type: str, date: datetime) -> str:
    """Generate a URL-friendly slug for an SEO page.

    Args:
        market_type: stock, crypto, or forex.
        date: Page date.

    Returns:
        Slug like 'nifty-50-analysis-2026-03-27'.
    """
    prefix = MARKET_SLUG_PREFIX.get(market_type, f"{market_type}-analysis")
    date_str = date.strftime("%Y-%m-%d")
    return f"{prefix}-{date_str}"


def generate_meta_description(title: str, content: str) -> str:
    """Generate a meta description from page content.

    Args:
        title: Page title.
        content: Full page content.

    Returns:
        SEO meta description (max 160 chars).
    """
    # Take first sentence of content
    first_sentence = content.split(".")[0] + "." if "." in content else content[:150]
    desc = first_sentence[:157] + "..." if len(first_sentence) > 160 else first_sentence
    return desc


def generate_page_title(market_type: str, date: datetime) -> str:
    """Generate SEO-optimized page title.

    Args:
        market_type: stock, crypto, or forex.
        date: Page date.

    Returns:
        Title like 'NIFTY 50 Analysis Today - 27 March 2026 | SignalFlow AI'.
    """
    titles = {
        "stock": "NIFTY 50 Analysis Today",
        "crypto": "Crypto Market Analysis Today",
        "forex": "Forex Analysis Today",
    }
    base = titles.get(market_type, f"{market_type.title()} Analysis Today")
    date_str = date.strftime("%d %B %Y")
    return f"{base} - {date_str} | SignalFlow AI"


async def create_seo_page(
    db: AsyncSession,
    market_type: str,
    content: str,
    date: datetime | None = None,
) -> dict[str, Any]:
    """Create an SEO page from morning brief content.

    Args:
        db: Database session.
        market_type: stock, crypto, or forex.
        content: Morning brief text content.
        date: Page date (defaults to today).

    Returns:
        Created page dict.
    """
    from app.models.seo_page import SeoPage

    if date is None:
        date = datetime.now(timezone.utc)

    slug = generate_slug(market_type, date)
    title = generate_page_title(market_type, date)
    meta_desc = generate_meta_description(title, content)

    page = SeoPage(
        slug=slug,
        title=title,
        content=content,
        market_type=market_type,
        meta_description=meta_desc,
        page_date=date,
        is_published=True,
    )

    db.add(page)
    await db.flush()

    return {
        "id": page.id,
        "slug": page.slug,
        "title": page.title,
        "meta_description": page.meta_description,
        "market_type": page.market_type,
        "page_date": date.isoformat(),
    }


async def get_seo_page_by_slug(db: AsyncSession, slug: str) -> dict[str, Any] | None:
    """Fetch a published SEO page by slug.

    Args:
        db: Database session.
        slug: URL slug.

    Returns:
        Page dict or None if not found.
    """
    from app.models.seo_page import SeoPage

    result = await db.execute(
        select(SeoPage).where(SeoPage.slug == slug, SeoPage.is_published.is_(True))
    )
    page = result.scalars().first()
    if not page:
        return None

    return {
        "id": page.id,
        "slug": page.slug,
        "title": page.title,
        "content": page.content,
        "meta_description": page.meta_description,
        "market_type": page.market_type,
        "page_date": page.page_date.isoformat() if page.page_date else None,
        "created_at": page.created_at.isoformat() if page.created_at else None,
    }


async def list_seo_pages(
    db: AsyncSession,
    market_type: str | None = None,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """List published SEO pages for sitemap generation.

    Args:
        db: Database session.
        market_type: Optional filter.
        limit: Max pages to return.

    Returns:
        List of page summary dicts.
    """
    from app.models.seo_page import SeoPage

    query = select(SeoPage).where(SeoPage.is_published.is_(True))
    if market_type:
        query = query.where(SeoPage.market_type == market_type)
    query = query.order_by(SeoPage.page_date.desc()).limit(limit)

    result = await db.execute(query)
    pages = result.scalars().all()

    return [
        {
            "slug": p.slug,
            "title": p.title,
            "market_type": p.market_type,
            "page_date": p.page_date.isoformat() if p.page_date else None,
        }
        for p in pages
    ]
