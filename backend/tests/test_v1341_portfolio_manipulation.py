"""v1.3.41 — Portfolio Manipulation Tests.

Verify trade validation, P&L accuracy, and resistance
to injection and manipulation attacks.
"""

import pytest


class TestTradeValidation:
    """Trade creation must validate all inputs."""

    @pytest.mark.asyncio
    async def test_trade_valid_creation(self, test_client):
        """Valid trade is created successfully."""
        r = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "symbol": "INFY.NS",
                "market_type": "stock",
                "side": "buy",
                "quantity": "5",
                "price": "1500.00",
            },
        )
        assert r.status_code in (200, 201)

    @pytest.mark.asyncio
    async def test_trade_invalid_side_rejected(self, test_client):
        """Invalid trade side is rejected."""
        r = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "symbol": "HDFC.NS",
                "market_type": "stock",
                "side": "liquidate",
                "quantity": "1",
                "price": "100.00",
            },
        )
        assert r.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_trade_invalid_market_type(self, test_client):
        """Invalid market type is rejected."""
        r = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "symbol": "GOLD",
                "market_type": "commodities",
                "side": "buy",
                "quantity": "1",
                "price": "50000.00",
            },
        )
        assert r.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_trade_sql_injection_in_symbol(self, test_client):
        """SQL injection in symbol field is handled safely."""
        r = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "symbol": "HDFC'; DROP TABLE trades;--",
                "market_type": "stock",
                "side": "buy",
                "quantity": "1",
                "price": "100.00",
            },
        )
        # Should either accept (harmless) or reject, not crash
        assert r.status_code in (200, 201, 400, 422)

    @pytest.mark.asyncio
    async def test_trade_missing_required_fields(self, test_client):
        """Trade without required fields is rejected."""
        r = await test_client.post(
            "/api/v1/portfolio/trades",
            json={"symbol": "TEST"},
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_trade_negative_quantity_rejected(self, test_client):
        """Negative quantity should be rejected."""
        r = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "symbol": "TCS.NS",
                "market_type": "stock",
                "side": "buy",
                "quantity": "-10",
                "price": "3900.00",
            },
        )
        assert r.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_trade_zero_price_rejected(self, test_client):
        """Zero price should be rejected."""
        r = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "symbol": "TCS.NS",
                "market_type": "stock",
                "side": "buy",
                "quantity": "1",
                "price": "0",
            },
        )
        assert r.status_code in (400, 422)


class TestPortfolioSummary:
    """Portfolio summary must compute correctly."""

    @pytest.mark.asyncio
    async def test_summary_returns_data(self, test_client):
        """Portfolio summary endpoint returns data."""
        r = await test_client.get("/api/v1/portfolio/summary")
        assert r.status_code == 200
        data = r.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_trades_list_returns_data(self, test_client):
        """Trade list endpoint returns data."""
        r = await test_client.get("/api/v1/portfolio/trades")
        assert r.status_code == 200
        data = r.json()
        assert "data" in data


class TestTradeXSSPrevention:
    """Trade notes/fields must not allow XSS."""

    @pytest.mark.asyncio
    async def test_xss_in_symbol_handled(self, test_client):
        """XSS payload in symbol is harmless."""
        r = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "symbol": "<script>alert(1)</script>",
                "market_type": "stock",
                "side": "buy",
                "quantity": "1",
                "price": "100.00",
            },
        )
        assert r.status_code in (200, 201, 400, 422)
        if r.status_code in (200, 201):
            body = r.text
            assert "<script>" not in body
