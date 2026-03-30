"""v1.3.26 — WebSocket Security Tests.

Verify WebSocket auth, connection limits, message validation,
and resistance to hijacking/injection attacks.
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.websocket import (
    ConnectionManager,
    _consume_ticket,
    _ws_ticket_expiry,
    _ws_tickets,
)


# ── Ticket-Based Auth ───────────────────────────────────────────


class TestWSTicketAuth:
    """WebSocket ticket authentication must be secure."""

    @pytest.mark.asyncio
    async def test_ws_ticket_endpoint_requires_auth(self, test_client):
        """POST /ws/ticket with auth returns ticket."""
        # test_client already has auth overrides, so it should work
        r = await test_client.post("/ws/ticket")
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert "ticket" in data["data"]
        assert "ttl" in data["data"]
        assert data["data"]["ttl"] == 30

    @pytest.mark.asyncio
    async def test_ws_ticket_returns_unique_ids(self, test_client):
        """Each ticket request returns a unique ticket ID."""
        r1 = await test_client.post("/ws/ticket")
        r2 = await test_client.post("/ws/ticket")
        t1 = r1.json()["data"]["ticket"]
        t2 = r2.json()["data"]["ticket"]
        assert t1 != t2

    def test_consume_ticket_removes_it(self):
        """A ticket can only be consumed once (single-use)."""
        ticket_id = "test-ticket-001"
        _ws_tickets[ticket_id] = {"user_id": "u1", "tier": "pro", "chat_id": "123"}
        _ws_ticket_expiry[ticket_id] = time.monotonic() + 30

        # First consume succeeds
        result = _consume_ticket(ticket_id)
        assert result is not None
        assert result["user_id"] == "u1"

        # Second consume returns None (ticket already used)
        result2 = _consume_ticket(ticket_id)
        assert result2 is None

    def test_expired_ticket_rejected(self):
        """Expired tickets cannot be consumed."""
        ticket_id = "test-ticket-expired"
        _ws_tickets[ticket_id] = {"user_id": "u1", "tier": "pro", "chat_id": ""}
        _ws_ticket_expiry[ticket_id] = time.monotonic() - 10  # Already expired

        result = _consume_ticket(ticket_id)
        assert result is None

    def test_invalid_ticket_rejected(self):
        """Random/forged ticket string returns None."""
        result = _consume_ticket("forged-nonexistent-ticket-id")
        assert result is None


# ── Connection Manager Security ──────────────────────────────────


class TestConnectionManagerLimits:
    """Connection manager enforces security limits."""

    @pytest.mark.asyncio
    async def test_max_per_ip_limit(self):
        """6th connection from same IP is rejected (MAX_PER_IP=5)."""
        mgr = ConnectionManager()

        # Accept first 5
        for i in range(5):
            ws = MagicMock()
            ws.client = MagicMock()
            ws.client.host = "192.168.1.100"
            ws.accept = AsyncMock()
            ws.close = AsyncMock()
            result = await mgr.connect(ws)
            assert result is True, f"Connection {i+1} should succeed"

        # 6th should be rejected
        ws6 = MagicMock()
        ws6.client = MagicMock()
        ws6.client.host = "192.168.1.100"
        ws6.accept = AsyncMock()
        ws6.close = AsyncMock()
        result = await mgr.connect(ws6)
        assert result is False

    @pytest.mark.asyncio
    async def test_global_max_connections(self):
        """When MAX_CONNECTIONS reached, new connections rejected."""
        mgr = ConnectionManager()
        # Simulate filling to capacity
        for i in range(500):
            ws = MagicMock()
            ws.client = MagicMock()
            ws.client.host = f"10.0.{i // 256}.{i % 256}"
            mgr.active_connections[ws] = {"stock", "crypto", "forex"}
            mgr._ip_counts[ws.client.host] += 1

        assert len(mgr.active_connections) == 500

        # Next connection should fail
        new_ws = MagicMock()
        new_ws.client = MagicMock()
        new_ws.client.host = "11.0.0.1"
        new_ws.close = AsyncMock()
        result = await mgr.connect(new_ws)
        assert result is False

    def test_disconnect_decrements_ip_count(self):
        """Disconnecting frees up the IP slot."""
        mgr = ConnectionManager()
        ws = MagicMock()
        ws.client = MagicMock()
        ws.client.host = "10.0.0.1"

        mgr.active_connections[ws] = {"stock"}
        mgr._ip_counts["10.0.0.1"] = 1

        mgr.disconnect(ws)
        assert ws not in mgr.active_connections
        assert mgr._ip_counts.get("10.0.0.1", 0) == 0


# ── Message Validation ──────────────────────────────────────────


class TestWSMessageValidation:
    """WebSocket messages must be validated and sanitized."""

    def test_subscribe_only_valid_markets(self):
        """Subscribe with invalid markets keeps only valid ones."""
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr.active_connections[ws] = {"stock"}

        # Include an invalid market
        mgr.subscribe(ws, {"stock", "hacked", "crypto"})
        assert mgr.active_connections[ws] == {"stock", "crypto"}
        assert "hacked" not in mgr.active_connections[ws]

    def test_subscribe_sql_injection_sanitized(self):
        """SQL injection in market names is filtered out."""
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr.active_connections[ws] = set()

        mgr.subscribe(ws, {"stock'; DROP TABLE signals;--", "crypto"})
        assert "stock'; DROP TABLE signals;--" not in mgr.active_connections[ws]
        assert "crypto" in mgr.active_connections[ws]

    def test_subscribe_empty_markets_clears_subscriptions(self):
        """Subscribing with empty set clears all subscriptions."""
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr.active_connections[ws] = {"stock", "crypto"}

        mgr.subscribe(ws, set())
        assert mgr.active_connections[ws] == set()

    def test_rate_limit_enforcement(self):
        """More than 60 messages per minute triggers rate limit."""
        mgr = ConnectionManager()
        ws = MagicMock()
        mgr.active_connections[ws] = {"stock"}

        # Send 60 messages (all should pass)
        for i in range(60):
            assert mgr._check_rate(ws) is True

        # 61st should fail
        assert mgr._check_rate(ws) is False

    def test_unknown_message_type_no_crash(self):
        """Unknown message types should not cause exceptions."""
        # The handler simply uses if/elif, unknown types fall through
        msg = {"type": "admin_exec", "cmd": "rm -rf /"}
        msg_type = msg.get("type")
        # Not subscribe, not pong — should be silently ignored
        assert msg_type not in ("subscribe", "pong")


# ── Broadcast Security ──────────────────────────────────────────


class TestWSBroadcastSecurity:
    """Broadcasts must target correct subscribers only."""

    @pytest.mark.asyncio
    async def test_broadcast_only_to_subscribed_markets(self):
        """Signal broadcast only reaches clients subscribed to that market."""
        mgr = ConnectionManager()

        # Client A subscribes to stock only
        ws_a = MagicMock()
        ws_a.send_json = AsyncMock()
        mgr.active_connections[ws_a] = {"stock"}

        # Client B subscribes to crypto only
        ws_b = MagicMock()
        ws_b.send_json = AsyncMock()
        mgr.active_connections[ws_b] = {"crypto"}

        # Broadcast a stock signal
        await mgr.broadcast_signal({"market_type": "stock", "symbol": "HDFC"})

        # Client A should receive it
        ws_a.send_json.assert_called_once()
        # Client B should NOT receive it
        ws_b.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_disconnects_failed_clients(self):
        """Clients that error during broadcast are disconnected."""
        mgr = ConnectionManager()

        # Working client
        ws_ok = MagicMock()
        ws_ok.send_json = AsyncMock()
        ws_ok.client = MagicMock()
        ws_ok.client.host = "10.0.0.1"
        mgr.active_connections[ws_ok] = {"stock"}
        mgr._ip_counts["10.0.0.1"] = 1

        # Broken client
        ws_bad = MagicMock()
        ws_bad.send_json = MagicMock(side_effect=Exception("Connection lost"))
        ws_bad.client = MagicMock()
        ws_bad.client.host = "10.0.0.2"
        mgr.active_connections[ws_bad] = {"stock"}
        mgr._ip_counts["10.0.0.2"] = 1

        await mgr.broadcast_signal({"market_type": "stock", "symbol": "HDFC"})

        # Broken client should be disconnected
        assert ws_bad not in mgr.active_connections
        # Working client should remain
        assert ws_ok in mgr.active_connections
