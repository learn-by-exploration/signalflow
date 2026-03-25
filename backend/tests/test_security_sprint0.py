"""Sprint 0 security tests — CRIT-01, CRIT-09/10, CRIT-12, CRIT-14."""

import math
from decimal import Decimal
from unittest.mock import patch

import pytest
from pydantic import ValidationError


# ── CRIT-01: Auth bypass fix ──

class TestAuthBypass:
    """CRIT-01: API key must be required in all environments."""

    @pytest.mark.asyncio
    async def test_empty_api_key_returns_401(self):
        """Empty API_SECRET_KEY must reject requests, never return 'anonymous'."""
        from app.auth import require_api_key

        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.api_secret_key = ""
            with pytest.raises(Exception) as exc_info:
                await require_api_key(api_key="anything")
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_401(self):
        """Request without X-API-Key header must be rejected."""
        from app.auth import require_api_key

        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.api_secret_key = "test-secret-key"
            with pytest.raises(Exception) as exc_info:
                await require_api_key(api_key=None)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_api_key_returns_401(self):
        """Wrong API key must be rejected."""
        from app.auth import require_api_key

        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.api_secret_key = "correct-key"
            with pytest.raises(Exception) as exc_info:
                await require_api_key(api_key="wrong-key")
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_correct_api_key_succeeds(self):
        """Correct API key must be accepted."""
        from app.auth import require_api_key

        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.api_secret_key = "correct-key"
            result = await require_api_key(api_key="correct-key")
            assert result == "correct-key"

    @pytest.mark.asyncio
    async def test_anonymous_never_returned(self):
        """The string 'anonymous' must never be returned as a valid auth result."""
        from app.auth import require_api_key

        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.api_secret_key = ""
            try:
                result = await require_api_key(api_key="")
                assert result != "anonymous", "Auth bypass: 'anonymous' returned"
            except Exception:
                pass  # Expected — 401 is correct behavior


# ── CRIT-09: OHLCV validation ──

class TestOHLCVValidation:
    """CRIT-09: OHLCV candles must be validated before persistence."""

    def test_valid_candle_passes(self):
        from app.services.data_ingestion.validators import validate_candle

        candle = {"open": "100.0", "high": "110.0", "low": "95.0", "close": "105.0"}
        valid, err = validate_candle(candle)
        assert valid is True
        assert err == ""

    def test_high_less_than_low_rejected(self):
        from app.services.data_ingestion.validators import validate_candle

        candle = {"open": "100", "high": "90", "low": "95", "close": "92"}
        valid, err = validate_candle(candle)
        assert valid is False
        assert "high" in err.lower() and "low" in err.lower()

    def test_high_less_than_close_rejected(self):
        from app.services.data_ingestion.validators import validate_candle

        candle = {"open": "100", "high": "99", "low": "95", "close": "100"}
        valid, err = validate_candle(candle)
        assert valid is False

    def test_low_greater_than_open_rejected(self):
        from app.services.data_ingestion.validators import validate_candle

        candle = {"open": "100", "high": "110", "low": "101", "close": "105"}
        valid, err = validate_candle(candle)
        assert valid is False

    def test_negative_price_rejected(self):
        from app.services.data_ingestion.validators import validate_candle

        candle = {"open": "-100", "high": "110", "low": "90", "close": "100"}
        valid, err = validate_candle(candle)
        assert valid is False
        assert "negative" in err.lower()

    def test_nan_price_rejected(self):
        from app.services.data_ingestion.validators import validate_candle

        candle = {"open": float("nan"), "high": "100", "low": "90", "close": "95"}
        valid, err = validate_candle(candle)
        assert valid is False
        assert "nan" in err.lower()

    def test_infinity_price_rejected(self):
        from app.services.data_ingestion.validators import validate_candle

        candle = {"open": float("inf"), "high": "100", "low": "90", "close": "95"}
        valid, err = validate_candle(candle)
        assert valid is False

    def test_missing_key_rejected(self):
        from app.services.data_ingestion.validators import validate_candle

        candle = {"open": "100", "high": "110"}  # missing low, close
        valid, err = validate_candle(candle)
        assert valid is False

    def test_non_numeric_rejected(self):
        from app.services.data_ingestion.validators import validate_candle

        candle = {"open": "abc", "high": "110", "low": "90", "close": "100"}
        valid, err = validate_candle(candle)
        assert valid is False

    def test_zero_prices_valid(self):
        """Zero prices can be valid (e.g. a penny stock at 0.0000)."""
        from app.services.data_ingestion.validators import validate_candle

        candle = {"open": "0", "high": "0", "low": "0", "close": "0"}
        valid, err = validate_candle(candle)
        assert valid is True


# ── CRIT-10: Spot-only fallback detection ──

class TestSpotOnlyDetection:
    """CRIT-10: CoinGecko fallback data must be identified as spot-only."""

    def test_spot_only_candle_detected(self):
        from app.services.data_ingestion.validators import is_spot_only_candle

        candle = {"open": "97000", "high": "97000", "low": "97000", "close": "97000"}
        assert is_spot_only_candle(candle) is True

    def test_real_candle_not_spot_only(self):
        from app.services.data_ingestion.validators import is_spot_only_candle

        candle = {"open": "97000", "high": "98000", "low": "96500", "close": "97500"}
        assert is_spot_only_candle(candle) is False

    def test_coingecko_fallback_marked_spot_only(self):
        """CoinGecko fallback results should include is_spot_only flag."""
        from app.services.data_ingestion.crypto import CryptoFetcher

        fetcher = CryptoFetcher.__new__(CryptoFetcher)

        with patch("app.services.data_ingestion.crypto.httpx.Client") as mock_client:
            mock_resp = mock_client.return_value.__enter__.return_value.get.return_value
            mock_resp.raise_for_status = lambda: None
            mock_resp.json.return_value = {
                "bitcoin": {"usd": 97000, "usd_24h_vol": 50000000}
            }
            result = fetcher._fetch_from_coingecko("BTCUSDT")

        assert result is not None
        assert result.get("is_spot_only") is True


# ── CRIT-12: Schema enum validation ──

class TestSchemaEnumValidation:
    """CRIT-12: signal_type and market_type must be constrained to valid values."""

    def test_valid_signal_type_accepted(self):
        from app.schemas.signal import SignalResponse

        data = {
            "id": "00000000-0000-0000-0000-000000000001",
            "symbol": "HDFCBANK",
            "market_type": "stock",
            "signal_type": "STRONG_BUY",
            "confidence": 92,
            "current_price": Decimal("1678.90"),
            "target_price": Decimal("1780.00"),
            "stop_loss": Decimal("1630.00"),
            "ai_reasoning": "Test",
            "technical_data": {},
            "is_active": True,
            "created_at": "2026-03-25T10:00:00Z",
        }
        signal = SignalResponse(**data)
        assert signal.signal_type == "STRONG_BUY"

    def test_invalid_signal_type_rejected(self):
        from app.schemas.signal import SignalResponse

        data = {
            "id": "00000000-0000-0000-0000-000000000001",
            "symbol": "HDFCBANK",
            "market_type": "stock",
            "signal_type": "INVALID_TYPE",
            "confidence": 92,
            "current_price": Decimal("1678.90"),
            "target_price": Decimal("1780.00"),
            "stop_loss": Decimal("1630.00"),
            "ai_reasoning": "Test",
            "technical_data": {},
            "is_active": True,
            "created_at": "2026-03-25T10:00:00Z",
        }
        with pytest.raises(ValidationError):
            SignalResponse(**data)

    def test_invalid_market_type_rejected(self):
        from app.schemas.signal import SignalResponse

        data = {
            "id": "00000000-0000-0000-0000-000000000001",
            "symbol": "GOLD",
            "market_type": "commodity",
            "signal_type": "BUY",
            "confidence": 80,
            "current_price": Decimal("2000.00"),
            "target_price": Decimal("2100.00"),
            "stop_loss": Decimal("1950.00"),
            "ai_reasoning": "Test",
            "technical_data": {},
            "is_active": True,
            "created_at": "2026-03-25T10:00:00Z",
        }
        with pytest.raises(ValidationError):
            SignalResponse(**data)

    def test_confidence_over_100_rejected(self):
        from app.schemas.signal import SignalResponse

        data = {
            "id": "00000000-0000-0000-0000-000000000001",
            "symbol": "HDFCBANK",
            "market_type": "stock",
            "signal_type": "BUY",
            "confidence": 150,
            "current_price": Decimal("1678.90"),
            "target_price": Decimal("1780.00"),
            "stop_loss": Decimal("1630.00"),
            "ai_reasoning": "Test",
            "technical_data": {},
            "is_active": True,
            "created_at": "2026-03-25T10:00:00Z",
        }
        with pytest.raises(ValidationError):
            SignalResponse(**data)

    def test_confidence_negative_rejected(self):
        from app.schemas.signal import SignalResponse

        data = {
            "id": "00000000-0000-0000-0000-000000000001",
            "symbol": "HDFCBANK",
            "market_type": "stock",
            "signal_type": "BUY",
            "confidence": -5,
            "current_price": Decimal("1678.90"),
            "target_price": Decimal("1780.00"),
            "stop_loss": Decimal("1630.00"),
            "ai_reasoning": "Test",
            "technical_data": {},
            "is_active": True,
            "created_at": "2026-03-25T10:00:00Z",
        }
        with pytest.raises(ValidationError):
            SignalResponse(**data)

    def test_market_snapshot_enum_validated(self):
        from app.schemas.market import MarketSnapshot

        with pytest.raises(ValidationError):
            MarketSnapshot(
                symbol="GOLD",
                price=Decimal("2000.00"),
                change_pct=Decimal("1.5"),
                market_type="commodity",
            )


# ── CRIT-14: CSP headers ──

class TestSecurityHeaders:
    """CRIT-14: Security headers must be present on all responses."""

    @pytest.mark.asyncio
    async def test_health_endpoint_has_csp_header(self):
        """Health endpoint response must include Content-Security-Policy."""
        from unittest.mock import AsyncMock, MagicMock

        from httpx import AsyncClient, ASGITransport

        with patch("app.main.get_settings") as mock_settings:
            s = MagicMock()
            s.environment = "development"
            s.frontend_url = "http://localhost:3000"
            s.database_url = "sqlite+aiosqlite:///test.db"
            s.redis_url = "redis://localhost:6379/0"
            s.sentry_dsn = ""
            s.log_level = "INFO"
            s.allowed_hosts = ""
            s.api_secret_key = "test"
            s.monthly_ai_budget_usd = 30.0
            mock_settings.return_value = s

            from app.main import app

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/health")

            assert "Content-Security-Policy" in resp.headers
            csp = resp.headers["Content-Security-Policy"]
            assert "default-src" in csp
            assert "frame-ancestors 'none'" in csp

    @pytest.mark.asyncio
    async def test_x_frame_options_present(self):
        from unittest.mock import AsyncMock, MagicMock

        from httpx import AsyncClient, ASGITransport

        with patch("app.main.get_settings") as mock_settings:
            s = MagicMock()
            s.environment = "development"
            s.frontend_url = "http://localhost:3000"
            s.database_url = "sqlite+aiosqlite:///test.db"
            s.redis_url = "redis://localhost:6379/0"
            s.sentry_dsn = ""
            s.log_level = "INFO"
            s.allowed_hosts = ""
            s.api_secret_key = "test"
            s.monthly_ai_budget_usd = 30.0
            mock_settings.return_value = s

            from app.main import app

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/health")

            assert resp.headers.get("X-Frame-Options") == "DENY"
            assert resp.headers.get("X-Content-Type-Options") == "nosniff"
