"""Rate limiter instance shared across the application."""

import logging
import os

from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)


def _key_func_with_logging(request):
    """Extract client IP and log rate limit checks."""
    return get_remote_address(request)


# Disable rate limiting during tests (TESTING=1 env var)
_enabled = os.environ.get("TESTING", "0") != "1"

# Use Redis for distributed rate limiting when available
_storage_uri = None
if _enabled:
    _redis_url = os.environ.get("REDIS_URL", "")
    if _redis_url:
        _storage_uri = _redis_url
        logger.info("Rate limiter using Redis backend: %s", _redis_url.split("@")[-1])

limiter = Limiter(
    key_func=_key_func_with_logging,
    default_limits=["60/minute"],
    enabled=_enabled,
    storage_uri=_storage_uri,
)
