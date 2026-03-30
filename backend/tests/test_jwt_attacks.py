"""v1.3.10 — JWT Algorithm & Cryptographic Attack Tests.

Deep dive into JWT security: algorithm confusion, key confusion,
token forgery, and claim manipulation attacks.
"""

import base64
import json
import uuid
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest

from app.auth import create_access_token, decode_jwt_token
from app.config import get_settings


class TestAlgorithmConfusion:
    """Prevent algorithm confusion attacks (CVE-2015-9235 style)."""

    def test_only_configured_algorithm_accepted(self):
        """decode_jwt_token only accepts the configured algorithm."""
        settings = get_settings()
        payload = {
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        # Sign with different HMAC variant
        for algo in ["HS384", "HS512"]:
            if algo == settings.jwt_algorithm:
                continue
            token = pyjwt.encode(payload, settings.jwt_secret_key, algorithm=algo)
            from fastapi import HTTPException
            with pytest.raises(HTTPException):
                decode_jwt_token(token)

    def test_algorithms_param_is_list_not_string(self):
        """decode uses algorithms=[algo] (list), preventing injection."""
        import inspect
        source = inspect.getsource(decode_jwt_token)
        assert "algorithms=[" in source, "Must use algorithms= as list parameter"

    def test_unsigned_token_rejected(self):
        """Manually crafted unsigned token (alg=none) must fail."""
        # Build a token manually with alg=none
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "none", "typ": "JWT"}).encode()
        ).rstrip(b"=").decode()
        payload_data = {
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "type": "access",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        }
        payload = base64.urlsafe_b64encode(
            json.dumps(payload_data).encode()
        ).rstrip(b"=").decode()
        token = f"{header}.{payload}."
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_jwt_token(token)

    def test_empty_signature_rejected(self):
        """Token with empty signature segment must fail."""
        settings = get_settings()
        payload = {
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = pyjwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        parts = token.split(".")
        # Replace signature with empty string
        no_sig_token = f"{parts[0]}.{parts[1]}."
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_jwt_token(no_sig_token)


class TestTokenForgery:
    """Prevent various token forgery attacks."""

    def test_modified_sub_claim_fails(self):
        """Changing the 'sub' claim invalidates the signature."""
        uid = uuid.uuid4()
        token = create_access_token(uid, None, "free")
        settings = get_settings()

        # Decode without verification then re-encode without correct key
        payload = pyjwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        payload["sub"] = str(uuid.uuid4())  # Change user ID

        # Re-encode with wrong key
        forged = pyjwt.encode(payload, "wrong_secret_key", algorithm=settings.jwt_algorithm)
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_jwt_token(forged)

    def test_modified_tier_claim_fails(self):
        """Changing 'tier' from free to pro invalidates signature."""
        uid = uuid.uuid4()
        token = create_access_token(uid, None, "free")
        settings = get_settings()

        payload = pyjwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        payload["tier"] = "pro"  # Escalate privilege

        forged = pyjwt.encode(payload, "wrong_key_attempt", algorithm=settings.jwt_algorithm)
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_jwt_token(forged)

    def test_extended_exp_claim_fails(self):
        """Extending expiry time invalidates the signature."""
        uid = uuid.uuid4()
        token = create_access_token(uid, None, "free")
        settings = get_settings()

        payload = pyjwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        payload["exp"] = int((datetime.now(timezone.utc) + timedelta(days=365)).timestamp())

        forged = pyjwt.encode(payload, "attacker_key", algorithm=settings.jwt_algorithm)
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_jwt_token(forged)


class TestClaimValidation:
    """Verify token claims are properly validated."""

    def test_missing_type_claim_handled(self):
        """Token without 'type' claim should be handled safely."""
        settings = get_settings()
        payload = {
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            # Missing "type" claim
        }
        token = pyjwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        # Should decode successfully (type check happens in require_auth, not decode_jwt_token)
        decoded = decode_jwt_token(token)
        assert decoded.get("type") is None

    def test_missing_sub_claim_decoded(self):
        """Token without 'sub' claim should decode (validation upstream)."""
        settings = get_settings()
        payload = {
            "jti": str(uuid.uuid4()),
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = pyjwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        decoded = decode_jwt_token(token)
        assert "sub" not in decoded

    def test_extra_claims_ignored_safely(self):
        """Extra claims in token don't cause errors."""
        settings = get_settings()
        payload = {
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "admin": True,  # Attacker-added claim
            "role": "superadmin",
        }
        token = pyjwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        decoded = decode_jwt_token(token)
        # Extra claims are decoded but should be ignored by the app
        assert decoded.get("admin") is True  # Present but unused

    def test_negative_exp_rejected(self):
        """Token with negative/zero exp is immediately expired."""
        settings = get_settings()
        payload = {
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "exp": 0,
        }
        token = pyjwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_jwt_token(token)


class TestTokenStructuralIntegrity:
    """Verify structural requirements of JWT tokens."""

    def test_three_part_structure(self):
        """Access token must have exactly 3 dot-separated parts."""
        uid = uuid.uuid4()
        token = create_access_token(uid, None, "free")
        parts = token.split(".")
        assert len(parts) == 3, f"JWT should have 3 parts, got {len(parts)}"

    def test_header_specifies_algorithm(self):
        """JWT header must specify the algorithm."""
        uid = uuid.uuid4()
        token = create_access_token(uid, None, "free")
        header_b64 = token.split(".")[0]
        # Add padding
        padding = 4 - len(header_b64) % 4
        if padding != 4:
            header_b64 += "=" * padding
        header = json.loads(base64.urlsafe_b64decode(header_b64))
        settings = get_settings()
        assert header["alg"] == settings.jwt_algorithm
        assert header["typ"] == "JWT"
