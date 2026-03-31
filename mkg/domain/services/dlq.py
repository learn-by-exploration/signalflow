# mkg/domain/services/dlq.py
"""DeadLetterQueue — stores failed processing items for retry.

R-IA4: Failed extractions go to DLQ with retry logic.
"""

from datetime import datetime, timezone
from typing import Any, Optional


class DeadLetterQueue:
    """In-memory dead letter queue for failed pipeline items."""

    def __init__(self, max_retries: int = 3) -> None:
        self._items: dict[str, dict[str, Any]] = {}
        self._max_retries = max_retries

    async def add(
        self, item_id: str, reason: str, metadata: dict[str, Any]
    ) -> None:
        """Add a failed item to the DLQ."""
        self._items[item_id] = {
            "item_id": item_id,
            "reason": reason,
            "metadata": metadata,
            "retry_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    async def increment_retry(self, item_id: str) -> None:
        """Increment retry count for an item."""
        if item_id in self._items:
            self._items[item_id]["retry_count"] += 1

    async def is_exhausted(self, item_id: str) -> bool:
        """Check if an item has exceeded max retries."""
        item = self._items.get(item_id)
        if not item:
            return False
        return item["retry_count"] >= self._max_retries

    async def get_retriable(self) -> list[dict[str, Any]]:
        """Get items that can still be retried."""
        return [
            item for item in self._items.values()
            if item["retry_count"] < self._max_retries
        ]

    async def get_all(self) -> list[dict[str, Any]]:
        """Get all DLQ items."""
        return list(self._items.values())

    async def remove(self, item_id: str) -> None:
        """Remove an item from the DLQ (after successful reprocessing)."""
        self._items.pop(item_id, None)

    async def get_stats(self) -> dict[str, int]:
        """Get DLQ statistics."""
        total = len(self._items)
        exhausted = sum(
            1 for item in self._items.values()
            if item["retry_count"] >= self._max_retries
        )
        return {
            "total": total,
            "retriable": total - exhausted,
            "exhausted": exhausted,
        }
