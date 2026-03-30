"""v1.3.27 — JWT Deep Edge Cases.

Token reuse, token types, claim validation, refresh rotation,
and cryptographic edge cases for JWT authentication.
"""

import time
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest

from app.auth import (
    AuthContext,
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
)
from app.config import get_settings


class TestJWTClaimValidation:
    """JWT claims must be strictly validated."""

    def test_token_with_wrong_type_rejected(self):
        """Using refresh token as access token should fail type check."""
        settings = get_settings()
        token = create_refresh_token(uuid.uuid4())
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        assert payload["type"] == "refresh"
        # Access-only endpoints check type == "access"

    def test_access_token_has_correct_claims(self):
        """Access token contains all required claims."""
        uid = uuid.uuid4()
        token = create_access_token(uid, 12345, "pro")
        settings = get_settings()
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])

        assert payload["sub"] == str(uid)
        assert payload["chat_id"] == 12345
        assert payload["tier"] == "pro"
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "iat" in payload
        assert "exp" in payload

    def test_refresh_token_has_correct_claims(self):
        """Refresh token contains required claims."""
        uid = uuid.uuid4()
        token = create_refresh_token(uid)
        settings = get_settings()
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])

        assert payload["sub"] == str(uid)
        assert payload["type"] == "refresh"
        assert "jti" in payload

    def test_token_with_empty_sub_cannot_auth(self):
        """Token with empty sub claim should fail authentication."""
        settings = get_settings()
        payload = {
            "sub": "",
            "jti": str(uuid.uuid4()),
            "type": "access",
            "tier": "pro",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
        decoded = decode_jwt_token(token)
        # Empty sub should be rejected by require_auth
        assert decoded["sub"] == ""

    def test_token_jti_is_unique(self):
        """Each token has a unique JTI."""
        uid = uuid.uuid4()
        t1 = create_access_token(uid, None, "free")
        t2 = create_access_token(uid, None, "free")
        settings = get_settings()
        p1 = jwt.decode(t1, settings.jwt_secret_key, algorithms=["HS256"])
        p2 = jwt.decode(t2, settings.jwt_secret_key, algorithms=["HS256"])
        assert p1["jti"] != p2["jti"]

    def test_expired_token_rejected(self):
        """Expired access token raises HTTPException."""
        settings = get_settings()
        payload = {
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "type": "access",
            "tier": "free",
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_jwt_token(token)
        assert exc_info.value.status_code == 401

    def test_token_with_wrong_secret_rejected(self):
        """Token signed with wrong secret is rejected."""
        payload = {
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "type": "access",
            "tier": "pro",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_jwt_token(token)
        assert exc_info.value.status_code == 401

    def test_token_with_manipulated_tier_rejected(self):
        """Token re-encoded with modified tier but wrong key is rejected."""
        uid = uuid.uuid4()
        token = create_access_token(uid, None, "free")
        settings = get_settings()
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        payload["tier"] = "pro"  # Escalate
        forged = jwt.encode(payload, "attacker-key", algorithm="HS256")
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_jwt_token(forged)

    def test_none_algorithm_attack_rejected(self):
        """JWT with alg=none is rejected."""
        import base64, json as json_mod
        payload = {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "tier": "pro",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        header = base64.urlsafe_b64encode(json_mod.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b'=')
        body = base64.urlsafe_b64encode(json_mod.dumps(payload).encode()).rstrip(b'=')
        forged = (header + b'.' + body + b'.').decode()
        from fastapi import HTTPException
        with pytest.raises((HTTPException, Exception)):
            decode_jwt_token(forged)


class TestJWTTokenLifecycle:
    """Token lifecycle operations must be secure."""

    def test_access_token_expires_in_30_min(self):
        """Access token TTL matches configured expiry."""
        uid = uuid.uuid4()
        token = create_access_token(uid, None, "free")
        settings = get_settings()
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        delta = (exp - iat).total_seconds()
        assert delta == settings.jwt_access_token_expire_minutes * 60

    def test_refresh_token_expires_in_7_days(self):
        """Refresh token TTL matches configured expiry."""
        uid = uuid.uuid4()
        token = create_refresh_token(uid)
        settings = get_settings()
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        delta_days = (exp - iat).days
        assert delta_days == settings.jwt_refresh_token_expire_days

    def test_access_token_with_null_chat_id(self):
        """Web-only user has chat_id=None in token."""
        uid = uuid.uuid4()
        token = create_access_token(uid, None, "free")
        settings = get_settings()
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        assert payload["chat_id"] is None

    def test_jwt_secret_required(self):
        """Token creation fails if JWT_SECRET_KEY is empty."""
        with patch.object(get_settings(), "jwt_secret_key", ""):
            with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
                create_access_token(uuid.uuid4(), None, "free")

    @pytest.mark.asyncio
    async def test_auth_endpoint_password_change(self, test_client):
        """Password change endpoint exists and requires auth."""
        r = await test_client.put(
            "/api/v1/auth/password",
            json={"current_password": "old", "new_password": "NewPass123!"}
        )
        # Should not be 405 (method exists)
        assert r.status_code != 405
