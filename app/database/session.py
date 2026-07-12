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

# ---------------------------------------------------------------------------
# Normalise DATABASE_URL for asyncpg compatibility
# ---------------------------------------------------------------------------
import re as _re  # noqa: PLC0415

_db_url = settings.DATABASE_URL

# 1. Fix scheme — asyncpg requires postgresql+asyncpg://
_db_url = _re.sub(r"^postgres(ql)?://", "postgresql+asyncpg://", _db_url)

# 2. Strip query params that asyncpg does not understand
#    (sslmode, channel_binding are psycopg2/libpq-only)
_pg_ssl = False
if "sslmode=require" in _db_url or "sslmode=verify" in _db_url:
    _pg_ssl = True   # we'll pass ssl=True via connect_args instead
for _param in ("sslmode", "channel_binding"):
    _db_url = _re.sub(rf"[&?]{_param}=[^&]*", "", _db_url)
# Clean up any trailing ? or ?&
_db_url = _re.sub(r"\?$", "", _db_url)
_db_url = _re.sub(r"\?&", "?", _db_url)

# ------------------------------------------------------------------ #
# Engine
# ------------------------------------------------------------------ #

if "sqlite" in _db_url:
    # SQLite: use StaticPool so all sessions share ONE connection.
    from sqlalchemy.pool import StaticPool  # noqa: PLC0415
    engine = create_async_engine(
        _db_url,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL (production)
    _pg_connect_args: dict = {}
    if _pg_ssl:
        import ssl as _ssl  # noqa: PLC0415
        _pg_connect_args["ssl"] = _ssl.create_default_context()
    engine = create_async_engine(
        _db_url,
        echo=settings.DEBUG,
        connect_args=_pg_connect_args,
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
    if "sqlite" not in _db_url:
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
