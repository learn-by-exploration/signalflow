"""Tests for the circuit breaker pattern (H5).

Verifies that the circuit breaker correctly tracks failures, opens
the circuit after threshold, and recovers after timeout.
"""

import time
from unittest.mock import MagicMock


class TestCircuitBreaker:
    """Test CircuitBreaker state machine."""

    def _make_breaker(self, name="test", failure_threshold=3, recovery_timeout=10):
        """Create a circuit breaker with mocked Redis."""
        from app.services.circuit_breaker import CircuitBreaker

        breaker = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )

        # Create a mock Redis that behaves like a real one
        mock_redis = MagicMock()
        store = {}

        def mock_get(key):
            return store.get(key)

        def mock_set(key, value, ex=None):
            store[key] = value

        def mock_delete(*keys):
            for key in keys:
                store.pop(key, None)

        def mock_incr(key):
            val = int(store.get(key, "0")) + 1
            store[key] = str(val)
            return val

        def mock_exists(key):
            return key in store

        def mock_expire(key, ttl):
            pass  # No-op for tests

        mock_redis.get = mock_get
        mock_redis.set = mock_set
        mock_redis.delete = mock_delete
        mock_redis.incr = mock_incr
        mock_redis.exists = mock_exists
        mock_redis.expire = mock_expire

        breaker._redis = mock_redis
        return breaker, store

    def test_initial_state_is_closed(self):
        breaker, _ = self._make_breaker()
        assert breaker.is_open() is False
        assert breaker.get_state() == "closed"

    def test_circuit_opens_after_threshold_failures(self):
        breaker, _ = self._make_breaker(failure_threshold=3)
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.is_open() is False  # Still below threshold

        breaker.record_failure()  # Hits threshold
        assert breaker.is_open() is True
        assert breaker.get_state() == "open"

    def test_success_resets_failures(self):
        breaker, store = self._make_breaker(failure_threshold=3)
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()  # Reset

        # Should be closed again
        assert breaker.is_open() is False
        assert breaker.get_state() == "closed"

        # Need 3 more fresh failures to open
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.is_open() is False  # Only 2 since reset

    def test_circuit_half_open_after_recovery_timeout(self):
        breaker, store = self._make_breaker(failure_threshold=2, recovery_timeout=5)
        breaker.record_failure()
        breaker.record_failure()  # Opens circuit

        assert breaker.is_open() is True

        # Simulate time passing by manipulating the stored timestamp
        store[f"circuit:{breaker.name}:opened_at"] = str(time.time() - 10)
        assert breaker.is_open() is False  # Half-open
        assert breaker.get_state() == "half_open"

    def test_redis_unavailable_fails_open(self):
        """If Redis is down, circuit breaker should allow calls through."""
        import redis as redis_mod

        from app.services.circuit_breaker import CircuitBreaker

        breaker = CircuitBreaker("test_redis_fail", failure_threshold=2, recovery_timeout=5)
        mock_redis = MagicMock()
        mock_redis.get.side_effect = redis_mod.ConnectionError("Connection refused")
        breaker._redis = mock_redis

        # Should not raise, should return False (allow calls)
        assert breaker.is_open() is False

    def test_record_failure_tolerates_redis_down(self):
        """record_failure should not raise if Redis is unavailable."""
        import redis as redis_mod

        from app.services.circuit_breaker import CircuitBreaker

        breaker = CircuitBreaker("test_fail_redis", failure_threshold=2, recovery_timeout=5)
        mock_redis = MagicMock()
        mock_redis.incr.side_effect = redis_mod.ConnectionError("Connection refused")
        breaker._redis = mock_redis

        # Should not raise
        breaker.record_failure()

    def test_record_success_tolerates_redis_down(self):
        """record_success should not raise if Redis is unavailable."""
        import redis as redis_mod

        from app.services.circuit_breaker import CircuitBreaker

        breaker = CircuitBreaker("test_success_redis", failure_threshold=2, recovery_timeout=5)
        mock_redis = MagicMock()
        mock_redis.delete.side_effect = redis_mod.ConnectionError("Connection refused")
        breaker._redis = mock_redis

        # Should not raise
        breaker.record_success()
