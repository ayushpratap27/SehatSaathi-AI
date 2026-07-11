"""User and RefreshToken repositories."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import RefreshToken, User
from app.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def email_exists(self, db: AsyncSession, email: str) -> bool:
        return await self.get_by_email(db, email) is not None

    async def username_exists(self, db: AsyncSession, username: str) -> bool:
        return await self.get_by_username(db, username) is not None


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    model = RefreshToken

    async def get_by_jti(self, db: AsyncSession, jti: str) -> Optional[RefreshToken]:
        result = await db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
        return result.scalar_one_or_none()

    async def revoke(self, db: AsyncSession, jti: str) -> bool:
        token = await self.get_by_jti(db, jti)
        if token is None:
            return False
        token.is_revoked = True
        await db.flush()
        return True

    async def revoke_all_for_user(self, db: AsyncSession, user_id: str) -> int:
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
        )
        tokens = result.scalars().all()
        for t in tokens:
            t.is_revoked = True
        await db.flush()
        return len(tokens)

    async def is_valid(self, db: AsyncSession, jti: str) -> bool:
        token = await self.get_by_jti(db, jti)
        return token is not None and not token.is_revoked and token.expires_at > datetime.now(timezone.utc)


user_repository         = UserRepository()
refresh_token_repository = RefreshTokenRepository()
