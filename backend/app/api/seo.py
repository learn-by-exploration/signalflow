"""SEO content API endpoints.

Public endpoints (no auth) for serving auto-generated market analysis pages.
Designed for search engine indexing.
"""

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.seo import get_seo_page_by_slug, list_seo_pages

router = APIRouter(prefix="/analysis", tags=["seo"])

_SLUG_RE = re.compile(r"^[a-z0-9-]{1,100}$")
VALID_MARKETS = {"stock", "crypto", "forex"}


@router.get("/", response_model=dict)
async def list_analysis_pages(
    market: str | None = Query(None),
    limit: int = Query(default=30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List available analysis pages.

    Public endpoint for sitemap generation. No auth required.
    """
    if market and market not in VALID_MARKETS:
        raise HTTPException(status_code=400, detail=f"Invalid market: {market}")
    pages = await list_seo_pages(db, market_type=market, limit=limit)
    return {"data": pages, "meta": {"count": len(pages)}}


@router.get("/{slug}", response_model=dict)
async def get_analysis_page(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get an analysis page by slug.

    Public endpoint for SEO. No auth required.
    Example: /analysis/nifty-50-analysis-2026-03-27
    """
    if not _SLUG_RE.match(slug):
        raise HTTPException(status_code=400, detail="Invalid slug format")
    page = await get_seo_page_by_slug(db, slug)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return {"data": page}
