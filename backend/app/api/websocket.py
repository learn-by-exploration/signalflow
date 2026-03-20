"""WebSocket endpoint for real-time signal streaming."""

import json
import logging
from collections.abc import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections and market subscriptions."""

    def __init__(self) -> None:
        self.active_connections: dict[WebSocket, set[str]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[websocket] = {"stock", "crypto", "forex"}

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        self.active_connections.pop(websocket, None)

    def subscribe(self, websocket: WebSocket, markets: Set[str]) -> None:
        """Update market subscriptions for a connection."""
        valid = {"stock", "crypto", "forex"}
        self.active_connections[websocket] = valid & set(markets)

    async def broadcast_signal(self, signal_data: dict) -> None:
        """Send a signal to all connected clients subscribed to its market."""
        market = signal_data.get("market_type", "")
        disconnected = []
        for ws, markets in self.active_connections.items():
            if market in markets:
                try:
                    await ws.send_json({"type": "signal", "data": signal_data})
                except Exception:
                    disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)

    async def broadcast_market_update(self, update_data: dict) -> None:
        """Send a market price update to all connected clients."""
        disconnected = []
        for ws in self.active_connections:
            try:
                await ws.send_json({"type": "market_update", "data": update_data})
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)


manager = ConnectionManager()


@router.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time signal and market updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                continue

            msg_type = message.get("type")
            if msg_type == "subscribe":
                markets = message.get("markets", [])
                manager.subscribe(websocket, set(markets))
            elif msg_type == "pong":
                pass  # Client heartbeat acknowledgment
    except WebSocketDisconnect:
        manager.disconnect(websocket)
