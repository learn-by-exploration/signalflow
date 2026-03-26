"""Tests for authentication endpoints — register, login, refresh, logout, profile."""

import hashlib
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.auth import hash_password, verify_password, create_access_token, create_refresh_token
from app.models.user import User, RefreshToken


# ─── Password hashing tests ───


class TestPasswordHashing:
    def test_hash_password_returns_bcrypt_string(self):
        hashed = hash_password("testpassword")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        assert len(hashed) == 60

    def test_verify_password_correct(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_hash_password_unique_salts(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # bcrypt generates unique salts


# ─── Auth API tests ───


@pytest_asyncio.fixture
async def auth_client(db_engine_and_session):
    """HTTP test client WITHOUT auth overrides — tests real auth flow."""
    from app.database import get_db
    from app.main import app

    _engine, session_factory = db_engine_and_session

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded_user(db_engine_and_session):
    """Seed a test user into the DB and return their credentials."""
    _engine, session_factory = db_engine_and_session
    email = "testuser@signalflow.ai"
    password = "Test@Secure1"
    async with session_factory() as session:
        user = User(
            email=email,
            password_hash=hash_password(password),
            tier="free",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return {"email": email, "password": password, "user_id": str(user.id)}


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, auth_client):
        res = await auth_client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "password": "Secure@Pass1",
        })
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["user"]["email"] == "new@example.com"
        assert data["user"]["tier"] == "free"
        assert data["user"]["is_active"] is True
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        assert data["tokens"]["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, auth_client):
        await auth_client.post("/api/v1/auth/register", json={
            "email": "dup@example.com",
            "password": "Valid@Pass1",
        })
        res = await auth_client.post("/api/v1/auth/register", json={
            "email": "dup@example.com",
            "password": "Another@Pass1",
        })
        assert res.status_code == 409
        assert "already registered" in res.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_short_password(self, auth_client):
        res = await auth_client.post("/api/v1/auth/register", json={
            "email": "short@example.com",
            "password": "abc",
        })
        assert res.status_code == 422  # Pydantic validation

    @pytest.mark.asyncio
    async def test_register_weak_password_rejected(self, auth_client):
        """Password without uppercase/special char is rejected."""
        res = await auth_client.post("/api/v1/auth/register", json={
            "email": "weak@example.com",
            "password": "alllowercase123",
        })
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_register_no_digit_password_rejected(self, auth_client):
        """Password without digits is rejected."""
        res = await auth_client.post("/api/v1/auth/register", json={
            "email": "nodigit@example.com",
            "password": "NoDigits@Here",
        })
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, auth_client):
        res = await auth_client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "Valid@Pass1",
        })
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_register_with_telegram_chat_id(self, auth_client):
        res = await auth_client.post("/api/v1/auth/register", json={
            "email": "telegram@example.com",
            "password": "Tele@gram1",
            "telegram_chat_id": 123456789,
        })
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["user"]["telegram_chat_id"] == 123456789


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, auth_client, seeded_user):
        res = await auth_client.post("/api/v1/auth/login", json={
            "email": seeded_user["email"],
            "password": seeded_user["password"],
        })
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["user"]["email"] == seeded_user["email"]
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, auth_client, seeded_user):
        res = await auth_client.post("/api/v1/auth/login", json={
            "email": seeded_user["email"],
            "password": "wrongpassword",
        })
        assert res.status_code == 401
        assert "invalid" in res.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, auth_client):
        res = await auth_client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "doesntmatter",
        })
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_login_returns_valid_jwt(self, auth_client, seeded_user):
        res = await auth_client.post("/api/v1/auth/login", json={
            "email": seeded_user["email"],
            "password": seeded_user["password"],
        })
        tokens = res.json()["data"]["tokens"]
        # Use the access token to call /api/v1/auth/profile
        profile_res = await auth_client.get("/api/v1/auth/profile", headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        })
        assert profile_res.status_code == 200
        assert profile_res.json()["data"]["email"] == seeded_user["email"]


class TestRefresh:
    @pytest.mark.asyncio
    async def test_refresh_success(self, auth_client, seeded_user):
        # Login first
        login_res = await auth_client.post("/api/v1/auth/login", json={
            "email": seeded_user["email"],
            "password": seeded_user["password"],
        })
        old_tokens = login_res.json()["data"]["tokens"]

        # Refresh
        res = await auth_client.post("/api/v1/auth/refresh", json={
            "refresh_token": old_tokens["refresh_token"],
        })
        assert res.status_code == 200
        new_tokens = res.json()["data"]["tokens"]
        assert new_tokens["access_token"] != old_tokens["access_token"]
        assert new_tokens["refresh_token"] != old_tokens["refresh_token"]

    @pytest.mark.asyncio
    async def test_refresh_revoked_token_rejected(self, auth_client, seeded_user):
        # Login
        login_res = await auth_client.post("/api/v1/auth/login", json={
            "email": seeded_user["email"],
            "password": seeded_user["password"],
        })
        old_refresh = login_res.json()["data"]["tokens"]["refresh_token"]

        # Use refresh token once (rotates it)
        await auth_client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})

        # Try using the old (now revoked) refresh token
        res = await auth_client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, auth_client):
        res = await auth_client.post("/api/v1/auth/refresh", json={
            "refresh_token": "completely-invalid-token",
        })
        assert res.status_code == 401


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_revokes_token(self, auth_client, seeded_user):
        # Login
        login_res = await auth_client.post("/api/v1/auth/login", json={
            "email": seeded_user["email"],
            "password": seeded_user["password"],
        })
        refresh_token = login_res.json()["data"]["tokens"]["refresh_token"]

        # Logout
        res = await auth_client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
        assert res.status_code == 200

        # Refresh should fail now
        res = await auth_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert res.status_code == 401


class TestProfile:
    @pytest.mark.asyncio
    async def test_profile_unauthenticated(self, auth_client):
        res = await auth_client.get("/api/v1/auth/profile")
        assert res.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_profile_with_valid_token(self, auth_client, seeded_user):
        # Login
        login_res = await auth_client.post("/api/v1/auth/login", json={
            "email": seeded_user["email"],
            "password": seeded_user["password"],
        })
        access_token = login_res.json()["data"]["tokens"]["access_token"]

        res = await auth_client.get("/api/v1/auth/profile", headers={
            "Authorization": f"Bearer {access_token}",
        })
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["email"] == seeded_user["email"]
        assert "password" not in str(data)
        assert "password_hash" not in str(data)
