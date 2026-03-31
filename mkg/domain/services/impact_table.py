# mkg/domain/services/impact_table.py
"""ImpactTableBuilder — builds ranked impact table data for the frontend UI.

R-UI1 through R-UI5: Takes propagation results, resolves entity names,
ranks by impact, and returns a table structure ready for frontend rendering.
"""

from typing import Any, Optional

from mkg.domain.interfaces.graph_storage import GraphStorage


class ImpactTableBuilder:
    """Builds ranked impact tables from propagation results.

    Enriches raw propagation output with entity metadata for display.
    """

    def __init__(self, storage: GraphStorage) -> None:
        self._storage = storage

    async def build(
        self,
        propagation_results: list[dict[str, Any]],
        trigger_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """Build a ranked impact table.

        Args:
            propagation_results: Output from PropagationEngine.propagate().
            trigger_name: Optional label for the trigger event.

        Returns:
            Dict with rows (ranked list) and metadata.
        """
        if not propagation_results:
            return {"rows": [], "total": 0, "trigger": trigger_name}

        # Sort by impact descending
        sorted_results = sorted(
            propagation_results,
            key=lambda r: r["impact"],
            reverse=True,
        )

        rows: list[dict[str, Any]] = []
        for rank, result in enumerate(sorted_results, start=1):
            entity = await self._storage.get_entity(result["entity_id"])
            entity_name = entity.get("name", result["entity_id"]) if entity else result["entity_id"]
            entity_type = entity.get("entity_type", "Unknown") if entity else "Unknown"

            rows.append({
                "rank": rank,
                "entity_id": result["entity_id"],
                "entity_name": entity_name,
                "entity_type": entity_type,
                "impact_score": result["impact"],
                "impact_pct": round(result["impact"] * 100),
                "depth": result["depth"],
                "path": result.get("path", []),
            })

        return {
            "rows": rows,
            "total": len(rows),
            "trigger": trigger_name,
        }
