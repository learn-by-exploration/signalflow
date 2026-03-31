# mkg/domain/services/backpressure.py
"""BackpressureManager — rate limiting and flow control for the MKG pipeline.

R-BP1 through R-BP5: Manages queue depth, throttling, load shedding,
and recovery to prevent pipeline overwhelm under high article volume.
"""

from collections import deque
from typing import Any, Optional


class BackpressureManager:
    """Flow control with three states: normal, throttled, shedding.

    - normal: Queue utilization below throttle_threshold.
    - throttled: Utilization at or above threshold but below max.
    - shedding: Queue is full, new items are rejected.

    Attributes:
        max_queue_depth: Maximum items in the queue.
        throttle_threshold: Fraction [0, 1] at which throttling begins.
    """

    def __init__(
        self,
        max_queue_depth: int = 100,
        throttle_threshold: float = 0.8,
    ) -> None:
        if max_queue_depth <= 0:
            raise ValueError(f"max_queue_depth must be > 0, got {max_queue_depth}")
        if not 0.0 <= throttle_threshold <= 1.0:
            raise ValueError(f"throttle_threshold must be in [0, 1], got {throttle_threshold}")
        self.max_queue_depth = max_queue_depth
        self.throttle_threshold = throttle_threshold
        self._queue: deque[Any] = deque()

    @property
    def queue_depth(self) -> int:
        """Current number of items in the queue."""
        return len(self._queue)

    @property
    def utilization(self) -> float:
        """Current queue utilization [0, 1]."""
        if self.max_queue_depth == 0:
            return 1.0
        return self.queue_depth / self.max_queue_depth

    @property
    def state(self) -> str:
        """Current backpressure state."""
        if self.queue_depth >= self.max_queue_depth:
            return "shedding"
        if self.utilization >= self.throttle_threshold:
            return "throttled"
        return "normal"

    def can_accept(self) -> bool:
        """Check if the queue can accept new items."""
        return self.queue_depth < self.max_queue_depth

    def enqueue(self, item: Any) -> None:
        """Add an item to the queue.

        Does not reject — use try_enqueue for safe enqueue with rejection.
        """
        self._queue.append(item)

    def try_enqueue(self, item: Any) -> bool:
        """Try to enqueue an item, rejecting if full.

        Args:
            item: Item to enqueue.

        Returns:
            True if accepted, False if rejected (queue full).
        """
        if not self.can_accept():
            return False
        self._queue.append(item)
        return True

    def dequeue(self) -> Optional[Any]:
        """Remove and return the oldest item, or None if empty."""
        if self._queue:
            return self._queue.popleft()
        return None

    def get_stats(self) -> dict[str, Any]:
        """Get queue statistics.

        Returns:
            Dict with queue_depth, max_queue_depth, utilization, and state.
        """
        return {
            "queue_depth": self.queue_depth,
            "max_queue_depth": self.max_queue_depth,
            "utilization": round(self.utilization, 4),
            "state": self.state,
        }
