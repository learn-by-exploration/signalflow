# mkg/tests/test_backpressure.py
"""Tests for BackpressureManager — rate limiting and flow control.

R-BP1 through R-BP5: Queue depth limits, throttling, shed load
under pressure, and recovery.
"""

import pytest


class TestBackpressureManager:

    @pytest.fixture
    def manager(self):
        from mkg.domain.services.backpressure import BackpressureManager
        return BackpressureManager(max_queue_depth=10, throttle_threshold=0.8)

    def test_initial_state_is_normal(self, manager):
        assert manager.state == "normal"

    def test_accept_under_capacity(self, manager):
        assert manager.can_accept() is True

    def test_enqueue_increments_depth(self, manager):
        manager.enqueue("item-1")
        assert manager.queue_depth == 1

    def test_dequeue_decrements_depth(self, manager):
        manager.enqueue("item-1")
        manager.enqueue("item-2")
        item = manager.dequeue()
        assert item == "item-1"
        assert manager.queue_depth == 1

    def test_throttle_at_threshold(self, manager):
        for i in range(8):  # 80% of max_queue_depth=10
            manager.enqueue(f"item-{i}")
        assert manager.state == "throttled"

    def test_reject_when_full(self, manager):
        for i in range(10):
            manager.enqueue(f"item-{i}")
        assert manager.can_accept() is False
        assert manager.state == "shedding"

    def test_shed_returns_dropped_items(self, manager):
        for i in range(10):
            manager.enqueue(f"item-{i}")
        # Try to enqueue when full
        accepted = manager.try_enqueue("overflow-item")
        assert accepted is False

    def test_recovery_after_drain(self, manager):
        for i in range(10):
            manager.enqueue(f"item-{i}")
        assert manager.state == "shedding"
        # Drain all
        for _ in range(10):
            manager.dequeue()
        assert manager.state == "normal"

    def test_get_stats(self, manager):
        manager.enqueue("item-1")
        manager.enqueue("item-2")
        stats = manager.get_stats()
        assert stats["queue_depth"] == 2
        assert stats["max_queue_depth"] == 10
        assert stats["utilization"] == 0.2
        assert stats["state"] == "normal"

    def test_dequeue_empty_returns_none(self, manager):
        result = manager.dequeue()
        assert result is None
