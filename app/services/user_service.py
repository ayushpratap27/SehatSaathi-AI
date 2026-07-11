"""
User service — registration, login, token management.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)

# Pre-hashed dummy password used so verify_password() always runs,
# preventing timing side-channels that reveal whether an email is registered.
_DUMMY_HASH: str = hash_password("sehat-saathi-dummy-password-never-matches-any-real-hash")
from app.models.user import RefreshToken, User
from app.repositories.user_repo import refresh_token_repository, user_repository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenPair

logger = logging.getLogger(__name__)


class UserService:
    """Handles user registration, authentication, and token lifecycle."""

    async def register(self, db: AsyncSession, req: RegisterRequest) -> TokenPair:
        if await user_repository.email_exists(db, req.email):
            raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered.")
        if await user_repository.username_exists(db, req.username):
            raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken.")

        user = await user_repository.create(
            db,
            email=req.email,
            username=req.username,
            hashed_password=hash_password(req.password),
            full_name=req.full_name,
        )
        logger.info("User registered: %s", user.email)
        return await self._issue_tokens(db, user)

    async def login(self, db: AsyncSession, req: LoginRequest) -> TokenPair:
        user = await user_repository.get_by_email(db, req.email)
        # Always call verify_password — prevents timing side-channel that
        # reveals whether a given email address is registered.
        check_hash = user.hashed_password if user else _DUMMY_HASH
        password_ok = verify_password(req.password, check_hash)
        if not user or not password_ok:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password.")
        if not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is inactive.")

        logger.info("User logged in: %s", user.email)
        return await self._issue_tokens(db, user)

    async def refresh(self, db: AsyncSession, refresh_token_str: str) -> str:
        payload = decode_refresh_token(refresh_token_str)
        if not payload:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token.")

        jti = payload.get("jti", "")
        if not await refresh_token_repository.is_valid(db, jti):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token has been revoked.")

        user_id = payload["sub"]
        user = await user_repository.get_by_id(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found.")

        return create_access_token(user.id, user.email)

    async def logout(self, db: AsyncSession, refresh_token_str: str) -> None:
        payload = decode_refresh_token(refresh_token_str)
        if not payload:
            logger.info("Logout called with invalid or expired refresh token — no DB action taken")
            return
        await refresh_token_repository.revoke(db, payload.get("jti", ""))

    async def _issue_tokens(self, db: AsyncSession, user: User) -> TokenPair:
        access  = create_access_token(user.id, user.email)
        refresh_str, jti = create_refresh_token(user.id)
        from app.config.settings import get_settings  # noqa: PLC0415
        settings = get_settings()
        from datetime import timedelta  # noqa: PLC0415
        exp = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await refresh_token_repository.create(
            db,
            user_id=user.id,
            jti=jti,
            expires_at=exp,
            created_at=datetime.now(timezone.utc),
        )
        return TokenPair(access_token=access, refresh_token=refresh_str)


user_service = UserService()
