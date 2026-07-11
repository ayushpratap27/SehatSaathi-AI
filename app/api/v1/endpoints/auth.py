"""
Authentication endpoints — Phase 7 implementation.

POST /auth/register  — create account
POST /auth/login     — obtain access + refresh tokens
POST /auth/refresh   — get new access token
POST /auth/logout    — revoke refresh token
GET  /auth/me        — current user profile
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AccessToken,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserProfile,
)
from app.services.user_service import user_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=TokenPair, status_code=201,
             summary="Register a new user account")
async def register(
    req: RegisterRequest,
    db:  AsyncSession = Depends(get_db),
) -> TokenPair:
    """Create a new account and return access + refresh tokens."""
    logger.info("Register: %s", req.email)
    return await user_service.register(db, req)


@router.post("/login", response_model=TokenPair, summary="Login and get tokens")
async def login(
    req: LoginRequest,
    db:  AsyncSession = Depends(get_db),
) -> TokenPair:
    """Authenticate and return access + refresh tokens."""
    return await user_service.login(db, req)


@router.post("/refresh", response_model=AccessToken, summary="Refresh access token")
async def refresh_token(
    req: RefreshRequest,
    db:  AsyncSession = Depends(get_db),
) -> AccessToken:
    """Exchange a valid refresh token for a new access token."""
    new_access = await user_service.refresh(db, req.refresh_token)
    return AccessToken(access_token=new_access)


@router.post("/logout", response_model=MessageResponse, summary="Logout (revoke refresh token)")
async def logout(
    req: RefreshRequest,
    db:  AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Revoke the provided refresh token so it cannot be reused."""
    await user_service.logout(db, req.refresh_token)
    return MessageResponse(message="Logged out successfully.")


@router.get("/me", response_model=UserProfile, summary="Get current user profile")
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserProfile:
    """Return the profile of the currently authenticated user."""
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat(),
    )
