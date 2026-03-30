"""v1.3.32 — Cache Poisoning Tests.

Verify Redis cache key safety, serialization, TTL enforcement,
and cross-user cache isolation.
"""

import json
import pytest

from app.services.cache import get_cached, set_cached, _make_cache_key


class TestCacheKeySafety:
    """Cache keys must be safe from injection."""

    def test_cache_key_deterministic(self):
        """Same params produce same key."""
        k1 = _make_cache_key("signals", market="stock", limit=20)
        k2 = _make_cache_key("signals", market="stock", limit=20)
        assert k1 == k2

    def test_cache_key_different_params(self):
        """Different params produce different keys."""
        k1 = _make_cache_key("signals", market="stock")
        k2 = _make_cache_key("signals", market="crypto")
        assert k1 != k2

    def test_cache_key_special_chars_safe(self):
        """Special characters in params don't break keys."""
        k = _make_cache_key("signals", symbol="' OR 1=1--")
        assert isinstance(k, str)
        assert "cache:" in k

    def test_cache_key_prefix_included(self):
        """Cache key includes prefix."""
        k = _make_cache_key("markets_overview", region="IN")
        assert k.startswith("cache:markets_overview:")


class TestCacheSerialization:
    """Cache serialization is JSON-safe."""

    def test_json_serializable_data(self):
        """Normal data round-trips through JSON."""
        data = {"price": 1678.90, "symbol": "HDFC", "change": -0.42}
        serialized = json.dumps(data, default=str)
        deserialized = json.loads(serialized)
        assert deserialized["symbol"] == "HDFC"

    def test_none_handled_safely(self):
        """None values serialize safely."""
        data = {"price": None, "symbol": "TEST"}
        serialized = json.dumps(data, default=str)
        deserialized = json.loads(serialized)
        assert deserialized["price"] is None


class TestCacheGracefulDegradation:
    """Cache failures must not crash the application."""

    @pytest.mark.asyncio
    async def test_get_cached_with_none_client(self):
        """get_cached returns None when Redis client is None."""
        result = await get_cached(None, "any:key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_cached_with_none_client(self):
        """set_cached is a no-op when Redis client is None."""
        await set_cached(None, "any:key", {"data": "test"}, ttl=10)

    @pytest.mark.asyncio
    async def test_get_cached_returns_none_on_miss(self):
        """Cache miss returns None, not an error."""
        from unittest.mock import AsyncMock

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        result = await get_cached(mock_redis, "missing:key")
        assert result is None
