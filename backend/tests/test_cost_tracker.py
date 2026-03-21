"""Tests for AI engine cost tracker."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from app.services.ai_engine.cost_tracker import PRICING, CostTracker


@pytest.fixture
def tracker(tmp_path):
    """Create a CostTracker without Redis and temporary storage."""
    file_path = str(tmp_path / "test_costs.json")
    with patch("app.services.ai_engine.cost_tracker.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            monthly_ai_budget_usd=30.0,
            claude_model="claude-sonnet-4-20250514",
            redis_url="redis://nonexistent:6379/0",
        )
        with patch("app.services.ai_engine.cost_tracker.redis") as mock_redis_mod:
            mock_redis_mod.from_url.return_value.ping.side_effect = Exception("no redis")
            t = CostTracker(storage_path=file_path)
    return t


class TestCostCalculation:
    def test_calculate_cost_zero_tokens(self, tracker):
        assert tracker.calculate_cost(0, 0) == 0.0

    def test_calculate_cost_input_only(self, tracker):
        pricing = PRICING["claude-sonnet-4-20250514"]
        expected = (1000 / 1_000_000) * pricing["input"]
        assert abs(tracker.calculate_cost(1000, 0) - expected) < 0.00001

    def test_calculate_cost_output_only(self, tracker):
        pricing = PRICING["claude-sonnet-4-20250514"]
        expected = (1000 / 1_000_000) * pricing["output"]
        assert abs(tracker.calculate_cost(0, 1000) - expected) < 0.00001

    def test_calculate_cost_combined(self, tracker):
        pricing = PRICING["claude-sonnet-4-20250514"]
        expected = (500 / 1_000_000) * pricing["input"] + (200 / 1_000_000) * pricing["output"]
        assert abs(tracker.calculate_cost(500, 200) - round(expected, 6)) < 0.00001


class TestRecordUsage:
    def test_record_usage_returns_cost(self, tracker):
        cost = tracker.record_usage(100, 50, "sentiment", "BTCUSDT")
        assert cost > 0

    def test_record_usage_saves_to_file(self, tracker):
        tracker.record_usage(100, 50, "sentiment", "HDFCBANK")
        data = json.loads(tracker._storage_path.read_text())
        assert len(data["calls"]) == 1
        assert data["calls"][0]["task_type"] == "sentiment"
        assert data["calls"][0]["symbol"] == "HDFCBANK"

    def test_multiple_records_accumulate(self, tracker):
        tracker.record_usage(100, 50, "sentiment", "A")
        tracker.record_usage(200, 100, "reasoning", "B")
        data = json.loads(tracker._storage_path.read_text())
        assert len(data["calls"]) == 2
        month_key = tracker._get_month_key()
        assert data["monthly_totals"][month_key] > 0


class TestBudgetChecks:
    def test_budget_available_initially(self, tracker):
        assert tracker.is_budget_available() is True

    def test_remaining_budget_initially_full(self, tracker):
        assert tracker.get_remaining_budget() == 30.0

    def test_remaining_budget_decreases(self, tracker):
        tracker.record_usage(1_000_000, 1_000_000, "test")
        remaining = tracker.get_remaining_budget()
        assert remaining < 30.0

    def test_budget_exhaustion(self, tracker):
        """After spending > $30, budget should be exhausted."""
        # Sonnet: $3/1M input + $15/1M output
        # 2M output tokens = $30 exactly
        tracker.record_usage(0, 2_000_000, "test")
        assert tracker.is_budget_available() is False

    def test_get_monthly_spend(self, tracker):
        tracker.record_usage(500, 200, "sentiment", "X")
        spend = tracker.get_monthly_spend()
        assert spend > 0


class TestUsageSummary:
    def test_summary_structure(self, tracker):
        tracker.record_usage(100, 50, "sentiment", "BTC")
        summary = tracker.get_usage_summary()
        assert "month" in summary
        assert "total_calls" in summary
        assert "total_cost_usd" in summary
        assert "remaining_budget_usd" in summary
        assert "budget_pct_used" in summary
        assert "by_task_type" in summary

    def test_summary_by_task_type(self, tracker):
        tracker.record_usage(100, 50, "sentiment", "A")
        tracker.record_usage(200, 100, "reasoning", "B")
        tracker.record_usage(150, 75, "sentiment", "C")
        summary = tracker.get_usage_summary()
        assert "sentiment" in summary["by_task_type"]
        assert "reasoning" in summary["by_task_type"]
        assert summary["total_calls"] == 3


class TestCorruptedStorage:
    def test_corrupted_json_resets(self, tracker):
        """Corrupted JSON file should be handled gracefully."""
        tracker._storage_path.write_text("not valid json!!!")
        data = tracker._load_data()
        assert data == {"calls": [], "monthly_totals": {}}
