"""Rate limiter instance shared across the application."""

import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)


def _key_func_with_logging(request):
    """Extract client IP and log rate limit checks."""
    return get_remote_address(request)


limiter = Limiter(key_func=_key_func_with_logging, default_limits=["60/minute"])
