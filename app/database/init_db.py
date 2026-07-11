"""
Database initialisation helpers.

``init_db()`` creates all tables from ORM metadata — useful for
development and testing. In production, Alembic migrations should
be used instead.
"""

from __future__ import annotations

import logging

from app.database.base import Base
from app.database.session import engine

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """
    Create all database tables from the current ORM metadata.

    Safe to call at startup:  if tables already exist they are left untouched.
    Should be used only in development / testing.
    In production, prefer:  ``alembic upgrade head``
    """
    # Import all models so their tables are registered on Base.metadata
    import app.models  # noqa: F401  # triggers __init__.py imports

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created / verified.")


async def drop_db() -> None:
    """Drop all tables — use ONLY in test teardown."""
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("All database tables dropped.")
