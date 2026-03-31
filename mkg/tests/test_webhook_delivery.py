# mkg/tests/test_webhook_delivery.py
"""Tests for WebhookDelivery — delivers alerts to registered webhook endpoints.

R-WH1 through R-WH5: Webhook registration, payload formatting,
retry logic, and delivery tracking.
"""

import pytest


class TestWebhookDelivery:

    @pytest.fixture
    def delivery(self):
        from mkg.domain.services.webhook_delivery import WebhookDelivery
        return WebhookDelivery()

    def test_register_webhook(self, delivery):
        delivery.register("wh-1", url="https://example.com/hook", events=["alert"])
        assert len(delivery.webhooks) == 1

    def test_unregister_webhook(self, delivery):
        delivery.register("wh-1", url="https://example.com/hook", events=["alert"])
        delivery.unregister("wh-1")
        assert len(delivery.webhooks) == 0

    def test_format_payload(self, delivery):
        alert = {
            "id": "alert-1",
            "severity": "critical",
            "title": "TSMC → NVIDIA",
            "message": "Supply disruption",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }
        payload = delivery.format_payload(alert, event_type="alert")
        assert payload["event"] == "alert"
        assert payload["data"] == alert
        assert "sent_at" in payload

    def test_match_webhooks_by_event(self, delivery):
        delivery.register("wh-1", url="https://a.com/hook", events=["alert"])
        delivery.register("wh-2", url="https://b.com/hook", events=["chain_update"])
        matches = delivery.match_webhooks("alert")
        assert len(matches) == 1
        assert matches[0]["id"] == "wh-1"

    def test_match_webhooks_wildcard(self, delivery):
        delivery.register("wh-1", url="https://a.com/hook", events=["*"])
        matches = delivery.match_webhooks("any_event")
        assert len(matches) == 1

    def test_delivery_log_records_attempt(self, delivery):
        delivery.register("wh-1", url="https://example.com/hook", events=["alert"])
        delivery.record_delivery("wh-1", success=True, status_code=200)
        log = delivery.get_delivery_log("wh-1")
        assert len(log) == 1
        assert log[0]["success"] is True

    def test_delivery_log_tracks_failures(self, delivery):
        delivery.register("wh-1", url="https://example.com/hook", events=["alert"])
        delivery.record_delivery("wh-1", success=False, status_code=500)
        log = delivery.get_delivery_log("wh-1")
        assert log[0]["success"] is False
        assert log[0]["status_code"] == 500

    def test_get_webhook_stats(self, delivery):
        delivery.register("wh-1", url="https://example.com/hook", events=["alert"])
        delivery.record_delivery("wh-1", success=True, status_code=200)
        delivery.record_delivery("wh-1", success=False, status_code=500)
        stats = delivery.get_stats("wh-1")
        assert stats["total"] == 2
        assert stats["successes"] == 1
        assert stats["failures"] == 1

    def test_unregister_nonexistent_returns_false(self, delivery):
        assert delivery.unregister("nonexistent") is False

    def test_match_no_webhooks(self, delivery):
        matches = delivery.match_webhooks("alert")
        assert matches == []

    def test_stats_for_unregistered_webhook(self, delivery):
        stats = delivery.get_stats("nonexistent")
        assert stats["total"] == 0

    def test_delivery_log_limit(self, delivery):
        delivery.register("wh-1", url="https://example.com", events=["*"])
        for i in range(100):
            delivery.record_delivery("wh-1", success=True, status_code=200)
        log = delivery.get_delivery_log("wh-1", limit=10)
        assert len(log) == 10

    def test_delivery_log_order_is_newest_first(self, delivery):
        delivery.register("wh-1", url="https://example.com", events=["*"])
        delivery.record_delivery("wh-1", success=True, status_code=200)
        delivery.record_delivery("wh-1", success=False, status_code=500)
        log = delivery.get_delivery_log("wh-1")
        # Newest first
        assert log[0]["success"] is False
        assert log[1]["success"] is True

    def test_match_multiple_event_types(self, delivery):
        delivery.register("wh-1", url="https://a.com", events=["alert", "chain_update"])
        assert len(delivery.match_webhooks("alert")) == 1
        assert len(delivery.match_webhooks("chain_update")) == 1
        assert len(delivery.match_webhooks("other")) == 0

    def test_record_delivery_for_unregistered_webhook(self, delivery):
        """Should not crash for unregistered webhook."""
        delivery.record_delivery("nonexistent", success=False, status_code=0)
        log = delivery.get_delivery_log("nonexistent")
        assert len(log) == 1  # Still recorded
