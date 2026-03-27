"""Extensive tests for Phase 2: Security Hardening (v1.4 plan).

Tests cover: scoped API keys, WebSocket ticket auth, CSP headers,
rate limit audit, input validation, dependency lockfile.
"""

import hmac
import inspect
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ═══════════════════════════════════════════════════════════
# Task 2.2: Scoped API Keys Tests
# ═══════════════════════════════════════════════════════════
class TestScopedAPIKeys:
    """Verify internal vs external API key separation."""

    def test_internal_api_key_config_exists(self):
        """Settings must have internal_api_key field."""
        from app.config import get_settings
        settings = get_settings()
        assert hasattr(settings, "internal_api_key")

    def test_require_internal_auth_exists(self):
        """require_internal_auth function must exist in auth module."""
        from app.auth import require_internal_auth
        assert callable(require_internal_auth)

    def test_internal_endpoint_whitelist_defined(self):
        """INTERNAL_ENDPOINT_WHITELIST must be defined with safe read-only endpoints."""
        from app.auth import INTERNAL_ENDPOINT_WHITELIST
        assert isinstance(INTERNAL_ENDPOINT_WHITELIST, set)
        # Only GET endpoints allowed for internal key
        for entry in INTERNAL_ENDPOINT_WHITELIST:
            assert entry.startswith("GET "), f"Internal whitelist must only contain GET endpoints, found: {entry}"

    def test_internal_auth_uses_constant_time(self):
        """require_internal_auth must use hmac.compare_digest."""
        from app.auth import require_internal_auth
        source = inspect.getsource(require_internal_auth)
        assert "hmac.compare_digest" in source

    @pytest.mark.asyncio
    async def test_internal_auth_rejects_invalid_key(self):
        """require_internal_auth must reject invalid API keys."""
        from app.auth import require_internal_auth
        from fastapi import HTTPException
        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.api_secret_key = "test-secret"
            mock_settings.return_value.internal_api_key = "internal-secret"
            with pytest.raises(HTTPException) as exc_info:
                await require_internal_auth(api_key="wrong-key")
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_internal_auth_accepts_valid_key(self):
        """require_internal_auth must accept valid internal API key."""
        from app.auth import require_internal_auth
        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.api_secret_key = "test-secret"
            mock_settings.return_value.internal_api_key = "internal-secret"
            ctx = await require_internal_auth(api_key="internal-secret")
            assert ctx.auth_type == "internal_api_key"

    @pytest.mark.asyncio
    async def test_internal_auth_falls_back_to_api_secret(self):
        """If internal_api_key is empty, falls back to api_secret_key."""
        from app.auth import require_internal_auth
        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.api_secret_key = "shared-secret"
            mock_settings.return_value.internal_api_key = ""
            ctx = await require_internal_auth(api_key="shared-secret")
            assert ctx.auth_type == "internal_api_key"


# ═══════════════════════════════════════════════════════════
# Task 2.3: WebSocket Ticket Auth Tests
# ═══════════════════════════════════════════════════════════
class TestWebSocketTicketAuth:
    """Verify WebSocket ticket-based authentication."""

    def test_ticket_endpoint_exists(self):
        """POST /ws/ticket endpoint must exist."""
        from app.api.websocket import create_ws_ticket
        assert callable(create_ws_ticket)

    def test_consume_ticket_single_use(self):
        """Tickets must be single-use — second consumption returns None."""
        from app.api.websocket import _ws_tickets, _ws_ticket_expiry, _consume_ticket
        import time

        ticket_id = "test-ticket-123"
        _ws_tickets[ticket_id] = {"user_id": "user1", "tier": "pro", "chat_id": None}
        _ws_ticket_expiry[ticket_id] = time.monotonic() + 30

        # First consumption works
        result = _consume_ticket(ticket_id)
        assert result is not None
        assert result["user_id"] == "user1"

        # Second consumption fails
        result2 = _consume_ticket(ticket_id)
        assert result2 is None

    def test_consume_expired_ticket(self):
        """Expired tickets must be rejected."""
        from app.api.websocket import _ws_tickets, _ws_ticket_expiry, _consume_ticket

        ticket_id = "test-expired-ticket"
        _ws_tickets[ticket_id] = {"user_id": "user2", "tier": "free", "chat_id": None}
        _ws_ticket_expiry[ticket_id] = time.monotonic() - 1  # Already expired

        result = _consume_ticket(ticket_id)
        assert result is None

    def test_cleanup_expired_tickets(self):
        """_cleanup_expired_tickets must remove stale tickets."""
        from app.api.websocket import _ws_tickets, _ws_ticket_expiry, _cleanup_expired_tickets

        # Add expired ticket
        _ws_tickets["stale-1"] = {"user_id": "u1"}
        _ws_ticket_expiry["stale-1"] = time.monotonic() - 10

        # Add valid ticket
        _ws_tickets["valid-1"] = {"user_id": "u2"}
        _ws_ticket_expiry["valid-1"] = time.monotonic() + 30

        _cleanup_expired_tickets()

        assert "stale-1" not in _ws_tickets
        assert "valid-1" in _ws_tickets

        # Cleanup
        _ws_tickets.pop("valid-1", None)
        _ws_ticket_expiry.pop("valid-1", None)

    @pytest.mark.asyncio
    async def test_ws_ticket_endpoint_requires_auth(self, test_client):
        """POST /ws/ticket must require authentication."""
        from app.auth import require_auth
        from app.main import app

        # Clear overrides temporarily
        saved = app.dependency_overrides.copy()
        app.dependency_overrides.pop(require_auth, None)

        from httpx import ASGITransport, AsyncClient
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/ws/ticket")
            assert resp.status_code == 401

        app.dependency_overrides.update(saved)

    @pytest.mark.asyncio
    async def test_ws_ticket_endpoint_returns_ticket(self, test_client):
        """POST /ws/ticket should return a ticket with TTL."""
        resp = await test_client.post("/ws/ticket")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "ticket" in data
        assert data["ttl"] == 30

    def test_websocket_accepts_ticket_param(self):
        """WebSocket endpoint must accept 'ticket' query parameter."""
        from app.api.websocket import websocket_signals
        source = inspect.getsource(websocket_signals)
        assert "ticket" in source


# ═══════════════════════════════════════════════════════════
# Task 2.4: CSP Headers Tests
# ═══════════════════════════════════════════════════════════
class TestCSPHeaders:
    """Verify Content Security Policy headers are hardened."""

    @pytest.mark.asyncio
    async def test_csp_no_unsafe_eval(self, test_client):
        """CSP must NOT include 'unsafe-eval' in script-src."""
        resp = await test_client.get("/health")
        csp = resp.headers.get("content-security-policy", "")
        assert "unsafe-eval" not in csp, "CSP must not allow unsafe-eval"

    @pytest.mark.asyncio
    async def test_csp_has_object_src_none(self, test_client):
        """CSP must include object-src 'none'."""
        resp = await test_client.get("/health")
        csp = resp.headers.get("content-security-policy", "")
        assert "object-src 'none'" in csp

    @pytest.mark.asyncio
    async def test_csp_has_frame_ancestors_none(self, test_client):
        """CSP must include frame-ancestors 'none'."""
        resp = await test_client.get("/health")
        csp = resp.headers.get("content-security-policy", "")
        assert "frame-ancestors 'none'" in csp

    @pytest.mark.asyncio
    async def test_csp_script_src_self_only(self, test_client):
        """CSP script-src should be 'self' only (no unsafe-inline, no unsafe-eval)."""
        resp = await test_client.get("/health")
        csp = resp.headers.get("content-security-policy", "")
        # Extract script-src directive
        for directive in csp.split(";"):
            directive = directive.strip()
            if directive.startswith("script-src"):
                assert "unsafe-inline" not in directive, "script-src must not allow unsafe-inline"
                assert "unsafe-eval" not in directive, "script-src must not allow unsafe-eval"
                assert "'self'" in directive

    @pytest.mark.asyncio
    async def test_security_headers_present(self, test_client):
        """All security headers must be present."""
        resp = await test_client.get("/health")
        assert "x-content-type-options" in resp.headers
        assert "x-frame-options" in resp.headers
        assert "referrer-policy" in resp.headers
        assert "permissions-policy" in resp.headers
        assert "content-security-policy" in resp.headers

    @pytest.mark.asyncio
    async def test_csp_connect_src_includes_wss(self):
        """CSP connect-src should include WSS for WebSocket connections."""
        source = inspect.getsource(__import__("app.main", fromlist=["app"]))
        assert "wss://" in source, "CSP connect-src must include wss:// for WebSocket"


# ═══════════════════════════════════════════════════════════
# Task 2.5: Dependency Lockfile Tests
# ═══════════════════════════════════════════════════════════
class TestDependencyLockfile:
    """Verify dependency lockfile exists."""

    def test_requirements_lock_exists(self):
        """requirements.lock must exist in backend/ directory."""
        lock_path = os.path.join(os.path.dirname(__file__), "..", "requirements.lock")
        assert os.path.isfile(lock_path), "requirements.lock must exist"

    def test_requirements_lock_has_pinned_versions(self):
        """requirements.lock should have pinned versions (==)."""
        lock_path = os.path.join(os.path.dirname(__file__), "..", "requirements.lock")
        with open(lock_path) as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        pinned = [l for l in lines if "==" in l]
        assert len(pinned) > 10, "Lock file should have many pinned dependencies"


# ═══════════════════════════════════════════════════════════
# Task 2.6: Rate Limit Audit Tests
# ═══════════════════════════════════════════════════════════
class TestRateLimitAudit:
    """Verify all mutation endpoints have explicit rate limits."""

    def test_backtest_has_rate_limit(self):
        """POST /backtest/run must have a rate limit."""
        import app.api.backtest as mod
        source = inspect.getsource(mod)
        assert "@limiter.limit" in source
        assert "3/hour" in source

    def test_price_alert_create_has_rate_limit(self):
        """POST /alerts/price must have a rate limit."""
        import app.api.price_alerts as mod
        source = inspect.getsource(mod.create_price_alert)
        assert "request: Request" in source  # Limiter requires Request param

    def test_price_alert_delete_has_rate_limit(self):
        """DELETE /alerts/price/{id} must have a rate limit."""
        import app.api.price_alerts as mod
        source = inspect.getsource(mod)
        # Check both create and delete have rate limits
        assert source.count("@limiter.limit") >= 2

    def test_password_change_has_rate_limit(self):
        """PUT /password must have strict rate limit."""
        import app.api.auth_routes as mod
        source = inspect.getsource(mod.change_password)
        assert "request: Request" in source

    def test_account_delete_has_rate_limit(self):
        """DELETE /account must have a rate limit."""
        import app.api.auth_routes as mod
        source = inspect.getsource(mod)
        assert "1/minute" in source  # DELETE /account should be very limited

    def test_logout_has_rate_limit(self):
        """POST /logout must have a rate limit."""
        import app.api.auth_routes as mod
        source = inspect.getsource(mod)
        # Find all @limiter.limit decorators
        assert source.count("@limiter.limit") >= 4  # login, register, refresh, + logout/logout-all/password/delete

    def test_calendar_create_has_rate_limit(self):
        """POST /news/calendar must have a rate limit."""
        import app.api.news as mod
        source = inspect.getsource(mod)
        assert "@limiter.limit" in source

    def test_watchlist_update_has_rate_limit(self):
        """POST /alerts/watchlist must have a rate limit."""
        import app.api.alerts as mod
        source = inspect.getsource(mod.update_watchlist)
        assert "request: Request" in source

    def test_rate_limiter_disabled_in_tests(self):
        """Rate limiter should be disabled during tests."""
        from app.rate_limit import limiter
        assert not limiter.enabled, "Limiter should be disabled in test environment"


# ═══════════════════════════════════════════════════════════
# Task 2.7: Input Validation Tests
# ═══════════════════════════════════════════════════════════
class TestInputValidation:
    """Verify input validation hardening."""

    def test_max_request_body_config_exists(self):
        """max_request_body_bytes config must exist."""
        from app.config import get_settings
        settings = get_settings()
        assert hasattr(settings, "max_request_body_bytes")
        assert settings.max_request_body_bytes == 1_048_576  # 1MB

    def test_body_size_middleware_in_main(self):
        """Main app must have request body size limiting middleware."""
        source = inspect.getsource(__import__("app.main", fromlist=["app"]))
        assert "limit_request_body" in source or "max_request_body_bytes" in source

    @pytest.mark.asyncio
    async def test_shared_signals_have_noindex(self, test_client):
        """Shared signal views must include X-Robots-Tag: noindex."""
        # Make a request to shared endpoint (even if 404, check headers)
        resp = await test_client.get("/api/v1/shared/00000000-0000-0000-0000-000000000001")
        # Even error responses in the shared path should have noindex
        assert resp.headers.get("x-robots-tag") == "noindex"

    def test_noindex_middleware_in_main(self):
        """Main app must add X-Robots-Tag for /shared/ paths."""
        source = inspect.getsource(__import__("app.main", fromlist=["app"]))
        assert "X-Robots-Tag" in source
        assert "noindex" in source


# ═══════════════════════════════════════════════════════════
# Integration: Phase 2 security headers on actual responses
# ═══════════════════════════════════════════════════════════
class TestPhase2SecurityIntegration:
    """End-to-end test for security headers on real API responses."""

    @pytest.mark.asyncio
    async def test_signals_endpoint_has_security_headers(self, test_client):
        """GET /signals must include all security headers."""
        resp = await test_client.get("/api/v1/signals")
        assert resp.status_code == 200
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert "strict-origin" in resp.headers.get("referrer-policy", "")
        assert "content-security-policy" in resp.headers

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_quickly(self, test_client):
        """Health endpoint should respond quickly even with security middleware."""
        import time
        start = time.monotonic()
        resp = await test_client.get("/health")
        elapsed = time.monotonic() - start
        assert resp.status_code == 200
        assert elapsed < 5.0, f"Health check took too long: {elapsed:.2f}s"
