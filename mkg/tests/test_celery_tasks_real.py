# mkg/tests/test_celery_tasks_real.py
"""Tests for real MKG Celery tasks.

Iterations 26-30: Real ingestion, analysis, and health check tasks.
"""

import os
import tempfile

import pytest


class _MockResponse:
    """Mock httpx response for RSS fetcher."""

    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text


_SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Financial News</title>
    <item>
      <title>TSMC Reports Record Revenue</title>
      <link>https://news.example.com/tsmc</link>
      <description>TSMC posted record quarterly revenue driven by AI chip demand from NVIDIA.</description>
      <pubDate>Tue, 01 Apr 2026 08:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""


class TestFetchAndProcessTask:

    @pytest.mark.asyncio
    async def test_fetch_and_process_pipeline(self):
        """Integration: fetch → process through pipeline."""
        from mkg.service_factory import ServiceFactory
        from mkg.infrastructure.external.real_news_fetcher import RSSNewsFetcher

        with tempfile.TemporaryDirectory() as tmpdir:
            factory = ServiceFactory(db_dir=tmpdir)
            await factory.initialize()

            try:
                # Set up mocked RSS fetcher
                rss = RSSNewsFetcher(feed_urls=["https://example.com/feed.xml"])

                async def mock_get(url, **kwargs):
                    return _MockResponse(200, text=_SAMPLE_RSS)

                rss._http_get = mock_get

                # Fetch articles
                articles = await rss.fetch()
                assert len(articles) == 1

                # Process through pipeline
                pipeline = factory.create_pipeline_orchestrator()
                art = articles[0]
                result = await pipeline.process_article(
                    title=art["title"],
                    content=art["content"],
                    source=art["source"],
                    url=art["url"],
                )
                assert result["status"] == "completed"
                assert result["entities_created"] >= 0

            finally:
                await factory.shutdown()


class TestPipelineWithPersistence:

    @pytest.mark.asyncio
    async def test_entities_persist_after_processing(self):
        """Entities created by pipeline should persist in SQLite."""
        from mkg.service_factory import ServiceFactory

        with tempfile.TemporaryDirectory() as tmpdir:
            # Session 1: process article
            factory1 = ServiceFactory(db_dir=tmpdir)
            await factory1.initialize()
            pipeline = factory1.create_pipeline_orchestrator()
            await pipeline.process_article(
                title="TSMC fab update",
                content="TSMC semiconductor manufacturing in Taiwan expands operations.",
                source="test",
            )
            # Check entities were created
            entities = await factory1.graph_storage.find_entities()
            count1 = len(entities)
            await factory1.shutdown()

            # Session 2: verify persistence
            factory2 = ServiceFactory(db_dir=tmpdir)
            await factory2.initialize()
            entities = await factory2.graph_storage.find_entities()
            assert len(entities) == count1
            assert len(entities) > 0
            await factory2.shutdown()


class TestServiceFactory:

    @pytest.mark.asyncio
    async def test_initialize_creates_databases(self):
        from mkg.service_factory import ServiceFactory

        with tempfile.TemporaryDirectory() as tmpdir:
            factory = ServiceFactory(db_dir=tmpdir)
            await factory.initialize()

            assert os.path.exists(os.path.join(tmpdir, "graph.db"))
            assert os.path.exists(os.path.join(tmpdir, "articles.db"))

            await factory.shutdown()

    @pytest.mark.asyncio
    async def test_create_extraction_orchestrator(self):
        from mkg.service_factory import ServiceFactory

        with tempfile.TemporaryDirectory() as tmpdir:
            factory = ServiceFactory(db_dir=tmpdir)
            await factory.initialize()

            orch = factory.create_extraction_orchestrator()
            assert orch is not None

            await factory.shutdown()

    @pytest.mark.asyncio
    async def test_create_pipeline_orchestrator(self):
        from mkg.service_factory import ServiceFactory

        with tempfile.TemporaryDirectory() as tmpdir:
            factory = ServiceFactory(db_dir=tmpdir)
            await factory.initialize()

            pipeline = factory.create_pipeline_orchestrator()
            assert pipeline is not None

            await factory.shutdown()

    @pytest.mark.asyncio
    async def test_create_news_fetcher(self):
        from mkg.service_factory import ServiceFactory

        with tempfile.TemporaryDirectory() as tmpdir:
            factory = ServiceFactory(db_dir=tmpdir)
            await factory.initialize()

            fetcher = factory.create_news_fetcher()
            assert fetcher is not None

            await factory.shutdown()

    @pytest.mark.asyncio
    async def test_health_check(self):
        from mkg.service_factory import ServiceFactory

        with tempfile.TemporaryDirectory() as tmpdir:
            factory = ServiceFactory(db_dir=tmpdir)
            await factory.initialize()

            health = await factory.graph_storage.health_check()
            assert health["status"] == "healthy"
            assert health["backend"] == "sqlite"

            await factory.shutdown()
