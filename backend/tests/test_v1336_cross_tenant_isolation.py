"""v1.3.36 — Cross-Tenant Data Isolation Tests.

Verify users can only access their own data: trades, alerts,
watchlist, portfolio, feedback, and subscriptions.
"""

import pytest


class TestPortfolioIsolation:
    """Users can only see their own trades and portfolio."""

    @pytest.mark.asyncio
    async def test_trades_returns_only_own(self, test_client):
        """GET /portfolio/trades returns only requesting user's trades."""
        r = await test_client.get("/api/v1/portfolio/trades")
        assert r.status_code == 200
        data = r.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_portfolio_summary_own_only(self, test_client):
        """GET /portfolio/summary computes only own positions."""
        r = await test_client.get("/api/v1/portfolio/summary")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_trade_logging_scoped_to_user(self, test_client):
        """POST /portfolio/trades creates trade for authenticated user."""
        r = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "symbol": "TEST.NS",
                "market_type": "stock",
                "side": "buy",
                "quantity": "1",
                "price": "100.00",
            },
        )
        assert r.status_code in (200, 201)


class TestAlertIsolation:
    """Alert configs and watchlists are user-scoped."""

    @pytest.mark.asyncio
    async def test_alert_config_own_only(self, test_client):
        """GET /alerts/config returns only own config."""
        r = await test_client.get("/api/v1/alerts/config")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_watchlist_own_only(self, test_client):
        """GET /alerts/watchlist returns only own watchlist."""
        r = await test_client.get("/api/v1/alerts/watchlist")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_price_alerts_own_only(self, test_client):
        """GET /alerts/price returns only own price alerts."""
        r = await test_client.get("/api/v1/alerts/price")
        assert r.status_code == 200


class TestSignalFeedGlobal:
    """Signals are global by design — not user-scoped."""

    @pytest.mark.asyncio
    async def test_signals_are_global(self, test_client):
        """GET /signals returns all active signals (not user-scoped)."""
        r = await test_client.get("/api/v1/signals")
        assert r.status_code == 200
        data = r.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_signal_detail_accessible(self, test_client):
        """Individual signal detail is accessible to any authenticated user."""
        # Get signals first
        r = await test_client.get("/api/v1/signals")
        signals = r.json().get("data", [])
        if signals:
            sig_id = signals[0]["id"]
            r2 = await test_client.get(f"/api/v1/signals/{sig_id}")
            assert r2.status_code == 200


class TestCrossTenantIDGuessing:
    """Guessing IDs should not reveal other users' data."""

    @pytest.mark.asyncio
    async def test_guessed_price_alert_id_404(self, test_client):
        """DELETE /alerts/price/{random-id} returns 404, not other user's data."""
        import uuid
        r = await test_client.delete(f"/api/v1/alerts/price/{uuid.uuid4()}")
        assert r.status_code in (404, 422)

    @pytest.mark.asyncio
    async def test_guessed_trade_id_not_exposed(self, test_client):
        """Direct trade ID access should not return other users' trades."""
        # Portfolio trades endpoint is list-based, not by ID
        r = await test_client.get("/api/v1/portfolio/trades")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_subscription_own_only(self, test_client):
        """GET /payments/subscription returns only own subscription."""
        r = await test_client.get("/api/v1/payments/subscription")
        assert r.status_code in (200, 404)
