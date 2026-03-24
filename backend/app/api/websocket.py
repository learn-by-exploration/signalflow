"""WebSocket endpoint for real-time signal streaming."""

import asyncio
import json
import logging
import time
from collections import defaultdict
from collections.abc import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()

# Connection limits
MAX_CONNECTIONS = 500
MAX_PER_IP = 5
IDLE_TIMEOUT = 300  # seconds
MAX_MSG_PER_MIN = 60


class ConnectionManager:
    """Manages active WebSocket connections and market subscriptions."""

    def __init__(self) -> None:
        self.active_connections: dict[WebSocket, set[str]] = {}
        self._ip_counts: dict[str, int] = defaultdict(int)
        self._last_activity: dict[WebSocket, float] = {}
        self._msg_counts: dict[WebSocket, list[float]] = defaultdict(list)

    def _client_ip(self, websocket: WebSocket) -> str:
        return websocket.client.host if websocket.client else "unknown"

    async def connect(self, websocket: WebSocket) -> bool:
        """Accept and register a new WebSocket connection. Returns False if rejected."""
        if len(self.active_connections) >= MAX_CONNECTIONS:
            await websocket.close(code=1013, reason="Server at capacity")
            return False

        ip = self._client_ip(websocket)
        if self._ip_counts[ip] >= MAX_PER_IP:
            await websocket.close(code=1008, reason="Too many connections from this IP")
            return False

        await websocket.accept()
        self.active_connections[websocket] = {"stock", "crypto", "forex"}
        self._ip_counts[ip] += 1
        self._last_activity[websocket] = time.monotonic()
        return True

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            ip = self._client_ip(websocket)
            self._ip_counts[ip] = max(0, self._ip_counts[ip] - 1)
            if self._ip_counts[ip] == 0:
                self._ip_counts.pop(ip, None)
        self.active_connections.pop(websocket, None)
        self._last_activity.pop(websocket, None)
        self._msg_counts.pop(websocket, None)

    def _check_rate(self, websocket: WebSocket) -> bool:
        """Return True if the client hasn't exceeded message rate limit."""
        now = time.monotonic()
        timestamps = self._msg_counts[websocket]
        # Remove timestamps older than 60 seconds
        self._msg_counts[websocket] = [t for t in timestamps if now - t < 60]
        if len(self._msg_counts[websocket]) >= MAX_MSG_PER_MIN:
            return False
        self._msg_counts[websocket].append(now)
        return True

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
    connected = await manager.connect(websocket)
    if not connected:
        return

    async def send_pings() -> None:
        """Send heartbeat pings every 30 seconds and disconnect idle clients."""
        try:
            while True:
                await asyncio.sleep(30)
                # Check idle timeout
                last = manager._last_activity.get(websocket, 0)
                if time.monotonic() - last > IDLE_TIMEOUT:
                    try:
                        await websocket.close(code=1000, reason="Idle timeout")
                    except Exception:
                        pass
                    break
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
        except asyncio.CancelledError:
            pass

    ping_task = asyncio.create_task(send_pings())

    try:
        while True:
            data = await websocket.receive_text()
            manager._last_activity[websocket] = time.monotonic()

            if not manager._check_rate(websocket):
                await websocket.send_json({"type": "error", "message": "Rate limit exceeded"})
                continue

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
        pass
    finally:
        ping_task.cancel()
        manager.disconnect(websocket)
