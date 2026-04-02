# mkg/domain/services/contradiction_detector.py
"""ContradictionDetector — detect and resolve conflicting signals.

C1: When multiple propagation paths produce opposing directions for the
same entity, flag as contradictions and suggest resolution strategies.
"""

from collections import defaultdict
from typing import Any


class ContradictionDetector:
    """Detects conflicting signals about the same entity."""

    def detect(self, signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Find contradictions: same entity with opposing directions.

        Args:
            signals: List of propagation results, each with entity_id,
                     impact, direction, and source.

        Returns:
            List of contradiction dicts with entity_id, conflicting_signals,
            and suggested resolution strategy.
        """
        if not signals:
            return []

        # Group by entity_id
        by_entity: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for signal in signals:
            eid = signal.get("entity_id", "")
            if eid:
                by_entity[eid].append(signal)

        contradictions: list[dict[str, Any]] = []

        for entity_id, entity_signals in by_entity.items():
            directions = {s.get("direction", "positive") for s in entity_signals}
            if "positive" in directions and "negative" in directions:
                resolution = self._suggest_resolution(entity_signals)
                contradictions.append({
                    "entity_id": entity_id,
                    "conflicting_signals": entity_signals,
                    "resolution": resolution,
                })

        return contradictions

    def resolve(self, signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Resolve contradictions by picking the most credible signal per entity.

        For entities with no contradiction, passes through unchanged.
        For contradicting entities, picks the signal with higher credibility
        (falls back to higher impact).

        Args:
            signals: Full list of signals.

        Returns:
            Deduplicated list with one signal per entity.
        """
        by_entity: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for signal in signals:
            eid = signal.get("entity_id", "")
            if eid:
                by_entity[eid].append(signal)

        resolved: list[dict[str, Any]] = []
        for entity_id, entity_signals in by_entity.items():
            directions = {s.get("direction", "positive") for s in entity_signals}
            if "positive" in directions and "negative" in directions:
                # Pick highest credibility, then highest impact
                winner = max(
                    entity_signals,
                    key=lambda s: (s.get("credibility", 0.5), s.get("impact", 0.0)),
                )
                resolved.append(winner)
            else:
                # No contradiction — pick highest impact
                resolved.append(max(entity_signals, key=lambda s: s.get("impact", 0.0)))

        return resolved

    def _suggest_resolution(self, signals: list[dict[str, Any]]) -> str:
        """Suggest a resolution strategy based on signal properties."""
        credibilities = [s.get("credibility", 0.0) for s in signals]
        has_explicit_credibility = any(c > 0 for c in credibilities)

        if has_explicit_credibility:
            max_cred = max(credibilities)
            min_cred = min(credibilities)
            if max_cred - min_cred > 0.3:
                return "higher_credibility"

        impacts = [s.get("impact", 0.0) for s in signals]
        max_impact = max(impacts)
        min_impact = min(impacts)
        if max_impact - min_impact > 0.3:
            return "higher_impact"

        return "flag_for_review"
