"""
Redis connection management for Phase 8 caching.

Falls back gracefully when Redis is unavailable (e.g., dev without Docker).
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_redis_client: Optional[object] = None
_redis_available: bool = False


def get_redis():
    """
    Return the global Redis client or None if Redis is unavailable.

    Lazy-initialised on first call.
    """
    global _redis_client, _redis_available

    if _redis_client is not None:
        return _redis_client if _redis_available else None

    from app.config.settings import get_settings  # noqa: PLC0415
    settings = get_settings()
    redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")

    try:
        import redis  # noqa: PLC0415
        client = redis.from_url(redis_url, decode_responses=True, socket_timeout=2)
        client.ping()
        _redis_client   = client
        _redis_available = True
        logger.info("Redis connected: %s", redis_url)
    except Exception as exc:
        logger.warning("Redis unavailable (%s) — caching disabled.", exc)
        _redis_client   = None
        _redis_available = False

    return _redis_client if _redis_available else None


def close_redis() -> None:
    """Close the Redis connection if open."""
    global _redis_client, _redis_available
    if _redis_client and _redis_available:
        try:
            _redis_client.close()  # type: ignore[union-attr]
        except Exception:
            pass
    _redis_client   = None
    _redis_available = False
