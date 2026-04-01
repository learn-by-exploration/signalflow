# mkg/tests/test_circuit_breaker.py
"""Tests for CircuitBreaker pattern implementation.

Verifies:
1. Circuit starts closed and allows requests
2. Circuit opens after failure_threshold consecutive failures
3. Circuit transitions to half-open after recovery_timeout
4. Circuit closes again after success_threshold successes in half-open
5. Registry manages named circuit breakers
"""

import time

import pytest

from mkg.domain.services.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitState,
)


class TestCircuitBreaker:
    """Core circuit breaker state machine."""

    def test_initial_state_is_closed(self):
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED
        assert cb.is_closed
        assert not cb.is_open

    def test_allows_requests_when_closed(self):
        cb = CircuitBreaker("test")
        assert cb.allow_request() is True

    def test_stays_closed_under_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True

    def test_opens_at_failure_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.is_open
        assert cb.allow_request() is False

    def test_rejects_requests_when_open(self):
        cb = CircuitBreaker("test", failure_threshold=1)
        cb.record_failure()
        assert cb.allow_request() is False

    def test_transitions_to_half_open_after_timeout(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.01)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.allow_request() is True

    def test_closes_after_success_in_half_open(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.01, success_threshold=2)
        cb.record_failure()
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.HALF_OPEN  # Need 2 successes
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_reopens_on_failure_in_half_open(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.01)
        cb.record_failure()
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        # After success, failure count resets
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED  # Still under threshold

    def test_manual_reset(self):
        cb = CircuitBreaker("test", failure_threshold=1)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True

    def test_get_status(self):
        cb = CircuitBreaker("test_api", failure_threshold=5)
        cb.record_failure()
        status = cb.get_status()
        assert status["name"] == "test_api"
        assert status["state"] == "closed"
        assert status["failure_count"] == 1
        assert status["failure_threshold"] == 5


class TestCircuitBreakerRegistry:
    """Registry for named circuit breakers."""

    def test_get_or_create_new(self):
        registry = CircuitBreakerRegistry()
        cb = registry.get_or_create("claude_api")
        assert cb.name == "claude_api"

    def test_get_or_create_reuses(self):
        registry = CircuitBreakerRegistry()
        cb1 = registry.get_or_create("news_api")
        cb2 = registry.get_or_create("news_api")
        assert cb1 is cb2

    def test_get_all_status(self):
        registry = CircuitBreakerRegistry()
        registry.get_or_create("api1")
        registry.get_or_create("api2")
        statuses = registry.get_all_status()
        assert len(statuses) == 2
        names = {s["name"] for s in statuses}
        assert names == {"api1", "api2"}

    def test_reset_all(self):
        registry = CircuitBreakerRegistry()
        cb1 = registry.get_or_create("api1", failure_threshold=1)
        cb2 = registry.get_or_create("api2", failure_threshold=1)
        cb1.record_failure()
        cb2.record_failure()
        assert cb1.is_open
        assert cb2.is_open
        registry.reset_all()
        assert cb1.is_closed
        assert cb2.is_closed
