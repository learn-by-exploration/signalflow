# mkg/domain/services/webhook_delivery.py
"""WebhookDelivery — delivers alerts to registered webhook endpoints.

R-WH1 through R-WH5: Manages webhook registrations, payload formatting,
event matching, delivery logging, and stats.

Actual HTTP delivery is handled by infrastructure adapters;
this service manages the domain logic.
"""

from datetime import datetime, timezone
from typing import Any, Optional


class WebhookDelivery:
    """Manages webhook registrations and delivery tracking.

    Does not perform HTTP calls — that's the infrastructure layer's job.
    This service handles registration, event matching, payload formatting,
    and delivery log bookkeeping.
    """

    def __init__(self) -> None:
        self.webhooks: dict[str, dict[str, Any]] = {}
        self._delivery_logs: dict[str, list[dict[str, Any]]] = {}

    def register(
        self,
        webhook_id: str,
        url: str,
        events: list[str],
    ) -> dict[str, Any]:
        """Register a webhook endpoint.

        Args:
            webhook_id: Unique identifier for the webhook.
            url: Target URL.
            events: List of event types to subscribe to. ["*"] = all events.

        Returns:
            Webhook registration dict.
        """
        webhook = {
            "id": webhook_id,
            "url": url,
            "events": events,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        self.webhooks[webhook_id] = webhook
        self._delivery_logs.setdefault(webhook_id, [])
        return webhook

    def unregister(self, webhook_id: str) -> bool:
        """Remove a webhook registration.

        Returns:
            True if removed, False if not found.
        """
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            self._delivery_logs.pop(webhook_id, None)
            return True
        return False

    def format_payload(
        self,
        data: dict[str, Any],
        event_type: str,
    ) -> dict[str, Any]:
        """Format a delivery payload.

        Args:
            data: Alert or event data.
            event_type: Event type string.

        Returns:
            Formatted payload with event, data, and sent_at.
        """
        return {
            "event": event_type,
            "data": data,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }

    def match_webhooks(self, event_type: str) -> list[dict[str, Any]]:
        """Find webhooks subscribed to an event type.

        Args:
            event_type: The event type to match.

        Returns:
            List of matching webhook dicts.
        """
        matches: list[dict[str, Any]] = []
        for webhook in self.webhooks.values():
            events = webhook.get("events", [])
            if "*" in events or event_type in events:
                matches.append(webhook)
        return matches

    def record_delivery(
        self,
        webhook_id: str,
        success: bool,
        status_code: Optional[int] = None,
    ) -> None:
        """Record a delivery attempt.

        Args:
            webhook_id: The webhook that was called.
            success: Whether delivery succeeded.
            status_code: HTTP response status code.
        """
        self._delivery_logs.setdefault(webhook_id, []).append({
            "success": success,
            "status_code": status_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_delivery_log(
        self,
        webhook_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get delivery log for a webhook.

        Args:
            webhook_id: The webhook to get logs for.
            limit: Maximum number of log entries.

        Returns:
            List of delivery log entries, newest first.
        """
        logs = self._delivery_logs.get(webhook_id, [])
        return list(reversed(logs[-limit:]))

    def get_stats(self, webhook_id: str) -> dict[str, Any]:
        """Get delivery stats for a webhook.

        Returns:
            Dict with total, successes, failures counts.
        """
        logs = self._delivery_logs.get(webhook_id, [])
        successes = sum(1 for l in logs if l["success"])
        return {
            "total": len(logs),
            "successes": successes,
            "failures": len(logs) - successes,
        }
