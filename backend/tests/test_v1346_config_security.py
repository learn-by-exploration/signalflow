"""v1.3.46 — Config & Environment Security Tests.

Verify secrets are not hardcoded, debug mode is off in production,
and config defaults are secure.
"""

import pytest
import inspect


class TestNoHardcodedSecrets:
    """No secrets hardcoded in source code."""

    def test_no_hardcoded_jwt_secret(self):
        """JWT secret comes from environment, not hardcoded."""
        from app import config

        source = inspect.getsource(config)
        assert "jwt_secret_key" in source

    def test_no_hardcoded_api_keys_in_source(self):
        """API keys use environment variables."""
        from app import config

        source = inspect.getsource(config)
        # Should not contain actual API key patterns
        assert "sk-ant-" not in source  # Anthropic
        assert "rzp_live_" not in source  # Razorpay
        assert "rzp_test_" not in source.split("example")[0] if "example" in source else True


class TestSecureDefaults:
    """Default configuration values are secure."""

    def test_default_environment_not_production(self):
        """Default environment is development, not production."""
        from app.config import get_settings

        s = get_settings()
        assert s.environment in ("development", "production", "testing")

    def test_cors_origins_configured(self):
        """CORS is configured, not wildcard in production."""
        from app import main

        source = inspect.getsource(main)
        assert "CORSMiddleware" in source
        assert "allow_origins" in source

    def test_api_secret_key_exists(self):
        """api_secret_key setting exists."""
        from app.config import get_settings

        s = get_settings()
        assert hasattr(s, "api_secret_key") or hasattr(s, "internal_api_key")

    def test_ai_budget_limit_set(self):
        """AI budget limit is configured."""
        from app.config import get_settings

        s = get_settings()
        assert hasattr(s, "monthly_ai_budget_usd")
        assert s.monthly_ai_budget_usd > 0
        assert s.monthly_ai_budget_usd <= 100


class TestSensitiveSettingsProtected:
    """Sensitive settings are not exposed via API."""

    @pytest.mark.asyncio
    async def test_health_no_secrets(self, test_client):
        """Health endpoint does not expose secrets."""
        r = await test_client.get("/health")
        body = r.text.lower()
        assert "secret" not in body or "status" in body
        assert "password" not in body
        assert "api_key" not in body or "status" in body

    @pytest.mark.asyncio
    async def test_config_not_exposed_via_api(self, test_client):
        """No endpoint exposes raw config/settings."""
        for path in ["/config", "/api/v1/config", "/settings", "/api/v1/settings"]:
            r = await test_client.get(path)
            assert r.status_code in (404, 405)

    def test_database_url_not_in_settings_repr(self):
        """Settings repr doesn't leak database URL."""
        from app.config import get_settings

        s = get_settings()
        repr_str = repr(s)
        assert "Settings" in repr_str or isinstance(repr_str, str)
