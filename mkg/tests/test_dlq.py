# mkg/tests/test_dlq.py
"""Tests for DeadLetterQueue — stores failed processing items for retry."""

from datetime import datetime, timezone

import pytest


class TestDeadLetterQueue:

    @pytest.fixture
    def dlq(self):
        from mkg.domain.services.dlq import DeadLetterQueue
        return DeadLetterQueue(max_retries=3)

    @pytest.mark.asyncio
    async def test_add_failed_item(self, dlq):
        await dlq.add("art-001", "extraction_failed", {"error": "timeout"})
        items = await dlq.get_all()
        assert len(items) == 1
        assert items[0]["item_id"] == "art-001"

    @pytest.mark.asyncio
    async def test_item_has_retry_count(self, dlq):
        await dlq.add("art-001", "extraction_failed", {})
        items = await dlq.get_all()
        assert items[0]["retry_count"] == 0

    @pytest.mark.asyncio
    async def test_retry_increments_count(self, dlq):
        await dlq.add("art-001", "extraction_failed", {})
        await dlq.increment_retry("art-001")
        items = await dlq.get_all()
        assert items[0]["retry_count"] == 1

    @pytest.mark.asyncio
    async def test_item_exceeds_max_retries(self, dlq):
        await dlq.add("art-001", "extraction_failed", {})
        for _ in range(3):
            await dlq.increment_retry("art-001")
        assert await dlq.is_exhausted("art-001") is True

    @pytest.mark.asyncio
    async def test_get_retriable_items(self, dlq):
        await dlq.add("art-001", "fail1", {})
        await dlq.add("art-002", "fail2", {})
        for _ in range(3):
            await dlq.increment_retry("art-002")
        retriable = await dlq.get_retriable()
        assert len(retriable) == 1
        assert retriable[0]["item_id"] == "art-001"

    @pytest.mark.asyncio
    async def test_remove_item(self, dlq):
        await dlq.add("art-001", "fail", {})
        await dlq.remove("art-001")
        items = await dlq.get_all()
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_stats(self, dlq):
        await dlq.add("art-001", "fail1", {})
        await dlq.add("art-002", "fail2", {})
        for _ in range(3):
            await dlq.increment_retry("art-002")
        stats = await dlq.get_stats()
        assert stats["total"] == 2
        assert stats["retriable"] == 1
        assert stats["exhausted"] == 1

    @pytest.mark.asyncio
    async def test_increment_retry_nonexistent_item(self, dlq):
        """Incrementing retry on nonexistent item should be a no-op."""
        await dlq.increment_retry("nonexistent")
        items = await dlq.get_all()
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_is_exhausted_nonexistent_returns_false(self, dlq):
        assert await dlq.is_exhausted("nonexistent") is False

    @pytest.mark.asyncio
    async def test_remove_nonexistent_is_noop(self, dlq):
        await dlq.remove("nonexistent")
        items = await dlq.get_all()
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_stats_empty_queue(self, dlq):
        stats = await dlq.get_stats()
        assert stats["total"] == 0
        assert stats["retriable"] == 0
        assert stats["exhausted"] == 0

    @pytest.mark.asyncio
    async def test_add_preserves_metadata(self, dlq):
        meta = {"error": "timeout", "retry_after": 60}
        await dlq.add("art-001", "extraction_failed", meta)
        items = await dlq.get_all()
        assert items[0]["metadata"] == meta

    @pytest.mark.asyncio
    async def test_item_has_created_at_timestamp(self, dlq):
        await dlq.add("art-001", "fail", {})
        items = await dlq.get_all()
        assert "created_at" in items[0]

    @pytest.mark.asyncio
    async def test_add_duplicate_replaces(self, dlq):
        await dlq.add("art-001", "fail1", {"attempt": 1})
        await dlq.add("art-001", "fail2", {"attempt": 2})
        items = await dlq.get_all()
        assert len(items) == 1
        assert items[0]["reason"] == "fail2"
