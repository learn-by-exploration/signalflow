# mkg/infrastructure/neo4j/graph_storage.py
"""Neo4jGraphStorage — Dummy connector implementing GraphStorage.

Delegates all operations to InMemoryGraphStorage while logging
Neo4j-style Cypher queries that *would* execute against a real Neo4j
instance. Swap this for a real neo4j-driver implementation when
Neo4j CE 5.18+ is provisioned.

This lets the full pipeline (API → services → storage) run end-to-end
without requiring a live Neo4j database.
"""

import logging
from typing import Any, Optional

from mkg.domain.interfaces.graph_storage import GraphStorage
from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage

logger = logging.getLogger(__name__)


class Neo4jGraphStorage(GraphStorage):
    """Dummy Neo4j connector backed by InMemoryGraphStorage.

    Logs Cypher-style query stubs for debugging and future migration.
    Drop-in replacement once neo4j-driver is wired up.
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password",
        database: str = "mkg",
    ) -> None:
        self._uri = uri
        self._username = username
        self._database = database
        self._delegate = InMemoryGraphStorage()
        self._connected = False
        logger.info(
            "Neo4jGraphStorage DUMMY initialised — uri=%s db=%s (in-memory delegate)",
            uri,
            database,
        )

    # --- Connection lifecycle ---

    async def connect(self) -> None:
        """Simulate connection to Neo4j."""
        logger.info("DUMMY connect: MATCH (n) RETURN count(n) — using in-memory")
        self._connected = True

    async def close(self) -> None:
        """Simulate closing Neo4j driver."""
        logger.info("DUMMY close: driver.close()")
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    # --- Entity CRUD ---

    async def create_entity(
        self,
        entity_type: str,
        properties: dict[str, Any],
        entity_id: Optional[str] = None,
    ) -> dict[str, Any]:
        logger.debug(
            "CYPHER: CREATE (n:%s {name: $name, ...}) RETURN n",
            entity_type,
        )
        return await self._delegate.create_entity(entity_type, properties, entity_id)

    async def get_entity(self, entity_id: str) -> Optional[dict[str, Any]]:
        logger.debug("CYPHER: MATCH (n {id: $id}) RETURN n")
        return await self._delegate.get_entity(entity_id)

    async def update_entity(
        self, entity_id: str, properties: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        logger.debug("CYPHER: MATCH (n {id: $id}) SET n += $props RETURN n")
        return await self._delegate.update_entity(entity_id, properties)

    async def delete_entity(self, entity_id: str) -> bool:
        logger.debug("CYPHER: MATCH (n {id: $id}) DETACH DELETE n")
        return await self._delegate.delete_entity(entity_id)

    async def find_entities(
        self,
        entity_type: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        logger.debug("CYPHER: MATCH (n:%s) WHERE ... RETURN n LIMIT %d", entity_type, limit)
        return await self._delegate.find_entities(entity_type, filters, limit, offset)

    # --- Edge CRUD ---

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: dict[str, Any],
        edge_id: Optional[str] = None,
    ) -> dict[str, Any]:
        logger.debug(
            "CYPHER: MATCH (a {id: $src}), (b {id: $tgt}) CREATE (a)-[r:%s]->(b) RETURN r",
            relation_type,
        )
        return await self._delegate.create_edge(
            source_id, target_id, relation_type, properties, edge_id
        )

    async def get_edge(self, edge_id: str) -> Optional[dict[str, Any]]:
        logger.debug("CYPHER: MATCH ()-[r {id: $id}]->() RETURN r")
        return await self._delegate.get_edge(edge_id)

    async def update_edge(
        self, edge_id: str, properties: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        logger.debug("CYPHER: MATCH ()-[r {id: $id}]->() SET r += $props RETURN r")
        return await self._delegate.update_edge(edge_id, properties)

    async def delete_edge(self, edge_id: str) -> bool:
        logger.debug("CYPHER: MATCH ()-[r {id: $id}]->() DELETE r")
        return await self._delegate.delete_edge(edge_id)

    async def find_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        logger.debug("CYPHER: MATCH (a)-[r:%s]->(b) RETURN r LIMIT %d", relation_type, limit)
        return await self._delegate.find_edges(source_id, target_id, relation_type, limit)

    # --- Traversal ---

    async def get_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[str] = None,
        direction: str = "both",
    ) -> list[dict[str, Any]]:
        logger.debug("CYPHER: MATCH (n {id: $id})-[r]-(m) RETURN m")
        return await self._delegate.get_neighbors(entity_id, relation_type, direction)

    async def get_subgraph(
        self,
        entity_id: str,
        max_depth: int = 2,
        relation_types: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        logger.debug(
            "CYPHER: MATCH path=(n {id: $id})-[*1..%d]-(m) RETURN path",
            max_depth,
        )
        return await self._delegate.get_subgraph(entity_id, max_depth, relation_types)

    async def traverse(
        self,
        start_entity_id: str,
        max_depth: int = 4,
        min_weight: float = 0.0,
        relation_types: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        logger.debug(
            "CYPHER: CALL apoc.path.expand(n, '%s', '', 1, %d) — propagation",
            relation_types,
            max_depth,
        )
        return await self._delegate.traverse(
            start_entity_id, max_depth, min_weight, relation_types
        )

    # --- Search ---

    async def search(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 20,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> list[dict[str, Any]]:
        logger.debug(
            "CYPHER: CALL db.index.fulltext.queryNodes('entitySearch', $query) "
            "YIELD node, score — hybrid search (vector=%.1f, kw=%.1f)",
            vector_weight,
            keyword_weight,
        )
        return await self._delegate.search(
            query, entity_type, limit, vector_weight, keyword_weight
        )

    # --- Merge / Dedup ---

    async def merge_entity(
        self,
        entity_type: str,
        match_properties: dict[str, Any],
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        logger.debug(
            "CYPHER: MERGE (n:%s {canonical_name: $cn}) SET n += $props RETURN n",
            entity_type,
        )
        return await self._delegate.merge_entity(entity_type, match_properties, properties)

    # --- Backup ---

    async def backup(self, backup_path: str) -> bool:
        logger.info("DUMMY backup: neo4j-admin database dump — path=%s", backup_path)
        return await self._delegate.backup(backup_path)

    # --- Health ---

    async def health_check(self) -> dict[str, Any]:
        delegate_health = await self._delegate.health_check()
        return {
            **delegate_health,
            "backend": "neo4j_dummy",
            "uri": self._uri,
            "database": self._database,
            "connected": self._connected,
        }
