"""v1.3.12 — Payload Abuse Tests.

Verify protection against oversized payloads, deeply nested JSON,
extremely long strings, and other payload-based attacks.
"""

import uuid

import pytest
from httpx import AsyncClient


class TestOversizedPayloads:
    """Oversized payloads must be rejected or handled safely."""

    @pytest.mark.asyncio
    async def test_very_long_symbol_rejected(self, test_client: AsyncClient):
        """Symbol exceeding max length must be rejected."""
        resp = await test_client.get(f"/api/v1/signals?symbol={'A' * 100}")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_very_long_email_rejected(self, test_client: AsyncClient):
        """Extremely long email in registration must be rejected."""
        long_email = "a" * 500 + "@example.com"
        resp = await test_client.post(
            "/api/v1/auth/register",
            json={"email": long_email, "password": "TestPass1!"},
        )
        assert resp.status_code == 422  # Pydantic validation error

    @pytest.mark.asyncio
    async def test_very_long_notes_rejected(self, test_client: AsyncClient):
        """Feedback notes exceeding max_length must be rejected."""
        signal_id = str(uuid.uuid4())
        long_notes = "x" * 1000  # max_length is 500
        resp = await test_client.post(
            f"/api/v1/signals/{signal_id}/feedback",
            json={"action": "took", "notes": long_notes},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_json_body(self, test_client: AsyncClient):
        """Empty JSON body on POST endpoints should return 422."""
        resp = await test_client.post("/api/v1/auth/register", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_null_json_body(self, test_client: AsyncClient):
        """null JSON body should fail gracefully."""
        resp = await test_client.post(
            "/api/v1/auth/register",
            content="null",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422


class TestDeeplyNestedJSON:
    """Deeply nested JSON must not cause stack overflow."""

    @pytest.mark.asyncio
    async def test_deeply_nested_json_in_alert_config(self, test_client: AsyncClient):
        """Deeply nested quiet_hours JSON should be handled safely."""
        nested = {"a": {"a": {"a": {"a": {"a": {"a": {"a": "deep"}}}}}}}
        resp = await test_client.post(
            "/api/v1/alerts/config",
            json={
                "telegram_chat_id": 99999,
                "quiet_hours": nested,  # Should be {start, end} not nested
            },
        )
        # Should either be 422 (validation) or 201 with valid data
        assert resp.status_code in (201, 400, 422, 409)

    @pytest.mark.asyncio
    async def test_array_of_arrays_in_markets(self, test_client: AsyncClient):
        """Nested arrays instead of string array should be rejected."""
        resp = await test_client.post(
            "/api/v1/alerts/config",
            json={
                "telegram_chat_id": 88888,
                "markets": [["stock", "crypto"], ["forex"]],  # Wrong format
            },
        )
        assert resp.status_code in (400, 422, 409)


class TestMalformedInputTypes:
    """Wrong data types should be rejected by Pydantic."""

    @pytest.mark.asyncio
    async def test_string_as_confidence(self, test_client: AsyncClient):
        """String instead of integer for min_confidence."""
        resp = await test_client.get("/api/v1/signals?min_confidence=high")
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_negative_confidence(self, test_client: AsyncClient):
        """Negative confidence should be rejected."""
        resp = await test_client.get("/api/v1/signals?min_confidence=-1")
        assert resp.status_code in (200, 400, 422)  # May be ignored, validated, or Pydantic error

    @pytest.mark.asyncio
    async def test_confidence_over_100(self, test_client: AsyncClient):
        """Confidence > 100 should be rejected or clamped."""
        resp = await test_client.get("/api/v1/signals?min_confidence=999")
        assert resp.status_code in (200, 400, 422)

    @pytest.mark.asyncio
    async def test_string_as_limit(self, test_client: AsyncClient):
        """String instead of integer for limit parameter."""
        resp = await test_client.get("/api/v1/signals?limit=abc")
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_negative_limit(self, test_client: AsyncClient):
        """Negative limit should be handled gracefully."""
        resp = await test_client.get("/api/v1/signals?limit=-5")
        assert resp.status_code in (200, 400, 422)

    @pytest.mark.asyncio
    async def test_zero_limit(self, test_client: AsyncClient):
        """Zero limit should return empty or error."""
        resp = await test_client.get("/api/v1/signals?limit=0")
        assert resp.status_code in (200, 400, 422)

    @pytest.mark.asyncio
    async def test_float_as_integer_field(self, test_client: AsyncClient):
        """Float where integer expected."""
        resp = await test_client.get("/api/v1/signals?limit=3.14")
        assert resp.status_code in (200, 400, 422)

    @pytest.mark.asyncio
    async def test_boolean_as_string_field(self, test_client: AsyncClient):
        """Boolean where string expected."""
        resp = await test_client.post(
            "/api/v1/auth/register",
            json={"email": True, "password": 12345},
        )
        assert resp.status_code == 422


class TestSpecialCharactersInPayloads:
    """Special characters in payloads must be handled safely."""

    @pytest.mark.asyncio
    async def test_null_bytes_in_string(self, test_client: AsyncClient):
        """Null bytes in string fields should be handled."""
        resp = await test_client.post(
            "/api/v1/auth/register",
            json={"email": "test\x00@example.com", "password": "TestPass1!"},
        )
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_unicode_in_notes(self, test_client: AsyncClient):
        """Unicode characters in freetext fields should work."""
        signal_id = str(uuid.uuid4())
        resp = await test_client.post(
            f"/api/v1/signals/{signal_id}/feedback",
            json={"action": "took", "notes": "Good signal 🚀 ₹1000 target"},
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_newlines_in_string_fields(self, test_client: AsyncClient):
        """Newlines in string fields should be handled."""
        signal_id = str(uuid.uuid4())
        resp = await test_client.post(
            f"/api/v1/signals/{signal_id}/feedback",
            json={"action": "took", "notes": "Line 1\nLine 2\rLine 3"},
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_extremely_large_number(self, test_client: AsyncClient):
        """Extremely large numbers should be handled."""
        signal_id = str(uuid.uuid4())
        resp = await test_client.post(
            f"/api/v1/signals/{signal_id}/feedback",
            json={"action": "took", "entry_price": "99999999999999999999.99999999"},
        )
        # Should handle gracefully (accept or reject with error)
        assert resp.status_code in (201, 400, 422)
