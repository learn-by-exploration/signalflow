# mkg/domain/services/tribal_knowledge.py
"""TribalKnowledgeInput — human expert knowledge injection into the graph.

R-TK1 through R-TK5: Allows analysts to manually add entities, edges,
override confidence scores, annotate entities, and maintains an audit trail.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from mkg.domain.interfaces.graph_storage import GraphStorage


class TribalKnowledgeInput:
    """Supports manual expert knowledge injection into the knowledge graph.

    All mutations are attributed to the expert and logged in the audit trail.
    """

    def __init__(self, storage: GraphStorage) -> None:
        self._storage = storage
        self._audit: list[dict[str, Any]] = []

    async def add_entity(
        self,
        name: str,
        entity_type: str,
        expert: str,
        notes: Optional[str] = None,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """Add an entity from expert knowledge.

        Args:
            name: Entity name.
            entity_type: Entity type (Company, Product, etc.).
            expert: Identifier of the expert adding this.
            notes: Optional notes/context.
            confidence: Override confidence (default 1.0 for expert input).

        Returns:
            Created entity dict.
        """
        props: dict[str, Any] = {
            "name": name,
            "confidence": confidence,
            "source": f"expert:{expert}",
        }
        if notes:
            props["notes"] = notes

        result = await self._storage.create_entity(entity_type, props)

        self._log_action("add_entity", expert, {
            "entity_id": result["id"],
            "name": name,
            "entity_type": entity_type,
        })
        return result

    async def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        weight: float,
        expert: str,
        notes: Optional[str] = None,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """Add an edge from expert knowledge.

        Args:
            source_id: Source entity ID.
            target_id: Target entity ID.
            relation_type: Relationship type.
            weight: Edge weight.
            expert: Expert identifier.
            notes: Optional notes.
            confidence: Override confidence.

        Returns:
            Created edge dict.
        """
        props: dict[str, Any] = {
            "weight": weight,
            "confidence": confidence,
            "source": f"expert:{expert}",
        }
        if notes:
            props["notes"] = notes

        result = await self._storage.create_edge(
            source_id, target_id, relation_type, props
        )

        self._log_action("add_edge", expert, {
            "edge_id": result["id"],
            "source_id": source_id,
            "target_id": target_id,
            "relation_type": relation_type,
        })
        return result

    async def override_confidence(
        self,
        entity_id: str,
        new_confidence: float,
        expert: str,
        reason: str,
    ) -> dict[str, Any]:
        """Override an entity's confidence score.

        Args:
            entity_id: Entity to update.
            new_confidence: New confidence value [0, 1].
            expert: Expert identifier.
            reason: Why the override is warranted.

        Returns:
            Updated entity dict.
        """
        if not 0.0 <= new_confidence <= 1.0:
            raise ValueError(f"Confidence must be in [0, 1], got {new_confidence}")

        result = await self._storage.update_entity(entity_id, {
            "confidence": new_confidence,
        })
        if result is None:
            raise ValueError(f"Entity {entity_id} not found for confidence override")

        self._log_action("override_confidence", expert, {
            "entity_id": entity_id,
            "new_confidence": new_confidence,
            "reason": reason,
        })
        return result

    async def annotate(
        self,
        entity_id: str,
        annotation: str,
        expert: str,
    ) -> dict[str, Any]:
        """Add an annotation to an entity.

        Args:
            entity_id: Entity to annotate.
            annotation: Annotation text.
            expert: Expert identifier.

        Returns:
            Updated entity dict with annotations list.
        """
        entity = await self._storage.get_entity(entity_id)
        if entity is None:
            raise ValueError(f"Entity {entity_id} not found")

        annotations = entity.get("annotations", [])
        annotations.append({
            "text": annotation,
            "expert": expert,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        result = await self._storage.update_entity(entity_id, {
            "annotations": annotations,
        })

        self._log_action("annotate", expert, {
            "entity_id": entity_id,
            "annotation": annotation,
        })
        return result

    def get_audit_trail(
        self,
        expert: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get audit trail of expert actions.

        Args:
            expert: Optional filter by expert.
            limit: Maximum entries to return.

        Returns:
            List of audit entries, newest first.
        """
        entries = self._audit
        if expert:
            entries = [e for e in entries if e["expert"] == expert]
        return list(reversed(entries[-limit:]))

    def _log_action(
        self,
        action: str,
        expert: str,
        details: dict[str, Any],
    ) -> None:
        """Log an expert action to the audit trail."""
        self._audit.append({
            "action": action,
            "expert": expert,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
