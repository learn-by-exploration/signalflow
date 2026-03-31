# mkg/infrastructure/in_memory/graph_storage.py
"""InMemoryGraphStorage — test double implementing GraphStorage.

Stores all entities and edges in Python dicts. Used for unit and
integration testing without requiring a real Neo4j instance.
Thread-safe for single-threaded async usage (no concurrent writes).
"""

import uuid
from typing import Any, Optional

from mkg.domain.interfaces.graph_storage import GraphStorage


class InMemoryGraphStorage(GraphStorage):
    """In-memory implementation of GraphStorage for testing.

    Data is stored in plain dicts keyed by ID. No persistence.
    """

    def __init__(self) -> None:
        self._entities: dict[str, dict[str, Any]] = {}
        self._edges: dict[str, dict[str, Any]] = {}

    # --- Entity CRUD ---

    async def create_entity(
        self,
        entity_type: str,
        properties: dict[str, Any],
        entity_id: Optional[str] = None,
    ) -> dict[str, Any]:
        eid = entity_id or str(uuid.uuid4())
        entity = {"id": eid, "entity_type": entity_type, **properties}
        self._entities[eid] = entity
        return dict(entity)

    async def get_entity(self, entity_id: str) -> Optional[dict[str, Any]]:
        entity = self._entities.get(entity_id)
        return dict(entity) if entity else None

    async def update_entity(
        self, entity_id: str, properties: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        if entity_id not in self._entities:
            return None
        self._entities[entity_id].update(properties)
        return dict(self._entities[entity_id])

    async def delete_entity(self, entity_id: str) -> bool:
        if entity_id not in self._entities:
            return False
        del self._entities[entity_id]
        # Cascade: remove all edges connected to this entity
        edges_to_remove = [
            eid for eid, edge in self._edges.items()
            if edge["source_id"] == entity_id or edge["target_id"] == entity_id
        ]
        for eid in edges_to_remove:
            del self._edges[eid]
        return True

    async def find_entities(
        self,
        entity_type: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        results = list(self._entities.values())
        if entity_type:
            results = [e for e in results if e.get("entity_type") == entity_type]
        if filters:
            for key, value in filters.items():
                results = [e for e in results if e.get(key) == value]
        return [dict(e) for e in results[offset:offset + limit]]

    # --- Edge CRUD ---

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: dict[str, Any],
        edge_id: Optional[str] = None,
    ) -> dict[str, Any]:
        if source_id not in self._entities:
            raise ValueError(f"source entity '{source_id}' not found")
        if target_id not in self._entities:
            raise ValueError(f"target entity '{target_id}' not found")
        eid = edge_id or str(uuid.uuid4())
        edge = {
            "id": eid,
            "source_id": source_id,
            "target_id": target_id,
            "relation_type": relation_type,
            **properties,
        }
        self._edges[eid] = edge
        return dict(edge)

    async def get_edge(self, edge_id: str) -> Optional[dict[str, Any]]:
        edge = self._edges.get(edge_id)
        return dict(edge) if edge else None

    async def update_edge(
        self, edge_id: str, properties: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        if edge_id not in self._edges:
            return None
        self._edges[edge_id].update(properties)
        return dict(self._edges[edge_id])

    async def delete_edge(self, edge_id: str) -> bool:
        if edge_id not in self._edges:
            return False
        del self._edges[edge_id]
        return True

    async def find_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        results = list(self._edges.values())
        if source_id:
            results = [e for e in results if e["source_id"] == source_id]
        if target_id:
            results = [e for e in results if e["target_id"] == target_id]
        if relation_type:
            results = [e for e in results if e["relation_type"] == relation_type]
        return [dict(e) for e in results[:limit]]

    # --- Traversal ---

    async def get_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[str] = None,
        direction: str = "both",
    ) -> list[dict[str, Any]]:
        neighbors = []
        for edge in self._edges.values():
            if relation_type and edge["relation_type"] != relation_type:
                continue
            if direction in ("outgoing", "both") and edge["source_id"] == entity_id:
                entity = self._entities.get(edge["target_id"])
                if entity:
                    neighbors.append(dict(entity))
            if direction in ("incoming", "both") and edge["target_id"] == entity_id:
                entity = self._entities.get(edge["source_id"])
                if entity:
                    neighbors.append(dict(entity))
        return neighbors

    async def get_subgraph(
        self,
        entity_id: str,
        max_depth: int = 2,
        relation_types: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        visited_nodes: dict[str, dict[str, Any]] = {}
        collected_edges: list[dict[str, Any]] = []
        queue: list[tuple[str, int]] = [(entity_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited_nodes:
                continue
            entity = self._entities.get(current_id)
            if not entity:
                continue
            visited_nodes[current_id] = dict(entity)

            if depth < max_depth:
                for edge in self._edges.values():
                    if relation_types and edge["relation_type"] not in relation_types:
                        continue
                    if edge["source_id"] == current_id:
                        collected_edges.append(dict(edge))
                        queue.append((edge["target_id"], depth + 1))
                    elif edge["target_id"] == current_id:
                        collected_edges.append(dict(edge))
                        queue.append((edge["source_id"], depth + 1))

        return {
            "nodes": list(visited_nodes.values()),
            "edges": collected_edges,
        }

    async def traverse(
        self,
        start_entity_id: str,
        max_depth: int = 4,
        min_weight: float = 0.0,
        relation_types: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        visited: set[str] = set()

        queue: list[tuple[str, int, list[str], float]] = [
            (start_entity_id, 0, [start_entity_id], 1.0)
        ]

        while queue:
            current_id, depth, path, cumulative_weight = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            if depth > 0:
                entity = self._entities.get(current_id)
                if entity:
                    results.append({
                        "entity": dict(entity),
                        "depth": depth,
                        "path": list(path),
                        "cumulative_weight": cumulative_weight,
                    })

            if depth < max_depth:
                for edge in self._edges.values():
                    if relation_types and edge["relation_type"] not in relation_types:
                        continue
                    if edge["source_id"] == current_id:
                        edge_weight = edge.get("weight", 1.0)
                        if edge_weight >= min_weight:
                            new_cumulative = cumulative_weight * edge_weight
                            queue.append((
                                edge["target_id"],
                                depth + 1,
                                path + [edge["target_id"]],
                                new_cumulative,
                            ))

        return results

    # --- Search ---

    async def search(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 20,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> list[dict[str, Any]]:
        """Simple keyword search for in-memory testing (no vectors)."""
        results = []
        query_lower = query.lower()
        for entity in self._entities.values():
            if entity_type and entity.get("entity_type") != entity_type:
                continue
            # Score by keyword presence in any string property
            score = 0.0
            for value in entity.values():
                if isinstance(value, str) and query_lower in value.lower():
                    score = 1.0
                    break
            if score > 0:
                results.append({**dict(entity), "score": score})
        return results[:limit]

    # --- Merge / Dedup ---

    async def merge_entity(
        self,
        entity_type: str,
        match_properties: dict[str, Any],
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        # Find existing entity matching all match_properties
        for entity in self._entities.values():
            if entity.get("entity_type") != entity_type:
                continue
            if all(entity.get(k) == v for k, v in match_properties.items()):
                entity.update(properties)
                return dict(entity)
        # No match found — create new
        return await self.create_entity(entity_type, properties)

    # --- Backup ---

    async def backup(self, backup_path: str) -> bool:
        # In-memory: no-op, always succeeds
        return True

    # --- Health ---

    async def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "backend": "in_memory",
            "entity_count": len(self._entities),
            "edge_count": len(self._edges),
        }
