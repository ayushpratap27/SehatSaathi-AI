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

if "sqlite" in settings.DATABASE_URL:
    # SQLite: use StaticPool so all sessions share ONE connection.
    # This completely eliminates "database is locked" errors because
    # writes are serialised at the connection level.  Safe for single-
    # process development; switch to PostgreSQL for production.
    from sqlalchemy.pool import StaticPool  # noqa: PLC0415
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL (production): use default async pool
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
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
