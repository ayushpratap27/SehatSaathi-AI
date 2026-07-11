"""
JWT handler — creates and verifies access and refresh tokens.

Access tokens:  short-lived (30 min), stateless.
Refresh tokens: long-lived (7 days), JTI stored in DB for revocation.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import bcrypt

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

ALGORITHM = "HS256"


# ------------------------------------------------------------------ #
# Password utilities
# ------------------------------------------------------------------ #

def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of ``plain_password``."""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if ``plain_password`` matches ``hashed_password``."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# ------------------------------------------------------------------ #
# Token creation
# ------------------------------------------------------------------ #

def create_access_token(user_id: str, email: str) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        user_id: UUID string of the authenticated user.
        email:   User's email address.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub":   user_id,
        "email": email,
        "type":  "access",
        "exp":   expire,
        "iat":   datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """
    Create a long-lived JWT refresh token.

    Args:
        user_id: UUID string of the authenticated user.

    Returns:
        Tuple of (encoded_jwt, jti) where ``jti`` should be stored in DB.
    """
    jti    = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub":  user_id,
        "jti":  jti,
        "type": "refresh",
        "exp":  expire,
        "iat":  datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token, jti


# ------------------------------------------------------------------ #
# Token verification
# ------------------------------------------------------------------ #

def decode_token(token: str, expected_type: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Args:
        token:         Raw JWT string.
        expected_type: "access" or "refresh".

    Returns:
        Decoded payload dict, or ``None`` if invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            logger.warning("Token type mismatch: expected %s, got %s", expected_type, payload.get("type"))
            return None
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
        return None
    except jwt.InvalidTokenError as exc:
        logger.debug("Invalid token: %s", exc)
        return None


def decode_access_token(token: str) -> Optional[dict]:
    """Decode an access token. Returns payload or None."""
    return decode_token(token, "access")


def decode_refresh_token(token: str) -> Optional[dict]:
    """Decode a refresh token. Returns payload or None."""
    return decode_token(token, "refresh")
