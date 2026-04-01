# mkg/domain/services/circuit_breaker.py
"""CircuitBreaker — prevents cascading failures in external service calls.

Implements the circuit breaker pattern:
- CLOSED: Normal operation, calls pass through
- OPEN: Too many recent failures, calls are rejected immediately
- HALF_OPEN: After cooldown, allow one test call to check recovery
"""

import logging
import time
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker for protecting external service calls.

    Args:
        name: Identifier for this circuit (e.g., "claude_api", "news_api").
        failure_threshold: Number of consecutive failures before opening.
        recovery_timeout: Seconds to wait before transitioning to half-open.
        success_threshold: Successes needed in half-open to close again.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._last_state_change: float = time.time()

    @property
    def state(self) -> CircuitState:
        """Current circuit state, with automatic OPEN→HALF_OPEN transition."""
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._transition(CircuitState.HALF_OPEN)
        return self._state

    @property
    def is_closed(self) -> bool:
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    def allow_request(self) -> bool:
        """Check if a request should be allowed through."""
        current = self.state
        if current == CircuitState.CLOSED:
            return True
        if current == CircuitState.HALF_OPEN:
            return True  # Allow test request
        return False  # OPEN — reject

    def record_success(self) -> None:
        """Record a successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._transition(CircuitState.CLOSED)
        else:
            self._failure_count = 0
            self._success_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._success_count = 0
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._transition(CircuitState.OPEN)
        elif self._failure_count >= self.failure_threshold:
            self._transition(CircuitState.OPEN)

    def reset(self) -> None:
        """Manually reset to closed state."""
        self._transition(CircuitState.CLOSED)

    def get_status(self) -> dict[str, Any]:
        """Get circuit breaker status for monitoring."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }

    def _transition(self, new_state: CircuitState) -> None:
        old_state = self._state
        self._state = new_state
        self._last_state_change = time.time()

        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0

        if new_state == CircuitState.HALF_OPEN:
            self._success_count = 0

        logger.info(
            "CircuitBreaker[%s]: %s → %s (failures=%d)",
            self.name, old_state.value, new_state.value, self._failure_count,
        )


class CircuitBreakerRegistry:
    """Registry of named circuit breakers for the MKG pipeline."""

    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> CircuitBreaker:
        """Get an existing breaker or create a new one."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
            )
        return self._breakers[name]

    def get_all_status(self) -> list[dict[str, Any]]:
        """Get status of all registered circuit breakers."""
        return [cb.get_status() for cb in self._breakers.values()]

    def reset_all(self) -> None:
        """Reset all circuit breakers to closed."""
        for cb in self._breakers.values():
            cb.reset()
