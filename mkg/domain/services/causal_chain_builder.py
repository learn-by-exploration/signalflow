# mkg/domain/services/causal_chain_builder.py
"""CausalChainBuilder — builds narrative causal chains from propagation results.

R-CC1 through R-CC5: Translates raw BFS propagation paths into structured
causal chain objects with edge labels, impact scores, and human-readable
narratives.
"""

from typing import Any, Optional
import logging

from mkg.domain.interfaces.graph_storage import GraphStorage

logger = logging.getLogger(__name__)


class CausalChainBuilder:
    """Builds structured causal chains from propagation results.

    Given a trigger event and propagation results, resolves entity names
    and edge labels to produce chains that explain *why* an entity is affected.
    """

    def __init__(self, storage: GraphStorage) -> None:
        self._storage = storage

    async def build_chains(
        self,
        trigger_entity_id: str,
        trigger_event: str,
        propagation_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build causal chains from propagation results.

        Args:
            trigger_entity_id: The entity where the event originated.
            trigger_event: Description of the trigger event.
            propagation_results: Output from PropagationEngine.propagate().

        Returns:
            List of chain dicts with trigger, affected_entity, impact_score,
            hops, edge_labels, and narrative.
        """
        if not propagation_results:
            return []

        # Cache entity lookups
        entity_cache: dict[str, dict[str, Any]] = {}

        async def _get_entity_name(eid: str) -> str:
            if eid not in entity_cache:
                entity = await self._storage.get_entity(eid)
                if entity is None:
                    logger.warning("Entity %s not found in storage during chain building", eid)
                entity_cache[eid] = entity or {}
            return entity_cache.get(eid, {}).get("name", eid)

        chains: list[dict[str, Any]] = []

        for result in propagation_results:
            path = result.get("path", [])
            edge_labels = await self._resolve_edge_labels(path)

            trigger_name = await _get_entity_name(trigger_entity_id)
            affected_name = await _get_entity_name(result["entity_id"])

            narrative = self._build_narrative(
                trigger_name, trigger_event, affected_name,
                edge_labels, result["impact"],
            )

            chains.append({
                "trigger": trigger_entity_id,
                "trigger_name": trigger_name,
                "trigger_event": trigger_event,
                "affected_entity": result["entity_id"],
                "affected_name": affected_name,
                "impact_score": result["impact"],
                "hops": result["depth"],
                "path": path,
                "edge_labels": edge_labels,
                "narrative": narrative,
            })

        return chains

    async def _resolve_edge_labels(self, path: list[str]) -> list[str]:
        """Resolve edge relation types along a path."""
        labels: list[str] = []
        for i in range(len(path) - 1):
            edges = await self._storage.find_edges(
                source_id=path[i], target_id=path[i + 1], limit=1
            )
            if edges:
                labels.append(edges[0].get("relation_type", "UNKNOWN"))
            else:
                # Try reverse direction
                edges = await self._storage.find_edges(
                    source_id=path[i + 1], target_id=path[i], limit=1
                )
                labels.append(edges[0].get("relation_type", "UNKNOWN") if edges else "UNKNOWN")
        return labels

    def _build_narrative(
        self,
        trigger_name: str,
        trigger_event: str,
        affected_name: str,
        edge_labels: list[str],
        impact: float,
    ) -> str:
        """Build a human-readable narrative for the causal chain."""
        impact_pct = round(impact * 100)
        if not edge_labels:
            return f"{trigger_event} at {trigger_name} may affect {affected_name} ({impact_pct}% impact)."

        relation_desc = " → ".join(
            label.replace("_", " ").lower() for label in edge_labels
        )
        return (
            f"{trigger_event} at {trigger_name} affects {affected_name} "
            f"via {relation_desc} ({impact_pct}% impact)."
        )
