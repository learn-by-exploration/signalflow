# mkg/tests/test_article_storage.py
"""Tests for ArticleStorage — persistent article storage interface + in-memory impl.

R-AS1 through R-AS5: CRUD for articles, search, status tracking.
"""

import pytest
from datetime import datetime, timezone


class TestArticleStorage:

    @pytest.fixture
    def storage(self):
        from mkg.infrastructure.in_memory.article_storage import InMemoryArticleStorage
        return InMemoryArticleStorage()

    @pytest.mark.asyncio
    async def test_store_article(self, storage):
        article = {
            "id": "art-1",
            "url": "https://example.com/news/1",
            "title": "TSMC builds new factory",
            "content": "TSMC announced...",
            "status": "pending",
        }
        result = await storage.store(article)
        assert result["id"] == "art-1"

    @pytest.mark.asyncio
    async def test_get_article(self, storage):
        await storage.store({"id": "art-1", "title": "Test", "status": "pending"})
        article = await storage.get("art-1")
        assert article is not None
        assert article["title"] == "Test"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, storage):
        article = await storage.get("nonexistent")
        assert article is None

    @pytest.mark.asyncio
    async def test_update_status(self, storage):
        await storage.store({"id": "art-1", "title": "Test", "status": "pending"})
        result = await storage.update_status("art-1", "completed")
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_list_by_status(self, storage):
        await storage.store({"id": "art-1", "title": "A", "status": "pending"})
        await storage.store({"id": "art-2", "title": "B", "status": "completed"})
        await storage.store({"id": "art-3", "title": "C", "status": "pending"})
        pending = await storage.list_by_status("pending")
        assert len(pending) == 2

    @pytest.mark.asyncio
    async def test_search_by_keyword(self, storage):
        await storage.store({"id": "art-1", "title": "TSMC factory fire", "content": "Fire at the TSMC plant", "status": "completed"})
        await storage.store({"id": "art-2", "title": "NVIDIA earnings", "content": "NVIDIA reported", "status": "completed"})
        results = await storage.search("TSMC")
        assert len(results) == 1
        assert results[0]["id"] == "art-1"

    @pytest.mark.asyncio
    async def test_delete_article(self, storage):
        await storage.store({"id": "art-1", "title": "Test", "status": "pending"})
        deleted = await storage.delete("art-1")
        assert deleted is True
        assert await storage.get("art-1") is None

    @pytest.mark.asyncio
    async def test_count_by_status(self, storage):
        await storage.store({"id": "art-1", "title": "A", "status": "pending"})
        await storage.store({"id": "art-2", "title": "B", "status": "pending"})
        await storage.store({"id": "art-3", "title": "C", "status": "completed"})
        counts = await storage.count_by_status()
        assert counts["pending"] == 2
        assert counts["completed"] == 1
