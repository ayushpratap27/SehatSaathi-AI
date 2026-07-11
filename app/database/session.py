"""
Async SQLAlchemy session factory and FastAPI database dependency.

For development:   sqlite+aiosqlite:///./sehat_saathi.db
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

# SQLite-specific: check_same_thread=False is needed for SQLite
connect_args: dict = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args["check_same_thread"] = False

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
)

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
    Used as a FastAPI dependency: ``db: AsyncSession = Depends(get_db)``.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
