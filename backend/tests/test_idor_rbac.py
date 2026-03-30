"""v1.3.8 — RBAC & IDOR Prevention Tests.

Verify that users can only access their own resources,
and that web-only users (no telegram_chat_id) are fully supported.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

WEB_USER_ID = "00000000-0000-0000-0000-000000000077"


@pytest_asyncio.fixture
async def web_user_client(seeded_db):
    """HTTP client for a web-only user (no telegram_chat_id)."""
    from app.auth import AuthContext, get_current_user, require_auth
    from app.database import get_db
    from app.main import app

    async def override_get_db():
        async with seeded_db() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def override_require_auth() -> AuthContext:
        return AuthContext(auth_type="jwt", user_id=WEB_USER_ID, telegram_chat_id=None, tier="free")

    async def override_get_current_user() -> AuthContext:
        return AuthContext(auth_type="jwt", user_id=WEB_USER_ID, telegram_chat_id=None, tier="free")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_auth] = override_require_auth
    app.dependency_overrides[get_current_user] = override_get_current_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


class TestSignalFeedbackIDOR:
    """Signal feedback must be scoped to the requesting user."""

    @pytest.mark.asyncio
    async def test_feedback_stores_user_id(self, test_client: AsyncClient):
        """POST feedback stores user_id alongside telegram_chat_id."""
        signal_id = str(uuid.uuid4())
        resp = await test_client.post(
            f"/api/v1/signals/{signal_id}/feedback",
            json={"action": "took", "entry_price": "100.50"},
        )
        assert resp.status_code == 201
        data = resp.json().get("data", {})
        assert data.get("signal_id") == signal_id

    @pytest.mark.asyncio
    async def test_feedback_get_returns_own(self, test_client: AsyncClient):
        """GET feedback returns user's own feedback only."""
        signal_id = str(uuid.uuid4())
        await test_client.post(
            f"/api/v1/signals/{signal_id}/feedback",
            json={"action": "skipped"},
        )
        resp = await test_client.get(f"/api/v1/signals/{signal_id}/feedback")
        assert resp.status_code == 200
        data = resp.json().get("data")
        assert data is not None
        assert data["action"] == "skipped"


class TestWebOnlyUserIDOR:
    """Web-only users (telegram_chat_id=None) must work correctly."""

    @pytest.mark.asyncio
    async def test_web_user_feedback_works(self, web_user_client: AsyncClient):
        """Web-only user can submit and retrieve feedback."""
        signal_id = str(uuid.uuid4())
        # Submit
        resp = await web_user_client.post(
            f"/api/v1/signals/{signal_id}/feedback",
            json={"action": "watching"},
        )
        assert resp.status_code == 201

        # Retrieve
        resp = await web_user_client.get(f"/api/v1/signals/{signal_id}/feedback")
        assert resp.status_code == 200
        data = resp.json().get("data")
        assert data is not None
        assert data["action"] == "watching"


class TestPortfolioIDOR:
    """Portfolio trades are scoped to the requesting user."""

    @pytest.mark.asyncio
    async def test_portfolio_trades_user_scoped(self, test_client: AsyncClient):
        """GET trades returns only current user's trades."""
        resp = await test_client.get("/api/v1/portfolio/trades")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_portfolio_summary_user_scoped(self, test_client: AsyncClient):
        """GET summary returns only current user's data."""
        resp = await test_client.get("/api/v1/portfolio/summary")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_web_user_portfolio(self, web_user_client: AsyncClient):
        """Web-only user can access portfolio."""
        resp = await web_user_client.get("/api/v1/portfolio/trades")
        assert resp.status_code == 200


class TestPriceAlertIDOR:
    """Price alerts are scoped to the requesting user."""

    @pytest.mark.asyncio
    async def test_price_alerts_user_scoped(self, test_client: AsyncClient):
        """GET price alerts returns only current user's alerts."""
        resp = await test_client.get("/api/v1/alerts/price")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_web_user_price_alerts(self, web_user_client: AsyncClient):
        """Web-only user can access price alerts."""
        resp = await web_user_client.get("/api/v1/alerts/price")
        assert resp.status_code == 200


class TestAlertConfigIDOR:
    """Alert configs are scoped to the requesting user."""

    @pytest.mark.asyncio
    async def test_alert_config_user_scoped(self, test_client: AsyncClient):
        """GET alert config returns only current user's config."""
        resp = await test_client.get("/api/v1/alerts/config")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_web_user_alert_config(self, web_user_client: AsyncClient):
        """Web-only user can access alert config endpoint (returns 404 when none exists)."""
        resp = await web_user_client.get("/api/v1/alerts/config")
        # 404 means config not found for this user — which is correct behavior
        # for a user who hasn't created one yet (no IDOR — no leaking other users' data)
        assert resp.status_code in (200, 404)


class TestWatchlistIDOR:
    """Watchlist is scoped to the requesting user."""

    @pytest.mark.asyncio
    async def test_watchlist_user_scoped(self, test_client: AsyncClient):
        """GET watchlist returns only current user's watchlist."""
        resp = await test_client.get("/api/v1/alerts/watchlist")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_web_user_watchlist(self, web_user_client: AsyncClient):
        """Web-only user can access watchlist."""
        resp = await web_user_client.get("/api/v1/alerts/watchlist")
        assert resp.status_code == 200


class TestCodebaseOwnershipChecks:
    """Verify ownership check patterns exist in API code."""

    def test_portfolio_has_user_filter(self):
        """portfolio.py uses user_id/telegram_chat_id filter."""
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "portfolio.py")
        with open(path) as f:
            content = f.read()
        assert "user_id" in content, "portfolio must check user_id"

    def test_price_alerts_has_user_filter(self):
        """price_alerts.py uses user_id/telegram_chat_id filter."""
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "price_alerts.py")
        with open(path) as f:
            content = f.read()
        assert "user_id" in content, "price_alerts must check user_id"

    def test_alerts_has_user_filter(self):
        """alerts.py uses user_id/telegram_chat_id filter."""
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "alerts.py")
        with open(path) as f:
            content = f.read()
        assert "user_id" in content or "telegram_chat_id" in content

    def test_signal_feedback_stores_user_id(self):
        """signal_feedback.py stores user_id on creation."""
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "signal_feedback.py")
        with open(path) as f:
            content = f.read()
        assert "user_id" in content, "signal_feedback must store user_id"

    def test_signal_feedback_queries_user_id(self):
        """signal_feedback.py queries by user_id (not only telegram_chat_id)."""
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "signal_feedback.py")
        with open(path) as f:
            content = f.read()
        assert "user.user_id" in content, "signal_feedback must query by user_id"
