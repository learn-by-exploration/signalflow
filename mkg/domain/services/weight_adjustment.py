# mkg/domain/services/weight_adjustment.py
"""WeightAdjustmentService — Weighted Adjacency Network edge weight management.

R-WAN-1 through R-WAN-5: Temporal decay, confidence-weighted updates,
batch recalculation. Ensures edge weights stay current and meaningful.
"""

import math
from datetime import datetime, timezone
from typing import Any, Optional

from mkg.domain.interfaces.graph_storage import GraphStorage


class WeightAdjustmentService:
    """Manages edge weight decay and evidence-based updates.

    Attributes:
        weight_floor: Minimum weight an edge can decay to (never reaches 0).
    """

    def __init__(
        self,
        storage: GraphStorage,
        weight_floor: float = 0.01,
    ) -> None:
        if not 0.0 <= weight_floor < 1.0:
            raise ValueError(f"weight_floor must be in [0, 1), got {weight_floor}")
        self._storage = storage
        self.weight_floor = weight_floor

    def apply_time_decay(
        self,
        weight: float,
        days_old: float,
        half_life_days: float = 90.0,
    ) -> float:
        """Apply exponential time decay to a weight.

        Uses half-life formula: w * 2^(-t/half_life).
        Result is clamped to [weight_floor, 1.0].

        Args:
            weight: Current edge weight.
            days_old: Age of the evidence in days.
            half_life_days: Days until weight halves.

        Returns:
            Decayed weight, never below weight_floor.
        """
        if days_old <= 0:
            return weight
        decay_factor = math.pow(2, -days_old / half_life_days)
        decayed = weight * decay_factor
        return max(decayed, self.weight_floor)

    def get_edge_age_days(self, edge: dict[str, Any]) -> float:
        """Calculate edge age in days from created_at.

        Handles both datetime objects and ISO 8601 strings.
        Naive datetimes are assumed to be UTC.
        """
        created_str = edge.get("created_at")
        if created_str is None:
            return 0.0
        if isinstance(created_str, datetime):
            created = created_str
        elif isinstance(created_str, str):
            # Handle 'Z' suffix (common in JSON)
            normalized = created_str.replace("Z", "+00:00") if created_str.endswith("Z") else created_str
            created = datetime.fromisoformat(normalized)
        else:
            return 0.0
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - created
        return max(delta.total_seconds() / 86400.0, 0.0)

    async def update_edge_weight(
        self,
        edge_id: str,
        new_evidence_weight: float,
        evidence_confidence: float,
    ) -> Optional[dict[str, Any]]:
        """Update an edge weight using confidence-weighted blending.

        New weight = (old * (1 - alpha)) + (new * alpha)
        where alpha = evidence_confidence.

        Args:
            edge_id: Edge to update.
            new_evidence_weight: Weight from new evidence.
            evidence_confidence: Confidence in the new evidence [0, 1].

        Returns:
            Updated edge dict or None if edge not found.
        """
        edge = await self._storage.get_edge(edge_id)
        if edge is None:
            return None

        old_weight = edge.get("weight", 0.5)
        alpha = max(0.0, min(1.0, evidence_confidence))
        blended = (old_weight * (1 - alpha)) + (new_evidence_weight * alpha)
        clamped = max(0.0, min(1.0, blended))

        return await self._storage.update_edge(edge_id, {"weight": clamped})

    async def batch_decay(
        self,
        days_old: float,
        half_life_days: float = 90.0,
    ) -> dict[str, Any]:
        """Apply time decay to all edges in the graph.

        Args:
            days_old: Assumed age for all edges (or use per-edge age).
            half_life_days: Half-life parameter.

        Returns:
            Summary dict with edges_updated count.
        """
        all_edges = await self._storage.find_edges(limit=10000)
        updated = 0

        for edge in all_edges:
            age = days_old if days_old > 0 else self.get_edge_age_days(edge)
            old_weight = edge.get("weight", 0.5)
            new_weight = self.apply_time_decay(old_weight, age, half_life_days)

            if abs(new_weight - old_weight) > 1e-9:
                await self._storage.update_edge(edge["id"], {"weight": new_weight})
                updated += 1

        return {"edges_updated": updated}
