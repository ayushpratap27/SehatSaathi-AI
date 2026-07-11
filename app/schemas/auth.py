"""
Pydantic schemas for authentication endpoints.
"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ------------------------------------------------------------------ #
# Request schemas
# ------------------------------------------------------------------ #

class RegisterRequest(BaseModel):
    email:    EmailStr = Field(..., description="Valid email address")
    username: str      = Field(..., min_length=3, max_length=50)
    password: str      = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError("Username may only contain letters, digits, _, . and -")
        return v


class LoginRequest(BaseModel):
    email:    EmailStr = Field(..., description="Registered email")
    password: str      = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh token")


# ------------------------------------------------------------------ #
# Response schemas
# ------------------------------------------------------------------ #

class TokenPair(BaseModel):
    """Access + refresh tokens returned after login/register."""
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


class AccessToken(BaseModel):
    """New access token returned by the refresh endpoint."""
    access_token: str
    token_type:   str = "bearer"


class UserProfile(BaseModel):
    """Public user profile returned by GET /auth/me."""
    id:          str
    email:       str
    username:    str
    full_name:   Optional[str]
    is_active:   bool
    is_verified: bool
    created_at:  str

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
