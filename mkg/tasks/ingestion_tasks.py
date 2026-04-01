# mkg/tasks/ingestion_tasks.py
"""News ingestion Celery tasks.

Contains both dummy tasks (backward compat) and real implementations
that use ServiceFactory to wire the full pipeline.
"""

import asyncio
import logging
import os
from typing import Any

from mkg.tasks.celery_app import app

logger = logging.getLogger(__name__)


def _fetch_articles(sources: list[str] | None = None) -> list[dict[str, Any]]:
    """Fetch articles from RSS feeds (sync wrapper).

    Uses RealMultiSourceFetcher under the hood.
    Separated for testability (can be mocked in tests).
    """
    from mkg.infrastructure.external.real_news_fetcher import (
        RSSNewsFetcher,
        RealMultiSourceFetcher,
    )
    fetcher = RealMultiSourceFetcher(fetchers=[RSSNewsFetcher()])
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(fetcher.fetch())
    finally:
        loop.close()


def _get_factory(db_dir: str | None = None):
    """Create and initialize a ServiceFactory (sync wrapper)."""
    from mkg.service_factory import ServiceFactory
    factory = ServiceFactory(db_dir=db_dir)
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(factory.initialize())
    finally:
        loop.close()
    return factory


@app.task(name="mkg.tasks.fetch_news")
def fetch_news(sources: list[str] | None = None) -> dict[str, Any]:
    """Fetch news articles from configured sources and process through pipeline.

    Fetches articles from RSS feeds and runs each through the full MKG pipeline
    with provenance tracking and audit logging.
    """
    db_dir = os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
    sources = sources or ["reuters", "sec_filings", "industry_rss"]
    try:
        articles = _fetch_articles(sources)
        logger.info("Fetched %d articles from news sources", len(articles))

        if not articles:
            return {"status": "completed", "sources_checked": sources, "articles_fetched": 0}

        factory = _get_factory(db_dir)
        pipeline = factory.create_pipeline_orchestrator()
        loop = asyncio.new_event_loop()
        processed = 0
        try:
            for article in articles:
                result = loop.run_until_complete(
                    pipeline.process_article(
                        title=article.get("title", ""),
                        content=article.get("content", ""),
                        source=article.get("source", "rss"),
                        url=article.get("url"),
                    )
                )
                if result.get("status") == "completed":
                    processed += 1
        finally:
            loop.run_until_complete(factory.shutdown())
            loop.close()

        return {
            "status": "completed",
            "sources_checked": sources,
            "articles_fetched": len(articles),
            "articles_processed": processed,
        }
    except Exception as e:
        logger.error("fetch_news failed: %s", e)
        return {"status": "error", "error": str(e), "articles_fetched": 0}


def fetch_news_real(
    sources: list[str] | None = None,
    db_dir: str | None = None,
) -> dict[str, Any]:
    """Real implementation of fetch_news.

    Fetches articles from RSS feeds and processes each through the pipeline.
    """
    db_dir = db_dir or os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
    try:
        articles = _fetch_articles(sources)
        logger.info("Fetched %d articles from news sources", len(articles))

        if not articles:
            return {"status": "completed", "articles_fetched": 0}

        # Process each article through the pipeline
        factory = _get_factory(db_dir)
        pipeline = factory.create_pipeline_orchestrator()
        loop = asyncio.new_event_loop()
        processed = 0
        try:
            for article in articles:
                result = loop.run_until_complete(
                    pipeline.process_article(
                        title=article.get("title", ""),
                        content=article.get("content", ""),
                        source=article.get("source", "rss"),
                        url=article.get("url"),
                    )
                )
                if result.get("status") == "completed":
                    processed += 1
        finally:
            loop.run_until_complete(factory.shutdown())
            loop.close()

        return {
            "status": "completed",
            "articles_fetched": len(articles),
            "articles_processed": processed,
        }
    except Exception as e:
        logger.error("fetch_news_real failed: %s", e)
        return {"status": "error", "error": str(e), "articles_fetched": 0}


def process_article_real(
    title: str,
    content: str,
    source: str = "unknown",
    url: str | None = None,
    db_dir: str | None = None,
) -> dict[str, Any]:
    """Real implementation of process_article.

    Runs a single article through the full MKG pipeline with provenance
    and audit wired.
    """
    db_dir = db_dir or os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
    factory = _get_factory(db_dir)
    pipeline = factory.create_pipeline_orchestrator()
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            pipeline.process_article(
                title=title,
                content=content,
                source=source,
                url=url,
            )
        )
        return result
    except Exception as e:
        logger.error("process_article_real failed: %s", e)
        return {"status": "error", "error": str(e)}
    finally:
        loop.run_until_complete(factory.shutdown())
        loop.close()


@app.task(name="mkg.tasks.process_article")
def process_article(
    title: str = "",
    content: str = "",
    source: str = "unknown",
    url: str | None = None,
    article_id: str | None = None,
) -> dict[str, Any]:
    """Process a single article through the full MKG pipeline.

    Runs dedup → extraction → verification → graph mutation → propagation.
    Provenance and audit are recorded at each step.
    """
    db_dir = os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
    # Support legacy call with just article_id (look up from storage)
    if article_id and not content:
        logger.info("process_article called with article_id=%s but no content; skipping", article_id)
        return {"status": "skipped", "article_id": article_id, "reason": "no content provided"}

    factory = _get_factory(db_dir)
    pipeline = factory.create_pipeline_orchestrator()
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            pipeline.process_article(
                title=title,
                content=content,
                source=source,
                url=url,
            )
        )
        return result
    except Exception as e:
        logger.error("process_article failed: %s", e)
        return {"status": "error", "error": str(e)}
    finally:
        loop.run_until_complete(factory.shutdown())
        loop.close()


@app.task(name="mkg.tasks.batch_extract")
def batch_extract(articles: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Batch process multiple articles through the MKG pipeline.

    Args:
        articles: List of article dicts with title, content, source, url keys.
    """
    if not articles:
        return {"status": "completed", "count": 0, "processed": 0}

    db_dir = os.environ.get("MKG_DB_DIR", "/tmp/mkg_data")
    factory = _get_factory(db_dir)
    pipeline = factory.create_pipeline_orchestrator()
    loop = asyncio.new_event_loop()
    processed = 0
    errors = 0
    try:
        for article in articles:
            try:
                result = loop.run_until_complete(
                    pipeline.process_article(
                        title=article.get("title", ""),
                        content=article.get("content", ""),
                        source=article.get("source", "unknown"),
                        url=article.get("url"),
                    )
                )
                if result.get("status") == "completed":
                    processed += 1
            except Exception as e:
                logger.error("batch_extract article error: %s", e)
                errors += 1
    finally:
        loop.run_until_complete(factory.shutdown())
        loop.close()

    return {
        "status": "completed",
        "count": len(articles),
        "processed": processed,
        "errors": errors,
    }
