"""Regression tests for web-only users (no telegram_chat_id).

These tests verify that portfolio, watchlist, and price alert endpoints
work correctly for users who registered via the web UI and do NOT have
a telegram_chat_id. This was the root cause of "Failed to load portfolio"
and "Failed to load watchlist" bugs after the auth system was wired up.
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

WEB_USER_ID = "00000000-0000-0000-0000-000000000077"


@pytest_asyncio.fixture
async def web_user_client(seeded_db):
    """HTTP test client authenticated as a web-only user (no telegram_chat_id)."""
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


class TestWebUserPortfolio:
    """Portfolio endpoints must work for web users without telegram_chat_id."""

    @pytest.mark.asyncio
    async def test_list_trades_empty(self, web_user_client: AsyncClient) -> None:
        resp = await web_user_client.get("/api/v1/portfolio/trades")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"] == []

    @pytest.mark.asyncio
    async def test_log_trade(self, web_user_client: AsyncClient) -> None:
        trade = {
            "symbol": "HDFCBANK.NS",
            "market_type": "stock",
            "side": "buy",
            "quantity": "10",
            "price": "1650.00",
        }
        resp = await web_user_client.post("/api/v1/portfolio/trades", json=trade)
        assert resp.status_code == 201
        body = resp.json()
        assert body["data"]["symbol"] == "HDFCBANK.NS"

    @pytest.mark.asyncio
    async def test_logged_trade_appears_in_list(self, web_user_client: AsyncClient) -> None:
        trade = {
            "symbol": "BTCUSDT",
            "market_type": "crypto",
            "side": "buy",
            "quantity": "0.5",
            "price": "95000.00",
        }
        await web_user_client.post("/api/v1/portfolio/trades", json=trade)
        resp = await web_user_client.get("/api/v1/portfolio/trades")
        assert resp.status_code == 200
        symbols = [t["symbol"] for t in resp.json()["data"]]
        assert "BTCUSDT" in symbols

    @pytest.mark.asyncio
    async def test_portfolio_summary(self, web_user_client: AsyncClient) -> None:
        resp = await web_user_client.get("/api/v1/portfolio/summary")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body


class TestWebUserWatchlist:
    """Watchlist endpoints must work for web users without telegram_chat_id."""

    @pytest.mark.asyncio
    async def test_get_watchlist_empty(self, web_user_client: AsyncClient) -> None:
        resp = await web_user_client.get("/api/v1/alerts/watchlist")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"] == []

    @pytest.mark.asyncio
    async def test_add_to_watchlist(self, web_user_client: AsyncClient) -> None:
        resp = await web_user_client.post(
            "/api/v1/alerts/watchlist",
            json={"symbol": "RELIANCE.NS", "action": "add"},
        )
        assert resp.status_code == 200
        assert "RELIANCE.NS" in resp.json()["data"]

    @pytest.mark.asyncio
    async def test_remove_from_watchlist(self, web_user_client: AsyncClient) -> None:
        await web_user_client.post(
            "/api/v1/alerts/watchlist",
            json={"symbol": "RELIANCE.NS", "action": "add"},
        )
        resp = await web_user_client.post(
            "/api/v1/alerts/watchlist",
            json={"symbol": "RELIANCE.NS", "action": "remove"},
        )
        assert resp.status_code == 200
        assert "RELIANCE.NS" not in resp.json()["data"]


class TestWebUserPriceAlerts:
    """Price alert endpoints must work for web users without telegram_chat_id."""

    @pytest.mark.asyncio
    async def test_list_price_alerts_empty(self, web_user_client: AsyncClient) -> None:
        resp = await web_user_client.get("/api/v1/alerts/price")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"] == []

    @pytest.mark.asyncio
    async def test_create_price_alert(self, web_user_client: AsyncClient) -> None:
        alert = {
            "symbol": "BTCUSDT",
            "market_type": "crypto",
            "condition": "above",
            "threshold": "100000.00",
        }
        resp = await web_user_client.post("/api/v1/alerts/price", json=alert)
        assert resp.status_code == 201
        body = resp.json()
        assert body["data"]["symbol"] == "BTCUSDT"

    @pytest.mark.asyncio
    async def test_delete_price_alert(self, web_user_client: AsyncClient) -> None:
        alert = {
            "symbol": "ETHUSDT",
            "market_type": "crypto",
            "condition": "above",
            "threshold": "5000.00",
        }
        create_resp = await web_user_client.post("/api/v1/alerts/price", json=alert)
        alert_id = create_resp.json()["data"]["id"]
        del_resp = await web_user_client.delete(f"/api/v1/alerts/price/{alert_id}")
        assert del_resp.status_code == 200


class TestWebUserAlertConfig:
    """Alert config endpoints must work for web users without telegram_chat_id."""

    @pytest.mark.asyncio
    async def test_create_alert_config(self, web_user_client: AsyncClient) -> None:
        payload = {
            "username": "web_user",
            "markets": ["stock", "crypto"],
            "min_confidence": 70,
            "signal_types": ["STRONG_BUY", "BUY"],
        }
        resp = await web_user_client.post("/api/v1/alerts/config", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["data"]["min_confidence"] == 70
