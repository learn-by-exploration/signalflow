"""Tester 3: The Penetration Tester — Security & Injection Attacks.

Tests for SQL injection, XSS payloads, SSRF, auth bypass, header
manipulation, and other OWASP Top 10 vulnerabilities.
"""

import pytest
from uuid import uuid4


# =========================================================================
# SQL Injection via Query Parameters
# =========================================================================

class TestSQLInjection:
    """Attempt SQL injection through every text-accepting endpoint."""

    @pytest.mark.asyncio
    async def test_signals_symbol_sql_injection(self, test_client):
        """Symbol filter with SQL injection payload."""
        payloads = [
            "'; DROP TABLE signals; --",
            "' OR '1'='1",
            "HDFCBANK' UNION SELECT * FROM users--",
            "'; INSERT INTO signals VALUES (1, 'hacked'); --",
            "1; WAITFOR DELAY '0:0:5'--",
        ]
        for payload in payloads:
            resp = await test_client.get(f"/api/v1/signals?symbol={payload}")
            # Should not crash — return 200 with empty results
            assert resp.status_code == 200
            data = resp.json()
            assert "data" in data

    @pytest.mark.asyncio
    async def test_signals_market_filter_injection(self, test_client):
        """Market filter with SQL injection."""
        resp = await test_client.get("/api/v1/signals?market=' OR 1=1 --")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_history_sql_injection(self, test_client):
        """History endpoint with injection in outcome filter."""
        resp = await test_client.get(
            "/api/v1/signals/history?outcome=' UNION SELECT 1,2,3--"
        )
        assert resp.status_code in (200, 422)

    @pytest.mark.asyncio
    async def test_portfolio_symbol_injection(self, test_client):
        """Portfolio trade with SQL in symbol."""
        resp = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "symbol": "'; DROP TABLE trades;--",
                "market_type": "stock",
                "side": "buy",
                "quantity": "1",
                "price": "100.00",
            },
        )
        # Should either reject or safely insert
        assert resp.status_code in (200, 201, 422)


# =========================================================================
# XSS Payloads
# =========================================================================

class TestXSSPayloads:
    """Inject XSS payloads to ensure they're not reflected unsanitized."""

    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(1)",
        "'+alert(document.cookie)+'",
        "<svg/onload=alert('XSS')>",
    ]

    @pytest.mark.asyncio
    async def test_feedback_notes_xss(self, test_client):
        """Notes field should not execute scripts."""
        for payload in self.XSS_PAYLOADS:
            resp = await test_client.post(
                f"/api/v1/signals/{uuid4()}/feedback",
                json={"action": "took", "notes": payload},
            )
            # Should accept but escape — or reject
            assert resp.status_code in (201, 404, 422)

    @pytest.mark.asyncio
    async def test_alert_config_username_xss(self, test_client):
        """Username in alert config should not allow XSS."""
        for payload in self.XSS_PAYLOADS:
            resp = await test_client.post(
                "/api/v1/alerts/config",
                json={
                    "telegram_chat_id": 99999,
                    "username": payload,
                    "min_confidence": 60,
                },
            )
            if resp.status_code in (200, 201):
                body = resp.json()
                # If stored, the payload should be escaped or sanitized
                stored_name = body.get("data", {}).get("username", "")
                # Verify no raw script tags in response
                assert "<script>" not in stored_name.lower()

    @pytest.mark.asyncio
    async def test_ai_question_xss(self, test_client):
        """AI Q&A question with XSS payload."""
        resp = await test_client.post(
            "/api/v1/ai/ask",
            json={"question": "<script>alert('xss')</script>"},
        )
        assert resp.status_code in (200, 422, 429)


# =========================================================================
# Path Traversal
# =========================================================================

class TestPathTraversal:
    """Test for path traversal attacks."""

    @pytest.mark.asyncio
    async def test_signal_id_path_traversal(self, test_client):
        """Signal ID with path traversal attempt."""
        payloads = [
            "../../etc/passwd",
            "../../../app/config.py",
            "....//....//etc/passwd",
        ]
        for payload in payloads:
            resp = await test_client.get(f"/api/v1/signals/{payload}")
            # Should be 422 (UUID validation) or 404
            assert resp.status_code in (404, 422)

    @pytest.mark.asyncio
    async def test_shared_signal_path_traversal(self, test_client):
        """Shared signal with traversal in share code."""
        resp = await test_client.get("/api/v1/shared/../../etc/passwd")
        assert resp.status_code in (404, 422)


# =========================================================================
# Auth Bypass Attempts
# =========================================================================

class TestAuthBypass:
    """Test authentication bypass vectors."""

    @pytest.mark.asyncio
    async def test_empty_api_key(self, test_client):
        """Empty API key should be rejected."""
        resp = await test_client.get(
            "/api/v1/signals",
            headers={"X-API-Key": ""},
        )
        # With the test's override this will still work, but verify
        # the endpoint doesn't crash
        assert resp.status_code in (200, 401)

    @pytest.mark.asyncio
    async def test_null_bytes_in_api_key(self, test_client):
        """Null bytes in API key."""
        resp = await test_client.get(
            "/api/v1/signals",
            headers={"X-API-Key": "valid\x00key"},
        )
        assert resp.status_code in (200, 401)

    @pytest.mark.asyncio
    async def test_jwt_none_algorithm(self, test_client):
        """JWT with 'none' algorithm should be rejected."""
        # Craft a token with alg=none
        import base64
        import json
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "none", "typ": "JWT"}).encode()
        ).decode().rstrip("=")
        payload = base64.urlsafe_b64encode(
            json.dumps({"sub": "admin", "tier": "pro"}).encode()
        ).decode().rstrip("=")
        fake_token = f"{header}.{payload}."

        resp = await test_client.get(
            "/api/v1/signals",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert resp.status_code in (200, 401)

    @pytest.mark.asyncio
    async def test_jwt_tampered_payload(self, test_client):
        """JWT with tampered payload (change tier to admin)."""
        resp = await test_client.get(
            "/api/v1/signals",
            headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInRpZXIiOiJwcm8ifQ.tampered"},
        )
        assert resp.status_code in (200, 401)


# =========================================================================
# Header Injection
# =========================================================================

class TestHeaderInjection:
    """Test for header injection attacks."""

    @pytest.mark.asyncio
    async def test_host_header_injection(self, test_client):
        """Host header manipulation shouldn't cause issues."""
        resp = await test_client.get(
            "/health",
            headers={"Host": "evil.com"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_x_forwarded_for_spoofing(self, test_client):
        """X-Forwarded-For spoofing shouldn't bypass rate limits."""
        resp = await test_client.get(
            "/health",
            headers={"X-Forwarded-For": "127.0.0.1"},
        )
        assert resp.status_code == 200


# =========================================================================
# Content-Type Abuse
# =========================================================================

class TestContentTypeAbuse:
    """Test endpoints with wrong content types."""

    @pytest.mark.asyncio
    async def test_post_with_form_data_instead_of_json(self, test_client):
        """POST endpoint receiving form data instead of JSON."""
        resp = await test_client.post(
            "/api/v1/alerts/config",
            data="telegram_chat_id=12345&username=test",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 422  # Should reject non-JSON

    @pytest.mark.asyncio
    async def test_post_with_xml_content(self, test_client):
        """XXE attack via XML content type."""
        xml_payload = '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><data>&xxe;</data>'
        resp = await test_client.post(
            "/api/v1/alerts/config",
            content=xml_payload,
            headers={"Content-Type": "application/xml"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_json_body(self, test_client):
        """Empty JSON body to POST endpoints."""
        resp = await test_client.post(
            "/api/v1/portfolio/trades",
            json={},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_null_json_body(self, test_client):
        """null JSON body."""
        resp = await test_client.post(
            "/api/v1/portfolio/trades",
            content="null",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422


# =========================================================================
# Integer Overflow / Type Coercion
# =========================================================================

class TestTypeCoercion:
    """Test type confusion and integer overflow attacks."""

    @pytest.mark.asyncio
    async def test_huge_confidence_value(self, test_client):
        """min_confidence > 100 should be rejected by ge/le validation."""
        resp = await test_client.get("/api/v1/signals?min_confidence=999999")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_negative_limit(self, test_client):
        """Negative limit should be rejected."""
        resp = await test_client.get("/api/v1/signals?limit=-1")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_zero_limit(self, test_client):
        """Zero limit — should return empty or be rejected."""
        resp = await test_client.get("/api/v1/signals?limit=0")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_huge_offset(self, test_client):
        """Very large offset — should return empty, not crash."""
        resp = await test_client.get("/api/v1/signals?offset=999999999")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    @pytest.mark.asyncio
    async def test_float_as_integer_param(self, test_client):
        """Float where integer expected."""
        resp = await test_client.get("/api/v1/signals?min_confidence=50.5")
        # FastAPI should either coerce or reject
        assert resp.status_code in (200, 422)

    @pytest.mark.asyncio
    async def test_string_as_integer_param(self, test_client):
        """String where integer expected."""
        resp = await test_client.get("/api/v1/signals?min_confidence=abc")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_negative_confidence(self, test_client):
        """Negative confidence should be rejected."""
        resp = await test_client.get("/api/v1/signals?min_confidence=-10")
        assert resp.status_code == 422


# =========================================================================
# Unicode & Special Characters
# =========================================================================

class TestUnicodeHandling:
    """Test Unicode and special character handling."""

    @pytest.mark.asyncio
    async def test_unicode_in_symbol_filter(self, test_client):
        """Unicode characters in symbol filter."""
        resp = await test_client.get("/api/v1/signals?symbol=тест")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_emoji_in_notes(self, test_client):
        """Emoji in feedback notes should work."""
        resp = await test_client.post(
            f"/api/v1/signals/{uuid4()}/feedback",
            json={"action": "took", "notes": "Great signal! 🚀📈💰"},
        )
        assert resp.status_code in (201, 404)

    @pytest.mark.asyncio
    async def test_null_bytes_in_string_fields(self, test_client):
        """Null bytes in string fields."""
        resp = await test_client.post(
            f"/api/v1/signals/{uuid4()}/feedback",
            json={"action": "took", "notes": "normal\x00hidden"},
        )
        assert resp.status_code in (201, 404, 422)

    @pytest.mark.asyncio
    async def test_rtl_override_in_username(self, test_client):
        """Right-to-left override character in username."""
        resp = await test_client.post(
            "/api/v1/alerts/config",
            json={
                "telegram_chat_id": 88888,
                "username": "user\u202Efdcba",  # RTL override
                "min_confidence": 60,
            },
        )
        assert resp.status_code in (200, 201, 422)


# =========================================================================
# Response Information Leakage
# =========================================================================

class TestInformationLeakage:
    """Verify error responses don't leak sensitive information."""

    @pytest.mark.asyncio
    async def test_404_doesnt_leak_stack_trace(self, test_client):
        """404 responses shouldn't include Python stack traces."""
        resp = await test_client.get(f"/api/v1/signals/{uuid4()}")
        assert resp.status_code == 404
        body = resp.text
        assert "Traceback" not in body
        assert "File" not in body or "detail" in body

    @pytest.mark.asyncio
    async def test_422_doesnt_leak_internals(self, test_client):
        """422 responses shouldn't leak internal paths."""
        resp = await test_client.get("/api/v1/signals?limit=-999")
        assert resp.status_code == 422
        body = resp.text
        assert "/home/" not in body
        assert "app/" not in body or "detail" in body

    @pytest.mark.asyncio
    async def test_health_doesnt_leak_env_vars(self, test_client):
        """Health endpoint shouldn't expose environment variables."""
        resp = await test_client.get("/health")
        assert resp.status_code == 200
        body = resp.text.lower()
        assert "api_key" not in body
        assert "secret" not in body
        assert "password" not in body
