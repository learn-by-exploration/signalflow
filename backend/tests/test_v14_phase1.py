"""Extensive tests for Phase 1 implementation (v1.4 plan).

Tests cover: sentiment weight changes, temperature=0, retry logic,
singleton engine, pipeline alerting, tier enforcement, JWT revocation,
SEBI compliance, constant-time comparison, pool recycle, and supervisord.
"""

import hmac
import inspect
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


# ═══════════════════════════════════════════════════════════
# Task 1.3: Sentiment Weight Tests
# ═══════════════════════════════════════════════════════════
class TestSentimentWeightReduction:
    """Verify sentiment weights were reduced from 40% to 15% (no-chain) and 15%→10% (chain)."""

    def test_chain_aware_weights_reduced(self):
        """Chain-aware blend: 65/25/10 (was 50/35/15)."""
        from app.services.signal_gen.scorer import TECHNICAL_BLEND, CHAIN_BLEND, SENTIMENT_BLEND

        assert TECHNICAL_BLEND == 0.65, f"TECHNICAL_BLEND should be 0.65, got {TECHNICAL_BLEND}"
        assert CHAIN_BLEND == 0.25, f"CHAIN_BLEND should be 0.25, got {CHAIN_BLEND}"
        assert SENTIMENT_BLEND == 0.10, f"SENTIMENT_BLEND should be 0.10, got {SENTIMENT_BLEND}"
        assert abs(TECHNICAL_BLEND + CHAIN_BLEND + SENTIMENT_BLEND - 1.0) < 0.001

    def test_no_chain_fallback_weights(self):
        """No-chain fallback: 85% tech, 15% sentiment (was 60/40)."""
        from app.services.signal_gen.scorer import compute_final_confidence

        # Create data where tech=80 (bullish), sentiment=20 (bearish)
        tech_data = {
            "rsi": {"value": 35, "signal": "buy", "strength": 75},
            "macd": {"value": 1, "signal": "buy", "strength": 80},
            "bollinger": {"value": -1, "signal": "buy", "strength": 70},
            "volume": {"ratio": 1.5, "signal": "buy", "strength": 65},
            "sma_cross": {"value": 1, "signal": "buy", "strength": 85},
        }
        sentiment_data = {
            "sentiment_score": 20,  # Very bearish
            "confidence_in_analysis": 80,
            "events": [],  # No chain events → fallback path
        }

        # With 85/15 weights, result should be much more bullish than with 60/40
        confidence, signal_type = compute_final_confidence(tech_data, sentiment_data)
        # Tech score ~76, Sent score ~20 → 76*0.85 + 20*0.15 = 64.6 + 3 = 67.6
        assert confidence >= 60, f"With 85/15 weights, bearish sentiment shouldn't drag score below 60, got {confidence}"

    def test_no_ai_cap_unchanged(self):
        """NO_AI_CONFIDENCE_CAP still at 60."""
        from app.services.signal_gen.scorer import NO_AI_CONFIDENCE_CAP

        assert NO_AI_CONFIDENCE_CAP == 60

    def test_chain_aware_scoring_path(self):
        """Chain-aware path uses 65/25/10 blend."""
        from app.services.signal_gen.scorer import compute_final_confidence

        tech_data = {
            "rsi": {"value": 40, "signal": "buy", "strength": 70},
            "macd": {"value": 1, "signal": "buy", "strength": 75},
            "bollinger": {"value": -1, "signal": "buy", "strength": 65},
            "volume": {"ratio": 1.3, "signal": "buy", "strength": 60},
            "sma_cross": {"value": 1, "signal": "buy", "strength": 80},
        }
        # Include events to trigger chain-aware path
        sentiment_data = {
            "sentiment_score": 70,
            "confidence_in_analysis": 80,
            "events": [
                {"description": "Earnings beat", "impact": "positive", "magnitude": 0.8, "category": "earnings"},
            ],
        }

        confidence, signal_type = compute_final_confidence(tech_data, sentiment_data)
        assert 50 <= confidence <= 100
        # With strong tech + events, should be bullish
        assert signal_type in ("BUY", "STRONG_BUY")


# ═══════════════════════════════════════════════════════════
# Task 1.4: Temperature=0 Tests
# ═══════════════════════════════════════════════════════════
class TestTemperatureZero:
    """Verify all Claude API calls use temperature=0."""

    def test_reasoner_uses_temperature_zero(self):
        """AIReasoner must pass temperature=0 in the API JSON body."""
        import app.services.ai_engine.reasoner as mod

        source = inspect.getsource(mod.AIReasoner.generate_reasoning)
        assert '"temperature": 0' in source or "'temperature': 0" in source, \
            "AIReasoner.generate_reasoning must include temperature=0 in the API call"

    def test_sentiment_event_chain_uses_temperature_zero(self):
        """Sentiment event chain call must pass temperature=0."""
        import app.services.ai_engine.sentiment as mod

        source = inspect.getsource(mod.AISentimentEngine._call_claude_event_chain)
        assert '"temperature": 0' in source or "'temperature': 0" in source, \
            "_call_claude_event_chain must include temperature=0"

    def test_sentiment_fallback_uses_temperature_zero(self):
        """Sentiment fallback call must pass temperature=0."""
        import app.services.ai_engine.sentiment as mod

        source = inspect.getsource(mod.AISentimentEngine._call_claude_sentiment_fallback)
        assert '"temperature": 0' in source or "'temperature': 0" in source, \
            "_call_claude_sentiment_fallback must include temperature=0"


# ═══════════════════════════════════════════════════════════
# Task 1.5: Celery Retry Logic Tests
# ═══════════════════════════════════════════════════════════
class TestCeleryRetryLogic:
    """Verify all Celery tasks have retry configuration."""

    def test_data_tasks_have_retries(self):
        """All data ingestion tasks must have autoretry_for."""
        from app.tasks.data_tasks import fetch_indian_stocks, fetch_crypto, fetch_forex, health_check

        for task in [fetch_indian_stocks, fetch_crypto, fetch_forex, health_check]:
            assert task.autoretry_for is not None, f"{task.name} missing autoretry_for"
            assert task.max_retries >= 1, f"{task.name} max_retries should be >= 1"

    def test_signal_tasks_have_retries(self):
        """Signal generation and resolution tasks must have retries."""
        from app.tasks.signal_tasks import generate_signals, resolve_expired

        for task in [generate_signals, resolve_expired]:
            assert task.autoretry_for is not None, f"{task.name} missing autoretry_for"
            assert task.max_retries >= 1, f"{task.name} max_retries should be >= 1"

    def test_ai_tasks_have_retries(self):
        """AI tasks must have retry configuration."""
        from app.tasks.ai_tasks import run_sentiment, expire_stale_events

        assert run_sentiment.autoretry_for is not None
        assert run_sentiment.max_retries >= 1
        assert expire_stale_events.autoretry_for is not None

    def test_alert_tasks_have_retries(self):
        """Alert tasks must have retry configuration."""
        from app.tasks.alert_tasks import morning_brief, evening_wrap, weekly_digest

        for task in [morning_brief, evening_wrap, weekly_digest]:
            assert task.autoretry_for is not None, f"{task.name} missing autoretry_for"
            assert task.max_retries >= 1

    def test_analysis_task_has_retries(self):
        """Analysis task must have retry configuration."""
        from app.tasks.analysis_tasks import run_analysis

        assert run_analysis.autoretry_for is not None
        assert run_analysis.max_retries >= 1

    def test_price_alert_task_has_retries(self):
        """Price alert task must have retry configuration."""
        from app.tasks.price_alert_tasks import check_price_alerts

        assert check_price_alerts.autoretry_for is not None
        assert check_price_alerts.max_retries >= 1

    def test_backtest_task_has_retries(self):
        """Backtest task must have retry configuration."""
        from app.tasks.backtest_tasks import run_backtest

        assert run_backtest.autoretry_for is not None
        assert run_backtest.max_retries >= 1

    def test_data_tasks_use_specific_exceptions(self):
        """Data tasks must NOT use broad Exception — use specific exceptions."""
        from app.tasks.data_tasks import fetch_indian_stocks

        autoretry = fetch_indian_stocks.autoretry_for
        assert Exception not in autoretry, "Must use specific exceptions, not Exception"
        assert ConnectionError in autoretry or TimeoutError in autoretry

    def test_signal_tasks_have_retry_jitter(self):
        """Signal tasks should have retry_jitter=True to avoid thundering herd."""
        from app.tasks.signal_tasks import generate_signals

        # Check the task options for retry_jitter
        assert generate_signals.retry_jitter is True, "generate_signals should have retry_jitter=True"

    def test_calendar_task_has_retries(self):
        """Calendar seeding task must have retry configuration."""
        from app.tasks.calendar_tasks import seed_calendar_events

        assert seed_calendar_events.autoretry_for is not None


# ═══════════════════════════════════════════════════════════
# Task 1.6: Singleton Engine Tests
# ═══════════════════════════════════════════════════════════
class TestSingletonEngine:
    """Verify the Celery singleton engine module works correctly."""

    def test_engine_module_exists(self):
        """_engine.py module should exist and be importable."""
        from app.tasks._engine import get_task_engine, get_task_session_factory

        assert callable(get_task_engine)
        assert callable(get_task_session_factory)

    def test_signal_tasks_use_singleton_engine(self):
        """signal_tasks.py should import from _engine, not create_async_engine directly."""
        import app.tasks.signal_tasks as mod

        source = inspect.getsource(mod)
        assert "from app.tasks._engine import" in source, \
            "signal_tasks should use singleton engine from _engine module"
        assert "create_async_engine(settings.database_url" not in source, \
            "signal_tasks should NOT create engines per-task anymore"

    def test_engine_has_cleanup_signal(self):
        """The _engine module must register a worker_process_shutdown handler."""
        source_code = inspect.getsource(__import__("app.tasks._engine", fromlist=["dispose_engine"]))
        assert "worker_process_shutdown" in source_code, \
            "_engine module must register a cleanup signal handler"


# ═══════════════════════════════════════════════════════════
# Task 1.7: Database Pool Recycle
# ═══════════════════════════════════════════════════════════
class TestDatabasePoolRecycle:
    """Verify pool_recycle is set on the database engine."""

    def test_main_engine_has_pool_recycle(self):
        """Main database.py engine must have pool_recycle=1800."""
        source = inspect.getsource(__import__("app.database", fromlist=["engine"]))
        assert "pool_recycle=1800" in source, "database.py engine must have pool_recycle=1800"

    def test_singleton_engine_has_pool_recycle(self):
        """Task singleton engine must have pool_recycle=1800."""
        source = inspect.getsource(__import__("app.tasks._engine", fromlist=["get_task_engine"]))
        assert "pool_recycle=1800" in source, "Task engine must have pool_recycle=1800"


# ═══════════════════════════════════════════════════════════
# Task 1.11: Pipeline Staleness Alerting
# ═══════════════════════════════════════════════════════════
class TestPipelineStalenessAlerting:
    """Verify the pipeline health check task exists and works."""

    def test_pipeline_health_check_task_exists(self):
        """pipeline_health_check task should be importable."""
        from app.tasks.alert_tasks import pipeline_health_check

        assert callable(pipeline_health_check)
        assert pipeline_health_check.name == "app.tasks.alert_tasks.pipeline_health_check"

    def test_pipeline_health_check_in_scheduler(self):
        """pipeline_health_check should be in the Celery beat schedule."""
        from app.tasks.scheduler import CELERY_BEAT_SCHEDULE

        assert "pipeline-health-check" in CELERY_BEAT_SCHEDULE
        schedule = CELERY_BEAT_SCHEDULE["pipeline-health-check"]
        assert schedule["task"] == "app.tasks.alert_tasks.pipeline_health_check"
        # Should run every 15 minutes (900 seconds)
        assert schedule["schedule"] == 900.0


# ═══════════════════════════════════════════════════════════
# Task 1.13: Tier Enforcement Tests
# ═══════════════════════════════════════════════════════════
class TestTierEnforcement:
    """Verify tier gating on premium endpoints."""

    def test_backtest_requires_pro_tier(self):
        """Backtest endpoints should have require_tier('pro') dependency."""
        import app.api.backtest as mod

        source = inspect.getsource(mod)
        assert "require_tier" in source, "backtest.py must use require_tier"
        assert '"pro"' in source, "backtest must require pro tier"

    def test_ai_qa_requires_pro_tier(self):
        """AI Q&A endpoint should have require_tier('pro') dependency."""
        import app.api.ai_qa as mod

        source = inspect.getsource(mod)
        assert "require_tier" in source, "ai_qa.py must use require_tier"
        assert '"pro"' in source, "AI Q&A must require pro tier"

    @pytest.mark.asyncio
    async def test_backtest_rejects_free_tier(self, test_client):
        """Free tier user should get 403 on backtest endpoint."""
        from app.auth import AuthContext, require_auth
        from app.main import app

        original = app.dependency_overrides.get(require_auth)

        async def free_tier_auth() -> AuthContext:
            return AuthContext(auth_type="jwt", user_id="free-user-id", tier="free")

        app.dependency_overrides[require_auth] = free_tier_auth
        try:
            resp = await test_client.post(
                "/api/v1/backtest/run",
                json={"symbol": "HDFCBANK.NS", "market_type": "stock", "days": 30},
            )
            assert resp.status_code == 403
            assert "pro" in resp.json()["detail"].lower()
        finally:
            if original:
                app.dependency_overrides[require_auth] = original

    @pytest.mark.asyncio
    async def test_ai_qa_rejects_free_tier(self, test_client):
        """Free tier user should get 403 on AI Q&A endpoint."""
        from app.auth import AuthContext, require_auth
        from app.main import app

        original = app.dependency_overrides.get(require_auth)

        async def free_tier_auth() -> AuthContext:
            return AuthContext(auth_type="jwt", user_id="free-user-id", tier="free")

        app.dependency_overrides[require_auth] = free_tier_auth
        try:
            resp = await test_client.post(
                "/api/v1/ai/ask",
                json={"symbol": "HDFCBANK.NS", "question": "Is this a good buy?"},
            )
            assert resp.status_code == 403
        finally:
            if original:
                app.dependency_overrides[require_auth] = original

    @pytest.mark.asyncio
    async def test_pro_tier_can_access_backtest(self, test_client):
        """Pro tier user should be able to access backtest (not get 403)."""
        with patch("app.tasks.backtest_tasks.run_backtest") as mock_task:
            mock_task.delay = MagicMock()
            resp = await test_client.post(
                "/api/v1/backtest/run",
                json={"symbol": "HDFCBANK.NS", "market_type": "stock", "days": 30},
            )
            # Should not be 403 (may be 201 or other)
            assert resp.status_code != 403


# ═══════════════════════════════════════════════════════════
# Task 1.14: JWT Revocation Tests
# ═══════════════════════════════════════════════════════════
class TestJWTRevocation:
    """Verify JWT revocation store works correctly."""

    def test_revoke_token_function_exists(self):
        """revoke_token function should be importable."""
        from app.auth import revoke_token, revoke_all_user_tokens, is_token_revoked

        assert callable(revoke_token)
        assert callable(revoke_all_user_tokens)
        assert callable(is_token_revoked)

    def test_is_token_revoked_returns_false_when_no_redis(self):
        """When redis_url is not a real string, should return False."""
        from app.auth import is_token_revoked

        with patch("app.auth.get_settings") as mock_settings:
            mock_settings.return_value.redis_url = None
            result = is_token_revoked("test-jti", "test-user", 12345.0)
            assert result is False

    def test_require_auth_checks_revocation(self):
        """require_auth should call is_token_revoked for JWT tokens."""
        source = inspect.getsource(__import__("app.auth", fromlist=["require_auth"]))
        assert "is_token_revoked" in source, "require_auth must check token revocation"

    def test_revocation_check_in_jwt_path(self):
        """The JWT auth path in require_auth must call is_token_revoked."""
        from app.auth import require_auth

        source = inspect.getsource(require_auth)
        assert "is_token_revoked" in source


# ═══════════════════════════════════════════════════════════
# Task 2.1: Constant-Time Comparison Tests (moved to Phase 1)
# ═══════════════════════════════════════════════════════════
class TestConstantTimeComparison:
    """Verify API key comparisons use hmac.compare_digest."""

    def test_auth_uses_constant_time_comparison(self):
        """auth.py require_auth must use hmac.compare_digest for API keys."""
        from app.auth import require_auth

        source = inspect.getsource(require_auth)
        assert "hmac.compare_digest" in source, \
            "require_auth must use hmac.compare_digest, not == for API keys"
        assert "api_key ==" not in source or "api_key == settings" not in source, \
            "require_auth should not use plain == for API key comparison"

    def test_require_api_key_uses_constant_time(self):
        """require_api_key must use hmac.compare_digest."""
        from app.auth import require_api_key

        source = inspect.getsource(require_api_key)
        assert "hmac.compare_digest" in source

    def test_websocket_uses_constant_time(self):
        """WebSocket API key comparison must use hmac.compare_digest."""
        import app.api.websocket as mod

        source = inspect.getsource(mod)
        assert "hmac.compare_digest" in source, \
            "WebSocket module must use hmac.compare_digest for API key comparison"


# ═══════════════════════════════════════════════════════════
# Task 1.10: SEBI Compliance Tests
# ═══════════════════════════════════════════════════════════
class TestSEBICompliance:
    """Verify SEBI compliance: disclaimers present, sharing requires auth."""

    def test_signal_list_response_has_disclaimer(self):
        """SignalListResponse schema must include a disclaimer field."""
        from app.schemas.signal import SignalListResponse

        schema = SignalListResponse.model_json_schema()
        assert "disclaimer" in schema["properties"], "SignalListResponse must have disclaimer field"

    @pytest.mark.asyncio
    async def test_signal_list_includes_disclaimer(self, test_client):
        """GET /signals response must include a disclaimer."""
        resp = await test_client.get("/api/v1/signals")
        assert resp.status_code == 200
        data = resp.json()
        assert "disclaimer" in data
        assert "not investment advice" in data["disclaimer"].lower()

    def test_sharing_requires_authentication(self):
        """Signal sharing endpoints must require get_current_user."""
        import app.api.sharing as mod

        source = inspect.getsource(mod)
        assert "get_current_user" in source, "Sharing must require JWT auth"

    @pytest.mark.asyncio
    async def test_disclaimer_text_mentions_sebi(self, test_client):
        """Disclaimer must mention SEBI registration status."""
        resp = await test_client.get("/api/v1/signals")
        data = resp.json()
        disclaimer = data.get("disclaimer", "")
        assert "sebi" in disclaimer.lower() or "investment adviser" in disclaimer.lower()


# ═══════════════════════════════════════════════════════════
# Task 1.9: Process Supervision Tests
# ═══════════════════════════════════════════════════════════
class TestProcessSupervision:
    """Verify supervisord configuration exists and is correct."""

    def test_supervisord_conf_exists(self):
        """supervisord.conf should exist in the backend directory."""
        import os

        conf_path = os.path.join(os.path.dirname(__file__), "..", "supervisord.conf")
        assert os.path.isfile(conf_path), "supervisord.conf must exist in backend/"

    def test_supervisord_conf_has_all_programs(self):
        """supervisord.conf must define web, celery-worker, celery-beat, and migrate."""
        import os

        conf_path = os.path.join(os.path.dirname(__file__), "..", "supervisord.conf")
        with open(conf_path) as f:
            content = f.read()

        required_programs = ["[program:web]", "[program:celery-worker]", "[program:celery-beat]", "[program:migrate]"]
        for prog in required_programs:
            assert prog in content, f"supervisord.conf must define {prog}"

    def test_supervisord_uses_single_worker(self):
        """Until Redis PubSub is implemented, --workers 1."""
        import os

        conf_path = os.path.join(os.path.dirname(__file__), "..", "supervisord.conf")
        with open(conf_path) as f:
            content = f.read()

        assert "--workers 1" in content, "Must use --workers 1 until Redis PubSub is implemented"

    def test_railway_toml_uses_supervisord(self):
        """railway.toml must use supervisord as the start command."""
        import os

        toml_path = os.path.join(os.path.dirname(__file__), "..", "..", "railway.toml")
        with open(toml_path) as f:
            content = f.read()

        assert "supervisord" in content, "railway.toml must use supervisord"


# ═══════════════════════════════════════════════════════════
# Task 1.2: No Fake Candlestick Data Tests
# ═══════════════════════════════════════════════════════════
class TestNoFakeCandlestickData:
    """Verify that fake OHLC data generation has been removed."""

    def test_no_math_random_in_signal_detail(self):
        """Signal detail page must NOT contain Math.random() for price data."""
        import os

        page_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "frontend", "src", "app", "signal", "[id]", "page.tsx"
        )
        with open(page_path) as f:
            content = f.read()

        assert "Math.random()" not in content, \
            "Signal detail page must not use Math.random() for price data"

    def test_no_candlestick_chart_import(self):
        """Signal detail page must NOT import CandlestickChart."""
        import os

        page_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "frontend", "src", "app", "signal", "[id]", "page.tsx"
        )
        with open(page_path) as f:
            content = f.read()

        assert "CandlestickChart" not in content, \
            "Signal detail page must not reference CandlestickChart component"

    def test_no_chart_view_toggle(self):
        """Signal detail page should not have candle/line chart toggle."""
        import os

        page_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "frontend", "src", "app", "signal", "[id]", "page.tsx"
        )
        with open(page_path) as f:
            content = f.read()

        assert "chartView" not in content, "chartView state should be removed"


# ═══════════════════════════════════════════════════════════
# Task 1.12: Sentry Integration Tests
# ═══════════════════════════════════════════════════════════
class TestSentryIntegration:
    """Verify Sentry is properly configured."""

    def test_sentry_sdk_in_requirements(self):
        """sentry-sdk must be in requirements.txt."""
        import os

        req_path = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
        with open(req_path) as f:
            content = f.read()

        assert "sentry-sdk" in content

    def test_sentry_init_in_main(self):
        """Sentry init must be in main.py lifespan."""
        import os

        main_path = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")
        with open(main_path) as f:
            content = f.read()

        assert "sentry_sdk.init" in content

    def test_sentry_dsn_in_config(self):
        """sentry_dsn should be a configurable setting."""
        from app.config import get_settings

        settings = get_settings()
        # sentry_dsn should exist as an attribute (may be empty string)
        assert hasattr(settings, "sentry_dsn")


# ═══════════════════════════════════════════════════════════
# Integration: Weight cascading tests
# ═══════════════════════════════════════════════════════════
class TestWeightCascading:
    """Verify weight changes don't break the scoring pipeline."""

    def test_scoring_produces_valid_range(self):
        """compute_final_confidence must produce values in [0, 100]."""
        from app.services.signal_gen.scorer import compute_final_confidence

        tech_data = {
            "rsi": {"value": 50, "signal": "neutral", "strength": 50},
            "macd": {"value": 0, "signal": "neutral", "strength": 50},
            "bollinger": {"value": 0, "signal": "neutral", "strength": 50},
            "volume": {"ratio": 1.0, "signal": "neutral", "strength": 50},
            "sma_cross": {"value": 0, "signal": "neutral", "strength": 50},
        }

        # Test with no sentiment
        conf, sig = compute_final_confidence(tech_data, None)
        assert 0 <= conf <= 100

        # Test with sentiment
        conf2, sig2 = compute_final_confidence(tech_data, {
            "sentiment_score": 50,
            "confidence_in_analysis": 80,
        })
        assert 0 <= conf2 <= 100

    def test_extreme_bearish_sentiment_less_impact(self):
        """With 85/15 weights, extreme bearish sentiment has less impact than before."""
        from app.services.signal_gen.scorer import compute_final_confidence

        bullish_tech = {
            "rsi": {"value": 30, "signal": "buy", "strength": 80},
            "macd": {"value": 2, "signal": "buy", "strength": 85},
            "bollinger": {"value": -2, "signal": "buy", "strength": 75},
            "volume": {"ratio": 2.0, "signal": "buy", "strength": 70},
            "sma_cross": {"value": 1, "signal": "buy", "strength": 90},
        }

        extremely_bearish = {
            "sentiment_score": 5,  # Extremely bearish
            "confidence_in_analysis": 95,
            "events": [],  # No chains
        }

        confidence, _ = compute_final_confidence(bullish_tech, extremely_bearish)
        # At 85/15: ~82*0.85 + 5*0.15 = 69.7 + 0.75 = 70.45
        # At old 60/40: ~82*0.60 + 5*0.40 = 49.2 + 2.0 = 51.2
        # New should be higher than old would have been
        assert confidence >= 65, \
            f"With 85/15 weights, bullish tech should dominate bearish sentiment (got {confidence})"

    def test_all_signal_types_achievable(self):
        """All 5 signal types should still be achievable."""
        from app.services.signal_gen.scorer import compute_final_confidence

        # Strong buy: all bullish
        tech_strong_buy = {k: {"signal": "buy", "strength": 95} for k in ["rsi", "macd", "bollinger", "volume", "sma_cross"]}
        conf, sig = compute_final_confidence(tech_strong_buy, {"sentiment_score": 90, "confidence_in_analysis": 90, "events": []})
        assert sig in ("STRONG_BUY", "BUY")

        # Strong sell: all bearish
        tech_strong_sell = {k: {"signal": "sell", "strength": 95} for k in ["rsi", "macd", "bollinger", "volume", "sma_cross"]}
        conf, sig = compute_final_confidence(tech_strong_sell, {"sentiment_score": 10, "confidence_in_analysis": 90, "events": []})
        assert sig in ("STRONG_SELL", "SELL")

        # Hold: neutral
        tech_neutral = {k: {"signal": "neutral", "strength": 50} for k in ["rsi", "macd", "bollinger", "volume", "sma_cross"]}
        conf, sig = compute_final_confidence(tech_neutral, {"sentiment_score": 50, "confidence_in_analysis": 50, "events": []})
        assert sig == "HOLD"
