"""
Authentication endpoint — Phase 1 placeholder.

Full implementation (user registration, JWT login/logout, refresh tokens,
user-scoped document isolation) will be added in Phase 8.
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/register", summary="Register a new user account")
async def register() -> dict:
    """
    Create a new user account.

    Returns:
        Placeholder response until Phase 8 implementation.
    """
    return {
        "success": True,
        "message": "User registration — coming in Phase 8",
    }


@router.post("/login", summary="Login and receive an access token")
async def login() -> dict:
    """
    Authenticate a user and return JWT access and refresh tokens.

    Returns:
        Placeholder response until Phase 8 implementation.
    """
    return {
        "success": True,
        "message": "JWT login — coming in Phase 8",
    }


@router.post("/logout", summary="Invalidate the current session")
async def logout() -> dict:
    """
    Invalidate the current access token (server-side blacklist in Phase 8).

    Returns:
        Placeholder response until Phase 8 implementation.
    """
    return {
        "success": True,
        "message": "Logout — coming in Phase 8",
    }


@router.post("/refresh", summary="Refresh an expired access token")
async def refresh_token() -> dict:
    """
    Issue a new access token using a valid refresh token.

    Returns:
        Placeholder response until Phase 8 implementation.
    """
    return {
        "success": True,
        "message": "Token refresh — coming in Phase 8",
    }
