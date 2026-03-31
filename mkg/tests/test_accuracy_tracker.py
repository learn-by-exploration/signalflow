# mkg/tests/test_accuracy_tracker.py
"""Tests for AccuracyTracker — tracks prediction accuracy for calibration.

R-AT1 through R-AT5: Records predictions, outcomes, calculates accuracy
by entity, relation type, and time window.
"""

import pytest
from datetime import datetime, timezone, timedelta


class TestAccuracyTracker:

    @pytest.fixture
    def tracker(self):
        from mkg.domain.services.accuracy_tracker import AccuracyTracker
        return AccuracyTracker()

    def test_record_prediction(self, tracker):
        tracker.record_prediction(
            prediction_id="p1",
            entity_id="tsmc",
            predicted_impact=0.8,
            source="article-001",
        )
        assert len(tracker.predictions) == 1

    def test_record_outcome(self, tracker):
        tracker.record_prediction(
            prediction_id="p1",
            entity_id="tsmc",
            predicted_impact=0.8,
            source="article-001",
        )
        tracker.record_outcome(
            prediction_id="p1",
            actual_impact=0.75,
        )
        assert tracker.predictions["p1"]["actual_impact"] == 0.75

    def test_accuracy_for_single_prediction(self, tracker):
        tracker.record_prediction("p1", "tsmc", 0.8, "art-001")
        tracker.record_outcome("p1", 0.75)
        accuracy = tracker.get_accuracy()
        assert 0 <= accuracy <= 1.0
        # Error is |0.8 - 0.75| = 0.05, accuracy = 1 - 0.05 = 0.95
        assert abs(accuracy - 0.95) < 0.01

    def test_accuracy_by_entity(self, tracker):
        tracker.record_prediction("p1", "tsmc", 0.8, "art-001")
        tracker.record_prediction("p2", "nvidia", 0.6, "art-002")
        tracker.record_outcome("p1", 0.75)
        tracker.record_outcome("p2", 0.3)
        stats = tracker.get_accuracy_by_entity()
        assert "tsmc" in stats
        assert "nvidia" in stats
        assert stats["tsmc"] > stats["nvidia"]

    def test_accuracy_with_no_outcomes(self, tracker):
        tracker.record_prediction("p1", "tsmc", 0.8, "art-001")
        accuracy = tracker.get_accuracy()
        assert accuracy is None  # No outcomes to evaluate

    def test_get_stats_summary(self, tracker):
        tracker.record_prediction("p1", "tsmc", 0.8, "art-001")
        tracker.record_prediction("p2", "nvidia", 0.6, "art-002")
        tracker.record_outcome("p1", 0.75)
        tracker.record_outcome("p2", 0.55)
        stats = tracker.get_stats()
        assert stats["total_predictions"] == 2
        assert stats["resolved_predictions"] == 2
        assert "mean_accuracy" in stats

    def test_record_outcome_for_unknown_prediction(self, tracker):
        tracker.record_outcome("nonexistent", 0.5)
        # Should not raise, just skip
        assert len(tracker.predictions) == 0

    def test_multiple_predictions_accuracy(self, tracker):
        for i in range(10):
            tracker.record_prediction(f"p{i}", "tsmc", 0.7, f"art-{i}")
            tracker.record_outcome(f"p{i}", 0.7)
        accuracy = tracker.get_accuracy()
        assert abs(accuracy - 1.0) < 0.01  # Perfect predictions
