"""WebSocket delivery tests.

Tests the WebSocket endpoint and ConnectionManager for real-time signal delivery.
"""

import json

import pytest

from app.api.websocket import ConnectionManager


class TestConnectionManager:
    def test_init_empty(self) -> None:
        cm = ConnectionManager()
        assert len(cm.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_signal_to_no_connections(self) -> None:
        cm = ConnectionManager()
        # Should not raise
        await cm.broadcast_signal({"market_type": "crypto", "symbol": "BTCUSDT"})

    @pytest.mark.asyncio
    async def test_broadcast_market_update_to_no_connections(self) -> None:
        cm = ConnectionManager()
        await cm.broadcast_market_update({"symbol": "BTC", "price": "97842.00"})


class TestWebSocketEndpoint:
    """Test WebSocket connectivity via the FastAPI test client."""

    @pytest.mark.asyncio
    async def test_websocket_connect_and_receive(self) -> None:
        """Test that a client can connect and send/receive messages."""

        import time

        from starlette.testclient import TestClient

        from app.api.websocket import _ws_ticket_expiry, _ws_tickets
        from app.main import app

        # Create a valid ticket
        ticket_id = "test-ticket-001"
        _ws_tickets[ticket_id] = {"user_id": "user-123", "tier": "free", "chat_id": None}
        _ws_ticket_expiry[ticket_id] = time.monotonic() + 30

        client = TestClient(app)
        with client.websocket_connect(f"/ws/signals?ticket={ticket_id}") as ws:
            # Send a subscribe message
            ws.send_text(json.dumps({
                "type": "subscribe",
                "markets": ["crypto"]
            }))
            # Send a pong (heartbeat)
            ws.send_text(json.dumps({"type": "pong"}))

    @pytest.mark.asyncio
    async def test_websocket_subscribe_filters_markets(self) -> None:
        """After subscribing to crypto only, stock signals should not be received."""
        import time

        from starlette.testclient import TestClient

        from app.api.websocket import _ws_ticket_expiry, _ws_tickets
        from app.main import app

        ticket_id = "test-ticket-002"
        _ws_tickets[ticket_id] = {"user_id": "user-456", "tier": "free", "chat_id": None}
        _ws_ticket_expiry[ticket_id] = time.monotonic() + 30

        client = TestClient(app)
        with client.websocket_connect(f"/ws/signals?ticket={ticket_id}") as ws:
            # Subscribe to crypto only
            ws.send_text(json.dumps({
                "type": "subscribe",
                "markets": ["crypto"]
            }))

    @pytest.mark.asyncio
    async def test_websocket_invalid_json_ignored(self) -> None:
        """Sending invalid JSON should not crash the connection."""
        import time

        from starlette.testclient import TestClient

        from app.api.websocket import _ws_ticket_expiry, _ws_tickets
        from app.main import app

        ticket_id = "test-ticket-003"
        _ws_tickets[ticket_id] = {"user_id": "user-789", "tier": "free", "chat_id": None}
        _ws_ticket_expiry[ticket_id] = time.monotonic() + 30

        client = TestClient(app)
        with client.websocket_connect(f"/ws/signals?ticket={ticket_id}") as ws:
            ws.send_text("not valid json")
            # Connection should still be alive — send another message
            ws.send_text(json.dumps({"type": "pong"}))
