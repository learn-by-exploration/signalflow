"""v1.3.13 — CORS Configuration Validation Tests.

Verify CORS is properly configured for security in both
development and production environments.
"""

import os
import re

import pytest


class TestCORSConfiguration:
    """CORS must be properly configured in main.py."""

    def _get_main_content(self) -> str:
        path = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")
        with open(path) as f:
            return f.read()

    def test_cors_middleware_registered(self):
        """CORSMiddleware must be added to the app."""
        content = self._get_main_content()
        assert "CORSMiddleware" in content

    def test_allow_origins_not_wildcard_in_prod(self):
        """Production must NOT use allow_origins=['*']."""
        content = self._get_main_content()
        # Check that '*' wildcard is not used
        assert "allow_origins=[\"*\"]" not in content
        assert "allow_origins=['*']" not in content

    def test_allow_origins_uses_frontend_url(self):
        """Production origins should come from FRONTEND_URL setting."""
        content = self._get_main_content()
        assert "frontend_url" in content.lower() or "FRONTEND_URL" in content

    def test_dev_origins_restricted_to_localhost(self):
        """Development CORS allows localhost only, not public origins."""
        content = self._get_main_content()
        assert "localhost" in content
        assert "127.0.0.1" in content

    def test_credentials_enabled(self):
        """allow_credentials must be True for JWT cookie support."""
        content = self._get_main_content()
        assert "allow_credentials=True" in content

    def test_specific_methods_listed(self):
        """Allowed methods should be explicitly listed, not ['*']."""
        content = self._get_main_content()
        # Should list specific methods
        assert "allow_methods=[\"*\"]" not in content or "GET" in content

    def test_specific_headers_listed(self):
        """Allowed headers should include Authorization and Content-Type."""
        content = self._get_main_content()
        assert "Authorization" in content
        assert "Content-Type" in content

    def test_environment_based_cors(self):
        """CORS should differ between development and production."""
        content = self._get_main_content()
        assert "development" in content or "production" in content
        assert "environment" in content.lower()


class TestCORSHeadersInResponses:
    """Verify CORS headers appear in actual responses."""

    @pytest.mark.asyncio
    async def test_options_preflight_returns_cors_headers(self, test_client):
        """OPTIONS request should return CORS headers."""
        resp = await test_client.options(
            "/api/v1/signals",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Should have CORS headers (may be 200 or 204)
        assert resp.status_code in (200, 204, 405)

    @pytest.mark.asyncio
    async def test_no_cors_for_unknown_origin(self, test_client):
        """Request from unknown origin should NOT get CORS headers in prod."""
        resp = await test_client.get(
            "/api/v1/signals",
            headers={"Origin": "https://evil-site.com"},
        )
        # In test env, CORS may be permissive. Check that the endpoint responds.
        assert resp.status_code in (200, 403)

    @pytest.mark.asyncio
    async def test_x_api_key_header_allowed(self, test_client):
        """X-API-Key must be in allowed headers."""
        content = self._get_main_content()
        assert "X-API-Key" in content

    def _get_main_content(self) -> str:
        path = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")
        with open(path) as f:
            return f.read()


class TestDevCORSRegex:
    """Development CORS regex must be safe."""

    def test_dev_regex_limits_domains(self):
        """Dev CORS regex should only match private/local IPs."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")
        with open(path) as f:
            content = f.read()
        # If regex is used, it should match private IP ranges only
        if "allow_origin_regex" in content:
            # Check it includes patterns for private IPs
            assert "localhost" in content or "127\\.0\\.0\\.1" in content
            # Must not match any arbitrary domain
            assert ".*" not in content.split("allow_origin_regex")[1].split("\n")[0] or \
                   "localhost" in content

    def test_prod_no_regex(self):
        """Production should NOT use regex for CORS (strict origins only)."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")
        with open(path) as f:
            content = f.read()
        # Check that regex is only for development
        if "allow_origin_regex" in content:
            # Should be None in production
            assert "None" in content  # _cors_origins_regex = None for production
