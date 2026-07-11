"""
Async SQLAlchemy session factory and FastAPI database dependency.

For development:   sqlite+aiosqlite:////abs/path/sehat_saathi.db
For production:    postgresql+asyncpg://user:pass@host:5432/dbname
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ------------------------------------------------------------------ #
# Engine
# ------------------------------------------------------------------ #

# SQLite-specific connect args
connect_args: dict = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {
        "check_same_thread": False,
        "timeout": 30,          # wait up to 30 s for a write lock
    }

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
)

# ------------------------------------------------------------------ #
# WAL mode initialisation (called from app lifespan)
# ------------------------------------------------------------------ #

async def configure_sqlite() -> None:
    """
    Enable WAL (Write-Ahead Logging) on a SQLite database.

    WAL allows concurrent reads while a background task is writing,
    preventing "database is locked" errors. Must be called once at
    application startup, before the first request is served.
    """
    if "sqlite" not in settings.DATABASE_URL:
        return
    from sqlalchemy import text  # noqa: PLC0415
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL"))    # enable WAL
        await conn.execute(text("PRAGMA busy_timeout=30000"))  # 30 s retry window
        await conn.execute(text("PRAGMA synchronous=NORMAL"))  # safe + faster
    logger.info("SQLite WAL mode enabled.")

# ------------------------------------------------------------------ #
# Session factory
# ------------------------------------------------------------------ #

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)


# ------------------------------------------------------------------ #
# FastAPI dependency
# ------------------------------------------------------------------ #

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a scoped async database session.

    Commits on successful exit, rolls back on any exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
