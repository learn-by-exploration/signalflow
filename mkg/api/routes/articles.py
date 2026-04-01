# mkg/api/routes/articles.py
"""Article ingestion pipeline endpoints."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from mkg.api.dependencies import get_container
from mkg.api.schemas import (
    ExtractArticleRequest,
    IngestArticleRequest,
    UpdateArticleStatusRequest,
)

router = APIRouter()


@router.get("/articles/stats/summary")
async def article_stats() -> dict[str, Any]:
    """Get article pipeline statistics."""
    c = get_container()
    return {
        "data": {
            "pipeline": await c.article_pipeline.get_stats(),
            "dedup": c.article_dedup.get_stats(),
        }
    }


@router.get("/articles/dlq")
async def get_dead_letters() -> dict[str, Any]:
    """Get articles in the dead letter queue."""
    c = get_container()
    items = await c.dlq.get_all()
    stats = await c.dlq.get_stats()
    return {"data": items, "meta": stats}


@router.post("/articles", status_code=201)
async def ingest_article(body: IngestArticleRequest) -> dict[str, Any]:
    """Ingest a new article into the pipeline."""
    c = get_container()

    # Dedup check
    url = body.url or ""
    dedup_result = c.article_dedup.check_article(url, body.content)
    if dedup_result.get("is_duplicate"):
        return {"data": {"duplicate": True, "reason": dedup_result.get("reason", "")}}

    # Mark as seen
    if url:
        c.article_dedup.mark_seen_url(url)
    c.article_dedup.mark_seen_content(body.content)

    article = await c.article_pipeline.ingest(body.model_dump(exclude_none=True))
    return {"data": article}


@router.get("/articles/{article_id}")
async def get_article(article_id: str) -> dict[str, Any]:
    """Get an article by ID."""
    c = get_container()
    article = await c.article_pipeline.get_article(article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"data": article}


@router.get("/articles")
async def list_articles(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    """List articles optionally filtered by status."""
    c = get_container()
    if status:
        articles = await c.article_pipeline.get_by_status(status)
    else:
        articles = await c.article_pipeline.get_pending()
    return {
        "data": articles[:limit],
        "meta": {"count": min(len(articles), limit)},
    }


@router.put("/articles/{article_id}/status")
async def update_article_status(
    article_id: str, body: UpdateArticleStatusRequest
) -> dict[str, Any]:
    """Update an article's processing status."""
    c = get_container()
    try:
        article = await c.article_pipeline.update_status(article_id, body.status)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"data": article}


@router.post("/articles/extract")
async def extract_from_article(body: ExtractArticleRequest) -> dict[str, Any]:
    """Run NER/RE extraction on article text (uses cheapest available extractor)."""
    c = get_container()
    text = body.text or body.content
    if not text:
        raise HTTPException(status_code=400, detail="text or content is required")

    # Check budget
    if not c.cost_governance.is_within_budget():
        raise HTTPException(status_code=429, detail="Monthly AI budget exhausted")

    # Use regex extractor (always available, zero cost)
    from mkg.infrastructure.llm.regex_extractor import RegexExtractor

    extractor = RegexExtractor()
    result = await extractor.extract_all(text, body.context)

    # Verify hallucinations
    verified = c.hallucination_verifier.verify_result(result, text)

    return {"data": {"extraction": result, "verification": verified}}
