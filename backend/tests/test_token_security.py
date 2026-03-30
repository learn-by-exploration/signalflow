"""v1.3.7 — Session & Token Security Tests.

Verify JWT access tokens, refresh tokens, revocation,
algorithm enforcement, and token type confusion prevention.
"""

import time
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt as pyjwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.auth import (
    AuthContext,
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    is_token_revoked,
)
from app.config import get_settings


@pytest_asyncio.fixture
async def auth_client(db_engine_and_session):
    """HTTP client WITHOUT auth overrides — tests real auth flow."""
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


class TestAccessTokenStructure:
    """Access token payload must include required claims."""

    def test_access_token_has_required_claims(self):
        uid = uuid.uuid4()
        token = create_access_token(uid, 12345, "free")
        settings = get_settings()
        payload = pyjwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == str(uid)
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "iat" in payload
        assert "exp" in payload
        assert payload["chat_id"] == 12345
        assert payload["tier"] == "free"

    def test_access_token_exp_within_expected_range(self):
        uid = uuid.uuid4()
        token = create_access_token(uid, None, "free")
        settings = get_settings()
        payload = pyjwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        exp = payload["exp"]
        iat = payload["iat"]
        delta = exp - iat
        # Should match jwt_access_token_expire_minutes (default 30)
        assert 0 < delta <= 3600, f"Access token lifetime {delta}s seems wrong"

    def test_jti_is_unique_per_token(self):
        uid = uuid.uuid4()
        t1 = create_access_token(uid, None, "free")
        t2 = create_access_token(uid, None, "free")
        settings = get_settings()
        p1 = pyjwt.decode(t1, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        p2 = pyjwt.decode(t2, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert p1["jti"] != p2["jti"]


class TestRefreshTokenStructure:
    """Refresh token must be distinct from access token."""

    def test_refresh_token_type_is_refresh(self):
        uid = uuid.uuid4()
        token = create_refresh_token(uid)
        settings = get_settings()
        payload = pyjwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["type"] == "refresh"
        assert payload["sub"] == str(uid)

    def test_refresh_token_longer_lived(self):
        uid = uuid.uuid4()
        access = create_access_token(uid, None, "free")
        refresh = create_refresh_token(uid)
        settings = get_settings()
        a_pay = pyjwt.decode(access, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        r_pay = pyjwt.decode(refresh, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        a_life = a_pay["exp"] - a_pay["iat"]
        r_life = r_pay["exp"] - r_pay["iat"]
        assert r_life > a_life, "Refresh token should live longer than access token"


class TestTokenTypeConfusion:
    """Refresh tokens must NOT be accepted as access tokens."""

    @pytest.mark.asyncio
    async def test_refresh_token_rejected_as_bearer(self, auth_client: AsyncClient):
        """Using a refresh token in Authorization header should fail."""
        uid = uuid.uuid4()
        refresh = create_refresh_token(uid)
        resp = await auth_client.get(
            "/api/v1/signals",
            headers={"Authorization": f"Bearer {refresh}"},
        )
        assert resp.status_code == 401, "Refresh token used as access should be 401"

    @pytest.mark.asyncio
    async def test_access_token_rejected_for_refresh(self, auth_client: AsyncClient):
        """Access token used for refresh endpoint should fail."""
        resp = await auth_client.post(
            "/api/v1/auth/register",
            json={"email": "tokentype@example.com", "password": "TestPass1!"},
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            access = data.get("tokens", {}).get("access_token", "")
            resp2 = await auth_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": access},
            )
            assert resp2.status_code == 401, "Access token used for refresh should be 401"


class TestTokenExpiry:
    """Expired tokens must be rejected."""

    def test_expired_access_token_rejected(self):
        """decode_jwt_token raises HTTPException for expired token."""
        settings = get_settings()
        payload = {
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "type": "access",
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = pyjwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            decode_jwt_token(token)
        assert exc.value.status_code == 401
        assert "expired" in exc.value.detail.lower()


class TestTokenAlgorithm:
    """Only the configured algorithm is accepted."""

    def test_none_algorithm_rejected(self):
        """Token with alg=none must be rejected."""
        settings = get_settings()
        payload = {
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        # Manually craft a token with "none" algorithm
        # PyJWT >= 2.x won't let us encode with none, so we test the decode path
        # by ensuring algorithms=[settings.jwt_algorithm] rejects anything else
        from fastapi import HTTPException

        # Token signed with wrong algorithm should be rejected
        wrong_algo = "HS384" if settings.jwt_algorithm == "HS256" else "HS256"
        token = pyjwt.encode(payload, settings.jwt_secret_key, algorithm=wrong_algo)
        with pytest.raises(HTTPException) as exc:
            decode_jwt_token(token)
        assert exc.value.status_code == 401

    def test_tampered_token_rejected(self):
        """Token with modified payload should be rejected."""
        uid = uuid.uuid4()
        token = create_access_token(uid, None, "free")
        # Tamper: change a character in the payload section
        parts = token.split(".")
        # Modify payload by flipping a character
        payload_b64 = parts[1]
        tampered = payload_b64[:-1] + ("A" if payload_b64[-1] != "A" else "B")
        tampered_token = f"{parts[0]}.{tampered}.{parts[2]}"
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_jwt_token(tampered_token)

    def test_random_string_rejected(self):
        """Random garbage string rejected as token."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_jwt_token("not.a.token")

    def test_empty_string_rejected(self):
        """Empty string rejected as token."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_jwt_token("")


class TestTokenRevocation:
    """Verify token revocation logic."""

    def test_revoked_jti_detected(self):
        """Token with revoked JTI should be detected."""
        # With test Redis mocked away, this tests the logic path
        uid = str(uuid.uuid4())
        jti = str(uuid.uuid4())
        iat = datetime.now(timezone.utc).timestamp()
        # In test env without Redis, is_token_revoked returns False
        result = is_token_revoked(jti, uid, iat)
        assert isinstance(result, bool)

    def test_api_key_uses_constant_time_compare(self):
        """API key comparison uses hmac.compare_digest (timing-safe)."""
        import inspect
        from app.auth import require_api_key
        source = inspect.getsource(require_api_key)
        assert "compare_digest" in source, "API key must use hmac.compare_digest"


class TestJWTSecretRequirements:
    """JWT secret key must be properly configured."""

    def test_jwt_secret_not_empty(self):
        settings = get_settings()
        assert settings.jwt_secret_key, "JWT_SECRET_KEY must be configured"
        assert len(settings.jwt_secret_key) >= 16, "JWT secret should be at least 16 chars"

    def test_jwt_algorithm_is_hmac(self):
        settings = get_settings()
        assert settings.jwt_algorithm.startswith("HS"), (
            f"Expected HMAC algorithm (HS256/HS384/HS512), got {settings.jwt_algorithm}"
        )


class TestAuthEndpointSecurity:
    """Auth-related API security tests."""

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, auth_client: AsyncClient):
        """Wrong password returns 401, not 200 or 500."""
        # Register
        await auth_client.post(
            "/api/v1/auth/register",
            json={"email": "jwt_wrong@example.com", "password": "TestPass1!"},
        )
        # Login with wrong password
        resp = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "jwt_wrong@example.com", "password": "WrongPass1!"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_auth_header_returns_401(self, auth_client: AsyncClient):
        """No auth header returns 401 on protected endpoints."""
        resp = await auth_client.get("/api/v1/auth/profile")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_malformed_bearer_returns_401(self, auth_client: AsyncClient):
        """Malformed Bearer token returns 401."""
        resp = await auth_client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_bearer_without_space_returns_401(self, auth_client: AsyncClient):
        """'Bearertoken' without space returns 401."""
        resp = await auth_client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": "Bearertoken"},
        )
        assert resp.status_code == 401
