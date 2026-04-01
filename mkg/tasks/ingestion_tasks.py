# mkg/tasks/ingestion_tasks.py
"""News ingestion Celery tasks.

Dummy implementations that log what would happen with real data sources.
Replace the dummy fetchers once real news APIs are wired up.
"""

import logging
from typing import Any

from mkg.tasks.celery_app import app

logger = logging.getLogger(__name__)


@app.task(name="mkg.tasks.fetch_news")
def fetch_news(sources: list[str] | None = None) -> dict[str, Any]:
    """Fetch news articles from configured sources.

    Dummy: returns a sample batch size. Real version would call
    news APIs and pass articles to the ingestion pipeline.
    """
    sources = sources or ["reuters", "sec_filings", "industry_rss"]
    logger.info("DUMMY fetch_news: would fetch from %s", sources)
    return {
        "status": "dummy",
        "sources_checked": sources,
        "articles_fetched": 0,
        "message": "Dummy fetcher — no real news API connected",
    }


@app.task(name="mkg.tasks.process_article")
def process_article(article_id: str) -> dict[str, Any]:
    """Process a single article through NER/RE extraction.

    Dummy: logs the article_id. Real version would run the
    full extraction pipeline (dedup → NER/RE → graph mutation).
    """
    logger.info("DUMMY process_article: would process article_id=%s", article_id)
    return {
        "status": "dummy",
        "article_id": article_id,
        "message": "Dummy processor — no real LLM extraction",
    }


@app.task(name="mkg.tasks.batch_extract")
def batch_extract(article_ids: list[str]) -> dict[str, Any]:
    """Batch process multiple articles.

    Dummy: returns count. Real version would parallelize extraction.
    """
    logger.info("DUMMY batch_extract: would process %d articles", len(article_ids))
    return {
        "status": "dummy",
        "count": len(article_ids),
        "message": "Dummy batch — no real extraction",
    }
