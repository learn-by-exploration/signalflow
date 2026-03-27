"""Tests for Phase 5: Monetization (v1.4 plan).

Tests cover: Razorpay service, subscription model, payment endpoints,
free vs paid tier gating, plans endpoint, trial logic.
"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ═══════════════════════════════════════════════════════════
# Task 5.1: Razorpay Integration Tests
# ═══════════════════════════════════════════════════════════
class TestRazorpayService:
    """Verify Razorpay service functions."""

    def test_verify_webhook_signature_valid(self):
        """Valid HMAC-SHA256 signature should return True."""
        from app.services.payment.razorpay_service import verify_webhook_signature

        secret = "test_webhook_secret"
        body = b'{"event":"subscription.charged"}'
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        assert verify_webhook_signature(body, sig, secret) is True

    def test_verify_webhook_signature_invalid(self):
        """Invalid signature should return False."""
        from app.services.payment.razorpay_service import verify_webhook_signature

        body = b'{"event":"test"}'
        assert verify_webhook_signature(body, "invalid_sig", "secret") is False

    def test_plan_prices_defined(self):
        """All plan prices should be defined in paise."""
        from app.services.payment.razorpay_service import PLAN_PRICES

        assert PLAN_PRICES["monthly"] == 49900   # ₹499
        assert PLAN_PRICES["annual"] == 499900    # ₹4999
        assert PLAN_PRICES["trial"] == 0

    def test_subscription_model_fields(self):
        """Subscription model should have all required fields."""
        from app.models.subscription import Subscription

        assert hasattr(Subscription, "user_id")
        assert hasattr(Subscription, "plan")
        assert hasattr(Subscription, "status")
        assert hasattr(Subscription, "razorpay_subscription_id")
        assert hasattr(Subscription, "amount_paise")
        assert hasattr(Subscription, "current_period_end")
        assert hasattr(Subscription, "trial_end")

    def test_subscription_migration_exists(self):
        """Migration for subscriptions table should exist."""
        import os
        migration_dir = os.path.join(
            os.path.dirname(__file__), "..", "migrations", "versions",
        )
        files = os.listdir(migration_dir)
        sub_files = [f for f in files if "subscription" in f.lower()]
        assert len(sub_files) >= 1


# ═══════════════════════════════════════════════════════════
# Task 5.1: Payment Endpoints Tests
# ═══════════════════════════════════════════════════════════
class TestPaymentEndpoints:
    """Verify payment API endpoints."""

    @pytest.mark.asyncio
    async def test_list_plans_endpoint(self, test_client):
        """GET /payments/plans should return plan list."""
        resp = await test_client.get("/api/v1/payments/plans")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 3  # trial, monthly, annual
        plan_names = {p["plan"] for p in data}
        assert plan_names == {"trial", "monthly", "annual"}

    @pytest.mark.asyncio
    async def test_trial_plan_is_free(self, test_client):
        """Trial plan should have 0 amount."""
        resp = await test_client.get("/api/v1/payments/plans")
        trial = [p for p in resp.json()["data"] if p["plan"] == "trial"][0]
        assert trial["amount_paise"] == 0
        assert trial["duration_days"] == 7

    @pytest.mark.asyncio
    async def test_monthly_plan_price(self, test_client):
        """Monthly plan should be ₹499."""
        resp = await test_client.get("/api/v1/payments/plans")
        monthly = [p for p in resp.json()["data"] if p["plan"] == "monthly"][0]
        assert monthly["amount_paise"] == 49900

    @pytest.mark.asyncio
    async def test_annual_plan_price(self, test_client):
        """Annual plan should be ₹4999."""
        resp = await test_client.get("/api/v1/payments/plans")
        annual = [p for p in resp.json()["data"] if p["plan"] == "annual"][0]
        assert annual["amount_paise"] == 499900

    @pytest.mark.asyncio
    async def test_get_subscription_no_sub(self, test_client):
        """GET /payments/subscription with no subscription returns null data."""
        resp = await test_client.get("/api/v1/payments/subscription")
        assert resp.status_code == 200
        assert resp.json()["data"] is None

    @pytest.mark.asyncio
    async def test_webhook_rejects_missing_secret(self, test_client):
        """Webhook should reject when webhook secret not configured."""
        resp = await test_client.post(
            "/api/v1/payments/webhook",
            content=b'{"event": "test"}',
            headers={"X-Razorpay-Signature": "test"},
        )
        # Should fail with 503 or 400
        assert resp.status_code in (400, 503)


# ═══════════════════════════════════════════════════════════
# Task 5.2: Free vs Paid Tier Tests
# ═══════════════════════════════════════════════════════════
class TestTierGating:
    """Verify free vs paid tier differentiation."""

    def test_tier_gating_module_importable(self):
        """tier_gating module should be importable."""
        from app.services.tier_gating import (
            FREE_DETAIL_VIEWS_PER_WEEK,
            FREE_HISTORY_DAYS,
            LOCKED_FIELDS,
            redact_signal_for_free_tier,
        )
        assert FREE_DETAIL_VIEWS_PER_WEEK == 3
        assert FREE_HISTORY_DAYS == 7
        assert callable(redact_signal_for_free_tier)

    def test_locked_fields_defined(self):
        """Locked fields should include AI reasoning, targets, stop-loss."""
        from app.services.tier_gating import LOCKED_FIELDS
        assert "ai_reasoning" in LOCKED_FIELDS
        assert "target_price" in LOCKED_FIELDS
        assert "stop_loss" in LOCKED_FIELDS
        assert "technical_data" in LOCKED_FIELDS

    def test_redact_signal(self):
        """redact_signal_for_free_tier should replace locked fields."""
        from app.services.tier_gating import redact_signal_for_free_tier

        signal = {
            "symbol": "HDFCBANK",
            "signal_type": "STRONG_BUY",
            "confidence": 88,
            "ai_reasoning": "Credit growth accelerating...",
            "target_price": "1780.00",
            "stop_loss": "1630.00",
            "technical_data": {"rsi": {"value": 62}},
            "sentiment_data": {"score": 78},
        }

        redacted = redact_signal_for_free_tier(signal)
        assert "🔒" in redacted["ai_reasoning"]
        assert redacted["target_price"] is None
        assert redacted["stop_loss"] is None
        assert redacted["technical_data"] == {"locked": True}
        assert redacted["is_locked"] is True
        # Symbol and signal_type should still be visible
        assert redacted["symbol"] == "HDFCBANK"
        assert redacted["signal_type"] == "STRONG_BUY"
        assert redacted["confidence"] == 88

    def test_redact_preserves_original(self):
        """Redacting should not modify the original dict."""
        from app.services.tier_gating import redact_signal_for_free_tier

        original = {
            "ai_reasoning": "Important text",
            "target_price": "100.00",
            "stop_loss": "90.00",
            "technical_data": {"rsi": {"value": 50}},
            "sentiment_data": {"score": 60},
        }
        redact_signal_for_free_tier(original)
        assert original["ai_reasoning"] == "Important text"  # Original unchanged


# ═══════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════
class TestPaymentConfig:
    """Verify Razorpay config fields exist."""

    def test_razorpay_config_fields(self):
        """Config should have Razorpay-related settings."""
        from app.config import get_settings
        settings = get_settings()
        assert hasattr(settings, "razorpay_key_id")
        assert hasattr(settings, "razorpay_key_secret")
        assert hasattr(settings, "razorpay_webhook_secret")
        assert hasattr(settings, "razorpay_monthly_plan_id")
        assert hasattr(settings, "razorpay_annual_plan_id")
        assert hasattr(settings, "pro_trial_days")
        assert hasattr(settings, "payment_grace_days")

    def test_pro_trial_default(self):
        """Pro trial should default to 7 days."""
        from app.config import get_settings
        settings = get_settings()
        assert settings.pro_trial_days == 7

    def test_grace_period_default(self):
        """Payment grace period should default to 3 days."""
        from app.config import get_settings
        settings = get_settings()
        assert settings.payment_grace_days == 3


# ═══════════════════════════════════════════════════════════
# Scheduler Tests
# ═══════════════════════════════════════════════════════════
class TestSubscriptionScheduler:
    """Verify subscription management task in scheduler."""

    def test_subscription_task_in_schedule(self):
        """Beat schedule should include subscription check."""
        from app.tasks.scheduler import CELERY_BEAT_SCHEDULE
        assert "check-expired-subscriptions" in CELERY_BEAT_SCHEDULE
        task = CELERY_BEAT_SCHEDULE["check-expired-subscriptions"]
        assert task["task"] == "app.tasks.subscription_tasks.check_expired_subscriptions"

    def test_subscription_task_exists(self):
        """Subscription Celery task should be importable."""
        from app.tasks.subscription_tasks import check_expired_subscriptions
        assert callable(check_expired_subscriptions)
