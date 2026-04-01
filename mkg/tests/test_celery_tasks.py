# mkg/tests/test_celery_tasks.py
"""Tests for MKG Celery tasks (dummy implementations)."""

import pytest

from mkg.tasks.ingestion_tasks import batch_extract, fetch_news, process_article
from mkg.tasks.analysis_tasks import health_check, resolve_predictions, run_weight_decay
from mkg.tasks.scheduler import MKG_BEAT_SCHEDULE


class TestIngestionTasks:
    """Dummy news ingestion tasks."""

    def test_fetch_news_default_sources(self):
        result = fetch_news()
        assert result["status"] == "dummy"
        assert len(result["sources_checked"]) == 3
        assert result["articles_fetched"] == 0

    def test_fetch_news_custom_sources(self):
        result = fetch_news(sources=["bloomberg", "sec"])
        assert result["sources_checked"] == ["bloomberg", "sec"]

    def test_process_article(self):
        result = process_article("art-001")
        assert result["status"] == "dummy"
        assert result["article_id"] == "art-001"

    def test_batch_extract(self):
        result = batch_extract(["a1", "a2", "a3"])
        assert result["status"] == "dummy"
        assert result["count"] == 3

    def test_batch_extract_empty(self):
        result = batch_extract([])
        assert result["count"] == 0


class TestAnalysisTasks:
    """Dummy analysis tasks."""

    def test_run_weight_decay(self):
        result = run_weight_decay()
        assert result["status"] == "dummy"
        assert result["half_life_days"] == 90.0

    def test_run_weight_decay_custom(self):
        result = run_weight_decay(half_life_days=60.0)
        assert result["half_life_days"] == 60.0

    def test_resolve_predictions(self):
        result = resolve_predictions()
        assert result["status"] == "dummy"
        assert result["predictions_resolved"] == 0

    def test_health_check(self):
        result = health_check()
        assert result["status"] == "healthy"
        assert result["backend"] == "dummy"


class TestScheduler:
    """Beat schedule configuration."""

    def test_schedule_has_required_tasks(self):
        expected = [
            "mkg-fetch-news",
            "mkg-weight-decay",
            "mkg-resolve-predictions",
            "mkg-health-check",
        ]
        for task_name in expected:
            assert task_name in MKG_BEAT_SCHEDULE, f"Missing: {task_name}"

    def test_schedule_intervals_positive(self):
        for name, config in MKG_BEAT_SCHEDULE.items():
            schedule = config["schedule"]
            if isinstance(schedule, (int, float)):
                assert schedule > 0, f"{name} has non-positive interval"

    def test_all_tasks_have_task_name(self):
        for name, config in MKG_BEAT_SCHEDULE.items():
            assert "task" in config, f"{name} missing 'task' key"
