# mkg/tests/test_article_ingestion.py
"""Tests for ArticleIngestionPipeline — ingests articles for NER/RE extraction.

R-IA1 through R-IA5: Article model, ingestion, validation, status tracking.
"""

from datetime import datetime, timezone

import pytest


class TestArticleModel:
    """Test the Article domain model."""

    def test_create_article(self):
        from mkg.domain.entities.article import Article
        article = Article(
            id="art-001",
            title="TSMC Reports Record Revenue",
            content="Taiwan Semiconductor Manufacturing Company reported...",
            source="reuters",
            url="https://reuters.com/article/tsmc-revenue",
            published_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
        )
        assert article.id == "art-001"
        assert article.title == "TSMC Reports Record Revenue"

    def test_article_has_status(self):
        from mkg.domain.entities.article import Article, ArticleStatus
        article = Article(
            id="art-001",
            title="Test",
            content="Content",
            source="test",
        )
        assert article.status == ArticleStatus.PENDING

    def test_article_status_transitions(self):
        from mkg.domain.entities.article import ArticleStatus
        assert ArticleStatus.PENDING.value == "pending"
        assert ArticleStatus.PROCESSING.value == "processing"
        assert ArticleStatus.COMPLETED.value == "completed"
        assert ArticleStatus.FAILED.value == "failed"
        assert ArticleStatus.DUPLICATE.value == "duplicate"

    def test_article_to_dict(self):
        from mkg.domain.entities.article import Article
        article = Article(
            id="art-001",
            title="Test",
            content="Content",
            source="reuters",
        )
        d = article.to_dict()
        assert d["id"] == "art-001"
        assert d["status"] == "pending"

    def test_article_from_dict(self):
        from mkg.domain.entities.article import Article
        d = {
            "id": "art-001",
            "title": "Test",
            "content": "Content",
            "source": "reuters",
            "status": "completed",
        }
        article = Article.from_dict(d)
        from mkg.domain.entities.article import ArticleStatus
        assert article.status == ArticleStatus.COMPLETED

    def test_article_title_cannot_be_empty(self):
        from mkg.domain.entities.article import Article
        with pytest.raises(ValueError):
            Article(id="art-001", title="", content="Content", source="test")

    def test_article_content_cannot_be_empty(self):
        from mkg.domain.entities.article import Article
        with pytest.raises(ValueError):
            Article(id="art-001", title="Test", content="", source="test")


class TestIngestionPipeline:
    """Test the article ingestion pipeline."""

    @pytest.fixture
    def pipeline(self):
        from mkg.domain.services.article_pipeline import ArticleIngestionPipeline
        return ArticleIngestionPipeline()

    @pytest.mark.asyncio
    async def test_ingest_article_stores_it(self, pipeline):
        result = await pipeline.ingest({
            "title": "TSMC Revenue Record",
            "content": "TSMC reported record revenue in Q1 2026...",
            "source": "reuters",
            "url": "https://reuters.com/tsmc",
        })
        assert result is not None
        assert result["id"] is not None
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_ingest_assigns_unique_ids(self, pipeline):
        r1 = await pipeline.ingest({"title": "Article 1", "content": "Content 1", "source": "test"})
        r2 = await pipeline.ingest({"title": "Article 2", "content": "Content 2", "source": "test"})
        assert r1["id"] != r2["id"]

    @pytest.mark.asyncio
    async def test_get_article_by_id(self, pipeline):
        result = await pipeline.ingest({"title": "Test", "content": "Content", "source": "test"})
        fetched = await pipeline.get_article(result["id"])
        assert fetched is not None
        assert fetched["title"] == "Test"

    @pytest.mark.asyncio
    async def test_get_pending_articles(self, pipeline):
        await pipeline.ingest({"title": "A1", "content": "C1", "source": "test"})
        await pipeline.ingest({"title": "A2", "content": "C2", "source": "test"})
        pending = await pipeline.get_pending()
        assert len(pending) == 2

    @pytest.mark.asyncio
    async def test_update_article_status(self, pipeline):
        result = await pipeline.ingest({"title": "Test", "content": "Content", "source": "test"})
        updated = await pipeline.update_status(result["id"], "processing")
        assert updated["status"] == "processing"

    @pytest.mark.asyncio
    async def test_ingest_rejects_missing_title(self, pipeline):
        with pytest.raises(ValueError, match="title"):
            await pipeline.ingest({"content": "Content", "source": "test"})

    @pytest.mark.asyncio
    async def test_ingest_rejects_missing_content(self, pipeline):
        with pytest.raises(ValueError, match="content"):
            await pipeline.ingest({"title": "Test", "source": "test"})

    @pytest.mark.asyncio
    async def test_get_articles_by_status(self, pipeline):
        r1 = await pipeline.ingest({"title": "A1", "content": "C1", "source": "test"})
        await pipeline.ingest({"title": "A2", "content": "C2", "source": "test"})
        await pipeline.update_status(r1["id"], "completed")
        completed = await pipeline.get_by_status("completed")
        assert len(completed) == 1

    @pytest.mark.asyncio
    async def test_pipeline_stats(self, pipeline):
        await pipeline.ingest({"title": "A1", "content": "C1", "source": "test"})
        r2 = await pipeline.ingest({"title": "A2", "content": "C2", "source": "test"})
        await pipeline.update_status(r2["id"], "completed")
        stats = await pipeline.get_stats()
        assert stats["total"] == 2
        assert stats["pending"] == 1
        assert stats["completed"] == 1
