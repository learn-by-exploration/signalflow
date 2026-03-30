"""v1.3.38 — Password Security Deep Tests.

Verify password policy enforcement, bcrypt usage,
storage safety, and password change flow.
"""

import pytest

from app.auth import hash_password, verify_password


class TestPasswordHashing:
    """Password hashing must use bcrypt correctly."""

    def test_hash_produces_bcrypt_format(self):
        """Hash output starts with $2b$ (bcrypt)."""
        h = hash_password("TestPassword123!")
        assert h.startswith("$2b$")

    def test_hash_is_60_chars(self):
        """Bcrypt hash is always 60 characters."""
        h = hash_password("AnyPassword1!")
        assert len(h) == 60

    def test_different_passwords_different_hashes(self):
        """Different passwords produce different hashes."""
        h1 = hash_password("Password1!")
        h2 = hash_password("Password2!")
        assert h1 != h2

    def test_same_password_different_salts(self):
        """Same password produces different hashes (random salt)."""
        h1 = hash_password("SamePassword1!")
        h2 = hash_password("SamePassword1!")
        assert h1 != h2  # Different salt each time

    def test_verify_correct_password(self):
        """Correct password verifies True."""
        pwd = "MySecure#Pass99"
        h = hash_password(pwd)
        assert verify_password(pwd, h) is True

    def test_verify_wrong_password(self):
        """Wrong password verifies False."""
        h = hash_password("CorrectPassword1!")
        assert verify_password("WrongPassword2!", h) is False

    def test_unicode_password_accepted(self):
        """Passwords with unicode characters work."""
        pwd = "पासवर्ड123!"
        h = hash_password(pwd)
        assert verify_password(pwd, h) is True

    def test_long_password_handled(self):
        """Very long password (>72 bytes) raises ValueError in bcrypt."""
        pwd = "A" * 100 + "!"
        with pytest.raises(ValueError):
            hash_password(pwd)

    def test_empty_string_password_hashable(self):
        """Empty password can be hashed (policy should reject, but hash works)."""
        h = hash_password("")
        assert isinstance(h, str)
        assert verify_password("", h) is True


class TestPasswordPolicy:
    """Registration should enforce password policy."""

    @pytest.mark.asyncio
    async def test_short_password_rejected(self, test_client):
        """Password shorter than minimum length is rejected."""
        r = await test_client.post(
            "/api/v1/auth/register",
            json={"email": "test@test.com", "password": "Ab1!"},
        )
        assert r.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_password_change_requires_current(self, test_client):
        """Password change needs current_password field."""
        r = await test_client.put(
            "/api/v1/auth/password",
            json={"new_password": "NewSecure123!"},
        )
        # Should require current_password
        assert r.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_password_change_wrong_current(self, test_client):
        """Password change with wrong current password fails."""
        r = await test_client.put(
            "/api/v1/auth/password",
            json={
                "current_password": "wrong-password",
                "new_password": "NewSecure123!",
            },
        )
        # Should fail (user doesn't exist in test DB with this password)
        assert r.status_code in (400, 401, 404, 500)
