# mkg/domain/services/accuracy_tracker.py
"""AccuracyTracker — tracks prediction accuracy for confidence calibration.

R-AT1 through R-AT5: Records predictions and their outcomes, calculates
accuracy overall, by entity, and provides stats for feedback loops.
"""

from typing import Any, Optional


class AccuracyTracker:
    """In-memory prediction accuracy tracker.

    Records predicted vs actual impact scores and computes accuracy metrics.
    Production use would persist to database; this version is in-memory for
    domain logic testing.
    """

    def __init__(self) -> None:
        self.predictions: dict[str, dict[str, Any]] = {}

    def record_prediction(
        self,
        prediction_id: str,
        entity_id: str,
        predicted_impact: float,
        source: str,
    ) -> None:
        """Record a new prediction.

        Args:
            prediction_id: Unique prediction identifier.
            entity_id: Entity the prediction is about.
            predicted_impact: Predicted impact score [0, 1].
            source: Source article or event that triggered the prediction.
        """
        self.predictions[prediction_id] = {
            "entity_id": entity_id,
            "predicted_impact": predicted_impact,
            "actual_impact": None,
            "source": source,
        }

    def record_outcome(
        self,
        prediction_id: str,
        actual_impact: float,
    ) -> None:
        """Record the actual outcome for a prediction.

        Args:
            prediction_id: Previously recorded prediction ID.
            actual_impact: The actual realized impact [0, 1].
        """
        if prediction_id not in self.predictions:
            return
        self.predictions[prediction_id]["actual_impact"] = actual_impact

    def get_accuracy(self) -> Optional[float]:
        """Calculate overall mean accuracy (1 - mean absolute error).

        Returns:
            Accuracy between 0 and 1, or None if no resolved predictions.
        """
        resolved = [
            p for p in self.predictions.values()
            if p["actual_impact"] is not None
        ]
        if not resolved:
            return None

        total_error = sum(
            abs(p["predicted_impact"] - p["actual_impact"])
            for p in resolved
        )
        mean_error = total_error / len(resolved)
        return max(0.0, 1.0 - mean_error)

    def get_accuracy_by_entity(self) -> dict[str, float]:
        """Calculate accuracy grouped by entity.

        Returns:
            Dict mapping entity_id to accuracy score.
        """
        by_entity: dict[str, list[float]] = {}
        for p in self.predictions.values():
            if p["actual_impact"] is None:
                continue
            eid = p["entity_id"]
            error = abs(p["predicted_impact"] - p["actual_impact"])
            by_entity.setdefault(eid, []).append(error)

        return {
            eid: max(0.0, 1.0 - (sum(errors) / len(errors)))
            for eid, errors in by_entity.items()
        }

    def get_stats(self) -> dict[str, Any]:
        """Get summary statistics.

        Returns:
            Dict with total_predictions, resolved_predictions, mean_accuracy.
        """
        resolved = [
            p for p in self.predictions.values()
            if p["actual_impact"] is not None
        ]
        accuracy = self.get_accuracy()
        return {
            "total_predictions": len(self.predictions),
            "resolved_predictions": len(resolved),
            "mean_accuracy": accuracy,
        }
