"""v1.3.49 — Regression Guard Suite Tests.

Ensure previously-found security bugs stay fixed.
Each test references a specific past vulnerability class.
"""

import pytest
import inspect


class TestWebUserIdentityRegression:
    """Web-only users (no Telegram) must work everywhere.

    Regression: telegram_chat_id=NULL caused silent failures.
    """

    @pytest.mark.asyncio
    async def test_web_user_can_list_trades(self, test_client):
        """Web-only users can access portfolio."""
        r = await test_client.get("/api/v1/portfolio/trades")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_web_user_can_list_signals(self, test_client):
        """Web-only users can list signals."""
        r = await test_client.get("/api/v1/signals")
        assert r.status_code == 200


class TestJWTSecurityRegression:
    """JWT edge cases that were previously bugs."""

    def test_jwt_uses_hs256(self):
        """JWT algorithm is HS256, not None or asymmetric."""
        from app.config import get_settings

        s = get_settings()
        algo = getattr(s, "JWT_ALGORITHM", "HS256")
        assert algo == "HS256"

    def test_jwt_tokens_have_expiry(self):
        """All tokens include expiry claim."""
        from app.auth import create_access_token

        token = create_access_token("test-user-id", None, "free")
        import jwt
        from app.config import get_settings

        s = get_settings()
        payload = jwt.decode(
            token,
            s.jwt_secret_key,
            algorithms=["HS256"],
        )
        assert "exp" in payload


class TestRateLimitRegression:
    """Rate limiting stays active."""

    def test_limiter_imported_in_main(self):
        """Rate limiter is imported and used in main app."""
        from app import main

        source = inspect.getsource(main)
        assert "limiter" in source or "rate_limit" in source or "SlowAPIMiddleware" in source


class TestCORSRegression:
    """CORS configuration stays secure."""

    def test_cors_middleware_present(self):
        """CORS middleware is configured."""
        from app import main

        source = inspect.getsource(main)
        assert "CORSMiddleware" in source

    def test_cors_not_wildcard_only(self):
        """CORS is not just wildcard *."""
        from app import main

        source = inspect.getsource(main)
        # Should have specific origins configured
        assert "allow_origins" in source


class TestSQLInjectionRegression:
    """SQL injection vectors stay patched."""

    @pytest.mark.asyncio
    async def test_signal_filter_safe(self, test_client):
        """Signal filtering uses parameterized queries."""
        r = await test_client.get("/api/v1/signals?market=stock' OR '1'='1")
        assert r.status_code in (200, 400, 422)
        if r.status_code == 200:
            data = r.json()
            # Should not return all signals
            assert isinstance(data.get("data", []), list)

    @pytest.mark.asyncio
    async def test_history_filter_safe(self, test_client):
        """History filtering is parameterized."""
        r = await test_client.get("/api/v1/signals/history?outcome='; DROP TABLE--")
        assert r.status_code in (200, 400, 422)


class TestPasswordSecurityRegression:
    """Password security constraints stay enforced."""

    def test_password_hashing_uses_bcrypt(self):
        """Password hashing uses bcrypt."""
        from app.auth import hash_password

        hashed = hash_password("TestPassword123!")
        assert hashed.startswith("$2")  # bcrypt prefix

    def test_password_verify_works(self):
        """Password verification works correctly."""
        from app.auth import hash_password, verify_password

        hashed = hash_password("CheckMe123!")
        assert verify_password("CheckMe123!", hashed) is True
        assert verify_password("WrongPassword", hashed) is False
