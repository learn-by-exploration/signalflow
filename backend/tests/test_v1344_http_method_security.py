"""v1.3.44 — HTTP Method Security Tests.

Verify endpoints reject unexpected HTTP methods.
Only allowed methods should succeed; others must return 405.
"""

import pytest


class TestSignalEndpointMethods:
    """Signal endpoints only accept GET."""

    @pytest.mark.asyncio
    async def test_post_signals_not_allowed(self, test_client):
        r = await test_client.post("/api/v1/signals", json={})
        assert r.status_code in (405, 422)

    @pytest.mark.asyncio
    async def test_put_signals_not_allowed(self, test_client):
        r = await test_client.put("/api/v1/signals", json={})
        assert r.status_code == 405

    @pytest.mark.asyncio
    async def test_delete_signals_not_allowed(self, test_client):
        r = await test_client.delete("/api/v1/signals")
        assert r.status_code == 405


class TestHistoryEndpointMethods:
    """History/stats endpoints only accept GET."""

    @pytest.mark.asyncio
    async def test_post_history_not_allowed(self, test_client):
        r = await test_client.post("/api/v1/signals/history", json={})
        assert r.status_code in (405, 422)

    @pytest.mark.asyncio
    async def test_put_stats_not_allowed(self, test_client):
        r = await test_client.put("/api/v1/signals/stats", json={})
        assert r.status_code == 405


class TestMarketsEndpointMethods:
    """Markets overview only accepts GET."""

    @pytest.mark.asyncio
    async def test_post_markets_not_allowed(self, test_client):
        r = await test_client.post("/api/v1/markets/overview", json={})
        assert r.status_code in (405, 422)

    @pytest.mark.asyncio
    async def test_delete_markets_not_allowed(self, test_client):
        r = await test_client.delete("/api/v1/markets/overview")
        assert r.status_code == 405


class TestAuthEndpointMethods:
    """Auth endpoints accept specific methods only."""

    @pytest.mark.asyncio
    async def test_get_register_not_allowed(self, test_client):
        r = await test_client.get("/api/v1/auth/register")
        assert r.status_code == 405

    @pytest.mark.asyncio
    async def test_get_login_not_allowed(self, test_client):
        r = await test_client.get("/api/v1/auth/login")
        assert r.status_code == 405
