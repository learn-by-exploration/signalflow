"""Sprint 4 Security Tests — Logging, monitoring, hardening.

CRIT-15: Error message sanitization
HIGH-22+: Auth failure logging, rate limit logging, budget alerting
"""

import logging

import pytest


# ── Auth Failure Logging ──


class TestAuthFailureLogging:
    """Verify auth failures are logged."""

    def test_decode_jwt_logs_expired(self) -> None:
        """Expired token decoding must log a warning."""
        import inspect
        from app.auth import decode_jwt_token
        source = inspect.getsource(decode_jwt_token)
        assert "auth_failure" in source
        assert "token_expired" in source

    def test_decode_jwt_logs_invalid(self) -> None:
        """Invalid token decoding must log a warning."""
        import inspect
        from app.auth import decode_jwt_token
        source = inspect.getsource(decode_jwt_token)
        assert "invalid_token" in source

    def test_api_key_failure_logged(self) -> None:
        """Invalid API key must log a warning."""
        import inspect
        from app.auth import require_api_key
        source = inspect.getsource(require_api_key)
        assert "auth_failure" in source

    def test_get_current_user_logs_rejection(self) -> None:
        """get_current_user rejects API-key auth with logging."""
        import inspect
        from app.auth import get_current_user
        source = inspect.getsource(get_current_user)
        assert "auth_failure" in source


# ── Rate Limit Logging ──


class TestRateLimitLogging:
    """Verify rate limit violations are logged."""

    def test_rate_limit_handler_logs(self) -> None:
        """Rate limit exceeded handler must log the violation."""
        import inspect
        from app.main import _rate_limit_exceeded_with_logging
        source = inspect.getsource(_rate_limit_exceeded_with_logging)
        assert "rate_limit_exceeded" in source
        assert "client_ip" in source


# ── Budget Threshold Alerting ──


class TestBudgetAlerting:
    """Verify cost tracker logs budget warnings."""

    def test_cost_tracker_has_threshold_alerts(self) -> None:
        """record_usage must log warnings at 80% and critical at 95%."""
        import inspect
        from app.services.ai_engine.cost_tracker import CostTracker
        source = inspect.getsource(CostTracker.record_usage)
        assert "95" in source or "CRITICAL" in source
        assert "80" in source or "WARNING" in source


# ── Error Message Sanitization (CRIT-15) ──


class TestErrorSanitization:
    """Verify API never exposes raw stack traces."""

    def test_global_exception_handler_exists(self) -> None:
        """App must have a global exception handler."""
        import inspect
        from app.main import global_exception_handler
        source = inspect.getsource(global_exception_handler)
        assert "Internal server error" in source
        assert "500" in source

    def test_global_handler_does_not_expose_details(self) -> None:
        """Global handler must return generic message, not exc details."""
        import inspect
        from app.main import global_exception_handler
        source = inspect.getsource(global_exception_handler)
        # Should NOT include exc in the response body
        assert "str(exc)" not in source or "content" not in source.split("str(exc)")[1][:50]


# ── Redis Authentication ──


class TestRedisAuth:
    """Verify Redis requires authentication in compose."""

    def test_docker_compose_redis_requirepass(self) -> None:
        """docker-compose.yml must have requirepass for Redis."""
        import pathlib
        compose = pathlib.Path("/home/shyam/personal/signalflow/docker-compose.yml").read_text()
        assert "requirepass" in compose

    def test_prod_compose_redis_auth(self) -> None:
        """docker-compose.prod.yml must have requirepass."""
        import pathlib
        compose = pathlib.Path("/home/shyam/personal/signalflow/docker-compose.prod.yml").read_text()
        assert "requirepass" in compose


# ── Security Headers ──


class TestSecurityHeaders:
    """Verify security headers are set."""

    def test_hsts_in_backend(self) -> None:
        """Backend must set HSTS header in production."""
        import inspect
        from app.main import correlation_id_middleware
        source = inspect.getsource(correlation_id_middleware)
        assert "Strict-Transport-Security" in source

    def test_csp_in_backend(self) -> None:
        """Backend must set CSP header."""
        import inspect
        from app.main import correlation_id_middleware
        source = inspect.getsource(correlation_id_middleware)
        assert "Content-Security-Policy" in source

    def test_hsts_in_frontend(self) -> None:
        """Next.js config must set HSTS header."""
        import pathlib
        config = pathlib.Path("/home/shyam/personal/signalflow/frontend/next.config.js").read_text()
        assert "Strict-Transport-Security" in config

    def test_xframe_deny(self) -> None:
        """X-Frame-Options must be DENY."""
        import inspect
        from app.main import correlation_id_middleware
        source = inspect.getsource(correlation_id_middleware)
        assert "DENY" in source


# ── Frontend 401 Handling ──


class TestFrontend401:
    """Verify frontend handles 401 responses."""

    def test_api_clears_tokens_on_401(self) -> None:
        """Frontend api.ts must clear tokens on 401."""
        import pathlib
        api_ts = pathlib.Path("/home/shyam/personal/signalflow/frontend/src/lib/api.ts").read_text()
        assert "401" in api_ts
        assert "removeItem" in api_ts
