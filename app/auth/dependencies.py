"""
FastAPI auth dependencies.

Use these in endpoint functions:
  current_user = Depends(get_current_active_user)
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.auth.jwt_handler import decode_access_token
from app.database.session import get_db

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

oauth2_scheme          = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str                = Depends(oauth2_scheme),
    db:    AsyncSession       = Depends(get_db),
):
    """
    FastAPI dependency — returns the authenticated user.

    Raises HTTP 401 for missing/invalid/expired tokens and HTTP 403
    for inactive users.
    """
    from app.repositories.user_repo import user_repository  # noqa: PLC0415
    from app.models.user import User  # noqa: PLC0415

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exc

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise credentials_exc

    user: Optional[User] = await user_repository.get_by_id(db, user_id)
    if user is None:
        raise credentials_exc

    return user


async def get_current_active_user(
    current_user = Depends(get_current_user),
):
    """Dependency that additionally ensures the user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Contact support.",
        )
    return current_user


async def get_optional_current_user(
    token: Optional[str]  = Depends(oauth2_scheme_optional),
    db:    AsyncSession   = Depends(get_db),
):
    """
    Like ``get_current_user`` but returns ``None`` instead of raising
    if no valid token is provided.

    Useful for endpoints that work both authenticated and anonymously.
    """
    if not token:
        return None
    try:
        return await get_current_user(token=token, db=db)
    except HTTPException:
        return None
