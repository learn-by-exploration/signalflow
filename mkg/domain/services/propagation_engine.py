# mkg/domain/services/propagation_engine.py
"""PropagationEngine — BFS impact propagation through the knowledge graph.

R-PE1 through R-PE5: When a trigger event hits an entity, propagate the
impact through connected edges with weight-based decay, depth limiting,
and cycle prevention.
"""

from collections import deque
from typing import Any, Optional
import logging

from mkg.domain.interfaces.graph_storage import GraphStorage

logger = logging.getLogger(__name__)


class PropagationEngine:
    """BFS-based impact propagation through the knowledge graph.

    Given a trigger entity and impact score, propagates impact to connected
    entities. Impact decays by edge weight at each hop.
    """

    def __init__(self, storage: GraphStorage) -> None:
        self._storage = storage

    async def propagate(
        self,
        trigger_entity_id: str,
        impact_score: float,
        max_depth: int = 6,
        min_impact: float = 0.01,
        relation_types: Optional[list[str]] = None,
        as_of: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Propagate impact from a trigger entity through the graph via BFS.

        Impact at each hop = parent_impact * edge_weight * edge_confidence.
        Direction at each hop: positive * positive = positive,
                               positive * negative = negative,
                               negative * negative = positive.
        Stops when max_depth reached, impact below threshold, or no more neighbors.

        Args:
            trigger_entity_id: Entity where the event originated.
            impact_score: Initial impact magnitude [0, 1].
            max_depth: Maximum hops from trigger (default 6 for financial supply chains).
            min_impact: Minimum impact to continue propagation.
            relation_types: Optional filter by edge types.
            as_of: Optional ISO timestamp — only follow edges valid at this time.

        Returns:
            List of affected entities sorted by impact (descending).
            Each item has: entity_id, impact, depth, path, direction.
        """
        visited: set[str] = {trigger_entity_id}
        results: list[dict[str, Any]] = []

        # BFS queue: (entity_id, current_impact, depth, path, direction)
        queue: deque[tuple[str, float, int, list[str], str]] = deque()

        # Helper: get outgoing edges from an entity (optionally time-filtered)
        async def _outgoing_edges(eid: str) -> list[dict[str, Any]]:
            try:
                if as_of and hasattr(self._storage, "find_edges_at_time"):
                    edges = await self._storage.find_edges_at_time(
                        as_of=as_of, source_id=eid, limit=1000,
                    )
                else:
                    edges = await self._storage.find_edges(source_id=eid, limit=1000)
            except Exception:
                logger.exception("Failed to fetch edges for entity %s", eid)
                return []
            if relation_types:
                edges = [e for e in edges if e.get("relation_type") in relation_types]
            return edges

        def _combine_direction(parent_dir: str, edge_dir: str) -> str:
            """Combine parent and edge directions: neg×neg=pos, pos×neg=neg."""
            if parent_dir == edge_dir:
                return "positive"
            return "negative"

        # Seed with outgoing edges from trigger
        for edge in await _outgoing_edges(trigger_entity_id):
            neighbor_id = edge["target_id"]
            edge_weight = edge.get("weight", 0.5)
            edge_confidence = edge.get("confidence", 1.0)
            edge_direction = edge.get("direction", "positive")
            hop_impact = impact_score * edge_weight * edge_confidence
            if hop_impact >= min_impact and neighbor_id not in visited:
                queue.append((neighbor_id, hop_impact, 1, [trigger_entity_id, neighbor_id], edge_direction))
                visited.add(neighbor_id)

        while queue:
            entity_id, current_impact, depth, path, current_direction = queue.popleft()

            results.append({
                "entity_id": entity_id,
                "impact": current_impact,
                "depth": depth,
                "path": path,
                "direction": current_direction,
            })

            if depth >= max_depth:
                continue

            for edge in await _outgoing_edges(entity_id):
                neighbor_id = edge["target_id"]
                edge_weight = edge.get("weight", 0.5)
                edge_confidence = edge.get("confidence", 1.0)
                edge_direction = edge.get("direction", "positive")
                hop_impact = current_impact * edge_weight * edge_confidence
                combined_direction = _combine_direction(current_direction, edge_direction)
                if hop_impact >= min_impact and neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((
                        neighbor_id,
                        hop_impact,
                        depth + 1,
                        path + [neighbor_id],
                        combined_direction,
                    ))

        # Sort by impact descending
        results.sort(key=lambda r: r["impact"], reverse=True)
        return results

    async def propagate_multi(
        self,
        triggers: list[dict[str, Any]],
        max_depth: int = 6,
        min_impact: float = 0.01,
        relation_types: Optional[list[str]] = None,
        as_of: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Propagate from multiple trigger entities simultaneously.

        Runs propagation from each trigger, then merges results:
        - Same entity reached from multiple triggers: impacts are combined (max)
        - Each result includes trigger_sources tracking

        Args:
            triggers: List of dicts with 'entity_id' and 'impact_score'.
            max_depth: Maximum hops per trigger.
            min_impact: Minimum impact threshold.
            relation_types: Optional edge type filter.
            as_of: Optional temporal scope.

        Returns:
            Merged results sorted by impact (descending).
        """
        # Collect all results with trigger attribution
        entity_results: dict[str, dict[str, Any]] = {}

        for trigger in triggers:
            entity_id = trigger["entity_id"]
            impact_score = trigger["impact_score"]

            results = await self.propagate(
                trigger_entity_id=entity_id,
                impact_score=impact_score,
                max_depth=max_depth,
                min_impact=min_impact,
                relation_types=relation_types,
                as_of=as_of,
            )

            for r in results:
                eid = r["entity_id"]
                if eid in entity_results:
                    existing = entity_results[eid]
                    # Combine: use max impact, merge trigger sources
                    if r["impact"] > existing["impact"]:
                        existing["impact"] = r["impact"]
                        existing["depth"] = r["depth"]
                        existing["path"] = r["path"]
                        existing["direction"] = r["direction"]
                    existing["trigger_sources"].append(entity_id)
                else:
                    entity_results[eid] = {
                        **r,
                        "trigger_sources": [entity_id],
                    }

        merged = list(entity_results.values())
        merged.sort(key=lambda r: r["impact"], reverse=True)
        return merged

    @staticmethod
    def aggregate_confidence(results: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate confidence metrics across propagation results.

        Args:
            results: List of propagation result dicts.

        Returns:
            Dict with mean_impact, max_impact, entity_count,
            weighted_confidence, positive_count, negative_count.
        """
        if not results:
            return {
                "mean_impact": 0.0,
                "max_impact": 0.0,
                "entity_count": 0,
                "weighted_confidence": 0.0,
                "positive_count": 0,
                "negative_count": 0,
            }

        impacts = [r.get("impact", 0.0) for r in results]
        total_impact = sum(impacts)
        count = len(results)

        positive_count = sum(1 for r in results if r.get("direction", "positive") == "positive")
        negative_count = count - positive_count

        # Weighted confidence: impact-weighted average of (1/depth) as proxy
        weighted_sum = 0.0
        for r in results:
            depth = max(r.get("depth", 1), 1)
            weighted_sum += r.get("impact", 0.0) * (1.0 / depth)

        weighted_confidence = weighted_sum / total_impact if total_impact > 0 else 0.0

        return {
            "mean_impact": total_impact / count,
            "max_impact": max(impacts),
            "entity_count": count,
            "weighted_confidence": weighted_confidence,
            "positive_count": positive_count,
            "negative_count": negative_count,
        }
