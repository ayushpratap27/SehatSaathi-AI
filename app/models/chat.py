"""
ChatSession and ChatMessage ORM models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, _new_uuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.report import Report


class ChatSession(Base, TimestampMixin):
    """Groups messages for one conversation about a specific report."""

    __tablename__ = "chat_sessions"

    id:        Mapped[str]           = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id:   Mapped[str]           = mapped_column(String(36), ForeignKey("users.id",   ondelete="CASCADE"), nullable=False, index=True)
    report_id: Mapped[str]           = mapped_column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    title:     Mapped[str]           = mapped_column(String(255), nullable=False, default="Medical Report Chat")
    is_rag:    Mapped[bool]          = mapped_column(default=True, nullable=False)

    # Relationships
    user:     Mapped["User"]               = relationship("User",   back_populates="chat_sessions")
    report:   Mapped["Report"]             = relationship("Report", back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]]  = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id!r} title={self.title!r}>"


class ChatMessage(Base):
    """One turn in a chat conversation."""

    __tablename__ = "chat_messages"

    id:           Mapped[str]           = mapped_column(String(36), primary_key=True, default=_new_uuid)
    session_id:   Mapped[str]           = mapped_column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role:         Mapped[str]           = mapped_column(String(20), nullable=False)    # "user" | "assistant"
    content:      Mapped[str]           = mapped_column(Text, nullable=False)
    sources_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)           # JSON list of citations
    confidence:   Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamp (no updated_at — messages are immutable)
    from sqlalchemy import DateTime
    from sqlalchemy.sql import func
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id!r} role={self.role!r}>"
