"""
AuditLog ORM model — records security-relevant application events.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database.base import Base, _new_uuid


class AuditLog(Base):
    """Immutable record of a security or data-mutation event."""

    __tablename__ = "audit_logs"

    id:            Mapped[str]           = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id:       Mapped[Optional[str]] = mapped_column(String(36), nullable=True,  index=True)
    action:        Mapped[str]           = mapped_column(String(100), nullable=False, index=True)  # e.g. "user.login"
    resource_type: Mapped[Optional[str]] = mapped_column(String(50),  nullable=True)               # e.g. "report"
    resource_id:   Mapped[Optional[str]] = mapped_column(String(36),  nullable=True)
    ip_address:    Mapped[Optional[str]] = mapped_column(String(45),  nullable=True)               # IPv4/IPv6
    details:       Mapped[Optional[str]] = mapped_column(Text,        nullable=True)               # JSON extra info
    created_at:    Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id!r} action={self.action!r} user={self.user_id!r}>"
