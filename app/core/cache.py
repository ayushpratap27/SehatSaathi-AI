"""
Cache utilities — JSON-based get/set with TTL, backed by Redis.
Falls back to a no-op when Redis is unavailable.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def cache_get(key: str) -> Optional[Any]:
    """Return a cached value or None if missing / Redis unavailable."""
    from app.core.redis import get_redis  # noqa: PLC0415
    client = get_redis()
    if client is None:
        return None
    try:
        raw = client.get(key)  # type: ignore[union-attr]
        return json.loads(raw) if raw else None
    except Exception as exc:
        logger.debug("cache_get error: %s", exc)
        return None


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """
    Store a JSON-serialisable value in Redis with a TTL.

    Args:
        key:   Cache key string.
        value: JSON-serialisable value.
        ttl:   Time-to-live in seconds (default 300 = 5 min).
    """
    from app.core.redis import get_redis  # noqa: PLC0415
    client = get_redis()
    if client is None:
        return
    try:
        client.setex(key, ttl, json.dumps(value, default=str))  # type: ignore[union-attr]
    except Exception as exc:
        logger.debug("cache_set error: %s", exc)


def cache_delete(key: str) -> None:
    """Invalidate a cache entry."""
    from app.core.redis import get_redis  # noqa: PLC0415
    client = get_redis()
    if client:
        try:
            client.delete(key)  # type: ignore[union-attr]
        except Exception as exc:
            logger.debug("cache_delete error: %s", exc)


def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a glob pattern (use sparingly)."""
    from app.core.redis import get_redis  # noqa: PLC0415
    client = get_redis()
    if not client:
        return
    try:
        keys = client.keys(pattern)  # type: ignore[union-attr]
        if keys:
            client.delete(*keys)  # type: ignore[union-attr]
    except Exception as exc:
        logger.debug("cache_delete_pattern error: %s", exc)
