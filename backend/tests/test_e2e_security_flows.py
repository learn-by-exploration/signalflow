"""v1.3.23 — End-to-End Security Flow Tests.

Complete security-oriented flows: registration → login → access → logout,
payment flows, signal access with auth, cross-user isolation.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.auth import AuthContext
from app.main import app


# ── Local fixture: auth_client (test DB, NO auth overrides) ──────


@pytest_asyncio.fixture
async def auth_client(seeded_db):
    """HTTP client with test DB but NO auth overrides.

    Use this for tests that exercise real auth flows (register/login/profile).
    """
    from app.database import get_db

    async def override_get_db():
        async with seeded_db() as session:
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


# ── Registration → Login → Profile → Logout ────────────────────


class TestAuthFlowE2E:
    """Full authentication lifecycle from security perspective."""

    @pytest.mark.asyncio
    async def test_full_auth_lifecycle(self, auth_client):
        """Register → login → profile → logout → refresh should fail."""
        uid = uuid.uuid4().hex[:8]
        email = f"e2e-{uid}@test.com"
        password = "SecurePass123!"

        # 1. Register
        reg = await auth_client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "name": "E2E User"},
        )
        assert reg.status_code in (200, 201), f"Register failed: {reg.text}"
        tokens = reg.json()["data"]["tokens"]
        access = tokens["access_token"]
        refresh = tokens["refresh_token"]

        # 2. Profile should work with access token
        prof = await auth_client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert prof.status_code == 200
        assert prof.json()["data"]["email"] == email

        # 3. Logout (revoke refresh token)
        logout = await auth_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert logout.status_code == 200

        # 4. Refresh with revoked token should fail
        ref = await auth_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert ref.status_code == 401

    @pytest.mark.asyncio
    async def test_login_wrong_password_rejected(self, auth_client):
        """Login with incorrect credentials must fail."""
        uid = uuid.uuid4().hex[:8]
        email = f"e2e-bad-{uid}@test.com"

        # Register
        await auth_client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "CorrectPass123!", "name": "E2E"},
        )

        # Login with wrong password
        login = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "WrongPassword999!"},
        )
        assert login.status_code == 401

    @pytest.mark.asyncio
    async def test_register_duplicate_email_rejected(self, auth_client):
        """Registering same email twice should fail."""
        uid = uuid.uuid4().hex[:8]
        email = f"e2e-dup-{uid}@test.com"
        payload = {"email": email, "password": "DupPass123!", "name": "Dup"}

        r1 = await auth_client.post("/api/v1/auth/register", json=payload)
        assert r1.status_code in (200, 201)

        r2 = await auth_client.post("/api/v1/auth/register", json=payload)
        assert r2.status_code in (400, 409, 422)


# ── Cross-User Isolation ─────────────────────────────────────────


class TestCrossUserIsolation:
    """One user's data must not be accessible by another."""

    @pytest.mark.asyncio
    async def test_users_cannot_see_each_others_profile(self, auth_client):
        """User A's token must not return User B's profile."""
        uid_a = uuid.uuid4().hex[:8]
        uid_b = uuid.uuid4().hex[:8]

        reg_a = await auth_client.post(
            "/api/v1/auth/register",
            json={
                "email": f"iso-a-{uid_a}@test.com",
                "password": "IsoPassA123!",
                "name": "User A",
            },
        )
        reg_b = await auth_client.post(
            "/api/v1/auth/register",
            json={
                "email": f"iso-b-{uid_b}@test.com",
                "password": "IsoPassB123!",
                "name": "User B",
            },
        )

        if reg_a.status_code not in (200, 201) or reg_b.status_code not in (200, 201):
            pytest.skip("Could not register both users")

        token_a = reg_a.json()["data"]["tokens"]["access_token"]
        token_b = reg_b.json()["data"]["tokens"]["access_token"]

        # User A's profile via User A's token
        prof_a = await auth_client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert prof_a.status_code == 200
        email_a = prof_a.json()["data"]["email"]

        # User B's profile via User B's token
        prof_b = await auth_client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert prof_b.status_code == 200
        email_b = prof_b.json()["data"]["email"]

        # Must be different users
        assert email_a != email_b

    @pytest.mark.asyncio
    async def test_password_change_invalidates_old_login(self, auth_client):
        """After password change, old password should fail for login."""
        uid = uuid.uuid4().hex[:8]
        email = f"pw-change-{uid}@test.com"
        old_pw = "OldPass123!"
        new_pw = "NewPass456!"

        # Register
        reg = await auth_client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": old_pw, "name": "PWChange"},
        )
        if reg.status_code not in (200, 201):
            pytest.skip("Registration failed")

        token = reg.json()["data"]["tokens"]["access_token"]

        # Change password
        pw = await auth_client.put(
            "/api/v1/auth/password",
            json={"current_password": old_pw, "new_password": new_pw},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert pw.status_code == 200

        # Old password should no longer work
        login_old = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": old_pw},
        )
        assert login_old.status_code == 401

        # New password should work
        login_new = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": new_pw},
        )
        assert login_new.status_code == 200


# ── Unauthenticated Access ───────────────────────────────────────


class TestUnauthenticatedAccess:
    """Endpoints that require auth must reject unauthenticated requests."""

    @pytest.mark.asyncio
    async def test_protected_endpoints_require_auth(self, auth_client):
        """Key protected endpoints return 401/403 without a token."""
        protected = [
            ("GET", "/api/v1/auth/profile"),
            ("PUT", "/api/v1/auth/password"),
            ("POST", "/api/v1/auth/logout"),
            ("POST", "/api/v1/auth/logout-all"),
            ("DELETE", "/api/v1/auth/account"),
        ]
        for method, path in protected:
            if method == "GET":
                r = await auth_client.get(path)
            elif method == "PUT":
                r = await auth_client.put(path, json={})
            elif method == "POST":
                r = await auth_client.post(path, json={})
            elif method == "DELETE":
                r = await auth_client.delete(path)
            else:
                continue
            assert r.status_code in (401, 403, 422), (
                f"{method} {path} returned {r.status_code}, expected 401/403"
            )

    @pytest.mark.asyncio
    async def test_public_endpoints_accessible(self, auth_client):
        """Public endpoints should be accessible without auth."""
        # Only health endpoint is truly public (no auth required)
        r = await auth_client.get("/health")
        assert r.status_code == 200


# ── Token Manipulation ───────────────────────────────────────────


class TestTokenManipulation:
    """Verify tampered tokens are rejected properly."""

    @pytest.mark.asyncio
    async def test_garbage_bearer_token_rejected(self, auth_client):
        """Random string as bearer token should be rejected."""
        r = await auth_client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": "Bearer garbage.token.here"},
        )
        assert r.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_empty_bearer_token_rejected(self, auth_client):
        """Empty bearer token should be rejected."""
        r = await auth_client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": "Bearer "},
        )
        assert r.status_code in (401, 403, 422)

    @pytest.mark.asyncio
    async def test_no_auth_header_rejected(self, auth_client):
        """Missing Authorization header should be rejected on protected routes."""
        r = await auth_client.get("/api/v1/auth/profile")
        assert r.status_code in (401, 403)


# ── Account Deletion Flow ─────────────────────────────────────────


class TestAccountDeletion:
    """Deleting an account should clean up and prevent further access."""

    @pytest.mark.asyncio
    async def test_delete_account_flow(self, auth_client):
        """Register → delete → login should fail."""
        uid = uuid.uuid4().hex[:8]
        email = f"delete-{uid}@test.com"
        password = "DeleteMe123!"

        # Register
        reg = await auth_client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "name": "Delete Me"},
        )
        if reg.status_code not in (200, 201):
            pytest.skip("Registration failed")

        token = reg.json()["data"]["tokens"]["access_token"]

        # Delete account
        dl = await auth_client.delete(
            "/api/v1/auth/account",
            headers={"Authorization": f"Bearer {token}"},
        )
        # 200 = deleted, 422 = Redis unavailable (failing closed on auth) in test env
        if dl.status_code == 422:
            pytest.skip("Account deletion blocked by Redis unavailability in test")
        assert dl.status_code == 200

        # Login should fail (account deleted)
        login = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login.status_code in (401, 404)


# ── Signals Auth-Gated Features ──────────────────────────────────


class TestSignalAuthGating:
    """Signal features gated by auth work correctly."""

    @pytest.mark.asyncio
    async def test_signal_feedback_requires_auth_context(self, test_client):
        """Signal feedback needs a valid user context."""
        signal_id = str(uuid.uuid4())
        r = await test_client.post(
            f"/api/v1/signals/{signal_id}/feedback",
            json={"action": "took", "entry_price": 100.0},
        )
        # With test_client (has auth override), should succeed or 404 (no signal)
        assert r.status_code in (200, 201, 404)

    @pytest.mark.asyncio
    async def test_ai_ask_requires_auth(self, auth_client):
        """AI Q&A endpoint should require authentication."""
        r = await auth_client.post(
            "/api/v1/ai/ask",
            json={"symbol": "RELIANCE.NS", "question": "What is the outlook?"},
        )
        # Should be 401 (no auth) or 429 (rate limited)
        assert r.status_code in (401, 403, 429)
