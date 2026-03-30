"""v1.3.9 — Brute Force & Account Lockout Tests.

Verify login rate limiting, account lockout after failed attempts,
and lockout recovery.
"""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


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


class TestLoginRateLimiting:
    """Login endpoint must have rate limiting."""

    def test_login_has_rate_limit_decorator(self):
        """Login endpoint should have rate limiting configured."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "auth_routes.py")
        with open(path) as f:
            content = f.read()
        # Find login function and verify it has limiter
        assert "@limiter.limit" in content, "Login must have rate limiting"
        # Check the login-specific limit
        login_idx = content.find("async def login")
        assert login_idx != -1
        # Find the limiter line before the login function
        before_login = content[:login_idx]
        last_limiter = before_login.rfind("@limiter.limit")
        assert last_limiter != -1
        limit_line = content[last_limiter:content.find("\n", last_limiter)]
        # Extract the rate limit value — should be restrictive
        assert "/minute" in limit_line, f"Login rate limit should be per-minute: {limit_line}"

    def test_register_has_rate_limit(self):
        """Registration endpoint should have rate limiting."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "auth_routes.py")
        with open(path) as f:
            content = f.read()
        register_idx = content.find("async def register")
        before = content[:register_idx]
        last_limiter = before.rfind("@limiter.limit")
        assert last_limiter != -1
        limit_line = content[last_limiter:content.find("\n", last_limiter)]
        assert "/minute" in limit_line


class TestAccountLockout:
    """Account lockout after too many failed login attempts."""

    def test_lockout_constants_reasonable(self):
        """Lockout should be >= 5 min, max attempts <= 10."""
        from app.api.auth_routes import LOCKOUT_DURATION_SECONDS, MAX_FAILED_ATTEMPTS
        assert MAX_FAILED_ATTEMPTS <= 10, f"Max attempts {MAX_FAILED_ATTEMPTS} too high"
        assert MAX_FAILED_ATTEMPTS >= 3, f"Max attempts {MAX_FAILED_ATTEMPTS} too low"
        assert LOCKOUT_DURATION_SECONDS >= 300, "Lockout should be at least 5 minutes"
        assert LOCKOUT_DURATION_SECONDS <= 3600, "Lockout should be at most 1 hour"

    def test_lockout_key_includes_ip_and_email(self):
        """Lockout key should include both IP and email to prevent DoS."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "auth_routes.py")
        with open(path) as f:
            content = f.read()
        # The lockout key should combine IP and email
        assert "client_ip" in content, "Lockout should use client IP"
        assert "payload.email" in content, "Lockout should use email"

    @pytest.mark.asyncio
    async def test_wrong_password_returns_401(self, auth_client: AsyncClient):
        """Wrong password returns 401 with generic message."""
        # Register first
        await auth_client.post(
            "/api/v1/auth/register",
            json={"email": "brute@example.com", "password": "TestPass1!"},
        )
        # Wrong password
        resp = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "brute@example.com", "password": "WrongPass1!"},
        )
        assert resp.status_code == 401
        body = resp.json()
        detail = body.get("detail", "")
        # Must NOT reveal whether email exists
        assert "invalid" in detail.lower() or "incorrect" in detail.lower()

    @pytest.mark.asyncio
    async def test_nonexistent_email_returns_401(self, auth_client: AsyncClient):
        """Login with nonexistent email returns same 401 as wrong password."""
        resp = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "nonexist@example.com", "password": "TestPass1!"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_error_does_not_reveal_user_existence(self, auth_client: AsyncClient):
        """Error messages should be identical for wrong email vs wrong password."""
        # Register a user
        await auth_client.post(
            "/api/v1/auth/register",
            json={"email": "exist_check@example.com", "password": "TestPass1!"},
        )
        # Wrong password for existing user
        resp1 = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "exist_check@example.com", "password": "WrongPass1!"},
        )
        # Nonexistent user
        resp2 = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "no_such_user@example.com", "password": "TestPass1!"},
        )
        assert resp1.status_code == resp2.status_code
        # Error messages should be the same
        msg1 = resp1.json().get("detail", "")
        msg2 = resp2.json().get("detail", "")
        assert msg1 == msg2, "Error messages must be identical to prevent user enumeration"

    def test_failed_attempts_tracked_in_redis(self):
        """Login code tracks failed attempts in Redis."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "auth_routes.py")
        with open(path) as f:
            content = f.read()
        assert "incr" in content, "Failed attempts should be incremented in Redis"
        assert "failed_login" in content.lower() or "FAILED_LOGIN" in content

    def test_lockout_clears_on_success(self):
        """Successful login clears the failed attempt counter."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "auth_routes.py")
        with open(path) as f:
            content = f.read()
        # After successful login, the code should delete the failed key
        assert "delete(failed_key)" in content or "delete(lockout_key)" in content


class TestPasswordChangeProtection:
    """Password change should have rate limiting."""

    def test_password_change_has_rate_limit(self):
        """Password change endpoint should be rate limited."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "auth_routes.py")
        with open(path) as f:
            content = f.read()
        pw_change_idx = content.find("async def change_password")
        if pw_change_idx != -1:
            before = content[:pw_change_idx]
            last_limiter = before.rfind("@limiter.limit")
            assert last_limiter != -1, "Password change must have rate limiting"

    def test_account_delete_has_rate_limit(self):
        """Account deletion should be rate limited."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "auth_routes.py")
        with open(path) as f:
            content = f.read()
        delete_idx = content.find("async def delete_account")
        if delete_idx != -1:
            before = content[:delete_idx]
            last_limiter = before.rfind("@limiter.limit")
            assert last_limiter != -1, "Account deletion must have rate limiting"
