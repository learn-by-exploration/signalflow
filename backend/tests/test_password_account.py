"""Tests for password change and account deletion endpoints."""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.auth import AuthContext, hash_password
from app.models.user import User, RefreshToken
from app.models.alert_config import AlertConfig
from app.models.price_alert import PriceAlert
from app.models.trade import Trade


@pytest_asyncio.fixture
async def password_user(db_engine_and_session):
    """Seed a test user for password/account tests."""
    _engine, session_factory = db_engine_and_session
    user_id = uuid.uuid4()
    email = "pwdtest@signalflow.ai"
    password = "Old@Secure1"
    async with session_factory() as session:
        user = User(
            id=user_id,
            email=email,
            password_hash=hash_password(password),
            tier="free",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return {"email": email, "password": password, "user_id": str(user.id)}


@pytest_asyncio.fixture
async def pwd_client(db_engine_and_session, password_user):
    """HTTP test client with auth override pointing to the seeded user."""
    from app.auth import get_current_user, require_auth
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

    async def override_require_auth() -> AuthContext:
        return AuthContext(auth_type="jwt", user_id=password_user["user_id"])

    async def override_get_current_user() -> AuthContext:
        return AuthContext(auth_type="jwt", user_id=password_user["user_id"])

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_auth] = override_require_auth
    app.dependency_overrides[get_current_user] = override_get_current_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


class TestChangePassword:
    @pytest.mark.asyncio
    async def test_change_password_success(self, pwd_client, password_user):
        res = await pwd_client.put("/api/v1/auth/password", json={
            "current_password": password_user["password"],
            "new_password": "New@Secure2",
        })
        assert res.status_code == 200
        assert res.json()["data"] == "password_changed"

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, pwd_client):
        res = await pwd_client.put("/api/v1/auth/password", json={
            "current_password": "Wrong@Pass1",
            "new_password": "New@Secure2",
        })
        assert res.status_code == 401
        assert "incorrect" in res.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_change_password_same_as_current(self, pwd_client, password_user):
        res = await pwd_client.put("/api/v1/auth/password", json={
            "current_password": password_user["password"],
            "new_password": password_user["password"],
        })
        assert res.status_code == 400
        assert "different" in res.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_change_password_weak_new(self, pwd_client, password_user):
        res = await pwd_client.put("/api/v1/auth/password", json={
            "current_password": password_user["password"],
            "new_password": "weak",
        })
        assert res.status_code == 422  # validation error


class TestDeleteAccount:
    @pytest.mark.asyncio
    async def test_delete_account_success(self, pwd_client, password_user):
        res = await pwd_client.request("DELETE", "/api/v1/auth/account", json={
            "password": password_user["password"],
            "confirm": True,
        })
        assert res.status_code == 200
        assert res.json()["data"] == "account_deleted"

    @pytest.mark.asyncio
    async def test_delete_account_wrong_password(self, pwd_client):
        res = await pwd_client.request("DELETE", "/api/v1/auth/account", json={
            "password": "Wrong@Pass1",
            "confirm": True,
        })
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_account_no_confirm(self, pwd_client, password_user):
        res = await pwd_client.request("DELETE", "/api/v1/auth/account", json={
            "password": password_user["password"],
            "confirm": False,
        })
        assert res.status_code == 400
        assert "confirm" in res.json()["detail"].lower()


class TestDeleteAccountRequest:
    """Test the Pydantic schema validates correctly."""

    def test_valid_request(self):
        from app.schemas.auth import DeleteAccountRequest
        req = DeleteAccountRequest(password="test123", confirm=True)
        assert req.confirm is True

    def test_change_password_request_validation(self):
        from app.schemas.auth import ChangePasswordRequest
        req = ChangePasswordRequest(
            current_password="old",
            new_password="New@Secure1",
        )
        assert req.current_password == "old"

    def test_change_password_weak_rejected(self):
        from app.schemas.auth import ChangePasswordRequest
        with pytest.raises(Exception):
            ChangePasswordRequest(
                current_password="old",
                new_password="weak",
            )
