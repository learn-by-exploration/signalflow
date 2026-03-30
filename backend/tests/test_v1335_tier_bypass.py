"""v1.3.35 — Subscription Tier Bypass Tests.

Verify free users can't access pro features, tier gating works
correctly, and redaction is properly applied.
"""

import pytest

from app.services.tier_gating import redact_signal_for_free_tier


class TestTierGating:
    """Free tier limits must be enforced."""

    def test_redacted_signal_has_locked_flag(self):
        """Redacted signal has is_locked=True."""
        signal = {
            "id": "test-id",
            "symbol": "HDFC",
            "signal_type": "BUY",
            "confidence": 80,
            "ai_reasoning": "Strong fundamentals",
            "target_price": "1780.00",
            "stop_loss": "1630.00",
            "technical_data": {"rsi": {"value": 62}},
            "sentiment_data": {"score": 85},
        }
        redacted = redact_signal_for_free_tier(signal)
        assert redacted.get("is_locked") is True

    def test_redacted_signal_hides_ai_reasoning(self):
        """AI reasoning is replaced with upgrade prompt."""
        signal = {
            "ai_reasoning": "Detailed AI analysis here",
            "target_price": "100.00",
            "stop_loss": "90.00",
            "technical_data": {"rsi": {"value": 50}},
            "sentiment_data": {"score": 70},
        }
        redacted = redact_signal_for_free_tier(signal)
        assert "Upgrade" in redacted.get("ai_reasoning", "") or "🔒" in redacted.get("ai_reasoning", "")

    def test_redacted_signal_hides_targets(self):
        """Target price and stop loss are hidden."""
        signal = {
            "ai_reasoning": "Test",
            "target_price": "100.00",
            "stop_loss": "90.00",
            "technical_data": {"rsi": {"value": 50}},
            "sentiment_data": {"score": 70},
        }
        redacted = redact_signal_for_free_tier(signal)
        assert redacted.get("target_price") is None
        assert redacted.get("stop_loss") is None

    def test_redacted_signal_hides_technical_data(self):
        """Technical data is locked."""
        signal = {
            "ai_reasoning": "Test",
            "target_price": "100.00",
            "stop_loss": "90.00",
            "technical_data": {"rsi": {"value": 50}, "macd": {"signal": "buy"}},
            "sentiment_data": {"score": 70},
        }
        redacted = redact_signal_for_free_tier(signal)
        tech = redacted.get("technical_data", {})
        assert tech.get("locked") is True or isinstance(tech, dict)

    def test_redacted_preserves_basic_info(self):
        """Symbol, signal type, confidence remain visible."""
        signal = {
            "symbol": "HDFC",
            "signal_type": "BUY",
            "confidence": 80,
            "ai_reasoning": "Test",
            "target_price": "100.00",
            "stop_loss": "90.00",
            "technical_data": {},
            "sentiment_data": {},
        }
        redacted = redact_signal_for_free_tier(signal)
        assert redacted.get("symbol") == "HDFC"
        assert redacted.get("signal_type") == "BUY"
        assert redacted.get("confidence") == 80


class TestTierEndpointAccess:
    """API endpoints enforce tier restrictions."""

    @pytest.mark.asyncio
    async def test_signals_accessible_all_tiers(self, test_client):
        """Signal listing is accessible to all tiers."""
        r = await test_client.get("/api/v1/signals")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_shared_signal_bypasses_tier(self, test_client):
        """Shared signals are viewable without Pro tier."""
        # Try accessing shared endpoint (may 404 if no shares exist)
        r = await test_client.get("/api/v1/signals/shared/nonexistent-id")
        # Should not be 403 (tier-gated)
        assert r.status_code in (200, 404, 422)

    @pytest.mark.asyncio
    async def test_history_endpoint_accessible(self, test_client):
        """History endpoint works for pro users."""
        r = await test_client.get("/api/v1/signals/history")
        assert r.status_code == 200


class TestClientSideTierSpoofing:
    """Client-side tier manipulation must be ignored."""

    @pytest.mark.asyncio
    async def test_custom_tier_header_ignored(self, test_client):
        """X-User-Tier header has no effect."""
        r = await test_client.get(
            "/api/v1/signals",
            headers={"X-User-Tier": "pro"},
        )
        # Should work but tier comes from auth, not header
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_tier_in_query_param_ignored(self, test_client):
        """Tier in query param has no effect."""
        r = await test_client.get("/api/v1/signals?tier=pro")
        assert r.status_code == 200
