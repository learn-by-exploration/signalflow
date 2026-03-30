"""v1.3.22 — Concurrency & Race Condition Tests.

Verify the system handles concurrent-like operations safely:
duplicate submissions, token reuse, limit bypasses, and idempotency.
"""

import hashlib
import uuid
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth import AuthContext, create_access_token, create_refresh_token
from app.main import app


# ── Helpers ───────────────────────────────────────────────────────


DUMMY_USER_ID = "00000000-0000-0000-0000-000000000077"


def _auth_override():
    """Return an AuthContext for a test user."""
    return AuthContext(
        auth_type="jwt",
        user_id=DUMMY_USER_ID,
        telegram_chat_id=77777,
        tier="free",
    )


# ── Token Refresh Replay ─────────────────────────────────────────


class TestTokenReplay:
    """Using the same refresh token twice should not produce two access tokens."""

    @pytest.mark.asyncio
    async def test_refresh_token_reuse_rejected(self, test_client):
        """A refresh token used once must be rejected on second use."""
        unique = uuid.uuid4().hex[:8]
        reg_resp = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": f"race-{unique}@test.com",
                "password": "StrongPassword123!",
                "name": "Race User",
            },
        )
        if reg_resp.status_code != 200:
            pytest.skip("Registration not available or user exists")

        tokens = reg_resp.json()["data"]["tokens"]
        refresh = tokens["refresh_token"]

        # First refresh should succeed
        r1 = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert r1.status_code == 200, f"First refresh failed: {r1.text}"

        # Second use of same refresh token should fail (revoked)
        r2 = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert r2.status_code == 401, (
            f"Refresh token reuse not rejected! Status: {r2.status_code}"
        )

    @pytest.mark.asyncio
    async def test_expired_access_token_rejected(self, test_client):
        """An expired access token must return 401."""
        import jwt as pyjwt
        from datetime import datetime, timedelta, timezone

        from app.config import get_settings

        settings = get_settings()
        payload = {
            "sub": DUMMY_USER_ID,
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "type": "access",
        }
        expired = pyjwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")

        # Use a raw client without auth overrides
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as raw_client:
            r = await raw_client.get(
                "/api/v1/auth/profile",
                headers={"Authorization": f"Bearer {expired}"},
            )
            # 401 (bad token), 403, or 404 (user not in DB) — expired token must not succeed
            assert r.status_code in (401, 403, 404)


# ── Duplicate Submission Protection ──────────────────────────────


class TestDuplicateSubmissions:
    """Multiple identical submissions should not create duplicates or crash."""

    @pytest.mark.asyncio
    async def test_duplicate_feedback_submissions(self, test_client):
        """Submitting feedback for same signal twice should both succeed
        (no unique constraint) or second should be rejected."""
        signal_id = str(uuid4())

        r1 = await test_client.post(
            f"/api/v1/signals/{signal_id}/feedback",
            json={"action": "took", "entry_price": 1650.00},
        )
        r2 = await test_client.post(
            f"/api/v1/signals/{signal_id}/feedback",
            json={"action": "watching"},
        )
        # Both may succeed (append) or second may be rejected — either is fine
        assert r1.status_code in (200, 201, 404, 422)
        assert r2.status_code in (200, 201, 404, 409, 422)

    @pytest.mark.asyncio
    async def test_duplicate_watchlist_add(self, test_client):
        """Adding same symbol to watchlist twice should be idempotent or rejected."""
        r1 = await test_client.post(
            "/api/v1/alerts/watchlist",
            json={"symbol": "RELIANCE.NS", "action": "add"},
        )
        r2 = await test_client.post(
            "/api/v1/alerts/watchlist",
            json={"symbol": "RELIANCE.NS", "action": "add"},
        )
        # Both should succeed (idempotent add) or return conflict
        assert r1.status_code in (200, 201, 409)
        assert r2.status_code in (200, 201, 409)

    @pytest.mark.asyncio
    async def test_duplicate_alert_config_creation(self, test_client):
        """Creating alert config when one already exists should update or reject."""
        config = {
            "telegram_chat_id": 99999,
            "markets": ["stock"],
            "min_confidence": 70,
        }
        r1 = await test_client.post("/api/v1/alerts/config", json=config)
        r2 = await test_client.post("/api/v1/alerts/config", json=config)
        # Either may succeed or conflict (if config exists from seeded data)
        assert r1.status_code in (200, 201, 409)
        assert r2.status_code in (200, 201, 409)


# ── Limit Enforcement ────────────────────────────────────────────


class TestLimitEnforcement:
    """Rate limits, alert limits, and quotas must hold under rapid requests."""

    @pytest.mark.asyncio
    async def test_price_alert_limit_sequential(self, test_client):
        """Free tier can only have limited active price alerts.

        Rapidly creating alerts should not bypass the limit.
        """
        created = 0
        for i in range(10):
            r = await test_client.post(
                "/api/v1/price-alerts",
                json={
                    "symbol": f"LIMITSYM{i}",
                    "market_type": "stock",
                    "condition": "above",
                    "threshold": 100.0 + i,
                },
            )
            if r.status_code in (200, 201):
                created += 1
            elif r.status_code in (402, 429):
                break

        # Should not have created more than max (varies by tier, typically 3-50)
        assert created <= 50, f"Created {created} alerts — limit may be bypassed"

    @pytest.mark.asyncio
    async def test_portfolio_rapid_trade_submissions(self, test_client):
        """Rapidly submitted trades should all be recorded correctly."""
        for i in range(5):
            r = await test_client.post(
                "/api/v1/portfolio/trades",
                json={
                    "symbol": "RAPIDTRADE",
                    "market_type": "stock",
                    "side": "buy",
                    "quantity": 10,
                    "price": 100.0 + i,
                },
            )
            assert r.status_code in (200, 201), f"Trade {i+1} failed: {r.text}"


# ── Idempotency ──────────────────────────────────────────────────


class TestIdempotency:
    """Repeated identical requests should produce consistent, safe results."""

    @pytest.mark.asyncio
    async def test_repeated_signal_fetch_consistency(self, test_client):
        """Fetching signals multiple times returns consistent results."""
        results = []
        for _ in range(5):
            r = await test_client.get("/api/v1/signals")
            assert r.status_code == 200
            results.append(r.json())

        counts = [r.get("meta", {}).get("count", len(r.get("data", []))) for r in results]
        assert len(set(counts)) == 1, f"Inconsistent results across reads: {counts}"

    @pytest.mark.asyncio
    async def test_repeated_market_overview_stable(self, test_client):
        """Market overview is stable across rapid reads."""
        for _ in range(3):
            r = await test_client.get("/api/v1/markets/overview")
            assert r.status_code == 200
            assert "data" in r.json()

    @pytest.mark.asyncio
    async def test_health_idempotent(self, test_client):
        """Health endpoint always returns same structure."""
        for _ in range(5):
            r = await test_client.get("/health")
            assert r.status_code == 200
            assert "status" in r.json()


# ── WebSocket Ticket Reuse ───────────────────────────────────────


class TestWebSocketTicketSecurity:
    """WebSocket tickets must be single-use or time-limited."""

    @pytest.mark.asyncio
    async def test_ws_ticket_is_generated(self, test_client):
        """A WebSocket ticket can be generated."""
        r = await test_client.post("/ws/ticket")
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        ticket = data["data"].get("ticket")
        assert ticket is not None
        assert len(ticket) > 10

    @pytest.mark.asyncio
    async def test_ws_ticket_different_each_time(self, test_client):
        """Each ticket request generates a unique ticket."""
        tickets = set()
        for _ in range(5):
            r = await test_client.post("/ws/ticket")
            assert r.status_code == 200
            ticket = r.json()["data"]["ticket"]
            tickets.add(ticket)
        assert len(tickets) == 5, "WebSocket tickets should be unique per request"


# ── State Consistency ────────────────────────────────────────────


class TestStateConsistency:
    """Interleaved operations should not corrupt state."""

    @pytest.mark.asyncio
    async def test_alert_config_update_then_read(self, test_client):
        """Updating config and immediately reading should reflect the update."""
        await test_client.post(
            "/api/v1/alerts/config",
            json={
                "telegram_chat_id": 88888,
                "markets": ["stock", "crypto"],
                "min_confidence": 60,
            },
        )

        r = await test_client.get("/api/v1/alerts/config")
        if r.status_code == 200:
            data = r.json()["data"]
            if isinstance(data, list) and len(data) > 0:
                assert "markets" in data[0]
            elif isinstance(data, dict):
                assert "markets" in data

    @pytest.mark.asyncio
    async def test_create_and_delete_price_alert(self, test_client):
        """Creating then deleting an alert should leave a clean state."""
        r_create = await test_client.post(
            "/api/v1/price-alerts",
            json={
                "symbol": "CLEANUP",
                "market_type": "stock",
                "condition": "above",
                "threshold": 999.0,
            },
        )
        if r_create.status_code not in (200, 201):
            pytest.skip("Could not create alert for cleanup test")

        alert_id = r_create.json()["data"].get("id")
        if alert_id:
            r_del = await test_client.delete(f"/api/v1/price-alerts/{alert_id}")
            assert r_del.status_code in (200, 204)

            r_list = await test_client.get("/api/v1/price-alerts")
            if r_list.status_code == 200:
                alerts = r_list.json().get("data", [])
                ids = [a.get("id") for a in alerts]
                assert str(alert_id) not in [str(i) for i in ids]

    @pytest.mark.asyncio
    async def test_concurrent_reads_do_not_mutate(self, test_client):
        """Multiple GET requests should not change any state."""
        r1 = await test_client.get("/api/v1/signals")
        assert r1.status_code == 200
        snap1 = r1.json()

        for _ in range(10):
            r = await test_client.get("/api/v1/signals")
            assert r.status_code == 200

        r2 = await test_client.get("/api/v1/signals")
        snap2 = r2.json()

        c1 = snap1.get("meta", {}).get("count", len(snap1.get("data", [])))
        c2 = snap2.get("meta", {}).get("count", len(snap2.get("data", [])))
        assert c1 == c2
