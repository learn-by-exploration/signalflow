# mkg/domain/interfaces/graph_storage.py
"""GraphStorage — Abstract interface for all graph database operations.

This is the foundational port (R-PLAT-20, R-MF6) that decouples business logic
from the graph database implementation. Neo4j CE can be swapped for Enterprise,
Aura, or any other graph DB without touching domain services.

Every method is async for non-blocking I/O.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class GraphStorage(ABC):
    """Abstract interface for graph database operations.

    Implementations: Neo4jGraphStorage (production), InMemoryGraphStorage (tests).
    All methods are async. All financial values must use Decimal, never float.
    """

    # --- Entity CRUD ---

    @abstractmethod
    async def create_entity(
        self,
        entity_type: str,
        properties: dict[str, Any],
        entity_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a new entity node in the graph.

        Args:
            entity_type: Node label (Company, Product, Facility, Person, Country, Regulation).
            properties: Node properties dict. Must include 'name'.
            entity_id: Optional explicit ID. Auto-generated if None.

        Returns:
            Created entity dict with 'id' and all properties.

        Raises:
            ValueError: If entity_type is not a valid node type.
        """
        ...

    @abstractmethod
    async def get_entity(self, entity_id: str) -> Optional[dict[str, Any]]:
        """Retrieve an entity by ID.

        Returns:
            Entity dict or None if not found.
        """
        ...

    @abstractmethod
    async def update_entity(
        self, entity_id: str, properties: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Update an existing entity's properties.

        Args:
            entity_id: The entity to update.
            properties: Properties to merge (partial update).

        Returns:
            Updated entity dict or None if not found.
        """
        ...

    @abstractmethod
    async def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity and all its connected edges.

        Returns:
            True if deleted, False if not found.
        """
        ...

    @abstractmethod
    async def find_entities(
        self,
        entity_type: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Find entities matching criteria.

        Args:
            entity_type: Filter by node label. None = all types.
            filters: Property filters (exact match).
            limit: Max results (default 100).
            offset: Pagination offset.

        Returns:
            List of matching entity dicts.
        """
        ...

    # --- Edge CRUD ---

    @abstractmethod
    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: dict[str, Any],
        edge_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a relationship edge between two entities.

        Args:
            source_id: Source entity ID.
            target_id: Target entity ID.
            relation_type: Edge label (SUPPLIES_TO, COMPETES_WITH, etc.).
            properties: Edge properties. Must include 'weight' and 'confidence'.
            edge_id: Optional explicit ID. Auto-generated if None.

        Returns:
            Created edge dict with 'id', 'source_id', 'target_id', and properties.

        Raises:
            ValueError: If source or target entity not found.
        """
        ...

    @abstractmethod
    async def get_edge(self, edge_id: str) -> Optional[dict[str, Any]]:
        """Retrieve an edge by ID.

        Returns:
            Edge dict or None if not found.
        """
        ...

    @abstractmethod
    async def update_edge(
        self, edge_id: str, properties: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Update an existing edge's properties (including weight).

        Args:
            edge_id: The edge to update.
            properties: Properties to merge (partial update).

        Returns:
            Updated edge dict or None if not found.
        """
        ...

    @abstractmethod
    async def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge.

        Returns:
            True if deleted, False if not found.
        """
        ...

    @abstractmethod
    async def find_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Find edges matching criteria.

        Args:
            source_id: Filter by source entity.
            target_id: Filter by target entity.
            relation_type: Filter by edge label.
            limit: Max results.

        Returns:
            List of matching edge dicts.
        """
        ...

    # --- Traversal ---

    @abstractmethod
    async def get_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[str] = None,
        direction: str = "both",
    ) -> list[dict[str, Any]]:
        """Get immediate neighbors of an entity.

        Args:
            entity_id: The entity to find neighbors for.
            relation_type: Optional filter by edge type.
            direction: 'outgoing', 'incoming', or 'both'.

        Returns:
            List of neighbor dicts with edge info.
        """
        ...

    @abstractmethod
    async def get_subgraph(
        self,
        entity_id: str,
        max_depth: int = 2,
        relation_types: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Get a subgraph centered on an entity up to max_depth hops.

        Args:
            entity_id: Center entity.
            max_depth: Maximum traversal depth.
            relation_types: Optional filter by edge types.

        Returns:
            Dict with 'nodes' and 'edges' lists.
        """
        ...

    @abstractmethod
    async def traverse(
        self,
        start_entity_id: str,
        max_depth: int = 4,
        min_weight: float = 0.0,
        relation_types: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """Traverse the graph from a start entity for propagation.

        This is the core method used by the Propagation Engine (R-PE1).

        Args:
            start_entity_id: Trigger entity ID.
            max_depth: Maximum hops (default 4 per R-PE2).
            min_weight: Minimum edge weight to follow.
            relation_types: Optional filter by edge types.

        Returns:
            List of path dicts, each with 'entity', 'depth', 'path', 'cumulative_weight'.
        """
        ...

    # --- Search ---

    @abstractmethod
    async def search(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 20,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> list[dict[str, Any]]:
        """Hybrid search: vector similarity + keyword (BM25).

        Per R-KG8 and R-MF8: configurable vector/keyword weights.

        Args:
            query: Search query text.
            entity_type: Optional filter by node type.
            limit: Max results.
            vector_weight: Weight for vector similarity (default 0.7).
            keyword_weight: Weight for keyword/BM25 (default 0.3).

        Returns:
            List of matching entities with relevance scores.
        """
        ...

    # --- Merge / Dedup ---

    @abstractmethod
    async def merge_entity(
        self,
        entity_type: str,
        match_properties: dict[str, Any],
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update entity by matching properties (MERGE pattern).

        Per R-KG7: Entity dedup via canonical name resolution.
        If entity with matching properties exists, update it.
        If not, create it.

        Args:
            entity_type: Node label.
            match_properties: Properties to match on (e.g., {'canonical_name': 'TSMC'}).
            properties: Full properties to set on create/merge.

        Returns:
            The merged entity dict (created or updated).
        """
        ...

    # --- Backup ---

    @abstractmethod
    async def backup(self, backup_path: str) -> bool:
        """Create a backup of the graph database.

        Per R-PLAT-8: Automated backup support.

        Args:
            backup_path: File/directory path for the backup.

        Returns:
            True if backup succeeded.
        """
        ...

    # --- Health ---

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check graph database health and return status.

        Returns:
            Dict with 'healthy' (bool), 'node_count', 'edge_count',
            'latency_ms', and any adapter-specific info.
        """
        ...
