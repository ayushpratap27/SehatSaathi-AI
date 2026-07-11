"""ChatSession and ChatMessage repositories."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage, ChatSession
from app.repositories.base_repo import BaseRepository


class ChatSessionRepository(BaseRepository[ChatSession]):
    model = ChatSession

    async def get_by_report(
        self, db: AsyncSession, report_id: str, user_id: str
    ) -> List[ChatSession]:
        result = await db.execute(
            select(ChatSession)
            .where(and_(ChatSession.report_id == report_id, ChatSession.user_id == user_id))
            .order_by(ChatSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_user_session(
        self, db: AsyncSession, session_id: str, user_id: str
    ) -> Optional[ChatSession]:
        """Ownership-checked fetch."""
        result = await db.execute(
            select(ChatSession).where(
                and_(ChatSession.id == session_id, ChatSession.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()


class ChatMessageRepository(BaseRepository[ChatMessage]):
    model = ChatMessage

    async def get_by_session(
        self, db: AsyncSession, session_id: str, limit: int = 50
    ) -> List[ChatMessage]:
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())


chat_session_repository = ChatSessionRepository()
chat_message_repository = ChatMessageRepository()
