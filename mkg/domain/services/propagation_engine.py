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
    ) -> list[dict[str, Any]]:
        """Propagate impact from a trigger entity through the graph via BFS.

        Impact at each hop = parent_impact * edge_weight.
        Stops when max_depth reached, impact below threshold, or no more neighbors.

        Args:
            trigger_entity_id: Entity where the event originated.
            impact_score: Initial impact magnitude [0, 1].
            max_depth: Maximum hops from trigger (default 6 for financial supply chains).
            min_impact: Minimum impact to continue propagation.
            relation_types: Optional filter by edge types.

        Returns:
            List of affected entities sorted by impact (descending).
            Each item has: entity_id, impact, depth, path.
        """
        visited: set[str] = {trigger_entity_id}
        results: list[dict[str, Any]] = []

        # BFS queue: (entity_id, current_impact, depth, path)
        queue: deque[tuple[str, float, int, list[str]]] = deque()

        # Helper: get outgoing edges from an entity
        async def _outgoing_edges(eid: str) -> list[dict[str, Any]]:
            try:
                edges = await self._storage.find_edges(source_id=eid, limit=1000)
            except Exception:
                logger.exception("Failed to fetch edges for entity %s", eid)
                return []
            if relation_types:
                edges = [e for e in edges if e.get("relation_type") in relation_types]
            return edges

        # Seed with outgoing edges from trigger
        for edge in await _outgoing_edges(trigger_entity_id):
            neighbor_id = edge["target_id"]
            edge_weight = edge.get("weight", 0.5)
            hop_impact = impact_score * edge_weight
            if hop_impact >= min_impact and neighbor_id not in visited:
                queue.append((neighbor_id, hop_impact, 1, [trigger_entity_id, neighbor_id]))
                visited.add(neighbor_id)

        while queue:
            entity_id, current_impact, depth, path = queue.popleft()

            results.append({
                "entity_id": entity_id,
                "impact": current_impact,
                "depth": depth,
                "path": path,
            })

            if depth >= max_depth:
                continue

            for edge in await _outgoing_edges(entity_id):
                neighbor_id = edge["target_id"]
                edge_weight = edge.get("weight", 0.5)
                hop_impact = current_impact * edge_weight
                if hop_impact >= min_impact and neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((
                        neighbor_id,
                        hop_impact,
                        depth + 1,
                        path + [neighbor_id],
                    ))

        # Sort by impact descending
        results.sort(key=lambda r: r["impact"], reverse=True)
        return results
