"""Tests for password reset flow and email verification endpoints."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.auth import hash_password, create_access_token
from app.models.user import User, RefreshToken
from app.schemas.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)


# ── Schema validation tests ──


class TestForgotPasswordRequestSchema:
    def test_valid_email(self):
        req = ForgotPasswordRequest(email="user@example.com")
        assert req.email == "user@example.com"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            ForgotPasswordRequest(email="not-an-email")


class TestResetPasswordRequestSchema:
    def test_valid_request(self):
        req = ResetPasswordRequest(
            email="user@example.com",
            code="123456",
            new_password="NewSecure@1",
        )
        assert req.code == "123456"

    def test_code_too_short(self):
        with pytest.raises(ValidationError):
            ResetPasswordRequest(
                email="user@example.com",
                code="12345",
                new_password="NewSecure@1",
            )

    def test_code_too_long(self):
        with pytest.raises(ValidationError):
            ResetPasswordRequest(
                email="user@example.com",
                code="1234567",
                new_password="NewSecure@1",
            )

    def test_code_non_numeric(self):
        with pytest.raises(ValidationError):
            ResetPasswordRequest(
                email="user@example.com",
                code="abcdef",
                new_password="NewSecure@1",
            )

    def test_weak_password_rejected(self):
        with pytest.raises(ValidationError):
            ResetPasswordRequest(
                email="user@example.com",
                code="123456",
                new_password="weakpass",
            )

    def test_password_no_uppercase_rejected(self):
        with pytest.raises(ValidationError):
            ResetPasswordRequest(
                email="user@example.com",
                code="123456",
                new_password="nouppercase@1",
            )

    def test_password_no_special_char_rejected(self):
        with pytest.raises(ValidationError):
            ResetPasswordRequest(
                email="user@example.com",
                code="123456",
                new_password="NoSpecial1abc",
            )


class TestVerifyEmailRequestSchema:
    def test_valid_code(self):
        req = VerifyEmailRequest(code="654321")
        assert req.code == "654321"

    def test_non_numeric_code_rejected(self):
        with pytest.raises(ValidationError):
            VerifyEmailRequest(code="abcdef")

    def test_short_code_rejected(self):
        with pytest.raises(ValidationError):
            VerifyEmailRequest(code="123")


# ── Fixtures ──


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
    email = "resetuser@signalflow.ai"
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


# ── Forgot Password tests ──


class TestForgotPassword:
    @pytest.mark.asyncio
    async def test_forgot_password_existing_user(self, auth_client, seeded_user):
        """Should return success message (does not reveal whether user exists)."""
        with patch("app.api.auth_routes.aioredis") as mock_redis_mod:
            mock_client = AsyncMock()
            mock_redis_mod.from_url.return_value = mock_client

            res = await auth_client.post("/api/v1/auth/forgot-password", json={
                "email": seeded_user["email"],
            })
            assert res.status_code == 200
            assert "reset code" in res.json()["data"]["message"].lower()
            mock_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_user(self, auth_client):
        """Should still return success to prevent email enumeration."""
        res = await auth_client.post("/api/v1/auth/forgot-password", json={
            "email": "nobody@example.com",
        })
        assert res.status_code == 200
        assert "reset code" in res.json()["data"]["message"].lower()

    @pytest.mark.asyncio
    async def test_forgot_password_invalid_email(self, auth_client):
        res = await auth_client.post("/api/v1/auth/forgot-password", json={
            "email": "not-valid",
        })
        assert res.status_code == 422


# ── Reset Password tests ──


class TestResetPassword:
    @pytest.mark.asyncio
    async def test_reset_password_success(self, auth_client, seeded_user):
        """Valid code should reset password and revoke tokens."""
        with patch("app.api.auth_routes.aioredis") as mock_redis_mod:
            mock_client = AsyncMock()
            mock_client.get.return_value = b"123456"
            mock_redis_mod.from_url.return_value = mock_client

            res = await auth_client.post("/api/v1/auth/reset-password", json={
                "email": seeded_user["email"],
                "code": "123456",
                "new_password": "NewSecure@Pass1",
            })
            assert res.status_code == 200
            assert "reset" in res.json()["data"]["message"].lower()
            mock_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_password_wrong_code(self, auth_client, seeded_user):
        with patch("app.api.auth_routes.aioredis") as mock_redis_mod:
            mock_client = AsyncMock()
            mock_client.get.return_value = b"999999"
            mock_redis_mod.from_url.return_value = mock_client

            res = await auth_client.post("/api/v1/auth/reset-password", json={
                "email": seeded_user["email"],
                "code": "123456",
                "new_password": "NewSecure@Pass1",
            })
            assert res.status_code == 400
            assert "invalid or expired" in res.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_reset_password_expired_code(self, auth_client, seeded_user):
        """Expired/missing code returns error."""
        with patch("app.api.auth_routes.aioredis") as mock_redis_mod:
            mock_client = AsyncMock()
            mock_client.get.return_value = None  # code expired
            mock_redis_mod.from_url.return_value = mock_client

            res = await auth_client.post("/api/v1/auth/reset-password", json={
                "email": seeded_user["email"],
                "code": "123456",
                "new_password": "NewSecure@Pass1",
            })
            assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_reset_password_weak_password(self, auth_client):
        res = await auth_client.post("/api/v1/auth/reset-password", json={
            "email": "user@example.com",
            "code": "123456",
            "new_password": "weak",
        })
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_reset_password_can_login_with_new_password(self, auth_client, seeded_user):
        """After reset, user can log in with the new password."""
        new_password = "Brand@NewPass1"
        with patch("app.api.auth_routes.aioredis") as mock_redis_mod:
            mock_client = AsyncMock()
            mock_client.get.return_value = b"654321"
            mock_redis_mod.from_url.return_value = mock_client

            res = await auth_client.post("/api/v1/auth/reset-password", json={
                "email": seeded_user["email"],
                "code": "654321",
                "new_password": new_password,
            })
            assert res.status_code == 200

        # Now login with new password (need to patch Redis again for lockout check)
        with patch("app.api.auth_routes.aioredis") as mock_redis_mod:
            mock_client = AsyncMock()
            mock_client.get.return_value = None  # no lockout
            mock_redis_mod.from_url.return_value = mock_client

            login_res = await auth_client.post("/api/v1/auth/login", json={
                "email": seeded_user["email"],
                "password": new_password,
            })
            assert login_res.status_code == 200


# ── Email Verification tests ──


class TestVerifyEmail:
    @pytest.mark.asyncio
    async def test_verify_email_success(self, auth_client, seeded_user):
        """Valid code should mark email as verified."""
        # Get an access token first
        with patch("app.api.auth_routes.aioredis") as mock_redis_mod:
            mock_client = AsyncMock()
            mock_client.get.return_value = None  # no lockout
            mock_redis_mod.from_url.return_value = mock_client

            login_res = await auth_client.post("/api/v1/auth/login", json={
                "email": seeded_user["email"],
                "password": seeded_user["password"],
            })
        token = login_res.json()["data"]["tokens"]["access_token"]

        with patch("app.api.auth_routes.aioredis") as mock_redis_mod:
            mock_client = AsyncMock()
            mock_client.get.return_value = b"111222"
            mock_redis_mod.from_url.return_value = mock_client

            res = await auth_client.post(
                "/api/v1/auth/verify-email",
                json={"code": "111222"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert res.status_code == 200
            assert "verified" in res.json()["data"]["message"].lower()

    @pytest.mark.asyncio
    async def test_verify_email_wrong_code(self, auth_client, seeded_user):
        with patch("app.api.auth_routes.aioredis") as mock_redis_mod:
            mock_client = AsyncMock()
            mock_client.get.return_value = None  # no lockout
            mock_redis_mod.from_url.return_value = mock_client

            login_res = await auth_client.post("/api/v1/auth/login", json={
                "email": seeded_user["email"],
                "password": seeded_user["password"],
            })
        token = login_res.json()["data"]["tokens"]["access_token"]

        with patch("app.api.auth_routes.aioredis") as mock_redis_mod:
            mock_client = AsyncMock()
            mock_client.get.return_value = b"999999"
            mock_redis_mod.from_url.return_value = mock_client

            res = await auth_client.post(
                "/api/v1/auth/verify-email",
                json={"code": "111222"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_verify_email_requires_auth(self, auth_client):
        res = await auth_client.post("/api/v1/auth/verify-email", json={"code": "123456"})
        assert res.status_code == 401


class TestResendVerification:
    @pytest.mark.asyncio
    async def test_resend_verification_success(self, auth_client, seeded_user):
        with patch("app.api.auth_routes.aioredis") as mock_redis_mod:
            mock_client = AsyncMock()
            mock_client.get.return_value = None
            mock_redis_mod.from_url.return_value = mock_client

            login_res = await auth_client.post("/api/v1/auth/login", json={
                "email": seeded_user["email"],
                "password": seeded_user["password"],
            })
        token = login_res.json()["data"]["tokens"]["access_token"]

        with patch("app.api.auth_routes.aioredis") as mock_redis_mod:
            mock_client = AsyncMock()
            mock_redis_mod.from_url.return_value = mock_client

            res = await auth_client.post(
                "/api/v1/auth/resend-verification",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert res.status_code == 200
            assert "resent" in res.json()["data"]["message"].lower()

    @pytest.mark.asyncio
    async def test_resend_verification_requires_auth(self, auth_client):
        res = await auth_client.post("/api/v1/auth/resend-verification")
        assert res.status_code == 401
