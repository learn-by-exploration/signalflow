# mkg/domain/services/entity_service.py
"""EntityService — domain service for entity and edge CRUD.

Wraps GraphStorage with domain model conversion and business logic.
Depends on the GraphStorage port (R-PLAT-20 dependency inversion).
"""

from typing import Any, Optional

from mkg.domain.entities.edge import Edge, RelationType
from mkg.domain.entities.node import Entity, EntityType
from mkg.domain.interfaces.graph_storage import GraphStorage


class EntityService:
    """Domain service for entity and edge operations.

    Converts between raw dicts (GraphStorage) and typed domain models.
    Validates business rules before delegating to storage.
    """

    def __init__(self, storage: GraphStorage) -> None:
        self._storage = storage

    # --- Entity Operations ---

    async def create_entity(
        self,
        entity_type: EntityType,
        name: str,
        canonical_name: str,
        entity_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        confidence: float = 1.0,
        source: Optional[str] = None,
    ) -> Entity:
        """Create a new entity with domain validation."""
        if not name:
            raise ValueError("Entity name cannot be empty")

        properties = {
            "name": name,
            "canonical_name": canonical_name,
            "confidence": confidence,
            "metadata": metadata or {},
            "source": source,
        }
        result = await self._storage.create_entity(
            entity_type=entity_type.value,
            properties=properties,
            entity_id=entity_id,
        )
        return self._dict_to_entity(result)

    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID, returning a domain model."""
        result = await self._storage.get_entity(entity_id)
        if result is None:
            return None
        return self._dict_to_entity(result)

    async def find_entities(
        self,
        entity_type: Optional[EntityType] = None,
        filters: Optional[dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Entity]:
        """Find entities with optional type/property filters."""
        type_str = entity_type.value if entity_type else None
        results = await self._storage.find_entities(
            entity_type=type_str, filters=filters, limit=limit, offset=offset,
        )
        entities: list[Entity] = []
        for r in results:
            try:
                entities.append(self._dict_to_entity(r))
            except (ValueError, KeyError):
                continue  # skip malformed rows
        return entities

    async def update_entity(
        self,
        entity_id: str,
        name: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        confidence: Optional[float] = None,
    ) -> Optional[Entity]:
        """Update entity properties."""
        properties: dict[str, Any] = {}
        if name is not None:
            properties["name"] = name
        if metadata is not None:
            properties["metadata"] = metadata
        if confidence is not None:
            properties["confidence"] = confidence
        result = await self._storage.update_entity(entity_id, properties)
        if result is None:
            return None
        return self._dict_to_entity(result)

    async def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity and all connected edges."""
        return await self._storage.delete_entity(entity_id)

    # --- Edge Operations ---

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        weight: float,
        confidence: float,
        edge_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> Edge:
        """Create an edge with domain validation."""
        if source_id == target_id:
            raise ValueError("source_id and target_id cannot be the same (self-loops not allowed)")

        properties = {
            "weight": weight,
            "confidence": confidence,
            "metadata": metadata or {},
            "source": source,
        }
        result = await self._storage.create_edge(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type.value,
            properties=properties,
            edge_id=edge_id,
        )
        return self._dict_to_edge(result)

    async def get_edge(self, edge_id: str) -> Optional[Edge]:
        """Get an edge by ID."""
        result = await self._storage.get_edge(edge_id)
        if result is None:
            return None
        return self._dict_to_edge(result)

    async def find_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[RelationType] = None,
        limit: int = 100,
    ) -> list[Edge]:
        """Find edges with optional filters."""
        rel_str = relation_type.value if relation_type else None
        results = await self._storage.find_edges(
            source_id=source_id, target_id=target_id,
            relation_type=rel_str, limit=limit,
        )
        return [self._dict_to_edge(r) for r in results]

    # --- Conversion Helpers ---

    @staticmethod
    def _dict_to_entity(data: dict[str, Any]) -> Entity:
        """Convert a storage dict to an Entity domain model."""
        entity_id = data["id"]
        name = data.get("name") or entity_id
        return Entity(
            id=entity_id,
            entity_type=EntityType(data.get("entity_type", "Company")),
            name=name,
            canonical_name=data.get("canonical_name") or name,
            confidence=data.get("confidence", 1.0),
            metadata=data.get("metadata", {}),
            source=data.get("source"),
        )

    @staticmethod
    def _dict_to_edge(data: dict[str, Any]) -> Edge:
        """Convert a storage dict to an Edge domain model."""
        return Edge(
            id=data["id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation_type=RelationType(data.get("relation_type", "AFFECTS")),
            weight=data.get("weight", 0.5),
            confidence=data.get("confidence", 0.5),
            metadata=data.get("metadata", {}),
            source=data.get("source"),
        )
