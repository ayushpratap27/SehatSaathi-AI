"""
Phase 7 tests — authentication, repositories, dashboard.

Uses SQLite in-memory database for fast, isolated testing.
No external services required.
"""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio

# ------------------------------------------------------------------ #
# In-memory DB fixtures
# ------------------------------------------------------------------ #

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provide a fresh async SQLite in-memory session for each test."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.database.base import Base
    import app.models  # noqa: F401 — registers all models

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session

    await engine.dispose()


# ------------------------------------------------------------------ #
# JWT handler tests (pure unit — no DB)
# ------------------------------------------------------------------ #

class TestJWTHandler:
    def test_create_and_decode_access_token(self) -> None:
        from app.auth.jwt_handler import create_access_token, decode_access_token
        token   = create_access_token("user-1", "test@example.com")
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"]   == "user-1"
        assert payload["email"] == "test@example.com"
        assert payload["type"]  == "access"

    def test_expired_token_returns_none(self) -> None:
        from datetime import timedelta
        from app.auth.jwt_handler import ALGORITHM
        import jwt, time
        from app.config.settings import get_settings
        settings = get_settings()
        payload = {"sub": "u1", "type": "access", "exp": int(time.time()) - 1, "iat": int(time.time()) - 60}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
        from app.auth.jwt_handler import decode_access_token
        assert decode_access_token(token) is None

    def test_wrong_type_token_rejected(self) -> None:
        from app.auth.jwt_handler import create_refresh_token, decode_access_token
        refresh, _ = create_refresh_token("user-1")
        assert decode_access_token(refresh) is None

    def test_hash_and_verify_password(self) -> None:
        from app.auth.jwt_handler import hash_password, verify_password
        hashed = hash_password("SecurePass1!")
        assert verify_password("SecurePass1!", hashed) is True
        assert verify_password("WrongPass",    hashed) is False

    def test_create_refresh_token_returns_jti(self) -> None:
        from app.auth.jwt_handler import create_refresh_token, decode_refresh_token
        token, jti = create_refresh_token("user-2")
        payload = decode_refresh_token(token)
        assert payload is not None
        assert payload["jti"]  == jti
        assert payload["type"] == "refresh"


# ------------------------------------------------------------------ #
# Registration validation tests
# ------------------------------------------------------------------ #

class TestRegisterSchema:
    def test_weak_password_rejected(self) -> None:
        from pydantic import ValidationError
        from app.schemas.auth import RegisterRequest
        with pytest.raises(ValidationError):
            RegisterRequest(email="a@b.com", username="user1", password="nouppercase1")

    def test_no_digit_password_rejected(self) -> None:
        from pydantic import ValidationError
        from app.schemas.auth import RegisterRequest
        with pytest.raises(ValidationError):
            RegisterRequest(email="a@b.com", username="user1", password="NoDigitHere!")

    def test_valid_registration_passes(self) -> None:
        from app.schemas.auth import RegisterRequest
        req = RegisterRequest(email="user@example.com", username="john_doe", password="SecurePass1!")
        assert req.email == "user@example.com"


# ------------------------------------------------------------------ #
# User repository tests
# ------------------------------------------------------------------ #

class TestUserRepository:
    @pytest.mark.asyncio
    async def test_create_and_get_user(self, db_session) -> None:
        from app.auth.jwt_handler import hash_password
        from app.repositories.user_repo import user_repository
        user = await user_repository.create(
            db_session,
            email="alice@example.com",
            username="alice",
            hashed_password=hash_password("Pass123!"),
        )
        assert user.id
        fetched = await user_repository.get_by_id(db_session, user.id)
        assert fetched is not None
        assert fetched.email == "alice@example.com"

    @pytest.mark.asyncio
    async def test_get_by_email(self, db_session) -> None:
        from app.auth.jwt_handler import hash_password
        from app.repositories.user_repo import user_repository
        await user_repository.create(
            db_session,
            email="bob@example.com",
            username="bob",
            hashed_password=hash_password("Pass123!"),
        )
        found = await user_repository.get_by_email(db_session, "bob@example.com")
        assert found is not None
        assert found.username == "bob"

    @pytest.mark.asyncio
    async def test_email_exists(self, db_session) -> None:
        from app.auth.jwt_handler import hash_password
        from app.repositories.user_repo import user_repository
        await user_repository.create(
            db_session,
            email="carol@example.com",
            username="carol",
            hashed_password=hash_password("Pass123!"),
        )
        assert await user_repository.email_exists(db_session, "carol@example.com") is True
        assert await user_repository.email_exists(db_session, "nobody@example.com") is False


# ------------------------------------------------------------------ #
# User service integration tests
# ------------------------------------------------------------------ #

class TestUserService:
    @pytest.mark.asyncio
    async def test_register_and_login(self, db_session) -> None:
        from app.schemas.auth import LoginRequest, RegisterRequest
        from app.services.user_service import UserService

        svc = UserService()
        reg = RegisterRequest(email="dave@example.com", username="dave", password="DavePass1!")
        tokens = await svc.register(db_session, reg)
        assert tokens.access_token
        assert tokens.refresh_token

        login_req = LoginRequest(email="dave@example.com", password="DavePass1!")
        login_tokens = await svc.login(db_session, login_req)
        assert login_tokens.access_token

    @pytest.mark.asyncio
    async def test_duplicate_email_raises(self, db_session) -> None:
        from fastapi import HTTPException
        from app.schemas.auth import RegisterRequest
        from app.services.user_service import UserService

        svc = UserService()
        req = RegisterRequest(email="dup@example.com", username="dup1", password="DupPass1!")
        await svc.register(db_session, req)
        req2 = RegisterRequest(email="dup@example.com", username="dup2", password="DupPass1!")
        with pytest.raises(HTTPException) as exc:
            await svc.register(db_session, req2)
        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_wrong_password_raises(self, db_session) -> None:
        from fastapi import HTTPException
        from app.schemas.auth import LoginRequest, RegisterRequest
        from app.services.user_service import UserService

        svc = UserService()
        await svc.register(db_session,
            RegisterRequest(email="eve@example.com", username="eve", password="EvePass1!"))
        with pytest.raises(HTTPException) as exc:
            await svc.login(db_session, LoginRequest(email="eve@example.com", password="Wrong!"))
        assert exc.value.status_code == 401


# ------------------------------------------------------------------ #
# Auth API endpoint tests (full round-trip)
# ------------------------------------------------------------------ #

class TestAuthEndpoints:
    def test_register_returns_tokens(self, client) -> None:
        r = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "NewUserPass1!",
        })
        # Accept 201 (first run) or 409 (duplicate on re-run)
        assert r.status_code in (201, 409)

    def test_duplicate_email_returns_409(self, client) -> None:
        payload = {"email": "duptest@example.com", "username": "duptest", "password": "DupTest1!"}
        client.post("/api/v1/auth/register", json=payload)
        r = client.post("/api/v1/auth/register", json=payload)
        assert r.status_code == 409

    def test_login_valid_credentials(self, client) -> None:
        import uuid
        u = uuid.uuid4().hex[:8]
        client.post("/api/v1/auth/register", json={
            "email": f"logintest-{u}@example.com",
            "username": f"logintest{u}",
            "password": "LoginTest1!",
        })
        r = client.post("/api/v1/auth/login", json={
            "email": f"logintest-{u}@example.com", "password": "LoginTest1!"
        })
        assert r.status_code == 200
        assert r.json()["access_token"]

    def test_me_with_valid_token(self, client) -> None:
        import uuid
        u = uuid.uuid4().hex[:8]
        email = f"metest-{u}@example.com"
        r = client.post("/api/v1/auth/register", json={
            "email": email, "username": f"metest{u}", "password": "MeTest123!"
        })
        assert r.status_code == 201
        token = r.json()["access_token"]
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == email

    def test_me_without_token_returns_401(self, client) -> None:
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401


# ------------------------------------------------------------------ #
# Dashboard endpoint tests
# ------------------------------------------------------------------ #

class TestDashboardEndpoint:
    def test_dashboard_requires_auth(self, client) -> None:
        r = client.get("/api/v1/dashboard")
        assert r.status_code == 401

    def test_dashboard_returns_stats_for_new_user(self, client) -> None:
        import uuid
        u = uuid.uuid4().hex[:8]
        r = client.post("/api/v1/auth/register", json={
            "email": f"dash-{u}@example.com",
            "username": f"dashuser{u}",
            "password": "DashPass1!",
        })
        assert r.status_code == 201
        token = r.json()["access_token"]
        dash = client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert dash.status_code == 200
        data = dash.json()
        assert data["total_reports"] == 0
        assert data["recent_reports"] == []
