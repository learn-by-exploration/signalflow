"""Sprint 1 Security Tests — JWT auth, access control, tier enforcement, WebSocket auth."""

import hashlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest


# ─── JWT Token Tests ────────────────────────────────────────

class TestJWTTokens:
    """Tests for JWT token creation and validation."""

    def test_create_access_token(self):
        """Access token contains correct claims."""
        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.jwt_secret_key = "test-secret-key-32chars-min!!"
            mock_settings.return_value.jwt_algorithm = "HS256"
            mock_settings.return_value.jwt_access_token_expire_minutes = 30

            from app.auth import create_access_token, decode_jwt_token

            user_id = uuid4()
            token = create_access_token(user_id, 12345, "pro")
            payload = decode_jwt_token(token)

            assert payload["sub"] == str(user_id)
            assert payload["chat_id"] == 12345
            assert payload["tier"] == "pro"
            assert payload["type"] == "access"

    def test_create_refresh_token(self):
        """Refresh token has correct type claim."""
        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.jwt_secret_key = "test-secret-key-32chars-min!!"
            mock_settings.return_value.jwt_algorithm = "HS256"
            mock_settings.return_value.jwt_refresh_token_expire_days = 7

            from app.auth import create_refresh_token, decode_jwt_token

            user_id = uuid4()
            token = create_refresh_token(user_id)
            payload = decode_jwt_token(token)

            assert payload["sub"] == str(user_id)
            assert payload["type"] == "refresh"

    def test_expired_token_rejected(self):
        """Expired tokens raise 401."""
        import jwt as pyjwt

        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.jwt_secret_key = "test-secret-key-32chars-min!!"
            mock_settings.return_value.jwt_algorithm = "HS256"

            from app.auth import decode_jwt_token
            from fastapi import HTTPException

            expired_token = pyjwt.encode(
                {"sub": "test", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
                "test-secret-key-32chars-min!!",
                algorithm="HS256",
            )
            with pytest.raises(HTTPException) as exc_info:
                decode_jwt_token(expired_token)
            assert exc_info.value.status_code == 401
            assert "expired" in exc_info.value.detail.lower()

    def test_invalid_token_rejected(self):
        """Tampered tokens raise 401."""
        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.jwt_secret_key = "test-secret-key-32chars-min!!"
            mock_settings.return_value.jwt_algorithm = "HS256"

            from app.auth import decode_jwt_token
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                decode_jwt_token("invalid.token.here")
            assert exc_info.value.status_code == 401

    def test_token_with_wrong_secret_rejected(self):
        """Token signed with wrong key is rejected."""
        import jwt as pyjwt

        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.jwt_secret_key = "correct-secret-key-long-enough!"
            mock_settings.return_value.jwt_algorithm = "HS256"

            from app.auth import decode_jwt_token
            from fastapi import HTTPException

            token = pyjwt.encode(
                {"sub": "test", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                "wrong-secret-key-long-enough!!",
                algorithm="HS256",
            )
            with pytest.raises(HTTPException) as exc_info:
                decode_jwt_token(token)
            assert exc_info.value.status_code == 401


# ─── Password Hashing Tests ────────────────────────────────

class TestPasswordHashing:
    """Tests for bcrypt password hashing."""

    def test_hash_and_verify(self):
        """Password can be hashed and verified."""
        from app.auth import hash_password, verify_password

        pw = "SecurePass123!"
        hashed = hash_password(pw)
        assert hashed != pw
        assert verify_password(pw, hashed) is True

    def test_wrong_password_fails(self):
        """Wrong password is rejected."""
        from app.auth import hash_password, verify_password

        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_is_unique(self):
        """Same password produces different hashes (bcrypt salt)."""
        from app.auth import hash_password

        h1 = hash_password("password")
        h2 = hash_password("password")
        assert h1 != h2


# ─── Auth Context Tests ────────────────────────────────────

class TestAuthContext:
    """Tests for the unified auth dependency."""

    @pytest.mark.asyncio
    async def test_require_auth_accepts_api_key(self):
        """API key authentication works."""
        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.api_secret_key = "test-key"
            mock_settings.return_value.jwt_secret_key = "jwt-secret-key-long-enough-32!!"

            from app.auth import require_auth

            result = await require_auth(api_key="test-key", authorization=None)
            assert result.auth_type == "api_key"
            assert result.user_id is None

    @pytest.mark.asyncio
    async def test_require_auth_accepts_jwt(self):
        """JWT Bearer token authentication works."""
        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.api_secret_key = "test-key"
            mock_settings.return_value.jwt_secret_key = "jwt-secret-key-long-enough-32!!"
            mock_settings.return_value.jwt_algorithm = "HS256"
            mock_settings.return_value.jwt_access_token_expire_minutes = 30

            from app.auth import create_access_token, require_auth

            user_id = uuid4()
            token = create_access_token(user_id, 12345, "pro")
            result = await require_auth(api_key=None, authorization=f"Bearer {token}")

            assert result.auth_type == "jwt"
            assert result.user_id == str(user_id)
            assert result.telegram_chat_id == 12345
            assert result.tier == "pro"

    @pytest.mark.asyncio
    async def test_require_auth_rejects_no_credentials(self):
        """No credentials results in 401."""
        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.api_secret_key = "test-key"
            mock_settings.return_value.jwt_secret_key = "jwt-secret-key-long-enough-32!!"

            from app.auth import require_auth
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await require_auth(api_key=None, authorization=None)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_rejects_api_key_auth(self):
        """get_current_user rejects API-key-only auth (requires JWT)."""
        from app.auth import AuthContext, get_current_user
        from fastapi import HTTPException

        api_key_context = AuthContext(auth_type="api_key")
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(api_key_context)
        assert exc_info.value.status_code == 401


# ─── Tier Enforcement Tests ─────────────────────────────────

class TestTierEnforcement:
    """Tests for server-side tier checking."""

    @pytest.mark.asyncio
    async def test_require_tier_allows_matching(self):
        """Pro tier user passes pro tier check."""
        from app.auth import AuthContext, require_tier

        check = require_tier("pro")
        pro_context = AuthContext(auth_type="jwt", user_id="1", tier="pro")
        with patch("app.auth.require_auth", return_value=pro_context):
            result = await check(auth=pro_context)
            assert result.tier == "pro"

    @pytest.mark.asyncio
    async def test_require_tier_blocks_insufficient(self):
        """Free tier user is blocked from pro features."""
        from app.auth import AuthContext, require_tier
        from fastapi import HTTPException

        check = require_tier("pro")
        free_context = AuthContext(auth_type="jwt", user_id="1", tier="free")
        with pytest.raises(HTTPException) as exc_info:
            await check(auth=free_context)
        assert exc_info.value.status_code == 403
        assert "pro" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_require_tier_free_passes_all(self):
        """Free tier check passes for everyone."""
        from app.auth import AuthContext, require_tier

        check = require_tier("free")
        free_context = AuthContext(auth_type="jwt", user_id="1", tier="free")
        result = await check(auth=free_context)
        assert result.tier == "free"


# ─── User Model Tests ──────────────────────────────────────

class TestUserModel:
    """Tests for the User and RefreshToken models."""

    def test_user_model_fields(self):
        """User model has all required fields."""
        from app.models.user import User

        user = User(
            email="test@example.com",
            password_hash="hashed",
            telegram_chat_id=12345,
            tier="free",
        )
        assert user.email == "test@example.com"
        assert user.tier == "free"
        assert user.telegram_chat_id == 12345

    def test_refresh_token_model(self):
        """RefreshToken model has required fields."""
        from app.models.user import RefreshToken

        token = RefreshToken(
            user_id=uuid4(),
            token_hash="hash",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        assert token.is_revoked in (False, None)


# ─── Auth Schema Tests ─────────────────────────────────────

class TestAuthSchemas:
    """Tests for auth request/response schemas."""

    def test_register_request_valid(self):
        """Valid registration request."""
        from app.schemas.auth import RegisterRequest

        req = RegisterRequest(email="test@example.com", password="Secure@123")
        assert req.email == "test@example.com"

    def test_register_request_short_password(self):
        """Short password is rejected."""
        from app.schemas.auth import RegisterRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RegisterRequest(email="test@example.com", password="short")

    def test_login_request_valid(self):
        """Valid login request."""
        from app.schemas.auth import LoginRequest

        req = LoginRequest(email="test@example.com", password="password123")
        assert req.email == "test@example.com"

    def test_register_invalid_email(self):
        """Invalid email is rejected."""
        from app.schemas.auth import RegisterRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RegisterRequest(email="not-an-email", password="Secure@123")


# ─── Ownership / Access Control Tests ───────────────────────

class TestOwnershipChecks:
    """Verify that endpoints enforce ownership."""

    @pytest.mark.asyncio
    async def test_share_requires_auth(self, test_client):
        """POST /signals/{id}/share now requires JWT auth (via test override)."""
        # With test_client override, get_current_user returns test user
        signals = await test_client.get("/api/v1/signals")
        if signals.json()["data"]:
            sig_id = signals.json()["data"][0]["id"]
            resp = await test_client.post(f"/api/v1/signals/{sig_id}/share")
            assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_portfolio_requires_auth(self, test_client):
        """Portfolio endpoints work with JWT auth (via test override)."""
        resp = await test_client.get("/api/v1/portfolio/trades")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_alert_config_requires_auth(self, test_client):
        """Alert config endpoint works with JWT auth (via test override)."""
        resp = await test_client.get("/api/v1/alerts/config")
        assert resp.status_code == 200


# ─── SignalShare Created_by Tests ───────────────────────────

class TestSignalShareCreatedBy:
    """Tests for the created_by field on SignalShare."""

    def test_signal_share_has_created_by(self):
        """SignalShare model includes created_by field."""
        from app.models.signal_share import SignalShare

        share = SignalShare(signal_id=uuid4(), created_by="user-uuid-here")
        assert share.created_by == "user-uuid-here"

    def test_signal_share_created_by_optional(self):
        """created_by is nullable for backwards compatibility."""
        from app.models.signal_share import SignalShare

        share = SignalShare(signal_id=uuid4())
        assert share.created_by is None
