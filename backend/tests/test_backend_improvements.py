"""Tests for rate limiting, health endpoint, and WebSocket pings."""

import json

from starlette.testclient import TestClient

from app.main import app


class TestHealthEndpoint:
    """Test the enhanced health check endpoint."""

    def test_health_returns_status(self) -> None:
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded")
        assert "environment" in data
        assert "disclaimer" in data

    def test_health_has_db_and_redis_status(self) -> None:
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()
        # db_status and redis_status should be present (may be ok or error depending on env)
        assert "db_status" in data
        assert data["db_status"] in ("ok", "error")
        assert "redis_status" in data
        assert data["redis_status"] in ("ok", "error")

    def test_health_has_uptime(self) -> None:
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()
        assert "uptime" in data


class TestRateLimiting:
    """Test that rate limiting is configured."""

    def test_rate_limiter_is_configured(self) -> None:
        """Verify the limiter instance is attached to the app."""
        assert hasattr(app.state, "limiter")
        assert app.state.limiter is not None


class TestWebSocketPing:
    """Test that WebSocket connections work with the ping system."""

    def test_websocket_connect_and_subscribe(self) -> None:
        import time

        from app.api.websocket import _ws_ticket_expiry, _ws_tickets

        # Create a valid ticket
        ticket_id = "test-ticket-backend-001"
        _ws_tickets[ticket_id] = {"user_id": "user-123", "tier": "free", "chat_id": None}
        _ws_ticket_expiry[ticket_id] = time.monotonic() + 30

        client = TestClient(app)
        with client.websocket_connect(f"/ws/signals?ticket={ticket_id}") as ws:
            ws.send_text(json.dumps({
                "type": "subscribe",
                "markets": ["stock", "crypto"],
            }))
            # Send a pong response (as if responding to a server ping)
            ws.send_text(json.dumps({"type": "pong"}))

    def test_websocket_handles_malformed_json(self) -> None:
        import time

        from app.api.websocket import _ws_ticket_expiry, _ws_tickets

        # Create a valid ticket
        ticket_id = "test-ticket-backend-002"
        _ws_tickets[ticket_id] = {"user_id": "user-456", "tier": "free", "chat_id": None}
        _ws_ticket_expiry[ticket_id] = time.monotonic() + 30

        client = TestClient(app)
        with client.websocket_connect(f"/ws/signals?ticket={ticket_id}") as ws:
            ws.send_text("{malformed")
            # Connection survives
            ws.send_text(json.dumps({"type": "pong"}))
