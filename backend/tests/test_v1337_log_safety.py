"""v1.3.37 — Sensitive Data in Logs Tests.

Verify passwords, tokens, API keys, and PII are not
present in log output or error responses.
"""

import inspect
import logging

import pytest


class TestNoSecretsInLogs:
    """Secrets must never appear in log output."""

    def test_auth_module_no_password_logging(self):
        """Auth module doesn't log plaintext passwords."""
        from app import auth
        source = inspect.getsource(auth)
        # Should not have logger calls with password
        lines = source.split("\n")
        for line in lines:
            if "logger" in line and "password" in line.lower():
                # It's ok to log "password_changed" or "wrong_password" as events
                assert "password_hash" not in line
                assert "plain" not in line.lower()

    def test_auth_routes_no_password_logging(self):
        """Auth API routes don't log raw passwords."""
        from app.api import auth_routes
        source = inspect.getsource(auth_routes)
        lines = source.split("\n")
        for line in lines:
            if "logger" in line:
                assert "password=" not in line
                assert "password\":" not in line

    def test_config_no_secret_defaults(self):
        """Config has no hardcoded API keys as defaults."""
        from app.config import Settings
        source = inspect.getsource(Settings)
        assert "sk-ant-" not in source
        assert "rzp_" not in source


class TestNoSecretsInResponses:
    """API responses must not contain secrets."""

    @pytest.mark.asyncio
    async def test_health_no_db_url(self, test_client):
        """Health endpoint doesn't expose database URL."""
        r = await test_client.get("/health")
        body = r.text
        assert "postgresql" not in body.lower()
        assert "password" not in body.lower()

    @pytest.mark.asyncio
    async def test_health_no_api_keys(self, test_client):
        """Health endpoint doesn't expose API keys."""
        r = await test_client.get("/health")
        body = r.text
        assert "sk-ant" not in body
        assert "rzp_" not in body

    @pytest.mark.asyncio
    async def test_error_no_internals(self, test_client):
        """Error responses don't expose file paths."""
        r = await test_client.get("/api/v1/signals/not-a-valid-uuid")
        body = r.text
        assert "/home/" not in body
        assert "/app/" not in body or "app.api" not in body
        assert "Traceback" not in body


class TestProfileEndpointSafety:
    """Profile endpoint must not expose password hash."""

    @pytest.mark.asyncio
    async def test_profile_no_password_hash(self, test_client):
        """GET /auth/profile doesn't return password hash."""
        r = await test_client.get("/api/v1/auth/profile")
        if r.status_code == 200:
            body = r.text
            assert "$2b$" not in body  # bcrypt hash prefix
            assert "password_hash" not in body
            assert "password" not in body.lower() or "password_changed" in body.lower()


class TestStructuredLogging:
    """Log format must be consistent and safe."""

    def test_logger_exists_in_main(self):
        """Main app uses logging."""
        from app import main
        assert hasattr(main, "logger") or "logging" in inspect.getsource(main)

    def test_logger_exists_in_auth(self):
        """Auth module uses structured logging."""
        from app import auth
        assert hasattr(auth, "logger")
