"""Circuit breaker pattern for external API calls.

Prevents hammering failed external services (Binance, Twelve Data, Claude, etc.)
by tracking consecutive failures and temporarily stopping calls when a threshold
is exceeded.

Uses Redis for state storage so the circuit breaker works across Celery workers.

States:
    CLOSED  - Normal operation, calls go through
    OPEN    - Service is down, calls are blocked for recovery_timeout seconds
    HALF_OPEN - After recovery_timeout, allow one test call through

Usage:
    breaker = CircuitBreaker("binance", failure_threshold=5, recovery_timeout=300)
    if breaker.is_open():
        logger.warning("Binance circuit open, skipping fetch")
        return None
    try:
        result = call_binance_api()
        breaker.record_success()
        return result
    except Exception:
        breaker.record_failure()
        raise
"""

import logging
import time

import redis

from app.config import get_settings

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Redis-backed circuit breaker for external service calls.

    Args:
        name: Identifier for the service (e.g. "binance", "claude").
        failure_threshold: Consecutive failures before opening the circuit.
        recovery_timeout: Seconds to wait before allowing a test call (half-open).
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 300,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._prefix = f"circuit:{name}"
        self._redis: redis.Redis | None = None

    def _get_redis(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._redis is None:
            settings = get_settings()
            if settings.redis_url:
                self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            else:
                raise RuntimeError("Redis URL not configured for circuit breaker")
        return self._redis

    def record_success(self) -> None:
        """Record a successful API call. Resets failure count and closes circuit."""
        try:
            r = self._get_redis()
            r.delete(f"{self._prefix}:failures")
            r.delete(f"{self._prefix}:opened_at")
            logger.debug("Circuit %s: success recorded, circuit closed", self.name)
        except (redis.ConnectionError, redis.TimeoutError, OSError):
            logger.debug("Circuit %s: Redis unavailable, skipping success record", self.name)

    def record_failure(self) -> None:
        """Record a failed API call. Opens circuit if threshold exceeded."""
        try:
            r = self._get_redis()
            failures = r.incr(f"{self._prefix}:failures")
            # Set TTL on failure counter so it auto-clears eventually
            r.expire(f"{self._prefix}:failures", self.recovery_timeout * 2)

            if failures >= self.failure_threshold:
                r.set(
                    f"{self._prefix}:opened_at",
                    str(time.time()),
                    ex=self.recovery_timeout * 2,
                )
                logger.warning(
                    "Circuit %s: OPENED after %d consecutive failures (recovery in %ds)",
                    self.name,
                    failures,
                    self.recovery_timeout,
                )
        except (redis.ConnectionError, redis.TimeoutError, OSError):
            logger.debug("Circuit %s: Redis unavailable, skipping failure record", self.name)

    def is_open(self) -> bool:
        """Check if the circuit is open (calls should be blocked).

        Returns:
            True if circuit is open and calls should be blocked.
            False if circuit is closed or half-open (allow call).
        """
        try:
            r = self._get_redis()
            opened_at_str = r.get(f"{self._prefix}:opened_at")
            if not opened_at_str:
                return False

            opened_at = float(opened_at_str)
            elapsed = time.time() - opened_at

            if elapsed >= self.recovery_timeout:
                # Half-open: allow one test call through
                logger.info("Circuit %s: half-open, allowing test call", self.name)
                return False

            return True
        except (redis.ConnectionError, redis.TimeoutError, OSError):
            # If Redis is down, fail open (allow calls through)
            return False

    def get_state(self) -> str:
        """Get the current circuit state as a string.

        Returns:
            "closed", "open", or "half_open"
        """
        try:
            r = self._get_redis()
            opened_at_str = r.get(f"{self._prefix}:opened_at")
            if not opened_at_str:
                return "closed"

            elapsed = time.time() - float(opened_at_str)
            if elapsed >= self.recovery_timeout:
                return "half_open"
            return "open"
        except (redis.ConnectionError, redis.TimeoutError, OSError):
            return "closed"
