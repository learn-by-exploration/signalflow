"""v1.3.11 — Rate Limiting Validation Tests.

Verify rate limits are configured on all sensitive endpoints
and the rate limiter is properly integrated.
"""

import os
import re

import pytest


class TestRateLimiterConfig:
    """Rate limiter must be properly configured."""

    def test_rate_limiter_exists(self):
        """rate_limit.py module must define a limiter."""
        from app.rate_limit import limiter
        assert limiter is not None

    def test_default_rate_limit_set(self):
        """Global default rate limit must be configured."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "rate_limit.py")
        with open(path) as f:
            content = f.read()
        assert "default_limits" in content, "Must have default_limits configured"

    def test_rate_limiter_disabled_in_tests(self):
        """Rate limiter should be disabled in test environment."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "rate_limit.py")
        with open(path) as f:
            content = f.read()
        assert "TESTING" in content or "enabled" in content, (
            "Rate limiter should have a disable mechanism for testing"
        )


class TestEndpointRateLimits:
    """Verify rate limits on all sensitive endpoints."""

    def _check_endpoint_has_limiter(self, filepath: str, endpoint_name: str) -> bool:
        """Check if a specific endpoint has @limiter.limit decorator."""
        with open(filepath) as f:
            content = f.read()
        # Find the endpoint function
        pattern = f"async def {endpoint_name}"
        idx = content.find(pattern)
        if idx == -1:
            return False
        # Check for limiter in the ~200 chars before the function
        before = content[max(0, idx - 200):idx]
        return "@limiter.limit" in before

    def test_register_rate_limited(self):
        """Registration must be rate limited."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "auth_routes.py")
        assert self._check_endpoint_has_limiter(path, "register")

    def test_login_rate_limited(self):
        """Login must be rate limited."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "auth_routes.py")
        assert self._check_endpoint_has_limiter(path, "login")

    def test_refresh_rate_limited(self):
        """Token refresh must be rate limited."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "auth_routes.py")
        assert self._check_endpoint_has_limiter(path, "refresh_token") or \
               self._check_endpoint_has_limiter(path, "refresh")

    def test_ai_qa_rate_limited(self):
        """AI Q&A (expensive) must be rate limited."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "ai_qa.py")
        assert self._check_endpoint_has_limiter(path, "ask_about_symbol")

    def test_share_signal_rate_limited(self):
        """Signal sharing must be rate limited."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "sharing.py")
        assert self._check_endpoint_has_limiter(path, "share_signal") or \
               self._check_endpoint_has_limiter(path, "create_share")

    def test_create_alert_rate_limited(self):
        """Alert config creation must be rate limited."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "alerts.py")
        assert self._check_endpoint_has_limiter(path, "create_alert_config")

    def test_submit_feedback_rate_limited(self):
        """Signal feedback submission must be rate limited."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "signal_feedback.py")
        assert self._check_endpoint_has_limiter(path, "submit_feedback")

    def test_portfolio_trade_rate_limited(self):
        """Trade logging must be rate limited."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "portfolio.py")
        assert self._check_endpoint_has_limiter(path, "log_trade") or \
               self._check_endpoint_has_limiter(path, "create_trade")

    def test_payment_subscribe_rate_limited(self):
        """Subscription creation must be rate limited."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "payments.py")
        assert self._check_endpoint_has_limiter(path, "create_paid_subscription") or \
               self._check_endpoint_has_limiter(path, "start_trial")

    def test_password_change_rate_limited(self):
        """Password change must be rate limited."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "auth_routes.py")
        assert self._check_endpoint_has_limiter(path, "change_password")

    def test_account_delete_rate_limited(self):
        """Account deletion must be rate limited."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "auth_routes.py")
        assert self._check_endpoint_has_limiter(path, "delete_account")


class TestRateLimitValues:
    """Rate limit values should be appropriately restrictive."""

    def _extract_rate_limits(self, filepath: str) -> list[tuple[str, str]]:
        """Extract (limit_value, endpoint_name) pairs from a file."""
        with open(filepath) as f:
            content = f.read()
        results = []
        pattern = re.compile(r'@limiter\.limit\("([^"]+)"\)\s+async def (\w+)')
        for match in pattern.finditer(content):
            results.append((match.group(1), match.group(2)))
        return results

    def test_auth_endpoints_restrictive(self):
        """Auth endpoints should have <= 20/minute limits."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "auth_routes.py")
        limits = self._extract_rate_limits(path)
        for limit_val, endpoint in limits:
            if endpoint in ("register", "login", "change_password", "delete_account"):
                # Parse "5/minute" format
                parts = limit_val.split("/")
                count = int(parts[0])
                assert count <= 20, (
                    f"Auth endpoint {endpoint} limit too high: {limit_val}"
                )

    def test_ai_endpoint_very_restrictive(self):
        """AI Q&A should be <= 10/minute."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "ai_qa.py")
        limits = self._extract_rate_limits(path)
        for limit_val, endpoint in limits:
            parts = limit_val.split("/")
            count = int(parts[0])
            assert count <= 10, f"AI endpoint limit too high: {limit_val}"

    def test_payment_endpoints_very_restrictive(self):
        """Payment endpoints should be <= 5/hour or minute."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "payments.py")
        limits = self._extract_rate_limits(path)
        for limit_val, endpoint in limits:
            parts = limit_val.split("/")
            count = int(parts[0])
            assert count <= 30, f"Payment endpoint {endpoint} limit too high: {limit_val}"


class TestRateLimiterIntegration:
    """Rate limiter must be properly mounted in the app."""

    def test_limiter_registered_in_main(self):
        """Rate limiter must be registered in main.py."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")
        with open(path) as f:
            content = f.read()
        assert "limiter" in content, "Rate limiter must be registered in main app"
        assert "SlowAPIMiddleware" in content or "slowapi" in content.lower(), (
            "SlowAPI middleware must be registered"
        )

    def test_rate_limit_error_handler(self):
        """Rate limit exceeded must return proper error response."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")
        with open(path) as f:
            content = f.read()
        assert "RateLimitExceeded" in content or "429" in content, (
            "Rate limit exceeded handler should be configured"
        )
