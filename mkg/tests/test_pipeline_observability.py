# mkg/tests/test_pipeline_observability.py
"""Tests for PipelineObservability — metrics, health, and timing for the MKG pipeline.

R-OB1 through R-OB5: Stage timing, throughput counters, error rates,
health status, and metric export.
"""

import pytest
import time


class TestPipelineObservability:

    @pytest.fixture
    def observer(self):
        from mkg.domain.services.pipeline_observability import PipelineObservability
        return PipelineObservability()

    def test_record_stage_timing(self, observer):
        observer.record_stage("ingestion", duration_ms=150.0)
        metrics = observer.get_metrics()
        assert metrics["stages"]["ingestion"]["count"] == 1
        assert metrics["stages"]["ingestion"]["avg_ms"] == 150.0

    def test_record_multiple_timings_averages(self, observer):
        observer.record_stage("extraction", duration_ms=100.0)
        observer.record_stage("extraction", duration_ms=200.0)
        metrics = observer.get_metrics()
        assert metrics["stages"]["extraction"]["count"] == 2
        assert metrics["stages"]["extraction"]["avg_ms"] == 150.0

    def test_increment_counter(self, observer):
        observer.increment("articles_processed", 5)
        observer.increment("articles_processed", 3)
        metrics = observer.get_metrics()
        assert metrics["counters"]["articles_processed"] == 8

    def test_record_error(self, observer):
        observer.record_error("extraction", "JSONDecodeError")
        observer.record_error("extraction", "TimeoutError")
        metrics = observer.get_metrics()
        assert metrics["errors"]["extraction"] == 2

    def test_health_check_healthy(self, observer):
        observer.record_stage("ingestion", duration_ms=100.0)
        observer.increment("articles_processed", 1)
        health = observer.health_check()
        assert health["status"] == "healthy"

    def test_health_check_degraded_on_errors(self, observer):
        for _ in range(10):
            observer.record_error("extraction", "Error")
        health = observer.health_check()
        assert health["status"] in ("degraded", "unhealthy")

    def test_timer_context_manager(self, observer):
        with observer.timer("test_stage"):
            time.sleep(0.01)  # 10ms
        metrics = observer.get_metrics()
        assert metrics["stages"]["test_stage"]["count"] == 1
        assert metrics["stages"]["test_stage"]["avg_ms"] > 0

    def test_reset_metrics(self, observer):
        observer.record_stage("ingestion", duration_ms=100.0)
        observer.increment("articles_processed", 5)
        observer.reset()
        metrics = observer.get_metrics()
        assert len(metrics["stages"]) == 0
        assert len(metrics["counters"]) == 0

    def test_export_prometheus_format(self, observer):
        observer.record_stage("ingestion", duration_ms=100.0)
        observer.increment("articles_processed", 5)
        text = observer.export_prometheus()
        assert "mkg_stage_ingestion_count" in text
        assert "mkg_articles_processed" in text
