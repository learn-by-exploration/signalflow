# mkg/tasks/ingestion_tasks.py
"""News ingestion Celery tasks.

Dummy implementations that log what would happen with real data sources.
Real implementations (*_real functions) use actual pipeline services.
"""

import asyncio
import logging
import os
import uuid
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


def _fetch_articles() -> list[dict[str, Any]]:
    """Fetch articles from configured RSS feeds.

    Hook for real news fetcher. Tests mock this function.
    """
    from mkg.infrastructure.external.real_news_fetcher import RSSNewsFetcher

    fetcher = RSSNewsFetcher()
    feeds = fetcher.get_default_feeds()
    articles: list[dict[str, Any]] = []
    for feed in feeds:
        try:
            fetched = fetcher.fetch(feed["url"])
            articles.extend(fetched)
        except Exception as exc:
            logger.warning("Failed to fetch %s: %s", feed["url"], exc)
    return articles


def fetch_news_real(db_dir: str | None = None) -> dict[str, Any]:
    """Fetch news articles using real RSS fetcher.

    Args:
        db_dir: Directory for SQLite databases. Uses MKG_DB_DIR env var if not provided.

    Returns:
        Result dict with status and articles_fetched count.
    """
    db_dir = db_dir or os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
    os.makedirs(db_dir, exist_ok=True)

    try:
        articles = _fetch_articles()
        return {
            "status": "completed",
            "articles_fetched": len(articles),
        }
    except Exception as exc:
        logger.error("fetch_news_real failed: %s", exc)
        return {
            "status": "error",
            "error": str(exc),
        }


def process_article_real(
    title: str,
    content: str,
    source: str,
    db_dir: str | None = None,
    url: str | None = None,
) -> dict[str, Any]:
    """Process a single article through the real extraction pipeline.

    Args:
        title: Article title.
        content: Article body text.
        source: Source identifier (e.g., 'reuters', 'test').
        db_dir: Directory for SQLite databases.
        url: Optional article URL.

    Returns:
        Result dict with status, article_id, entities_created, provenance_chain.
    """
    db_dir = db_dir or os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
    os.makedirs(db_dir, exist_ok=True)

    if not content or not content.strip():
        return {"status": "failed", "error": "Empty content"}

    try:
        from mkg.domain.services.audit_logger import AuditAction
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger
        from mkg.infrastructure.persistent.provenance_tracker import PersistentProvenanceTracker
        from mkg.infrastructure.llm.regex_extractor import RegexExtractor

        article_id = str(uuid.uuid4())
        audit = PersistentAuditLogger(db_path=os.path.join(db_dir, "audit.db"))
        provenance = PersistentProvenanceTracker(db_path=os.path.join(db_dir, "provenance.db"))

        # Extract entities using regex extractor
        extractor = RegexExtractor()
        loop = asyncio.new_event_loop()
        try:
            entities = loop.run_until_complete(extractor.extract_entities(content))
        finally:
            loop.close()

        # Record provenance
        provenance.record_step(
            article_id=article_id,
            step="extraction",
            inputs={"title": title, "source": source, "url": url or ""},
            outputs={"entities_found": len(entities)},
        )

        # Record audit entries for created entities
        for entity in entities:
            audit.log(
                action=AuditAction.ENTITY_CREATED,
                actor="pipeline:extraction",
                target_id=entity.get("id", str(uuid.uuid4())),
                target_type="entity",
                details={"name": entity.get("name", ""), "article_id": article_id},
            )

        return {
            "status": "completed",
            "article_id": article_id,
            "entities_created": len(entities),
            "provenance_chain": [article_id],
        }
    except Exception as exc:
        logger.error("process_article_real failed: %s", exc)
        return {"status": "error", "error": str(exc)}
