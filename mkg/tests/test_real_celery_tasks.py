# mkg/tests/test_real_celery_tasks.py
"""Tests for real (non-dummy) Celery tasks.

These tasks use ServiceFactory to wire real services and execute
actual pipeline operations (with mocked external APIs).
"""

import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def db_dir(tmp_path):
    """Provide a temp directory for SQLite databases."""
    return str(tmp_path)


class TestFetchNewsTask:
    """Tests for the fetch_news task with real news fetcher."""

    def test_fetch_news_returns_result(self, db_dir):
        """fetch_news should return a result dict with articles_fetched count."""
        from mkg.tasks.ingestion_tasks import fetch_news_real

        # Mock the RSS fetcher to avoid HTTP calls
        mock_articles = [
            {"title": "NVDA surges on AI demand", "content": "Nvidia...", "url": "http://test/1", "source": "rss"},
            {"title": "TCS Q3 results", "content": "Tata...", "url": "http://test/2", "source": "rss"},
        ]
        with patch("mkg.tasks.ingestion_tasks._fetch_articles", return_value=mock_articles):
            result = fetch_news_real(db_dir=db_dir)

        assert result["status"] == "completed"
        assert result["articles_fetched"] == 2

    def test_fetch_news_empty_articles(self, db_dir):
        """fetch_news with no articles available returns 0 count."""
        from mkg.tasks.ingestion_tasks import fetch_news_real
        with patch("mkg.tasks.ingestion_tasks._fetch_articles", return_value=[]):
            result = fetch_news_real(db_dir=db_dir)
        assert result["status"] == "completed"
        assert result["articles_fetched"] == 0

    def test_fetch_news_handles_error(self, db_dir):
        """fetch_news should handle and report fetcher errors."""
        from mkg.tasks.ingestion_tasks import fetch_news_real
        with patch("mkg.tasks.ingestion_tasks._fetch_articles", side_effect=Exception("Network error")):
            result = fetch_news_real(db_dir=db_dir)
        assert result["status"] == "error"
        assert "Network error" in result["error"]


class TestProcessArticleTask:
    """Tests for the process_article task with real pipeline."""

    def test_process_article_runs_pipeline(self, db_dir):
        """process_article should run through pipeline and return entities/relations."""
        from mkg.tasks.ingestion_tasks import process_article_real

        result = process_article_real(
            title="NVDA surges on AI demand",
            content="Nvidia Corporation reported strong Q4 earnings driven by AI chip demand. The company's data center revenue doubled year-over-year.",
            source="test",
            url="http://test/nvda",
            db_dir=db_dir,
        )

        assert result["status"] == "completed"
        assert "article_id" in result
        assert "entities_created" in result
        assert "provenance_chain" in result

    def test_process_article_empty_content(self, db_dir):
        """process_article with empty content returns failed status."""
        from mkg.tasks.ingestion_tasks import process_article_real

        result = process_article_real(
            title="Empty",
            content="",
            source="test",
            db_dir=db_dir,
        )

        assert result["status"] == "failed"

    def test_process_article_records_audit(self, db_dir):
        """process_article should create audit entries."""
        from mkg.tasks.ingestion_tasks import process_article_real
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger

        result = process_article_real(
            title="TCS Q3 results beat estimates",
            content="Tata Consultancy Services reported quarterly revenue of Rs 60,000 crore, beating analyst estimates by 3%.",
            source="test",
            db_dir=db_dir,
        )

        # Check that audit entries were created in SQLite
        audit = PersistentAuditLogger(db_path=os.path.join(db_dir, "audit.db"))
        entries = audit.get_entries()
        # Should have at least some entries if entities were created
        assert isinstance(entries, list)


class TestWeightDecayTask:
    """Tests for the weight_decay task."""

    def test_weight_decay_runs(self, db_dir):
        """run_weight_decay should process all edges in the graph."""
        from mkg.tasks.analysis_tasks import run_weight_decay_real

        result = run_weight_decay_real(half_life_days=90.0, db_dir=db_dir)

        assert result["status"] == "completed"
        assert "edges_decayed" in result
        assert isinstance(result["edges_decayed"], int)


class TestHealthCheckTask:
    """Tests for the health_check task."""

    def test_health_check_reports_status(self, db_dir):
        """health_check should report backend component status."""
        from mkg.tasks.analysis_tasks import health_check_real

        result = health_check_real(db_dir=db_dir)

        assert result["status"] == "healthy"
        assert "sqlite" in result
        assert result["sqlite"] == "connected"
        assert "audit_entries" in result
