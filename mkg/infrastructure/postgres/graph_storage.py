# mkg/infrastructure/postgres/graph_storage.py
"""PostgresGraphStorage — production graph storage via asyncpg.

Implements the full GraphStorage interface using PostgreSQL with:
- TEXT[] columns + GIN indexes for tags on entities and edges
- Recursive CTEs for server-side BFS traversal (traverse, get_subgraph)
- pg_trgm for fuzzy entity search
- JSONB + GIN for flexible property queries
- asyncpg connection pool for concurrent access

Designed for 10K-50K entities and 100K-500K edges.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import asyncpg

from mkg.domain.interfaces.graph_storage import GraphStorage

logger = logging.getLogger(__name__)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS mkg_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,
    name TEXT NOT NULL,
    canonical_name TEXT NOT NULL DEFAULT '',
    tags TEXT[] NOT NULL DEFAULT '{}',
    properties JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mkg_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES mkg_entities(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES mkg_entities(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    confidence REAL NOT NULL DEFAULT 1.0,
    direction TEXT NOT NULL DEFAULT 'positive',
    tags TEXT[] NOT NULL DEFAULT '{}',
    properties JSONB NOT NULL DEFAULT '{}',
    valid_from TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mkg_entity_type ON mkg_entities (entity_type);
CREATE INDEX IF NOT EXISTS idx_mkg_entity_canonical ON mkg_entities (canonical_name);
CREATE INDEX IF NOT EXISTS idx_mkg_entity_tags ON mkg_entities USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_mkg_entity_props ON mkg_entities USING GIN (properties);
CREATE INDEX IF NOT EXISTS idx_mkg_edge_source ON mkg_edges (source_id);
CREATE INDEX IF NOT EXISTS idx_mkg_edge_target ON mkg_edges (target_id);
CREATE INDEX IF NOT EXISTS idx_mkg_edge_relation ON mkg_edges (relation_type);
CREATE INDEX IF NOT EXISTS idx_mkg_edge_tags ON mkg_edges USING GIN (tags);
"""

_TRGM_SQL = """
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_mkg_entity_name_trgm
    ON mkg_entities USING GIN (name gin_trgm_ops);
"""


class PostgresGraphStorage(GraphStorage):
    """Production graph storage backed by PostgreSQL via asyncpg.

    Args:
        database_url: PostgreSQL connection string (postgresql://...).
        min_pool: Minimum connection pool size.
        max_pool: Maximum connection pool size.
    """

    def __init__(
        self,
        database_url: str,
        min_pool: int = 2,
        max_pool: int = 10,
    ) -> None:
        # asyncpg needs plain postgresql:// URL, not postgresql+asyncpg://
        self._database_url = database_url.replace("+asyncpg", "")
        self._min_pool = min_pool
        self._max_pool = max_pool
        self._pool: Optional[asyncpg.Pool] = None
        self._has_trgm = False

    async def initialize(self) -> None:
        """Create connection pool and schema."""
        self._pool = await asyncpg.create_pool(
            self._database_url,
            min_size=self._min_pool,
            max_size=self._max_pool,
        )
        async with self._pool.acquire() as conn:
            await conn.execute(_SCHEMA_SQL)
            try:
                await conn.execute(_TRGM_SQL)
                self._has_trgm = True
            except Exception:
                logger.info("pg_trgm not available, falling back to ILIKE search")
                self._has_trgm = False
        logger.info("PostgresGraphStorage initialized (pool=%d-%d, trgm=%s)",
                     self._min_pool, self._max_pool, self._has_trgm)

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    @property
    def is_connected(self) -> bool:
        return self._pool is not None

    def _ensure_pool(self) -> asyncpg.Pool:
        if not self._pool:
            raise RuntimeError("Not initialized. Call initialize() first.")
        return self._pool

    # ── Row converters ──

    @staticmethod
    def _entity_to_dict(row: asyncpg.Record) -> dict[str, Any]:
        props = row["properties"] if isinstance(row["properties"], dict) else {}
        return {
            "id": str(row["id"]),
            "entity_type": row["entity_type"],
            "name": row["name"],
            "canonical_name": row["canonical_name"],
            "tags": list(row["tags"]) if row["tags"] else [],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            **props,
        }

    @staticmethod
    def _edge_to_dict(row: asyncpg.Record) -> dict[str, Any]:
        props = row["properties"] if isinstance(row["properties"], dict) else {}
        return {
            "id": str(row["id"]),
            "source_id": str(row["source_id"]),
            "target_id": str(row["target_id"]),
            "relation_type": row["relation_type"],
            "weight": row["weight"],
            "confidence": row["confidence"],
            "direction": row["direction"] or "positive",
            "tags": list(row["tags"]) if row["tags"] else [],
            "valid_from": row["valid_from"].isoformat() if row["valid_from"] else None,
            "valid_until": row["valid_until"].isoformat() if row["valid_until"] else None,
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            **props,
        }

    # ── Entity CRUD ──

    async def create_entity(
        self,
        entity_type: str,
        properties: dict[str, Any],
        entity_id: Optional[str] = None,
    ) -> dict[str, Any]:
        pool = self._ensure_pool()
        eid = entity_id or str(uuid.uuid4())
        props = dict(properties)
        name = props.pop("name", "")
        canonical_name = props.pop("canonical_name", name)
        tags = props.pop("tags", [])
        now = datetime.now(timezone.utc)

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO mkg_entities
                   (id, entity_type, name, canonical_name, tags, properties, created_at, updated_at)
                   VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $7)
                   RETURNING *""",
                uuid.UUID(eid), entity_type, name, canonical_name,
                tags, json.dumps(props), now,
            )
        return self._entity_to_dict(row)

    async def get_entity(self, entity_id: str) -> Optional[dict[str, Any]]:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM mkg_entities WHERE id = $1",
                uuid.UUID(entity_id),
            )
        return self._entity_to_dict(row) if row else None

    async def update_entity(
        self, entity_id: str, properties: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        pool = self._ensure_pool()
        existing = await self.get_entity(entity_id)
        if not existing:
            return None

        props = dict(properties)
        name = props.pop("name", existing["name"])
        canonical_name = props.pop("canonical_name", existing.get("canonical_name", name))
        tags = props.pop("tags", existing.get("tags", []))
        now = datetime.now(timezone.utc)

        exclude = {"id", "entity_type", "name", "canonical_name", "tags", "created_at", "updated_at"}
        merged = {k: v for k, v in existing.items() if k not in exclude}
        merged.update(props)

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE mkg_entities
                   SET name = $2, canonical_name = $3, tags = $4,
                       properties = $5, updated_at = $6
                   WHERE id = $1
                   RETURNING *""",
                uuid.UUID(entity_id), name, canonical_name, tags,
                json.dumps(merged), now,
            )
        return self._entity_to_dict(row) if row else None

    async def delete_entity(self, entity_id: str) -> bool:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM mkg_entities WHERE id = $1",
                uuid.UUID(entity_id),
            )
        return result == "DELETE 1"

    async def find_entities(
        self,
        entity_type: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        pool = self._ensure_pool()
        conditions: list[str] = []
        params: list[Any] = []
        idx = 1

        if entity_type:
            conditions.append(f"entity_type = ${idx}")
            params.append(entity_type)
            idx += 1

        if filters:
            for key, value in filters.items():
                if key == "tags":
                    # tags filter: array containment
                    tag_list = value if isinstance(value, list) else [value]
                    conditions.append(f"tags @> ${idx}::text[]")
                    params.append(tag_list)
                    idx += 1
                elif key in ("name", "canonical_name"):
                    conditions.append(f"{key} = ${idx}")
                    params.append(value)
                    idx += 1
                else:
                    conditions.append(f"properties->>'{key}' = ${idx}")
                    params.append(str(value))
                    idx += 1

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.extend([limit, offset])

        query = f"""SELECT * FROM mkg_entities {where}
                    ORDER BY created_at DESC
                    LIMIT ${idx} OFFSET ${idx + 1}"""

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        return [self._entity_to_dict(r) for r in rows]

    # ── Edge CRUD ──

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: dict[str, Any],
        edge_id: Optional[str] = None,
    ) -> dict[str, Any]:
        pool = self._ensure_pool()
        eid = edge_id or str(uuid.uuid4())
        props = dict(properties)
        weight = props.pop("weight", 1.0)
        confidence = props.pop("confidence", 1.0)
        direction = props.pop("direction", "positive")
        tags = props.pop("tags", [])
        valid_from = props.pop("valid_from", None)
        valid_until = props.pop("valid_until", None)
        now = datetime.now(timezone.utc)

        # Parse ISO strings to datetime if needed
        if isinstance(valid_from, str):
            valid_from = datetime.fromisoformat(valid_from)
        if isinstance(valid_until, str):
            valid_until = datetime.fromisoformat(valid_until)

        async with pool.acquire() as conn:
            # Validate entities exist
            src = await conn.fetchval(
                "SELECT id FROM mkg_entities WHERE id = $1", uuid.UUID(source_id))
            if not src:
                raise ValueError(f"source entity '{source_id}' not found")
            tgt = await conn.fetchval(
                "SELECT id FROM mkg_entities WHERE id = $1", uuid.UUID(target_id))
            if not tgt:
                raise ValueError(f"target entity '{target_id}' not found")

            row = await conn.fetchrow(
                """INSERT INTO mkg_edges
                   (id, source_id, target_id, relation_type, weight, confidence,
                    direction, tags, properties, valid_from, valid_until,
                    created_at, updated_at)
                   VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6,
                           $7, $8, $9, $10, $11, $12, $12)
                   RETURNING *""",
                uuid.UUID(eid), uuid.UUID(source_id), uuid.UUID(target_id),
                relation_type, weight, confidence, direction, tags,
                json.dumps(props), valid_from, valid_until, now,
            )
        return self._edge_to_dict(row)

    async def get_edge(self, edge_id: str) -> Optional[dict[str, Any]]:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM mkg_edges WHERE id = $1",
                uuid.UUID(edge_id),
            )
        return self._edge_to_dict(row) if row else None

    async def update_edge(
        self, edge_id: str, properties: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        pool = self._ensure_pool()
        existing = await self.get_edge(edge_id)
        if not existing:
            return None

        props = dict(properties)
        weight = props.pop("weight", existing["weight"])
        confidence = props.pop("confidence", existing["confidence"])
        direction = props.pop("direction", existing.get("direction", "positive"))
        tags = props.pop("tags", existing.get("tags", []))
        valid_from = props.pop("valid_from", existing.get("valid_from"))
        valid_until = props.pop("valid_until", existing.get("valid_until"))
        now = datetime.now(timezone.utc)

        if isinstance(valid_from, str):
            valid_from = datetime.fromisoformat(valid_from)
        if isinstance(valid_until, str):
            valid_until = datetime.fromisoformat(valid_until)

        exclude = {
            "id", "source_id", "target_id", "relation_type",
            "weight", "confidence", "direction", "tags",
            "valid_from", "valid_until", "created_at", "updated_at",
        }
        merged = {k: v for k, v in existing.items() if k not in exclude}
        merged.update(props)

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE mkg_edges
                   SET weight = $2, confidence = $3, direction = $4, tags = $5,
                       properties = $6, valid_from = $7, valid_until = $8, updated_at = $9
                   WHERE id = $1
                   RETURNING *""",
                uuid.UUID(edge_id), weight, confidence, direction, tags,
                json.dumps(merged), valid_from, valid_until, now,
            )
        return self._edge_to_dict(row) if row else None

    async def delete_edge(self, edge_id: str) -> bool:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM mkg_edges WHERE id = $1",
                uuid.UUID(edge_id),
            )
        return result == "DELETE 1"

    async def find_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        pool = self._ensure_pool()
        conditions: list[str] = []
        params: list[Any] = []
        idx = 1

        if source_id:
            conditions.append(f"source_id = ${idx}::uuid")
            params.append(uuid.UUID(source_id))
            idx += 1
        if target_id:
            conditions.append(f"target_id = ${idx}::uuid")
            params.append(uuid.UUID(target_id))
            idx += 1
        if relation_type:
            conditions.append(f"relation_type = ${idx}")
            params.append(relation_type)
            idx += 1

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)

        query = f"SELECT * FROM mkg_edges {where} LIMIT ${idx}"

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        return [self._edge_to_dict(r) for r in rows]

    # ── Traversal (recursive CTE) ──

    async def get_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[str] = None,
        direction: str = "both",
    ) -> list[dict[str, Any]]:
        pool = self._ensure_pool()
        eid = uuid.UUID(entity_id)
        neighbors: list[dict[str, Any]] = []
        seen: set[str] = set()

        async with pool.acquire() as conn:
            if direction in ("outgoing", "both"):
                query = """
                    SELECT e.* FROM mkg_entities e
                    JOIN mkg_edges r ON e.id = r.target_id
                    WHERE r.source_id = $1
                """
                params: list[Any] = [eid]
                if relation_type:
                    query += " AND r.relation_type = $2"
                    params.append(relation_type)
                for row in await conn.fetch(query, *params):
                    rid = str(row["id"])
                    if rid not in seen:
                        neighbors.append(self._entity_to_dict(row))
                        seen.add(rid)

            if direction in ("incoming", "both"):
                query = """
                    SELECT e.* FROM mkg_entities e
                    JOIN mkg_edges r ON e.id = r.source_id
                    WHERE r.target_id = $1
                """
                params = [eid]
                if relation_type:
                    query += " AND r.relation_type = $2"
                    params.append(relation_type)
                for row in await conn.fetch(query, *params):
                    rid = str(row["id"])
                    if rid not in seen:
                        neighbors.append(self._entity_to_dict(row))
                        seen.add(rid)

        return neighbors

    async def get_subgraph(
        self,
        entity_id: str,
        max_depth: int = 2,
        relation_types: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Extract connected subgraph using recursive CTE."""
        pool = self._ensure_pool()
        eid = uuid.UUID(entity_id)

        rel_filter = ""
        params: list[Any] = [eid, max_depth]
        if relation_types:
            rel_filter = "AND e.relation_type = ANY($3::text[])"
            params.append(relation_types)

        query = f"""
        WITH RECURSIVE subgraph AS (
            -- Base: the start entity
            SELECT id AS entity_id, 0 AS depth
            FROM mkg_entities WHERE id = $1

            UNION

            -- Outgoing edges
            SELECT e.target_id AS entity_id, sg.depth + 1
            FROM mkg_edges e
            JOIN subgraph sg ON e.source_id = sg.entity_id
            WHERE sg.depth < $2 {rel_filter}

            UNION

            -- Incoming edges
            SELECT e.source_id AS entity_id, sg.depth + 1
            FROM mkg_edges e
            JOIN subgraph sg ON e.target_id = sg.entity_id
            WHERE sg.depth < $2 {rel_filter}
        )
        SELECT DISTINCT entity_id FROM subgraph;
        """

        async with pool.acquire() as conn:
            entity_ids = [row["entity_id"] for row in await conn.fetch(query, *params)]

            if not entity_ids:
                return {"nodes": [], "edges": []}

            nodes = await conn.fetch(
                "SELECT * FROM mkg_entities WHERE id = ANY($1::uuid[])",
                entity_ids,
            )

            edge_query = """
                SELECT * FROM mkg_edges
                WHERE source_id = ANY($1::uuid[]) AND target_id = ANY($1::uuid[])
            """
            edge_params: list[Any] = [entity_ids]
            if relation_types:
                edge_query += " AND relation_type = ANY($2::text[])"
                edge_params.append(relation_types)

            edges = await conn.fetch(edge_query, *edge_params)

        return {
            "nodes": [self._entity_to_dict(r) for r in nodes],
            "edges": [self._edge_to_dict(r) for r in edges],
        }

    async def traverse(
        self,
        start_entity_id: str,
        max_depth: int = 4,
        min_weight: float = 0.0,
        relation_types: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """BFS traversal using recursive CTE with weight accumulation."""
        pool = self._ensure_pool()
        eid = uuid.UUID(start_entity_id)

        rel_filter = ""
        params: list[Any] = [eid, max_depth, min_weight]
        if relation_types:
            rel_filter = "AND e.relation_type = ANY($4::text[])"
            params.append(relation_types)

        query = f"""
        WITH RECURSIVE bfs AS (
            -- Base: direct outgoing edges from trigger
            SELECT
                e.target_id AS entity_id,
                1 AS depth,
                ARRAY[$1::uuid, e.target_id] AS path,
                (e.weight * e.confidence)::real AS cumulative_weight
            FROM mkg_edges e
            WHERE e.source_id = $1
              AND e.weight >= $3
              {rel_filter}

            UNION ALL

            -- Recursive: next hops
            SELECT
                e.target_id,
                b.depth + 1,
                b.path || e.target_id,
                (b.cumulative_weight * e.weight * e.confidence)::real
            FROM mkg_edges e
            JOIN bfs b ON e.source_id = b.entity_id
            WHERE b.depth < $2
              AND NOT (e.target_id = ANY(b.path))
              AND e.weight >= $3
              {rel_filter}
        )
        SELECT DISTINCT ON (entity_id)
            entity_id, depth, path, cumulative_weight
        FROM bfs
        ORDER BY entity_id, cumulative_weight DESC;
        """

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            results = []
            for row in rows:
                entity = await self.get_entity(str(row["entity_id"]))
                if entity:
                    results.append({
                        "entity": entity,
                        "depth": row["depth"],
                        "path": [str(p) for p in row["path"]],
                        "cumulative_weight": row["cumulative_weight"],
                    })

        return results

    # ── Search ──

    async def search(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 20,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> list[dict[str, Any]]:
        """Search entities with relevance scoring.

        Uses pg_trgm similarity if available, otherwise falls back to
        ILIKE with BM25-style ranking tiers.
        """
        pool = self._ensure_pool()
        query_lower = query.lower()

        if self._has_trgm:
            return await self._search_trgm(query, entity_type, limit)
        return await self._search_ilike(query_lower, entity_type, limit)

    async def _search_trgm(
        self, query: str, entity_type: Optional[str], limit: int
    ) -> list[dict[str, Any]]:
        """Trigram similarity search."""
        pool = self._ensure_pool()
        params: list[Any] = [query, limit]
        type_filter = ""
        if entity_type:
            type_filter = "AND entity_type = $3"
            params.append(entity_type)

        sql = f"""
            SELECT *,
                   GREATEST(
                       similarity(name, $1),
                       similarity(canonical_name, $1)
                   ) AS score
            FROM mkg_entities
            WHERE (name % $1 OR canonical_name % $1
                   OR name ILIKE '%' || $1 || '%'
                   OR canonical_name ILIKE '%' || $1 || '%')
            {type_filter}
            ORDER BY score DESC
            LIMIT $2
        """

        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            results = []
            for row in rows:
                entity = self._entity_to_dict(row)
                entity["score"] = float(row["score"])
                results.append(entity)
            return results

    async def _search_ilike(
        self, query_lower: str, entity_type: Optional[str], limit: int
    ) -> list[dict[str, Any]]:
        """Fallback ILIKE search with BM25-style ranking tiers."""
        pool = self._ensure_pool()
        params: list[Any] = [f"%{query_lower}%"]
        type_filter = ""
        if entity_type:
            type_filter = "AND entity_type = $2"
            params.append(entity_type)

        sql = f"""
            SELECT * FROM mkg_entities
            WHERE (name ILIKE $1 OR canonical_name ILIKE $1)
            {type_filter}
            LIMIT {limit * 3}
        """

        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)

        results = []
        for row in rows:
            entity = self._entity_to_dict(row)
            name_lower = entity.get("name", "").lower()
            canon_lower = entity.get("canonical_name", "").lower()

            if name_lower == query_lower:
                score = 1.0
            elif canon_lower == query_lower:
                score = 0.95
            elif name_lower.startswith(query_lower):
                score = 0.8
            elif canon_lower.startswith(query_lower):
                score = 0.75
            elif query_lower in name_lower:
                score = 0.5
            elif query_lower in canon_lower:
                score = 0.4
            else:
                score = 0.2
            entity["score"] = score
            results.append(entity)

        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]

    # ── Temporal queries ──

    async def find_edges_at_time(
        self,
        as_of: str,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Find edges valid at a specific point in time."""
        pool = self._ensure_pool()
        conditions = [
            "(valid_from IS NULL OR valid_from <= $1::timestamptz)",
            "(valid_until IS NULL OR valid_until > $1::timestamptz)",
        ]
        params: list[Any] = [as_of]
        idx = 2

        if source_id:
            conditions.append(f"source_id = ${idx}::uuid")
            params.append(uuid.UUID(source_id))
            idx += 1
        if target_id:
            conditions.append(f"target_id = ${idx}::uuid")
            params.append(uuid.UUID(target_id))
            idx += 1
        if relation_type:
            conditions.append(f"relation_type = ${idx}")
            params.append(relation_type)
            idx += 1

        params.append(limit)
        where = " AND ".join(conditions)
        query = f"SELECT * FROM mkg_edges WHERE {where} LIMIT ${idx}"

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        return [self._edge_to_dict(r) for r in rows]

    # ── Merge ──

    async def merge_entity(
        self,
        entity_type: str,
        match_properties: dict[str, Any],
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update entity by matching properties (MERGE pattern)."""
        existing = await self.find_entities(entity_type=entity_type, limit=500)
        for entity in existing:
            if all(entity.get(k) == v for k, v in match_properties.items()):
                updated = await self.update_entity(entity["id"], properties)
                if updated:
                    return updated

        return await self.create_entity(entity_type, properties)

    # ── Ops ──

    async def backup(self, backup_path: str) -> bool:
        """PostgreSQL backup via pg_dump would be used externally.

        This method creates a JSON export of all entities and edges.
        """
        pool = self._ensure_pool()
        try:
            async with pool.acquire() as conn:
                entities = await conn.fetch("SELECT * FROM mkg_entities")
                edges = await conn.fetch("SELECT * FROM mkg_edges")

            data = {
                "entities": [self._entity_to_dict(r) for r in entities],
                "edges": [self._edge_to_dict(r) for r in edges],
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }
            import json as json_mod
            with open(backup_path, "w") as f:
                json_mod.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error("Backup failed: %s", e)
            return False

    async def health_check(self) -> dict[str, Any]:
        pool = self._ensure_pool()
        try:
            async with pool.acquire() as conn:
                entity_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM mkg_entities")
                edge_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM mkg_edges")
            return {
                "status": "healthy",
                "backend": "postgres",
                "entity_count": entity_count,
                "edge_count": edge_count,
                "pool_size": self._pool.get_size() if self._pool else 0,
                "has_trgm": self._has_trgm,
            }
        except Exception as e:
            return {"status": "unhealthy", "backend": "postgres", "error": str(e)}
