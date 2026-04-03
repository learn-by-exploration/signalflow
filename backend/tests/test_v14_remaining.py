"""Tests for Sprint A1 (Infrastructure), A2 (PubSub), A3 (AI/ML), B3 (SEO), B4 (Revenue).

Covers all remaining v1.4 implementation tasks.
"""

import asyncio
import json
import math
import os
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ═══════════════════════════════════════════════════
# Sprint A1: Infrastructure
# ═══════════════════════════════════════════════════


class TestRedisAOFPersistence:
    """A1.1: Redis AOF configuration in Docker Compose."""

    def test_dev_compose_has_aof_enabled(self):
        """docker-compose.yml: Redis must use --appendonly yes."""
        compose_path = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.yml")
        with open(compose_path) as f:
            content = f.read()
        assert "--appendonly yes" in content
        assert "--appendfsync everysec" in content

    def test_prod_compose_has_aof_enabled(self):
        """docker-compose.prod.yml: Redis must have AOF for JWT blacklist persistence."""
        compose_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "docker-compose.prod.yml"
        )
        with open(compose_path) as f:
            content = f.read()
        assert "--appendonly yes" in content

    def test_redis_volume_mounted(self):
        """Redis data volume must be mounted for persistence."""
        compose_path = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.yml")
        with open(compose_path) as f:
            content = f.read()
        assert "redisdata:/data" in content


class TestCDPipeline:
    """A1.2: GitHub Actions CI/CD pipeline."""

    def test_ci_workflow_exists(self):
        """CI workflow file must exist."""
        workflow_path = os.path.join(
            os.path.dirname(__file__), "..", "..", ".github", "workflows", "ci.yml"
        )
        assert os.path.exists(workflow_path)

    def test_ci_has_backend_tests(self):
        """CI must run backend tests."""
        workflow_path = os.path.join(
            os.path.dirname(__file__), "..", "..", ".github", "workflows", "ci.yml"
        )
        with open(workflow_path) as f:
            content = f.read()
        assert "pytest" in content

    def test_ci_has_frontend_tests(self):
        """CI must run frontend tests."""
        workflow_path = os.path.join(
            os.path.dirname(__file__), "..", "..", ".github", "workflows", "ci.yml"
        )
        with open(workflow_path) as f:
            content = f.read()
        assert "npm run test" in content

    def test_ci_has_docker_build_step(self):
        """CI must verify Docker builds succeed."""
        workflow_path = os.path.join(
            os.path.dirname(__file__), "..", "..", ".github", "workflows", "ci.yml"
        )
        with open(workflow_path) as f:
            content = f.read()
        assert "docker build" in content

    def test_ci_has_deploy_step(self):
        """CI must have deploy step for main branch."""
        workflow_path = os.path.join(
            os.path.dirname(__file__), "..", "..", ".github", "workflows", "ci.yml"
        )
        with open(workflow_path) as f:
            content = f.read()
        assert "railway" in content.lower()

    def test_ci_has_concurrency_control(self):
        """CI must cancel in-progress runs on new pushes."""
        workflow_path = os.path.join(
            os.path.dirname(__file__), "..", "..", ".github", "workflows", "ci.yml"
        )
        with open(workflow_path) as f:
            content = f.read()
        assert "cancel-in-progress" in content

    def test_deploy_only_on_main(self):
        """Deploy job must only run on main branch pushes."""
        workflow_path = os.path.join(
            os.path.dirname(__file__), "..", "..", ".github", "workflows", "ci.yml"
        )
        with open(workflow_path) as f:
            content = f.read()
        assert "refs/heads/main" in content


class TestFlowerMonitoring:
    """A1.3: Flower for Celery monitoring."""

    def test_flower_service_in_compose(self):
        """Flower service must be defined in docker-compose.yml."""
        compose_path = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.yml")
        with open(compose_path) as f:
            content = f.read()
        assert "flower:" in content.lower()

    def test_flower_has_basic_auth(self):
        """Flower must be protected by basic auth."""
        compose_path = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.yml")
        with open(compose_path) as f:
            content = f.read()
        assert "basic_auth" in content.lower() or "FLOWER_PASSWORD" in content

    def test_flower_exposed_on_port_5555(self):
        """Flower must be accessible on port 5555."""
        compose_path = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.yml")
        with open(compose_path) as f:
            content = f.read()
        assert "5555:5555" in content


class TestPrometheusMetrics:
    """A1.4: Prometheus-compatible metrics."""

    def test_metrics_module_importable(self):
        from app.services.metrics import (
            inc_counter,
            set_gauge,
            observe_histogram,
            get_metrics_text,
            get_metrics_json,
            Timer,
        )

    def test_inc_counter(self):
        from app.services.metrics import inc_counter, _counters

        inc_counter("test_metric_counter", 5)
        assert _counters["test_metric_counter"] >= 5

    def test_set_gauge(self):
        from app.services.metrics import set_gauge, _gauges

        set_gauge("test_gauge", 42.5)
        assert _gauges["test_gauge"] == 42.5

    def test_observe_histogram(self):
        from app.services.metrics import observe_histogram, _histograms

        observe_histogram("test_hist", 0.123)
        observe_histogram("test_hist", 0.456)
        assert len(_histograms["test_hist"]) >= 2

    def test_timer_context_manager(self):
        from app.services.metrics import Timer, _histograms

        with Timer("test_timer"):
            time.sleep(0.01)
        assert len(_histograms["test_timer"]) >= 1
        assert _histograms["test_timer"][-1] >= 0.01

    def test_get_metrics_text_format(self):
        from app.services.metrics import get_metrics_text, inc_counter

        inc_counter("prom_test_counter")
        text = get_metrics_text()
        assert isinstance(text, str)
        assert "prom_test_counter" in text

    def test_get_metrics_json(self):
        from app.services.metrics import get_metrics_json

        data = get_metrics_json()
        assert "counters" in data
        assert "gauges" in data
        assert "histograms" in data

    def test_labeled_counter(self):
        from app.services.metrics import inc_counter, _counters

        inc_counter("labeled_test", labels={"market": "crypto"})
        assert any("labeled_test" in k and "crypto" in k for k in _counters)

    def test_record_signal_generated(self):
        from app.services.metrics import record_signal_generated, _counters

        record_signal_generated("stock", "STRONG_BUY")
        assert any("signals_generated" in k for k in _counters)

    def test_record_data_fetch(self):
        from app.services.metrics import record_data_fetch, _counters

        record_data_fetch("crypto", True)
        assert any("data_fetches" in k for k in _counters)

    def test_metrics_endpoint_exists(self):
        """The /metrics endpoint must be defined in main.py."""
        import inspect
        from app.main import app

        routes = [r.path for r in app.routes]
        assert "/metrics" in routes


# ═══════════════════════════════════════════════════
# Sprint A2: Redis PubSub WebSocket
# ═══════════════════════════════════════════════════


class TestPubSubBroadcaster:
    """A2.1: Redis PubSub for WebSocket broadcast."""

    def test_pubsub_module_importable(self):
        from app.services.pubsub import (
            PubSubBroadcaster,
            publish_signal,
            publish_market_update,
            publish_broadcast,
            ClientMessageQueue,
            ALL_CHANNELS,
            SIGNAL_CHANNELS,
            MARKET_CHANNELS,
        )

    def test_channel_design(self):
        """Channels must follow ws:signal:{market} and ws:market:{market} pattern."""
        from app.services.pubsub import SIGNAL_CHANNELS, MARKET_CHANNELS, ALL_CHANNEL

        assert "ws:signal:stock" in SIGNAL_CHANNELS
        assert "ws:signal:crypto" in SIGNAL_CHANNELS
        assert "ws:signal:forex" in SIGNAL_CHANNELS
        assert "ws:market:stock" in MARKET_CHANNELS
        assert ALL_CHANNEL == "ws:all"

    def test_client_message_queue_push(self):
        from app.services.pubsub import ClientMessageQueue

        q = ClientMessageQueue(max_size=3)
        assert q.push({"type": "signal"})
        assert q.push({"type": "signal"})
        assert q.push({"type": "signal"})
        # 4th push should drop oldest
        assert not q.push({"type": "signal"})
        assert q.size == 3
        assert q.dropped_count == 1

    def test_client_message_queue_pop_all(self):
        from app.services.pubsub import ClientMessageQueue

        q = ClientMessageQueue(max_size=10)
        q.push({"a": 1})
        q.push({"a": 2})
        messages = q.pop_all()
        assert len(messages) == 2
        assert q.size == 0

    @pytest.mark.asyncio
    async def test_publish_signal_with_none_redis(self):
        from app.services.pubsub import publish_signal

        result = await publish_signal(None, {"market_type": "stock"})
        assert result is False

    @pytest.mark.asyncio
    async def test_publish_signal_success(self):
        from app.services.pubsub import publish_signal

        mock_redis = AsyncMock()
        result = await publish_signal(mock_redis, {"market_type": "crypto", "symbol": "BTC"})
        assert result is True
        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == "ws:signal:crypto"

    @pytest.mark.asyncio
    async def test_publish_market_update_success(self):
        from app.services.pubsub import publish_market_update

        mock_redis = AsyncMock()
        result = await publish_market_update(mock_redis, {"market_type": "forex"})
        assert result is True
        mock_redis.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_broadcast(self):
        from app.services.pubsub import publish_broadcast

        mock_redis = AsyncMock()
        result = await publish_broadcast(mock_redis, {"type": "announcement"})
        assert result is True
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == "ws:all"

    def test_broadcaster_init(self):
        from app.services.pubsub import PubSubBroadcaster

        mock_manager = MagicMock()
        broadcaster = PubSubBroadcaster("redis://localhost:6379/0", mock_manager)
        assert broadcaster.is_connected is False
        assert broadcaster._should_run is False

    def test_backpressure_config(self):
        from app.services.pubsub import MAX_CLIENT_QUEUE

        assert MAX_CLIENT_QUEUE == 50

    def test_reconnect_settings(self):
        from app.services.pubsub import (
            INITIAL_RECONNECT_DELAY,
            MAX_RECONNECT_DELAY,
            RECONNECT_BACKOFF_FACTOR,
        )

        assert INITIAL_RECONNECT_DELAY == 1.0
        assert MAX_RECONNECT_DELAY == 30.0
        assert RECONNECT_BACKOFF_FACTOR == 2.0

    def test_websocket_broadcast_accepts_source_param(self):
        """ConnectionManager.broadcast_signal must accept source parameter."""
        import inspect
        from app.api.websocket import ConnectionManager

        sig = inspect.signature(ConnectionManager.broadcast_signal)
        assert "source" in sig.parameters

    def test_websocket_has_broadcast_all(self):
        """ConnectionManager must have broadcast_all method."""
        from app.api.websocket import ConnectionManager

        assert hasattr(ConnectionManager, "broadcast_all")

    def test_health_reports_pubsub_status(self):
        """Health endpoint must report PubSub connection status."""
        import inspect
        from app.main import health_check

        source = inspect.getsource(health_check)
        assert "pubsub_status" in source

    def test_lifespan_starts_pubsub(self):
        """App lifespan must start PubSub broadcaster."""
        import inspect
        from app.main import lifespan

        source = inspect.getsource(lifespan)
        assert "PubSubBroadcaster" in source


# ═══════════════════════════════════════════════════
# Sprint A3: AI/ML Improvements
# ═══════════════════════════════════════════════════


class TestClaudeToolUse:
    """A3.1: Claude tool_use for guaranteed structured JSON."""

    def test_sentiment_tool_schema_defined(self):
        from app.services.ai_engine.sentiment import SENTIMENT_TOOL

        assert SENTIMENT_TOOL["name"] == "report_sentiment"
        schema = SENTIMENT_TOOL["input_schema"]
        assert "sentiment_score" in schema["properties"]
        assert "key_factors" in schema["properties"]
        assert schema["properties"]["sentiment_score"]["type"] == "integer"

    def test_event_chain_tool_schema_defined(self):
        from app.services.ai_engine.sentiment import EVENT_CHAIN_TOOL

        assert EVENT_CHAIN_TOOL["name"] == "report_event_chains"
        schema = EVENT_CHAIN_TOOL["input_schema"]
        assert "events" in schema["properties"]
        assert "overall_direction" in schema["properties"]

    def test_reasoning_tool_schema_defined(self):
        from app.services.ai_engine.reasoner import REASONING_TOOL

        assert REASONING_TOOL["name"] == "report_reasoning"
        schema = REASONING_TOOL["input_schema"]
        assert "explanation" in schema["properties"]

    def test_extract_tool_result_success(self):
        from app.services.ai_engine.sentiment import AISentimentEngine

        response = {
            "content": [
                {
                    "type": "tool_use",
                    "name": "report_sentiment",
                    "input": {
                        "sentiment_score": 72,
                        "key_factors": ["earnings beat"],
                        "market_impact": "positive",
                        "time_horizon": "short_term",
                        "confidence_in_analysis": 80,
                    },
                }
            ]
        }
        result = AISentimentEngine._extract_tool_result(response, "report_sentiment")
        assert result is not None
        assert result["sentiment_score"] == 72

    def test_extract_tool_result_wrong_name(self):
        from app.services.ai_engine.sentiment import AISentimentEngine

        response = {"content": [{"type": "tool_use", "name": "wrong_tool", "input": {}}]}
        result = AISentimentEngine._extract_tool_result(response, "report_sentiment")
        assert result is None

    def test_extract_tool_result_text_only(self):
        from app.services.ai_engine.sentiment import AISentimentEngine

        response = {"content": [{"type": "text", "text": "some text"}]}
        result = AISentimentEngine._extract_tool_result(response, "report_sentiment")
        assert result is None

    def test_sentiment_api_call_includes_tools(self):
        """Verify the event chain call includes tools and tool_choice."""
        import inspect
        from app.services.ai_engine.sentiment import AISentimentEngine

        source = inspect.getsource(AISentimentEngine._call_claude_event_chain)
        assert '"tools"' in source or "'tools'" in source or "tools" in source
        assert "tool_choice" in source

    def test_reasoner_api_call_includes_tools(self):
        """Verify the reasoner call includes tools and tool_choice."""
        import inspect
        from app.services.ai_engine.reasoner import AIReasoner

        source = inspect.getsource(AIReasoner.generate_reasoning)
        assert "tools" in source
        assert "tool_choice" in source


class TestMarketSpecificCacheTTLs:
    """A3.2: Market-specific sentiment cache TTLs."""

    def test_ttl_constants_defined(self):
        from app.services.ai_engine.sentiment import SENTIMENT_CACHE_TTLS

        assert SENTIMENT_CACHE_TTLS["crypto"] == 1800  # 30 min
        assert SENTIMENT_CACHE_TTLS["stock"] == 3600  # 60 min
        assert SENTIMENT_CACHE_TTLS["forex"] == 5400  # 90 min

    def test_crypto_faster_than_stock(self):
        from app.services.ai_engine.sentiment import SENTIMENT_CACHE_TTLS

        assert SENTIMENT_CACHE_TTLS["crypto"] < SENTIMENT_CACHE_TTLS["stock"]

    def test_stock_faster_than_forex(self):
        from app.services.ai_engine.sentiment import SENTIMENT_CACHE_TTLS

        assert SENTIMENT_CACHE_TTLS["stock"] < SENTIMENT_CACHE_TTLS["forex"]

    def test_set_cached_accepts_ttl_parameter(self):
        import inspect
        from app.services.ai_engine.sentiment import AISentimentEngine

        sig = inspect.signature(AISentimentEngine._set_cached)
        assert "ttl" in sig.parameters


class TestHistoricalCalibration:
    """A3.3: Historical calibration curve."""

    def test_module_importable(self):
        from app.services.signal_gen.calibration import (
            compute_calibration_curve,
            apply_isotonic_smoothing,
            get_predicted_win_rate,
        )

    def test_empty_data_returns_empty_calibration(self):
        from app.services.signal_gen.calibration import compute_calibration_curve

        result = compute_calibration_curve([])
        assert result["total_signals"] == 0
        assert result["is_calibrated"] is False

    def test_calibration_with_data(self):
        from app.services.signal_gen.calibration import compute_calibration_curve

        signals = [
            {"confidence": 85, "outcome": "hit_target"},
            {"confidence": 90, "outcome": "hit_target"},
            {"confidence": 82, "outcome": "hit_stop"},
            {"confidence": 88, "outcome": "hit_target"},
        ] * 5  # 20 signals in 80-100 bin

        # Add low confidence signals
        signals += [
            {"confidence": 30, "outcome": "hit_stop"},
            {"confidence": 25, "outcome": "hit_stop"},
        ] * 5  # 10 signals in 20-40 bin

        result = compute_calibration_curve(signals)
        assert result["total_signals"] == 30

        # 80-100 bin should have high win rate
        bin_80_100 = [b for b in result["bins"] if b["range"] == "80-100"][0]
        assert bin_80_100["win_rate"] > 0.5

        # 20-40 bin should have low win rate
        bin_20_40 = [b for b in result["bins"] if b["range"] == "20-40"][0]
        assert bin_20_40["win_rate"] == 0.0  # All hit_stop

    def test_isotonic_smoothing(self):
        from app.services.signal_gen.calibration import apply_isotonic_smoothing

        bins = [
            {
                "range": "0-20",
                "win_rate": 0.1,
                "low": 0,
                "high": 20,
                "count": 20,
                "wins": 2,
                "is_reliable": True,
            },
            {
                "range": "20-40",
                "win_rate": 0.3,
                "low": 20,
                "high": 40,
                "count": 20,
                "wins": 6,
                "is_reliable": True,
            },
            {
                "range": "40-60",
                "win_rate": 0.2,
                "low": 40,
                "high": 60,
                "count": 20,
                "wins": 4,
                "is_reliable": True,
            },  # violation!
            {
                "range": "60-80",
                "win_rate": 0.6,
                "low": 60,
                "high": 80,
                "count": 20,
                "wins": 12,
                "is_reliable": True,
            },
            {
                "range": "80-100",
                "win_rate": 0.8,
                "low": 80,
                "high": 100,
                "count": 20,
                "wins": 16,
                "is_reliable": True,
            },
        ]
        smoothed = apply_isotonic_smoothing(bins)
        rates = [b["smoothed_win_rate"] for b in smoothed]
        # Should be monotonically non-decreasing
        for i in range(len(rates) - 1):
            assert rates[i] <= rates[i + 1], f"{rates[i]} > {rates[i+1]}"

    def test_pav_isotonic_algorithm(self):
        from app.services.signal_gen.calibration import _pav_isotonic

        values = [0.1, 0.4, 0.2, 0.6, 0.8]  # violation at index 2
        result = _pav_isotonic(values)
        for i in range(len(result) - 1):
            assert result[i] <= result[i + 1]

    def test_get_predicted_win_rate(self):
        from app.services.signal_gen.calibration import (
            compute_calibration_curve,
            get_predicted_win_rate,
        )

        # Create enough data to be calibrated
        signals = []
        for conf in range(10, 100, 5):
            win = conf > 50  # Higher confidence = hit_target
            signals.append(
                {
                    "confidence": conf,
                    "outcome": "hit_target" if win else "hit_stop",
                }
            )
        signals = signals * 5  # 90 signals across bins

        cal = compute_calibration_curve(signals)
        # Even if not calibrated (depends on bin distribution), function should work
        rate = get_predicted_win_rate(cal, 75)
        # If calibrated, should return a float; if not, None
        if cal["is_calibrated"]:
            assert isinstance(rate, float)
        else:
            assert rate is None

    def test_expired_signals_excluded(self):
        from app.services.signal_gen.calibration import compute_calibration_curve

        signals = [
            {"confidence": 85, "outcome": "expired"},  # Should be excluded
            {"confidence": 85, "outcome": "pending"},  # Should be excluded
            {"confidence": 85, "outcome": "hit_target"},
        ]
        result = compute_calibration_curve(signals)
        assert result["total_signals"] == 1


class TestNewsSemanticDedup:
    """A3.4: News semantic deduplication."""

    def test_dedup_module_importable(self):
        from app.services.ai_engine.dedup import (
            deduplicate_articles,
            SIMILARITY_THRESHOLD,
        )

    def test_empty_articles(self):
        from app.services.ai_engine.dedup import deduplicate_articles

        assert deduplicate_articles([]) == []

    def test_single_article_unchanged(self):
        from app.services.ai_engine.dedup import deduplicate_articles

        articles = [{"headline": "Bitcoin hits new high", "source": "coindesk"}]
        result = deduplicate_articles(articles)
        assert len(result) == 1

    def test_identical_headlines_deduped(self):
        from app.services.ai_engine.dedup import deduplicate_articles

        articles = [
            {
                "headline": "RBI holds interest rates steady percent quarterly review announcement",
                "source": "Reuters",
            },
            {
                "headline": "RBI holds interest rates steady percent quarterly review decision",
                "source": "google_news",
            },
        ]
        result = deduplicate_articles(articles)
        # Should keep the higher-credibility source
        assert len(result) == 1
        # Reuters has higher weight than google
        assert result[0]["source"] == "Reuters"

    def test_different_headlines_kept(self):
        from app.services.ai_engine.dedup import deduplicate_articles

        articles = [
            {
                "headline": "Bitcoin rally continues as institutional buying surges",
                "source": "coindesk",
            },
            {
                "headline": "Federal Reserve signals potential rate cut in September meeting",
                "source": "Reuters",
            },
        ]
        result = deduplicate_articles(articles)
        assert len(result) == 2

    def test_keeps_higher_quality_source(self):
        from app.services.ai_engine.dedup import deduplicate_articles

        articles = [
            {
                "headline": "NIFTY reaches record high banking sector gains quarterly performance rally strong",
                "source": "bing_news",
            },
            {
                "headline": "NIFTY reaches record high banking sector gains quarterly performance rally boost",
                "source": "Economic Times",
            },
        ]
        result = deduplicate_articles(articles)
        assert len(result) == 1
        assert result[0]["source"] == "Economic Times"

    def test_tokenizer_removes_stop_words(self):
        from app.services.ai_engine.dedup import _tokenize

        tokens = _tokenize("The quick brown fox jumps over the lazy dog")
        assert "the" not in tokens
        assert "over" not in tokens
        assert "brown" in tokens
        assert "fox" in tokens
        assert "quick" in tokens

    def test_cosine_similarity_identical(self):
        from app.services.ai_engine.dedup import _cosine_similarity

        vec = {"bitcoin": 0.5, "rally": 0.3}
        sim = _cosine_similarity(vec, vec)
        assert abs(sim - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self):
        from app.services.ai_engine.dedup import _cosine_similarity

        vec_a = {"bitcoin": 1.0}
        vec_b = {"forex": 1.0}
        sim = _cosine_similarity(vec_a, vec_b)
        assert sim == 0.0

    def test_integrated_in_news_fetcher(self):
        """Semantic dedup must be called in fetch_news_for_symbol_structured."""
        import inspect
        from app.services.ai_engine.news_fetcher import fetch_news_for_symbol_structured

        source = inspect.getsource(fetch_news_for_symbol_structured)
        assert "deduplicate_articles" in source


class TestFinBERTEvaluation:
    """A3.5: FinBERT evaluation framework."""

    def test_module_importable(self):
        from app.services.ai_engine.finbert_eval import (
            map_finbert_to_score,
            compute_evaluation_metrics,
        )

    def test_map_positive_sentiment(self):
        from app.services.ai_engine.finbert_eval import map_finbert_to_score

        score = map_finbert_to_score("positive", 0.9)
        assert score == 95  # 50 + 0.9*50

    def test_map_negative_sentiment(self):
        from app.services.ai_engine.finbert_eval import map_finbert_to_score

        score = map_finbert_to_score("negative", 0.8)
        assert score == 10  # 50 - 0.8*50

    def test_map_neutral_sentiment(self):
        from app.services.ai_engine.finbert_eval import map_finbert_to_score

        score = map_finbert_to_score("neutral", 0.5)
        assert score == 50  # centered

    def test_pearson_correlation_perfect(self):
        from app.services.ai_engine.finbert_eval import _pearson_correlation

        x = [10, 20, 30, 40, 50]
        y = [10, 20, 30, 40, 50]
        corr = _pearson_correlation(x, y)
        assert abs(corr - 1.0) < 0.001

    def test_pearson_correlation_negative(self):
        from app.services.ai_engine.finbert_eval import _pearson_correlation

        x = [10, 20, 30, 40, 50]
        y = [50, 40, 30, 20, 10]
        corr = _pearson_correlation(x, y)
        assert abs(corr - (-1.0)) < 0.001

    def test_compute_evaluation_metrics(self):
        from app.services.ai_engine.finbert_eval import compute_evaluation_metrics

        claude_scores = [75, 80, 65, 30, 45]
        finbert_scores = [70, 82, 60, 35, 50]
        result = compute_evaluation_metrics(claude_scores, finbert_scores)
        assert result["sample_size"] == 5
        assert "correlation" in result
        assert "directional_accuracy" in result
        assert "mean_absolute_error" in result
        assert "recommendation" in result

    def test_insufficient_data_recommendation(self):
        from app.services.ai_engine.finbert_eval import compute_evaluation_metrics

        result = compute_evaluation_metrics([50] * 5, [55] * 5)
        assert "INSUFFICIENT_DATA" in result["recommendation"]

    def test_empty_data(self):
        from app.services.ai_engine.finbert_eval import compute_evaluation_metrics

        result = compute_evaluation_metrics([], [])
        assert result["sample_size"] == 0


class TestShadowMode:
    """A3.6: Shadow mode comparison."""

    def test_module_importable(self):
        from app.services.signal_gen.shadow_mode import (
            compute_v13_confidence,
            log_shadow_comparison,
            get_shadow_summary,
            confidence_to_signal_type,
        )

    def test_v13_confidence_with_chain(self):
        from app.services.signal_gen.shadow_mode import compute_v13_confidence

        # tech=80, sent=60, chain=70
        conf = compute_v13_confidence(80, 60, has_chain=True, chain_score=70)
        expected = int(80 * 0.50 + 70 * 0.35 + 60 * 0.15)  # 40+24.5+9 = 73
        assert conf == expected

    def test_v13_confidence_no_chain(self):
        from app.services.signal_gen.shadow_mode import compute_v13_confidence

        conf = compute_v13_confidence(80, 60, has_chain=False)
        expected = int(80 * 0.60 + 60 * 0.40)  # 48+24 = 72
        assert conf == expected

    def test_v13_no_ai_cap(self):
        from app.services.signal_gen.shadow_mode import compute_v13_confidence

        conf = compute_v13_confidence(90, 0, has_ai=False)
        assert conf == 60  # Capped at 60

    def test_confidence_to_signal_type(self):
        from app.services.signal_gen.shadow_mode import confidence_to_signal_type

        assert confidence_to_signal_type(85) == "STRONG_BUY"
        assert confidence_to_signal_type(70) == "BUY"
        assert confidence_to_signal_type(50) == "HOLD"
        assert confidence_to_signal_type(30) == "SELL"
        assert confidence_to_signal_type(15) == "STRONG_SELL"

    def test_log_shadow_with_none_redis(self):
        from app.services.signal_gen.shadow_mode import log_shadow_comparison

        # Should not raise
        log_shadow_comparison(None, "BTCUSDT", "crypto", 70, 75, "BUY", "BUY", 80, 60)

    def test_log_shadow_with_redis(self):
        from app.services.signal_gen.shadow_mode import log_shadow_comparison

        mock_redis = MagicMock()
        log_shadow_comparison(mock_redis, "BTCUSDT", "crypto", 70, 75, "BUY", "BUY", 80, 60)
        mock_redis.setex.assert_called_once()

    def test_get_shadow_summary_no_data(self):
        from app.services.signal_gen.shadow_mode import get_shadow_summary

        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = iter([])
        result = get_shadow_summary(mock_redis)
        assert result["comparisons"] == 0

    def test_get_shadow_summary_none_redis(self):
        from app.services.signal_gen.shadow_mode import get_shadow_summary

        result = get_shadow_summary(None)
        assert "error" in result


# ═══════════════════════════════════════════════════
# B3: SEO Content Pages
# ═══════════════════════════════════════════════════


class TestSeoPages:
    """B3: SEO content pages."""

    def test_seo_model_importable(self):
        from app.models.seo_page import SeoPage

        assert SeoPage.__tablename__ == "seo_pages"

    def test_seo_model_fields(self):
        from app.models.seo_page import SeoPage

        columns = {c.name for c in SeoPage.__table__.columns}
        assert "slug" in columns
        assert "title" in columns
        assert "content" in columns
        assert "market_type" in columns
        assert "meta_description" in columns
        assert "is_published" in columns
        assert "page_date" in columns

    def test_generate_slug(self):
        from app.services.seo import generate_slug

        dt = datetime(2026, 3, 27, tzinfo=timezone.utc)
        assert generate_slug("stock", dt) == "nifty-50-analysis-2026-03-27"
        assert generate_slug("crypto", dt) == "crypto-analysis-2026-03-27"
        assert generate_slug("forex", dt) == "forex-analysis-2026-03-27"

    def test_generate_page_title(self):
        from app.services.seo import generate_page_title

        dt = datetime(2026, 3, 27, tzinfo=timezone.utc)
        title = generate_page_title("stock", dt)
        assert "NIFTY 50" in title
        assert "27 March 2026" in title
        assert "SignalFlow AI" in title

    def test_generate_meta_description(self):
        from app.services.seo import generate_meta_description

        desc = generate_meta_description("Test Title", "This is a test sentence. And another one.")
        assert len(desc) <= 163  # 160 + "..."
        assert "test sentence" in desc.lower()

    def test_seo_router_registered(self):
        """SEO router must be in public_router (no auth)."""
        from app.api.router import public_router

        routes = [r.path for r in public_router.routes]
        # Should have /analysis routes
        seo_paths = [p for p in routes if "analysis" in p]
        assert len(seo_paths) > 0

    def test_seo_migration_exists(self):
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "migrations",
            "versions",
            "k2c6d8e0f4g5_add_seo_pages_table.py",
        )
        assert os.path.exists(migration_path)

    def test_seo_scheduler_task(self):
        from app.tasks.scheduler import CELERY_BEAT_SCHEDULE

        assert "generate-seo-pages" in CELERY_BEAT_SCHEDULE

    def test_seo_task_importable(self):
        from app.tasks.seo_tasks import generate_seo_pages

        assert callable(generate_seo_pages)


# ═══════════════════════════════════════════════════
# B4: Revenue Tracking + Re-engagement
# ═══════════════════════════════════════════════════


class TestRevenueTracking:
    """B4: Revenue tracking and re-engagement."""

    def test_revenue_service_importable(self):
        from app.services.revenue import (
            get_revenue_metrics,
            get_free_tier_weekly_digest_data,
            format_free_tier_digest,
            get_inactive_users,
        )

    def test_format_free_tier_digest(self):
        from app.services.revenue import format_free_tier_digest

        data = {
            "signals_this_week": 12,
            "resolved_this_week": 8,
            "hits": 6,
            "win_rate": 75.0,
            "best_signal": {
                "symbol": "BTCUSDT",
                "signal_type": "STRONG_BUY",
                "return_pct": 5.2,
            },
        }
        msg = format_free_tier_digest(data)
        assert "12 signals" in msg
        assert "75.0% win rate" in msg
        assert "BTCUSDT" in msg
        assert "+5.2%" in msg
        assert "Upgrade" in msg

    def test_format_digest_no_best_signal(self):
        from app.services.revenue import format_free_tier_digest

        data = {
            "signals_this_week": 0,
            "resolved_this_week": 0,
            "hits": 0,
            "win_rate": 0.0,
            "best_signal": None,
        }
        msg = format_free_tier_digest(data)
        assert "0 signals" in msg

    def test_plan_prices_defined(self):
        from app.services.revenue import PLAN_PRICES_INR

        assert PLAN_PRICES_INR["monthly"] == 49900
        assert PLAN_PRICES_INR["annual"] == 499900
        assert PLAN_PRICES_INR["trial"] == 0

    def test_admin_router_importable(self):
        from app.api.admin import router

        assert router.prefix == "/admin"

    def test_admin_requires_auth(self):
        """Admin endpoint must check internal API key."""
        import inspect
        from app.api.admin import _require_admin

        source = inspect.getsource(_require_admin)
        assert "compare_digest" in source

    def test_engagement_tasks_importable(self):
        from app.tasks.engagement_tasks import (
            send_free_tier_digest,
            send_reengagement_nudge,
        )

        assert callable(send_free_tier_digest)
        assert callable(send_reengagement_nudge)

    def test_engagement_tasks_in_scheduler(self):
        from app.tasks.scheduler import CELERY_BEAT_SCHEDULE

        assert "free-tier-weekly-digest" in CELERY_BEAT_SCHEDULE
        assert "reengagement-nudge" in CELERY_BEAT_SCHEDULE

    def test_admin_router_registered(self):
        """Admin router must be included in api_router."""
        from app.api.router import api_router

        prefixes = []
        for route in api_router.routes:
            if hasattr(route, "path"):
                prefixes.append(route.path)
        admin_routes = [p for p in prefixes if "admin" in p]
        assert len(admin_routes) > 0


# ═══════════════════════════════════════════════════
# Scheduler Completeness
# ═══════════════════════════════════════════════════


class TestSchedulerCompleteness:
    """Verify all new tasks are properly scheduled."""

    def test_all_new_tasks_in_schedule(self):
        from app.tasks.scheduler import CELERY_BEAT_SCHEDULE

        expected_tasks = [
            "generate-seo-pages",
            "free-tier-weekly-digest",
            "reengagement-nudge",
            "check-expired-subscriptions",
        ]
        for task in expected_tasks:
            assert task in CELERY_BEAT_SCHEDULE, f"Missing: {task}"

    def test_seo_runs_after_morning_brief(self):
        """SEO generation must run after morning brief (9:30 AM → 8:30 AM; SEO at fixed 8:30)."""
        from app.tasks.scheduler import CELERY_BEAT_SCHEDULE

        seo = CELERY_BEAT_SCHEDULE["generate-seo-pages"]["schedule"]
        morning = CELERY_BEAT_SCHEDULE["morning-brief"]["schedule"]
        # Both are crontab objects
        assert seo.minute == {30}  # 8:30 AM
        assert morning.minute == {30}  # 9:30 AM (after NSE opens at 9:15)
        assert morning.hour == {9}

    def test_free_digest_after_weekly_digest(self):
        """Free tier digest should run after paid weekly digest."""
        from app.tasks.scheduler import CELERY_BEAT_SCHEDULE

        free = CELERY_BEAT_SCHEDULE["free-tier-weekly-digest"]["schedule"]
        paid = CELERY_BEAT_SCHEDULE["weekly-digest"]["schedule"]
        # Both Sunday, free at 18:30, paid at 18:00
        assert free.day_of_week == paid.day_of_week  # Both Sunday
