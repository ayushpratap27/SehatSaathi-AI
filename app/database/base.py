"""
SQLAlchemy 2.x declarative base and shared column mixins.

All ORM models inherit from ``Base``. ``TimestampMixin`` adds
``created_at`` / ``updated_at`` columns automatically.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _new_uuid() -> str:
    """Generate a new UUID4 string (used as default for primary keys)."""
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""
    pass


class TimestampMixin:
    """
    Adds ``created_at`` and ``updated_at`` columns to any model.

    Both columns are managed by the database server; Python code
    should never set them manually.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
