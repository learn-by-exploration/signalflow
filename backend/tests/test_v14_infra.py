"""Tests for Infrastructure Track (v1.4 plan).

Tests cover: Redis caching, graceful shutdown, multi-stage Dockerfile,
multi-TF scheduler entries, subscription task.
"""

import os
import inspect

import pytest


# ═══════════════════════════════════════════════════════════
# Caching Infrastructure Tests
# ═══════════════════════════════════════════════════════════
class TestCachingInfrastructure:
    """Verify Redis caching module."""

    def test_cache_module_importable(self):
        """Cache module should be importable."""
        from app.services.cache import (
            get_cached,
            set_cached,
            invalidate_cache,
            CACHE_TTLS,
            _make_cache_key,
        )
        assert callable(get_cached)
        assert callable(set_cached)
        assert callable(invalidate_cache)

    def test_cache_ttls_defined(self):
        """Cache TTLs should be defined for hot endpoints."""
        from app.services.cache import CACHE_TTLS
        assert "signals_list" in CACHE_TTLS
        assert "markets_overview" in CACHE_TTLS
        assert CACHE_TTLS["signals_list"] == 30
        assert CACHE_TTLS["markets_overview"] == 15

    def test_make_cache_key(self):
        """Cache key should be deterministic for same params."""
        from app.services.cache import _make_cache_key
        key1 = _make_cache_key("test", market="stock", limit=20)
        key2 = _make_cache_key("test", market="stock", limit=20)
        key3 = _make_cache_key("test", market="crypto", limit=20)
        assert key1 == key2  # Same params → same key
        assert key1 != key3  # Different params → different key
        assert key1.startswith("cache:test:")

    @pytest.mark.asyncio
    async def test_get_cached_returns_none_without_redis(self):
        """get_cached with None redis should return None."""
        from app.services.cache import get_cached
        result = await get_cached(None, "test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_cached_noop_without_redis(self):
        """set_cached with None redis should not raise."""
        from app.services.cache import set_cached
        await set_cached(None, "test_key", {"data": 1}, 30)

    @pytest.mark.asyncio
    async def test_invalidate_cache_noop_without_redis(self):
        """invalidate_cache with None redis should return 0."""
        from app.services.cache import invalidate_cache
        result = await invalidate_cache(None, "test_prefix")
        assert result == 0


# ═══════════════════════════════════════════════════════════
# Graceful Shutdown Tests
# ═══════════════════════════════════════════════════════════
class TestGracefulShutdown:
    """Verify graceful shutdown handling."""

    def test_lifespan_has_cleanup(self):
        """Lifespan should handle cleanup on shutdown."""
        source = inspect.getsource(
            __import__("app.main", fromlist=["lifespan"])
        )
        assert "dispose" in source
        assert "shutting_down" in source

    def test_lifespan_closes_database(self):
        """Lifespan should close database connections on shutdown."""
        source = inspect.getsource(
            __import__("app.main", fromlist=["lifespan"])
        )
        assert "database_connections_closed" in source


# ═══════════════════════════════════════════════════════════
# Multi-Stage Dockerfile Tests
# ═══════════════════════════════════════════════════════════
class TestDockerfile:
    """Verify multi-stage Dockerfile."""

    def test_dockerfile_has_builder_stage(self):
        """Dockerfile should use multi-stage build."""
        dockerfile_path = os.path.join(
            os.path.dirname(__file__), "..", "Dockerfile",
        )
        with open(dockerfile_path) as f:
            content = f.read()
        assert "AS builder" in content
        assert "COPY --from=builder" in content

    def test_dockerfile_no_build_essential_in_final(self):
        """Final stage should not install build-essential."""
        dockerfile_path = os.path.join(
            os.path.dirname(__file__), "..", "Dockerfile",
        )
        with open(dockerfile_path) as f:
            content = f.read()
        # After the second FROM, there should be no build-essential
        stages = content.split("FROM ")
        if len(stages) >= 3:
            final_stage = stages[2]
            assert "build-essential" not in final_stage

    def test_dockerfile_runs_as_non_root(self):
        """Dockerfile should run as non-root user."""
        dockerfile_path = os.path.join(
            os.path.dirname(__file__), "..", "Dockerfile",
        )
        with open(dockerfile_path) as f:
            content = f.read()
        assert "USER appuser" in content


# ═══════════════════════════════════════════════════════════
# Scheduler Completeness Tests
# ═══════════════════════════════════════════════════════════
class TestSchedulerCompleteness:
    """Verify all scheduler entries are up to date."""

    def test_all_critical_tasks_in_schedule(self):
        """All critical tasks should be in the beat schedule."""
        from app.tasks.scheduler import CELERY_BEAT_SCHEDULE

        required_tasks = [
            "fetch-indian-stocks",
            "fetch-crypto-prices",
            "fetch-forex-rates",
            "fetch-crypto-daily",
            "fetch-forex-4h",
            "run-technical-analysis",
            "run-sentiment-analysis",
            "generate-signals",
            "resolve-signals",
            "check-price-alerts",
            "pipeline-health-check",
            "check-expired-subscriptions",
        ]
        for task in required_tasks:
            assert task in CELERY_BEAT_SCHEDULE, f"Missing task: {task}"

    def test_higher_tf_tasks_slower_than_primary(self):
        """Higher-TF tasks should have longer intervals than primary TF."""
        from app.tasks.scheduler import CELERY_BEAT_SCHEDULE

        # Crypto daily should be slower than crypto primary (30s)
        assert CELERY_BEAT_SCHEDULE["fetch-crypto-daily"]["schedule"] > \
            CELERY_BEAT_SCHEDULE["fetch-crypto-prices"]["schedule"]

        # Forex 4h should be slower than forex primary (60s)
        assert CELERY_BEAT_SCHEDULE["fetch-forex-4h"]["schedule"] > \
            CELERY_BEAT_SCHEDULE["fetch-forex-rates"]["schedule"]
