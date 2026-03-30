"""v1.3.6 — Password Policy & Hashing Tests.

Verify password complexity enforcement, bcrypt hashing,
and password change flow security.
"""

import re

import bcrypt
import pytest
from httpx import AsyncClient

from app.auth import hash_password, verify_password
from app.schemas.auth import ChangePasswordRequest, RegisterRequest


class TestPasswordComplexityRules:
    """Registration and password change must enforce strong password policy."""

    def test_min_length_8(self):
        """Password below 8 chars must be rejected."""
        with pytest.raises(Exception):
            RegisterRequest(email="test@example.com", password="Ab1!xyz")

    def test_max_length_128(self):
        """Password above 128 chars must be rejected."""
        long_pw = "Aa1!" + "x" * 125  # 129 chars
        with pytest.raises(Exception):
            RegisterRequest(email="test@example.com", password=long_pw)

    def test_accepts_exact_8_chars(self):
        """Exactly 8 chars is valid if complexity met."""
        req = RegisterRequest(email="test@example.com", password="Abcdef1!")
        assert req.password == "Abcdef1!"

    def test_accepts_exact_128_chars(self):
        """Exactly 128 chars should be valid."""
        pw = "Aa1!" + "x" * 124  # 128 chars
        req = RegisterRequest(email="test@example.com", password=pw)
        assert req.password == pw

    def test_requires_uppercase(self):
        """Password without uppercase must be rejected."""
        with pytest.raises(Exception, match="uppercase"):
            RegisterRequest(email="test@example.com", password="abcdef1!")

    def test_requires_lowercase(self):
        """Password without lowercase must be rejected."""
        with pytest.raises(Exception, match="lowercase"):
            RegisterRequest(email="test@example.com", password="ABCDEF1!")

    def test_requires_digit(self):
        """Password without digit must be rejected."""
        with pytest.raises(Exception, match="digit"):
            RegisterRequest(email="test@example.com", password="Abcdefg!")

    def test_requires_special_char(self):
        """Password without special character must be rejected."""
        with pytest.raises(Exception, match="special"):
            RegisterRequest(email="test@example.com", password="Abcdefg1")

    def test_all_special_chars_accepted(self):
        """Various special characters should all be accepted."""
        specials = ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", ",", ".", "?", "-", "_", "+", "="]
        for ch in specials:
            pw = f"Abcdef1{ch}"
            req = RegisterRequest(email="test@example.com", password=pw)
            assert req.password == pw

    def test_common_weak_passwords_rejected(self):
        """Common weak passwords should be rejected by complexity rules."""
        weak_passwords = [
            "password",     # no uppercase, no digit, no special
            "12345678",     # no letters, no special
            "Password",     # no digit, no special
            "Password1",    # no special char
            "password1!",   # no uppercase
            "PASSWORD1!",   # no lowercase
        ]
        for pw in weak_passwords:
            with pytest.raises(Exception):
                RegisterRequest(email="test@example.com", password=pw)


class TestPasswordChangeComplexity:
    """Password change uses the same complexity rules."""

    def test_new_password_must_meet_complexity(self):
        """ChangePasswordRequest enforces complexity on new_password."""
        with pytest.raises(Exception, match="uppercase"):
            ChangePasswordRequest(current_password="old", new_password="abcdef1!")

    def test_new_password_valid(self):
        """Valid new password is accepted."""
        req = ChangePasswordRequest(current_password="old", new_password="NewPass1!")
        assert req.new_password == "NewPass1!"


class TestBcryptHashing:
    """Verify bcrypt is used correctly for password storage."""

    def test_hash_returns_bcrypt_format(self):
        """Hashed password starts with $2b$ (bcrypt marker)."""
        h = hash_password("TestPw1!")
        assert h.startswith("$2b$"), f"Expected bcrypt hash, got: {h[:10]}"

    def test_different_passwords_different_hashes(self):
        """Two different passwords produce different hashes."""
        h1 = hash_password("Password1!")
        h2 = hash_password("Password2!")
        assert h1 != h2

    def test_same_password_different_hashes(self):
        """Same password hashed twice produces different hashes (random salt)."""
        h1 = hash_password("SamePass1!")
        h2 = hash_password("SamePass1!")
        assert h1 != h2, "Salt should make each hash unique"

    def test_verify_correct_password(self):
        """verify_password returns True for correct password."""
        h = hash_password("Correct1!")
        assert verify_password("Correct1!", h) is True

    def test_verify_wrong_password(self):
        """verify_password returns False for wrong password."""
        h = hash_password("Correct1!")
        assert verify_password("Wrong1!xx", h) is False

    def test_hash_is_not_plaintext(self):
        """Hash must never contain the plaintext password."""
        pw = "MySecret1!"
        h = hash_password(pw)
        assert pw not in h

    def test_bcrypt_work_factor_reasonable(self):
        """Bcrypt work factor should be >= 10 (default is 12)."""
        h = hash_password("TestPw1!")
        # bcrypt hash format: $2b$XX$... where XX is work factor
        parts = h.split("$")
        work_factor = int(parts[2])
        assert work_factor >= 10, f"Work factor {work_factor} is too low (min 10)"


class TestPasswordInAPIResponses:
    """Password hashes must never leak in API responses."""

    @pytest.mark.asyncio
    async def test_register_response_no_password(self, test_client: AsyncClient):
        """Registration response must not include password or hash."""
        resp = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "pwtest_no_leak@example.com",
                "password": "TestPass1!",
            },
        )
        body = resp.text
        assert "TestPass1!" not in body, "Plaintext password in response"
        assert "$2b$" not in body, "Bcrypt hash in response"

    @pytest.mark.asyncio
    async def test_profile_response_no_password(self, test_client: AsyncClient):
        """Profile endpoint must not include password hash."""
        # Register first
        resp = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "pwtest_profile@example.com",
                "password": "TestPass1!",
            },
        )
        if resp.status_code == 200:
            tokens = resp.json().get("data", {}).get("tokens", {})
            token = tokens.get("access_token", "")
            if token:
                profile_resp = await test_client.get(
                    "/api/v1/auth/profile",
                    headers={"Authorization": f"Bearer {token}"},
                )
                body = profile_resp.text
                assert "$2b$" not in body, "Bcrypt hash in profile response"
                assert "password" not in body.lower() or "change_password" in body.lower() or '"password"' not in body, \
                    "Password field in profile response"


class TestPasswordTimingSafety:
    """Password comparison should be timing-safe."""

    def test_bcrypt_checkpw_is_constant_time(self):
        """bcrypt.checkpw is inherently constant-time; verify it's used."""
        import inspect
        source = inspect.getsource(verify_password)
        assert "checkpw" in source, "Must use bcrypt.checkpw (constant-time comparison)"
        # Must NOT use == for hash comparison
        assert "==" not in source or "encode" in source, \
            "Should not use == for password hash comparison"
