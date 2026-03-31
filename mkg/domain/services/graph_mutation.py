# mkg/domain/services/graph_mutation.py
"""GraphMutationService — applies verified extraction results to the knowledge graph.

Orchestrates entity dedup (via CanonicalEntityRegistry) and edge creation,
ensuring extraction results are safely persisted in the graph.
"""

from typing import Any, Optional
import logging

from mkg.domain.entities.node import EntityType
from mkg.domain.entities.edge import RelationType
from mkg.domain.interfaces.graph_storage import GraphStorage
from mkg.domain.services.canonical_registry import CanonicalEntityRegistry

logger = logging.getLogger(__name__)


class GraphMutationService:
    """Applies extraction results to the knowledge graph.

    Uses CanonicalEntityRegistry for entity dedup and GraphStorage for persistence.
    """

    def __init__(
        self,
        storage: GraphStorage,
        registry: CanonicalEntityRegistry,
    ) -> None:
        self._storage = storage
        self._registry = registry

    async def apply_entities(
        self,
        entities: list[dict[str, Any]],
        source: str,
    ) -> dict[str, Any]:
        """Apply a list of extracted entities to the graph.

        Args:
            entities: List of dicts with name, entity_type, confidence.
            source: Source attribution (article ID).

        Returns:
            Summary dict with created, updated, skipped counts.
        """
        created = 0
        updated = 0
        skipped = 0

        for raw in entities:
            name = raw.get("name", "").strip()
            if not name:
                skipped += 1
                continue

            try:
                entity_type = EntityType(raw.get("entity_type", "Company"))
            except ValueError:
                skipped += 1
                continue

            confidence = raw.get("confidence", 0.5)
            result = await self._registry.merge_or_create(
                storage=self._storage,
                entity_type=entity_type,
                name=name,
                properties={
                    "confidence": confidence,
                    "source": source,
                },
            )
            if result.get("_merged"):
                updated += 1
            else:
                created += 1

        return {"created": created, "updated": updated, "skipped": skipped}

    async def apply_relations(
        self,
        relations: list[dict[str, Any]],
        source: str,
    ) -> dict[str, Any]:
        """Apply a list of extracted relations to the graph.

        Resolves entity names to canonical IDs before creating edges.

        Args:
            relations: List of dicts with source, target, relation_type, weight, confidence.
            source: Source attribution.

        Returns:
            Summary dict with created and skipped counts.
        """
        created = 0
        skipped = 0

        for raw in relations:
            source_name = raw.get("source", "")
            target_name = raw.get("target", "")
            relation_type_str = raw.get("relation_type", "")

            # Validate relation type
            try:
                RelationType(relation_type_str)
            except ValueError:
                skipped += 1
                continue

            # Resolve canonical names and find entities
            source_canonical = self._registry.resolve(source_name)
            target_canonical = self._registry.resolve(target_name)

            source_entities = await self._storage.find_entities(
                filters={"canonical_name": source_canonical}
            )
            target_entities = await self._storage.find_entities(
                filters={"canonical_name": target_canonical}
            )

            if not source_entities or not target_entities:
                skipped += 1
                continue

            if len(source_entities) > 1:
                logger.warning(
                    "Multiple entities found for canonical name '%s' (using first of %d)",
                    source_canonical, len(source_entities),
                )
            if len(target_entities) > 1:
                logger.warning(
                    "Multiple entities found for canonical name '%s' (using first of %d)",
                    target_canonical, len(target_entities),
                )

            source_id = source_entities[0]["id"]
            target_id = target_entities[0]["id"]

            await self._storage.create_edge(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type_str,
                properties={
                    "weight": raw.get("weight", 0.5),
                    "confidence": raw.get("confidence", 0.5),
                    "source": source,
                },
            )
            created += 1

        return {"created": created, "skipped": skipped}

    async def apply(
        self,
        extraction: dict[str, Any],
        source: str,
    ) -> dict[str, Any]:
        """Apply a full extraction result (entities + relations).

        Args:
            extraction: Dict with 'entities' and 'relations' lists.
            source: Source attribution.

        Returns:
            Combined summary with entity and relation counts.
        """
        entities_result = await self.apply_entities(
            extraction.get("entities", []), source
        )
        relations_result = await self.apply_relations(
            extraction.get("relations", []), source
        )
        return {
            "entities": entities_result,
            "relations": relations_result,
        }
