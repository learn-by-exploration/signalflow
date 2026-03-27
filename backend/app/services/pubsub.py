"""Redis PubSub broadcast layer for WebSocket multi-worker support.

Enables WebSocket signal broadcast across multiple uvicorn workers
by publishing to Redis channels and fanning out to local connections.

Channels:
- ws:signal:{market_type} — New signal for a specific market
- ws:market:{market_type} — Market price update
- ws:all — Broadcast to all connected clients
"""

import asyncio
import json
import logging
import time
from collections import deque
from typing import Any

logger = logging.getLogger(__name__)

# Channel names
CHANNEL_PREFIX = "ws"
SIGNAL_CHANNELS = ["ws:signal:stock", "ws:signal:crypto", "ws:signal:forex"]
MARKET_CHANNELS = ["ws:market:stock", "ws:market:crypto", "ws:market:forex"]
ALL_CHANNEL = "ws:all"
ALL_CHANNELS = SIGNAL_CHANNELS + MARKET_CHANNELS + [ALL_CHANNEL]

# Backpressure: max queued messages per client
MAX_CLIENT_QUEUE = 50

# Reconnection settings
INITIAL_RECONNECT_DELAY = 1.0  # seconds
MAX_RECONNECT_DELAY = 30.0
RECONNECT_BACKOFF_FACTOR = 2.0


class PubSubBroadcaster:
    """Manages Redis PubSub subscription and fan-out to local WebSocket connections.

    Each uvicorn worker creates one instance that:
    1. Subscribes to all ws:* channels
    2. On message: decodes and fans out to local ConnectionManager clients
    3. Handles reconnection with exponential backoff

    Args:
        redis_url: Redis connection URL.
        connection_manager: The local WebSocket ConnectionManager instance.
    """

    def __init__(self, redis_url: str, connection_manager: Any) -> None:
        self.redis_url = redis_url
        self.manager = connection_manager
        self._pubsub: Any = None
        self._redis: Any = None
        self._listener_task: asyncio.Task | None = None
        self._is_connected = False
        self._reconnect_delay = INITIAL_RECONNECT_DELAY
        self._should_run = False

    @property
    def is_connected(self) -> bool:
        """Whether PubSub is actively connected and listening."""
        return self._is_connected

    async def start(self) -> None:
        """Start the PubSub listener in a background task."""
        self._should_run = True
        self._listener_task = asyncio.create_task(self._listen_loop())
        logger.info("pubsub_broadcaster_started")

    async def stop(self) -> None:
        """Gracefully stop the PubSub listener."""
        self._should_run = False
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        await self._cleanup()
        logger.info("pubsub_broadcaster_stopped")

    async def _listen_loop(self) -> None:
        """Main loop: connect, subscribe, listen. Reconnect on failure."""
        while self._should_run:
            try:
                await self._connect_and_subscribe()
                self._is_connected = True
                self._reconnect_delay = INITIAL_RECONNECT_DELAY
                logger.info("pubsub_connected", channels=ALL_CHANNELS)

                # Listen for messages
                while self._should_run:
                    message = await self._pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=1.0
                    )
                    if message and message["type"] == "message":
                        await self._handle_message(message)

            except asyncio.CancelledError:
                break
            except Exception:
                self._is_connected = False
                logger.warning(
                    "pubsub_disconnected",
                    reconnect_in=self._reconnect_delay,
                )
                await self._cleanup()

                if not self._should_run:
                    break

                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * RECONNECT_BACKOFF_FACTOR,
                    MAX_RECONNECT_DELAY,
                )

    async def _connect_and_subscribe(self) -> None:
        """Create Redis connection and subscribe to all channels."""
        import redis.asyncio as aioredis

        self._redis = aioredis.from_url(
            self.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(*ALL_CHANNELS)

    async def _cleanup(self) -> None:
        """Close Redis connections."""
        try:
            if self._pubsub:
                await self._pubsub.unsubscribe()
                await self._pubsub.close()
        except Exception:
            pass
        try:
            if self._redis:
                await self._redis.aclose()
        except Exception:
            pass
        self._pubsub = None
        self._redis = None
        self._is_connected = False

    async def _handle_message(self, message: dict) -> None:
        """Route a PubSub message to the appropriate broadcast method."""
        try:
            channel = message["channel"]
            data = json.loads(message["data"])

            if channel.startswith("ws:signal:"):
                market_type = channel.split(":")[-1]
                await self.manager.broadcast_signal(data, source="pubsub")
            elif channel.startswith("ws:market:"):
                await self.manager.broadcast_market_update(data, source="pubsub")
            elif channel == ALL_CHANNEL:
                await self.manager.broadcast_all(data, source="pubsub")

        except json.JSONDecodeError:
            logger.warning("pubsub_invalid_json", channel=message.get("channel"))
        except Exception:
            logger.exception("pubsub_message_handler_error")


async def publish_signal(redis_client: Any, signal_data: dict) -> bool:
    """Publish a new signal to the appropriate Redis PubSub channel.

    Called by signal generation task after creating a new signal.

    Args:
        redis_client: Redis client instance.
        signal_data: Signal dict with market_type field.

    Returns:
        True if published successfully.
    """
    if redis_client is None:
        return False
    try:
        market_type = signal_data.get("market_type", "")
        channel = f"ws:signal:{market_type}"
        payload = json.dumps(signal_data, default=str)
        await redis_client.publish(channel, payload)
        logger.debug("pubsub_signal_published", channel=channel, symbol=signal_data.get("symbol"))
        return True
    except Exception:
        logger.warning("pubsub_publish_failed", symbol=signal_data.get("symbol"))
        return False


async def publish_market_update(redis_client: Any, update_data: dict) -> bool:
    """Publish a market price update to Redis PubSub.

    Args:
        redis_client: Redis client instance.
        update_data: Market update dict with market_type field.

    Returns:
        True if published successfully.
    """
    if redis_client is None:
        return False
    try:
        market_type = update_data.get("market_type", "")
        channel = f"ws:market:{market_type}"
        payload = json.dumps(update_data, default=str)
        await redis_client.publish(channel, payload)
        return True
    except Exception:
        logger.warning("pubsub_market_update_failed")
        return False


async def publish_broadcast(redis_client: Any, data: dict) -> bool:
    """Publish a message to all connected clients via Redis PubSub.

    Args:
        redis_client: Redis client instance.
        data: Message dict.

    Returns:
        True if published successfully.
    """
    if redis_client is None:
        return False
    try:
        payload = json.dumps(data, default=str)
        await redis_client.publish(ALL_CHANNEL, payload)
        return True
    except Exception:
        logger.warning("pubsub_broadcast_failed")
        return False


class ClientMessageQueue:
    """Bounded message queue per WebSocket client for backpressure.

    Drops oldest messages when queue is full to prevent memory issues
    with slow clients.
    """

    def __init__(self, max_size: int = MAX_CLIENT_QUEUE) -> None:
        self._queue: deque[dict] = deque(maxlen=max_size)
        self._dropped_count = 0

    def push(self, message: dict) -> bool:
        """Add a message. Returns False if oldest message was dropped."""
        was_full = len(self._queue) == self._queue.maxlen
        self._queue.append(message)
        if was_full:
            self._dropped_count += 1
            return False
        return True

    def pop_all(self) -> list[dict]:
        """Drain all queued messages."""
        messages = list(self._queue)
        self._queue.clear()
        return messages

    @property
    def size(self) -> int:
        return len(self._queue)

    @property
    def dropped_count(self) -> int:
        return self._dropped_count
