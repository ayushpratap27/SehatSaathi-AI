"""
User ORM model and RefreshToken model.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, _new_uuid

if TYPE_CHECKING:
    from app.models.report import Report
    from app.models.chat import ChatSession


class User(Base, TimestampMixin):
    """Application user account."""

    __tablename__ = "users"

    id:              Mapped[str]  = mapped_column(String(36), primary_key=True, default=_new_uuid)
    email:           Mapped[str]  = mapped_column(String(255), unique=True, index=True, nullable=False)
    username:        Mapped[str]  = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str]  = mapped_column(String(255), nullable=False)
    full_name:       Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active:       Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified:     Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    reports:      Mapped[List["Report"]]      = relationship("Report",      back_populates="user", cascade="all, delete-orphan")
    chat_sessions: Mapped[List["ChatSession"]] = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r}>"


class RefreshToken(Base):
    """Persisted refresh token — allows server-side logout / revocation."""

    __tablename__ = "refresh_tokens"

    id:         Mapped[str]      = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id:    Mapped[str]      = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jti:        Mapped[str]      = mapped_column(String(36), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool]     = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
