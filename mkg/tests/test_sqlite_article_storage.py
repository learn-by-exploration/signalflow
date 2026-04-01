# mkg/tests/test_sqlite_article_storage.py
"""Tests for SQLiteArticleStorage — persistent article storage via aiosqlite.

Iterations 11-15: Full ArticleStorage interface compliance with persistence.
"""

import os
import tempfile
from datetime import datetime, timezone

import pytest


@pytest.fixture
async def storage():
    from mkg.infrastructure.sqlite.article_storage import SQLiteArticleStorage

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    store = SQLiteArticleStorage(db_path=db_path)
    await store.initialize()
    yield store
    await store.close()
    os.unlink(db_path)


def _article(title: str = "Test Article", **kwargs) -> dict:
    return {
        "id": kwargs.get("id", f"art-{title.replace(' ', '-').lower()}"),
        "title": title,
        "content": kwargs.get("content", f"Content for {title}"),
        "source": kwargs.get("source", "test"),
        "url": kwargs.get("url", f"https://example.com/{title.lower().replace(' ', '-')}"),
        "status": kwargs.get("status", "pending"),
        "published_at": kwargs.get(
            "published_at", datetime.now(timezone.utc).isoformat()
        ),
        "metadata": kwargs.get("metadata", {}),
    }


class TestSQLiteArticleStore:

    @pytest.mark.asyncio
    async def test_store_and_get(self, storage):
        art = _article("TSMC Revenue")
        stored = await storage.store(art)
        assert stored["id"] == art["id"]
        assert stored["title"] == "TSMC Revenue"

        found = await storage.get(art["id"])
        assert found is not None
        assert found["title"] == "TSMC Revenue"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, storage):
        result = await storage.get("nope")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_status(self, storage):
        art = _article("Test")
        await storage.store(art)
        updated = await storage.update_status(art["id"], "completed")
        assert updated is not None
        assert updated["status"] == "completed"

    @pytest.mark.asyncio
    async def test_update_status_nonexistent(self, storage):
        result = await storage.update_status("nope", "completed")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, storage):
        art = _article("ToDelete")
        await storage.store(art)
        assert await storage.delete(art["id"]) is True
        assert await storage.get(art["id"]) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, storage):
        assert await storage.delete("nope") is False

    @pytest.mark.asyncio
    async def test_list_by_status(self, storage):
        await storage.store(_article("A", status="pending"))
        await storage.store(_article("B", status="completed"))
        await storage.store(_article("C", status="pending"))
        pending = await storage.list_by_status("pending")
        assert len(pending) == 2
        completed = await storage.list_by_status("completed")
        assert len(completed) == 1

    @pytest.mark.asyncio
    async def test_list_by_status_with_limit(self, storage):
        for i in range(10):
            await storage.store(_article(f"Art-{i}", id=f"art-{i}", status="pending"))
        results = await storage.list_by_status("pending", limit=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search(self, storage):
        await storage.store(_article("TSMC Earnings Report", content="TSMC announced record Q3"))
        await storage.store(_article("NVIDIA GPU Launch", content="NVIDIA launched new GPU"))
        results = await storage.search("TSMC")
        assert len(results) >= 1
        assert any("TSMC" in r["title"] for r in results)

    @pytest.mark.asyncio
    async def test_search_in_content(self, storage):
        await storage.store(_article("Report", content="semiconductor shortage affects TSMC"))
        results = await storage.search("semiconductor")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_with_limit(self, storage):
        for i in range(20):
            await storage.store(_article(f"News {i}", id=f"news-{i}", content="market update"))
        results = await storage.search("market", limit=5)
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_count_by_status(self, storage):
        await storage.store(_article("A", id="a", status="pending"))
        await storage.store(_article("B", id="b", status="pending"))
        await storage.store(_article("C", id="c", status="completed"))
        await storage.store(_article("D", id="d", status="failed"))
        counts = await storage.count_by_status()
        assert counts["pending"] == 2
        assert counts["completed"] == 1
        assert counts["failed"] == 1


class TestSQLiteArticlePersistence:

    @pytest.mark.asyncio
    async def test_articles_persist_across_sessions(self):
        from mkg.infrastructure.sqlite.article_storage import SQLiteArticleStorage

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Session 1: store article
            store1 = SQLiteArticleStorage(db_path=db_path)
            await store1.initialize()
            await store1.store(_article("Persistent Art"))
            await store1.close()

            # Session 2: verify persistence
            store2 = SQLiteArticleStorage(db_path=db_path)
            await store2.initialize()
            found = await store2.get("art-persistent-art")
            assert found is not None
            assert found["title"] == "Persistent Art"
            await store2.close()
        finally:
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_status_persists(self):
        from mkg.infrastructure.sqlite.article_storage import SQLiteArticleStorage

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            store1 = SQLiteArticleStorage(db_path=db_path)
            await store1.initialize()
            await store1.store(_article("Status Test"))
            await store1.update_status("art-status-test", "completed")
            await store1.close()

            store2 = SQLiteArticleStorage(db_path=db_path)
            await store2.initialize()
            found = await store2.get("art-status-test")
            assert found["status"] == "completed"
            await store2.close()
        finally:
            os.unlink(db_path)
