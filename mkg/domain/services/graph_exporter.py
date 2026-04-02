# mkg/domain/services/graph_exporter.py
"""GraphExporter — export graph data as JSON or CSV.

D5: Enables graph data download in JSON (nodes + edges + metadata)
and CSV (edge list) formats, with optional entity type filtering.
"""

import csv
import io
from datetime import datetime, timezone
from typing import Any, Optional

from mkg.domain.interfaces.graph_storage import GraphStorage


class GraphExporter:
    """Exports graph data in JSON and CSV formats."""

    def __init__(self, storage: GraphStorage) -> None:
        self._storage = storage

    async def export_json(
        self,
        entity_types: Optional[list[str]] = None,
        relation_types: Optional[list[str]] = None,
        limit: int = 10000,
    ) -> dict[str, Any]:
        """Export graph as JSON with nodes, edges, and metadata.

        Args:
            entity_types: Filter nodes by entity type.
            relation_types: Filter edges by relation type.
            limit: Max entities/edges to export.

        Returns:
            Dict with nodes, edges, and metadata.
        """
        # Fetch entities
        if entity_types:
            nodes: list[dict[str, Any]] = []
            for et in entity_types:
                entities = await self._storage.find_entities(
                    entity_type=et, limit=limit
                )
                nodes.extend(entities)
        else:
            nodes = await self._storage.find_entities(limit=limit)

        # Fetch edges
        all_edges = await self._storage.find_edges(limit=limit)
        if relation_types:
            all_edges = [
                e for e in all_edges
                if e.get("relation_type") in relation_types
            ]

        # If entity_types filter is active, only include edges whose
        # source and target are in the node set
        if entity_types:
            node_ids = {n["id"] for n in nodes}
            all_edges = [
                e for e in all_edges
                if e.get("source_id") in node_ids and e.get("target_id") in node_ids
            ]

        return {
            "nodes": nodes,
            "edges": all_edges,
            "metadata": {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "node_count": len(nodes),
                "edge_count": len(all_edges),
            },
        }

    async def export_csv(
        self,
        relation_types: Optional[list[str]] = None,
        limit: int = 10000,
    ) -> str:
        """Export edges as CSV string.

        Format: source_id,target_id,relation_type,weight,confidence,direction

        Args:
            relation_types: Filter by edge type.
            limit: Max edges to export.

        Returns:
            CSV string with header row.
        """
        all_edges = await self._storage.find_edges(limit=limit)
        if relation_types:
            all_edges = [
                e for e in all_edges
                if e.get("relation_type") in relation_types
            ]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "source_id", "target_id", "relation_type",
            "weight", "confidence", "direction",
        ])
        for edge in all_edges:
            writer.writerow([
                edge.get("source_id", ""),
                edge.get("target_id", ""),
                edge.get("relation_type", ""),
                edge.get("weight", 0.0),
                edge.get("confidence", 1.0),
                edge.get("direction", "positive"),
            ])

        return output.getvalue()
