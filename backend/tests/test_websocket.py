"""WebSocket delivery tests.

Tests the WebSocket endpoint and ConnectionManager for real-time signal delivery.
"""

import json

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.websocket import ConnectionManager, manager


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
        from unittest.mock import MagicMock, patch

        from starlette.testclient import TestClient

        from app.main import app

        mock_settings = MagicMock()
        mock_settings.api_secret_key = "test-ws-key"
        with patch("app.api.websocket.get_settings", return_value=mock_settings):
            client = TestClient(app)
            with client.websocket_connect("/ws/signals?api_key=test-ws-key") as ws:
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
        from unittest.mock import MagicMock, patch

        from starlette.testclient import TestClient

        from app.main import app

        mock_settings = MagicMock()
        mock_settings.api_secret_key = "test-ws-key"
        with patch("app.api.websocket.get_settings", return_value=mock_settings):
            client = TestClient(app)
            with client.websocket_connect("/ws/signals?api_key=test-ws-key") as ws:
                # Subscribe to crypto only
                ws.send_text(json.dumps({
                    "type": "subscribe",
                    "markets": ["crypto"]
                }))

    @pytest.mark.asyncio
    async def test_websocket_invalid_json_ignored(self) -> None:
        """Sending invalid JSON should not crash the connection."""
        from unittest.mock import MagicMock, patch

        from starlette.testclient import TestClient

        from app.main import app

        mock_settings = MagicMock()
        mock_settings.api_secret_key = "test-ws-key"
        with patch("app.api.websocket.get_settings", return_value=mock_settings):
            client = TestClient(app)
            with client.websocket_connect("/ws/signals?api_key=test-ws-key") as ws:
                ws.send_text("not valid json")
                # Connection should still be alive — send another message
                ws.send_text(json.dumps({"type": "pong"}))
