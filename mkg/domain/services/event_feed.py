# mkg/domain/services/event_feed.py
"""EventFeed — event subscription and delivery for external consumers.

D3: Pub/sub event feed bridge. Consumers subscribe with filters
(event types, min impact), and events are delivered to handlers
or webhook URLs.
"""

import logging
import uuid
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class EventFeed:
    """In-process event pub/sub with filtering."""

    def __init__(self) -> None:
        self._subscriptions: dict[str, dict[str, Any]] = {}

    def subscribe(
        self,
        callback_url: Optional[str] = None,
        event_types: Optional[list[str]] = None,
        min_impact: float = 0.0,
        handler: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> str:
        """Subscribe to events with optional filtering.

        Args:
            callback_url: URL for webhook delivery (or None for in-process).
            event_types: Filter by event type (e.g., 'propagation').
            min_impact: Minimum impact threshold for delivery.
            handler: In-process callback (for testing / local consumers).

        Returns:
            Subscription ID.
        """
        sub_id = str(uuid.uuid4())
        self._subscriptions[sub_id] = {
            "callback_url": callback_url,
            "event_types": set(event_types) if event_types else None,
            "min_impact": min_impact,
            "handler": handler,
        }
        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription. Returns True if found."""
        return self._subscriptions.pop(subscription_id, None) is not None

    def publish(self, event: dict[str, Any]) -> int:
        """Publish an event to all matching subscribers.

        Args:
            event: Event dict with at least 'event_type'.

        Returns:
            Number of subscribers that received the event.
        """
        delivered = 0
        event_type = event.get("event_type", "")
        event_impact = event.get("impact", 0.0)

        for sub_id, sub in self._subscriptions.items():
            # Check event type filter
            if sub["event_types"] and event_type not in sub["event_types"]:
                continue
            # Check impact threshold
            if event_impact < sub["min_impact"]:
                continue

            # Deliver
            handler = sub.get("handler")
            if handler:
                try:
                    handler(event)
                    delivered += 1
                except Exception:
                    logger.exception("Handler failed for subscription %s", sub_id)
            elif sub.get("callback_url"):
                # In production: queue async HTTP POST
                logger.info(
                    "Would POST to %s: %s", sub["callback_url"], event_type
                )
                delivered += 1

        return delivered

    @property
    def subscription_count(self) -> int:
        """Number of active subscriptions."""
        return len(self._subscriptions)
