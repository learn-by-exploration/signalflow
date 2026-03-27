"""Redis-based endpoint caching for hot endpoints.

Uses per-endpoint TTLs with automatic invalidation.
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Per-endpoint cache TTLs (seconds)
CACHE_TTLS = {
    "signals_list": 30,
    "markets_overview": 15,
    "signals_stats": 300,
    "signals_performance": 600,
}


def _make_cache_key(prefix: str, **params: Any) -> str:
    """Build a Redis cache key from prefix + sorted query params."""
    param_str = json.dumps(params, sort_keys=True, default=str)
    param_hash = hashlib.md5(param_str.encode()).hexdigest()[:12]
    return f"cache:{prefix}:{param_hash}"


async def get_cached(redis_client: Any, key: str) -> dict | None:
    """Get a cached response from Redis.

    Args:
        redis_client: Redis client instance.
        key: Cache key.

    Returns:
        Cached dict or None if miss/expired.
    """
    if redis_client is None:
        return None
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception:
        logger.debug("Cache miss for %s (connection error)", key)
    return None


async def set_cached(
    redis_client: Any,
    key: str,
    data: dict,
    ttl: int,
) -> None:
    """Store a response in Redis cache.

    Args:
        redis_client: Redis client instance.
        key: Cache key.
        data: Response dict to cache.
        ttl: Time-to-live in seconds.
    """
    if redis_client is None:
        return
    try:
        await redis_client.setex(key, ttl, json.dumps(data, default=str))
    except Exception:
        logger.debug("Failed to cache %s", key)


async def invalidate_cache(redis_client: Any, prefix: str) -> int:
    """Invalidate all cache entries matching a prefix.

    Args:
        redis_client: Redis client instance.
        prefix: Cache key prefix (e.g., "signals_list").

    Returns:
        Number of keys deleted.
    """
    if redis_client is None:
        return 0
    try:
        keys = []
        async for key in redis_client.scan_iter(f"cache:{prefix}:*"):
            keys.append(key)
        if keys:
            await redis_client.delete(*keys)
        return len(keys)
    except Exception:
        logger.debug("Failed to invalidate cache prefix %s", prefix)
        return 0
