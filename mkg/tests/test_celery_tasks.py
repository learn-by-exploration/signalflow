# mkg/tests/test_celery_tasks.py
"""Tests for MKG Celery tasks (real implementations with SQLite storage)."""

import os
from unittest.mock import patch, MagicMock

import pytest

from mkg.tasks.ingestion_tasks import batch_extract, fetch_news, process_article
from mkg.tasks.analysis_tasks import health_check, resolve_predictions, run_weight_decay
from mkg.tasks.scheduler import MKG_BEAT_SCHEDULE


class TestIngestionTasks:
    """News ingestion tasks with real pipeline wiring."""

    @pytest.fixture(autouse=True)
    def _set_db_dir(self, tmp_path):
        old = os.environ.get("MKG_DB_DIR")
        os.environ["MKG_DB_DIR"] = str(tmp_path)
        yield
        if old is not None:
            os.environ["MKG_DB_DIR"] = old
        else:
            os.environ.pop("MKG_DB_DIR", None)

    @patch("mkg.tasks.ingestion_tasks._fetch_articles", return_value=[])
    def test_fetch_news_default_sources(self, mock_fetch):
        result = fetch_news()
        assert result["status"] == "completed"
        assert result["articles_fetched"] == 0

    @patch("mkg.tasks.ingestion_tasks._fetch_articles", return_value=[])
    def test_fetch_news_custom_sources(self, mock_fetch):
        result = fetch_news(sources=["bloomberg", "sec"])
        assert result["sources_checked"] == ["bloomberg", "sec"]
        assert result["articles_fetched"] == 0

    @patch("mkg.tasks.ingestion_tasks._fetch_articles", return_value=[
        {"title": "Test Article", "content": "NVIDIA announced new GPU chips.", "source": "rss"},
    ])
    def test_fetch_news_processes_articles(self, mock_fetch):
        result = fetch_news()
        assert result["status"] == "completed"
        assert result["articles_fetched"] == 1
        assert result["articles_processed"] >= 0

    def test_process_article_with_content(self):
        result = process_article(
            title="Test Article",
            content="TSMC fab disruption affects chip supply chain.",
            source="test",
        )
        assert result["status"] in ("completed", "error")

    def test_process_article_no_content(self):
        result = process_article(article_id="art-001")
        assert result["status"] == "skipped"

    def test_batch_extract_empty(self):
        result = batch_extract([])
        assert result["count"] == 0
        assert result["status"] == "completed"

    def test_batch_extract_none(self):
        result = batch_extract(None)
        assert result["count"] == 0

    def test_batch_extract_with_articles(self):
        articles = [
            {"title": "A1", "content": "Apple revenue beats estimates.", "source": "test"},
        ]
        result = batch_extract(articles)
        assert result["count"] == 1
        assert result["status"] == "completed"


class TestAnalysisTasks:
    """Analysis tasks with real wiring."""

    @pytest.fixture(autouse=True)
    def _set_db_dir(self, tmp_path):
        old = os.environ.get("MKG_DB_DIR")
        os.environ["MKG_DB_DIR"] = str(tmp_path)
        yield
        if old is not None:
            os.environ["MKG_DB_DIR"] = old
        else:
            os.environ.pop("MKG_DB_DIR", None)

    def test_run_weight_decay(self):
        result = run_weight_decay()
        assert result["status"] == "completed"
        assert result["half_life_days"] == 90.0

    def test_run_weight_decay_custom(self):
        result = run_weight_decay(half_life_days=60.0)
        assert result["half_life_days"] == 60.0

    def test_resolve_predictions(self):
        result = resolve_predictions()
        assert result["status"] == "completed"
        assert "total_predictions" in result

    def test_health_check(self):
        result = health_check()
        assert result["status"] == "healthy"
        assert "sqlite" in result


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
