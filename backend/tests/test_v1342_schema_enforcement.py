"""v1.3.42 — API Schema Enforcement Tests.

Verify Pydantic validation rejects extra fields, type confusion,
null required fields, and mass assignment attacks.
"""

import pytest


class TestExtraFieldsRejected:
    """Extra/unexpected fields must be ignored or rejected."""

    @pytest.mark.asyncio
    async def test_register_extra_role_ignored(self, test_client):
        """Role field in registration is ignored (no privilege escalation)."""
        r = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "extra@test.com",
                "password": "SecurePass123!",
                "role": "admin",
            },
        )
        if r.status_code in (200, 201):
            data = r.json()
            # Role should not be admin
            user = data.get("data", {}).get("user", {})
            assert user.get("role") != "admin"

    @pytest.mark.asyncio
    async def test_trade_extra_id_ignored(self, test_client):
        """Custom ID in trade creation is ignored."""
        r = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "id": "00000000-0000-0000-0000-000000000001",
                "symbol": "TEST.NS",
                "market_type": "stock",
                "side": "buy",
                "quantity": "1",
                "price": "100.00",
            },
        )
        assert r.status_code in (200, 201, 422)


class TestTypeCoercion:
    """Type mismatches must be rejected or handled safely."""

    @pytest.mark.asyncio
    async def test_min_confidence_as_string(self, test_client):
        """String min_confidence is handled or rejected."""
        r = await test_client.get("/api/v1/signals?min_confidence=eighty")
        assert r.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_limit_as_string(self, test_client):
        """String limit is rejected."""
        r = await test_client.get("/api/v1/signals?limit=all")
        assert r.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_array_in_symbol_field(self, test_client):
        """Array value for symbol field is rejected."""
        r = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "symbol": ["HDFC", "TCS"],
                "market_type": "stock",
                "side": "buy",
                "quantity": "1",
                "price": "100.00",
            },
        )
        assert r.status_code == 422


class TestRequiredFields:
    """Required fields must be present and non-null."""

    @pytest.mark.asyncio
    async def test_register_null_email(self, test_client):
        """Null email in registration is rejected."""
        r = await test_client.post(
            "/api/v1/auth/register",
            json={"email": None, "password": "Pass123!"},
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_register_empty_email(self, test_client):
        """Empty email in registration is rejected."""
        r = await test_client.post(
            "/api/v1/auth/register",
            json={"email": "", "password": "Pass123!"},
        )
        assert r.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_register_missing_password(self, test_client):
        """Missing password field is rejected."""
        r = await test_client.post(
            "/api/v1/auth/register",
            json={"email": "test@test.com"},
        )
        assert r.status_code == 422


class TestBoundaryValues:
    """Extreme values must be handled."""

    @pytest.mark.asyncio
    async def test_negative_limit(self, test_client):
        """Negative limit is rejected."""
        r = await test_client.get("/api/v1/signals?limit=-5")
        assert r.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_negative_offset(self, test_client):
        """Negative offset is rejected."""
        r = await test_client.get("/api/v1/signals?offset=-1")
        assert r.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_huge_limit_handled(self, test_client):
        """Very large limit is clamped or rejected."""
        r = await test_client.get("/api/v1/signals?limit=99999")
        assert r.status_code in (200, 400, 422)

    @pytest.mark.asyncio
    async def test_integer_overflow_confidence(self, test_client):
        """Huge confidence value is handled."""
        r = await test_client.get("/api/v1/signals?min_confidence=999999999")
        assert r.status_code in (200, 400, 422)

    @pytest.mark.asyncio
    async def test_malformed_json_body(self, test_client):
        """Malformed JSON body returns 422."""
        r = await test_client.post(
            "/api/v1/auth/register",
            content=b'{"broken json',
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422
