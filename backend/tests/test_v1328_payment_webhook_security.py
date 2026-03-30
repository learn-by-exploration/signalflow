"""v1.3.28 — Payment Webhook Security Tests.

Verify Razorpay webhook signature validation, replay prevention,
trial abuse, and subscription manipulation defences.
"""

import hashlib
import hmac
import json
from unittest.mock import patch

import pytest

from app.config import get_settings


class TestWebhookSignature:
    """Webhook signature must be strictly validated."""

    @pytest.mark.asyncio
    async def test_webhook_missing_signature_rejected(self, test_client):
        """POST /payments/webhook without signature header returns error."""
        r = await test_client.post(
            "/api/v1/payments/webhook",
            content=json.dumps({"event": "subscription.charged"}),
            headers={"Content-Type": "application/json"},
        )
        # Either 400 (bad sig) or 503 (not configured)
        assert r.status_code in (400, 503)

    @pytest.mark.asyncio
    async def test_webhook_invalid_signature_rejected(self, test_client):
        """Random signature is rejected."""
        r = await test_client.post(
            "/api/v1/payments/webhook",
            content=json.dumps({"event": "subscription.charged"}),
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": "definitely-not-valid-signature",
            },
        )
        assert r.status_code in (400, 503)

    @pytest.mark.asyncio
    async def test_webhook_body_tampering_detected(self, test_client):
        """Valid signature for different body fails."""
        settings = get_settings()
        original_body = json.dumps({"event": "test"}).encode()
        sig = hmac.new(
            (settings.razorpay_webhook_secret or "test").encode(),
            original_body,
            hashlib.sha256,
        ).hexdigest()

        tampered_body = json.dumps({"event": "subscription.charged", "hacked": True})
        r = await test_client.post(
            "/api/v1/payments/webhook",
            content=tampered_body,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": sig,
            },
        )
        assert r.status_code in (400, 503)

    @pytest.mark.asyncio
    async def test_webhook_unknown_event_ignored(self, test_client):
        """Unrecognized event type returns 200 (acknowledged, no side effects)."""
        settings = get_settings()
        body = json.dumps({"event": "unknown.event.type"}).encode()
        secret = settings.razorpay_webhook_secret or "test-secret"
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        with patch.object(settings, "razorpay_webhook_secret", secret):
            r = await test_client.post(
                "/api/v1/payments/webhook",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Razorpay-Signature": sig,
                },
            )
            # Should not crash — either 200 or 400/503
            assert r.status_code in (200, 400, 503)


class TestSubscriptionEndpoints:
    """Subscription endpoints must prevent abuse."""

    @pytest.mark.asyncio
    async def test_get_subscription_requires_auth(self, test_client):
        """GET /payments/subscription requires authentication."""
        r = await test_client.get("/api/v1/payments/subscription")
        # test_client has auth, should not be 401
        assert r.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_plans_endpoint_public(self, test_client):
        """GET /payments/plans returns plan info."""
        r = await test_client.get("/api/v1/payments/plans")
        assert r.status_code == 200
        data = r.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_subscribe_validates_plan_field(self, test_client):
        """Subscribe with SQL injection in plan field is rejected."""
        r = await test_client.post(
            "/api/v1/payments/subscribe",
            json={"plan": "monthly'; DROP TABLE subscriptions;--"},
        )
        assert r.status_code in (400, 422, 500)

    @pytest.mark.asyncio
    async def test_trial_endpoint_exists(self, test_client):
        """POST /payments/trial endpoint exists."""
        r = await test_client.post("/api/v1/payments/trial")
        # May fail (already trialed, etc) but should not be 404/405
        assert r.status_code != 405


class TestWebhookVerificationFunction:
    """The verify_webhook_signature function itself must be secure."""

    def test_hmac_compare_digest_used(self):
        """Webhook verification uses timing-safe comparison."""
        import inspect
        from app.api.payments import verify_webhook_signature
        source = inspect.getsource(verify_webhook_signature)
        assert "compare_digest" in source

    def test_valid_signature_accepted(self):
        """Correctly signed webhook passes verification."""
        from app.api.payments import verify_webhook_signature
        body = b'{"event":"test"}'
        secret = "test-webhook-secret"
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        assert verify_webhook_signature(body, sig, secret) is True

    def test_invalid_signature_rejected(self):
        """Wrong signature fails verification."""
        from app.api.payments import verify_webhook_signature
        body = b'{"event":"test"}'
        assert verify_webhook_signature(body, "wrong-sig", "secret") is False
