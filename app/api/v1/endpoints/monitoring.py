"""
Health, readiness, and liveness endpoints — Phase 8.

GET /health    — liveness probe (always 200 if app is running)
GET /ready     — readiness probe (checks DB and Redis)
GET /metrics   — basic application metrics
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Monitoring"])

_start_time = time.time()


@router.get("/health", summary="Liveness probe")
async def health():
    """Return HTTP 200 as long as the application process is running."""
    from app.config.settings import get_settings  # noqa: PLC0415
    settings = get_settings()
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
        "uptime_seconds": round(time.time() - _start_time),
    }


@router.get("/ready", summary="Readiness probe")
async def readiness():
    """
    Check that the application is ready to serve traffic.

    Verifies database connectivity and (optionally) Redis.
    Returns HTTP 200 if ready, HTTP 503 if not.
    """
    from fastapi import HTTPException  # noqa: PLC0415
    from sqlalchemy import text  # noqa: PLC0415

    checks: dict = {}

    # Database check
    try:
        from app.database.session import AsyncSessionLocal  # noqa: PLC0415
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    # Redis check (optional)
    try:
        from app.core.redis import get_redis  # noqa: PLC0415
        from starlette.concurrency import run_in_threadpool  # noqa: PLC0415
        client = get_redis()
        if client:
            await run_in_threadpool(client.ping)   # blocking call → thread pool
            checks["redis"] = "ok"
        else:
            checks["redis"] = "unavailable"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    all_ok = checks.get("database") == "ok"
    if not all_ok:
        raise HTTPException(status_code=503, detail={"status": "not ready", "checks": checks})

    return {"status": "ready", "checks": checks}


@router.get("/metrics", summary="Basic application metrics")
async def metrics():
    """Return lightweight application metrics (no external monitoring required)."""
    import os  # noqa: PLC0415
    import sys  # noqa: PLC0415
    return {
        "uptime_seconds":   round(time.time() - _start_time),
        "python_version":   sys.version,
        "process_id":       os.getpid(),
        "memory_mb": None,   # Add psutil in future for detailed metrics
    }
