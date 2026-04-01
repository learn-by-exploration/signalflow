# mkg/infrastructure/sqlite/graph_storage.py
"""SQLiteGraphStorage — persistent graph storage via aiosqlite.

Implements the full GraphStorage interface using SQLite for persistence.
Suitable for single-node deployment and development. For multi-node
production, swap to Neo4j or PostgreSQL.
"""

import json
import logging
import shutil
import uuid
from typing import Any, Optional

import aiosqlite

from mkg.domain.interfaces.graph_storage import GraphStorage

logger = logging.getLogger(__name__)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    name TEXT NOT NULL,
    properties TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS edges (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    confidence REAL NOT NULL DEFAULT 1.0,
    properties TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation_type);
"""


class SQLiteGraphStorage(GraphStorage):
    """Persistent graph storage backed by SQLite via aiosqlite."""

    def __init__(self, db_path: str = "mkg_graph.db") -> None:
        self._db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Open database and create schema."""
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")
        await self._db.executescript(_SCHEMA_SQL)
        await self._db.commit()
        logger.info("SQLiteGraphStorage initialized: %s", self._db_path)

    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    @property
    def is_connected(self) -> bool:
        """Whether the database connection is open."""
        return self._db is not None

    def _ensure_db(self) -> aiosqlite.Connection:
        if not self._db:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._db

    # ── Entity helpers ──

    def _entity_to_dict(self, row: tuple) -> dict[str, Any]:
        """Convert a DB row to entity dict."""
        props = json.loads(row[3]) if row[3] else {}
        return {
            "id": row[0],
            "entity_type": row[1],
            "name": row[2],
            **props,
        }

    def _edge_to_dict(self, row: tuple) -> dict[str, Any]:
        """Convert a DB row to edge dict."""
        props = json.loads(row[6]) if row[6] else {}
        return {
            "id": row[0],
            "source_id": row[1],
            "target_id": row[2],
            "relation_type": row[3],
            "weight": row[4],
            "confidence": row[5],
            **props,
        }

    # ── Entity CRUD ──

    async def create_entity(
        self,
        entity_type: str,
        properties: dict[str, Any],
        entity_id: Optional[str] = None,
    ) -> dict[str, Any]:
        db = self._ensure_db()
        eid = entity_id or str(uuid.uuid4())
        name = properties.pop("name", "")
        props_json = json.dumps(properties)

        await db.execute(
            "INSERT INTO entities (id, entity_type, name, properties) VALUES (?, ?, ?, ?)",
            (eid, entity_type, name, props_json),
        )
        await db.commit()
        return {"id": eid, "entity_type": entity_type, "name": name, **properties}

    async def get_entity(self, entity_id: str) -> Optional[dict[str, Any]]:
        db = self._ensure_db()
        async with db.execute(
            "SELECT id, entity_type, name, properties FROM entities WHERE id = ?",
            (entity_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return self._entity_to_dict(row) if row else None

    async def update_entity(
        self, entity_id: str, properties: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        db = self._ensure_db()
        existing = await self.get_entity(entity_id)
        if not existing:
            return None

        name = properties.pop("name", existing["name"])
        # Merge properties
        merged = {k: v for k, v in existing.items() if k not in ("id", "entity_type", "name")}
        merged.update(properties)
        props_json = json.dumps(merged)

        await db.execute(
            "UPDATE entities SET name = ?, properties = ? WHERE id = ?",
            (name, props_json, entity_id),
        )
        await db.commit()
        return {"id": entity_id, "entity_type": existing["entity_type"], "name": name, **merged}

    async def delete_entity(self, entity_id: str) -> bool:
        db = self._ensure_db()
        # Delete edges first (FK cascade may handle this, but be explicit)
        await db.execute(
            "DELETE FROM edges WHERE source_id = ? OR target_id = ?",
            (entity_id, entity_id),
        )
        cursor = await db.execute(
            "DELETE FROM entities WHERE id = ?", (entity_id,)
        )
        await db.commit()
        return cursor.rowcount > 0

    async def find_entities(
        self,
        entity_type: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        db = self._ensure_db()
        query = "SELECT id, entity_type, name, properties FROM entities WHERE 1=1"
        params: list[Any] = []

        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)

        if filters:
            for key, value in filters.items():
                if key in ("name",):
                    query += f" AND {key} = ?"
                    params.append(value)
                else:
                    # Search in JSON properties
                    query += " AND json_extract(properties, ?) = ?"
                    params.append(f"$.{key}")
                    params.append(json.dumps(value) if not isinstance(value, str) else value)

        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [self._entity_to_dict(row) for row in rows]

    # ── Edge CRUD ──

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: dict[str, Any],
        edge_id: Optional[str] = None,
    ) -> dict[str, Any]:
        db = self._ensure_db()

        # Validate entities exist
        if not await self.get_entity(source_id):
            raise ValueError(f"source entity '{source_id}' not found")
        if not await self.get_entity(target_id):
            raise ValueError(f"target entity '{target_id}' not found")

        eid = edge_id or str(uuid.uuid4())
        weight = properties.pop("weight", 1.0)
        confidence = properties.pop("confidence", 1.0)
        props_json = json.dumps(properties)

        await db.execute(
            "INSERT INTO edges (id, source_id, target_id, relation_type, weight, confidence, properties) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (eid, source_id, target_id, relation_type, weight, confidence, props_json),
        )
        await db.commit()
        return {
            "id": eid,
            "source_id": source_id,
            "target_id": target_id,
            "relation_type": relation_type,
            "weight": weight,
            "confidence": confidence,
            **properties,
        }

    async def get_edge(self, edge_id: str) -> Optional[dict[str, Any]]:
        db = self._ensure_db()
        async with db.execute(
            "SELECT id, source_id, target_id, relation_type, weight, confidence, properties "
            "FROM edges WHERE id = ?",
            (edge_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return self._edge_to_dict(row) if row else None

    async def update_edge(
        self, edge_id: str, properties: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        db = self._ensure_db()
        existing = await self.get_edge(edge_id)
        if not existing:
            return None

        weight = properties.pop("weight", existing["weight"])
        confidence = properties.pop("confidence", existing["confidence"])
        merged = {
            k: v for k, v in existing.items()
            if k not in ("id", "source_id", "target_id", "relation_type", "weight", "confidence")
        }
        merged.update(properties)
        props_json = json.dumps(merged)

        await db.execute(
            "UPDATE edges SET weight = ?, confidence = ?, properties = ? WHERE id = ?",
            (weight, confidence, props_json, edge_id),
        )
        await db.commit()
        return {
            "id": edge_id,
            "source_id": existing["source_id"],
            "target_id": existing["target_id"],
            "relation_type": existing["relation_type"],
            "weight": weight,
            "confidence": confidence,
            **merged,
        }

    async def delete_edge(self, edge_id: str) -> bool:
        db = self._ensure_db()
        cursor = await db.execute("DELETE FROM edges WHERE id = ?", (edge_id,))
        await db.commit()
        return cursor.rowcount > 0

    async def find_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        db = self._ensure_db()
        query = (
            "SELECT id, source_id, target_id, relation_type, weight, confidence, properties "
            "FROM edges WHERE 1=1"
        )
        params: list[Any] = []

        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)
        if target_id:
            query += " AND target_id = ?"
            params.append(target_id)
        if relation_type:
            query += " AND relation_type = ?"
            params.append(relation_type)

        query += " LIMIT ?"
        params.append(limit)

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [self._edge_to_dict(row) for row in rows]

    # ── Traversal ──

    async def get_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[str] = None,
        direction: str = "both",
    ) -> list[dict[str, Any]]:
        db = self._ensure_db()
        neighbors: list[dict[str, Any]] = []
        seen: set[str] = set()

        if direction in ("outgoing", "both"):
            query = (
                "SELECT e.id, e.entity_type, e.name, e.properties "
                "FROM entities e JOIN edges r ON e.id = r.target_id "
                "WHERE r.source_id = ?"
            )
            params: list[Any] = [entity_id]
            if relation_type:
                query += " AND r.relation_type = ?"
                params.append(relation_type)
            async with db.execute(query, params) as cursor:
                for row in await cursor.fetchall():
                    if row[0] not in seen:
                        neighbors.append(self._entity_to_dict(row))
                        seen.add(row[0])

        if direction in ("incoming", "both"):
            query = (
                "SELECT e.id, e.entity_type, e.name, e.properties "
                "FROM entities e JOIN edges r ON e.id = r.source_id "
                "WHERE r.target_id = ?"
            )
            params = [entity_id]
            if relation_type:
                query += " AND r.relation_type = ?"
                params.append(relation_type)
            async with db.execute(query, params) as cursor:
                for row in await cursor.fetchall():
                    if row[0] not in seen:
                        neighbors.append(self._entity_to_dict(row))
                        seen.add(row[0])

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
            entity = await self.get_entity(current_id)
            if not entity:
                continue
            visited_nodes[current_id] = entity

            if depth < max_depth:
                edges = await self.find_edges(source_id=current_id)
                edges += await self.find_edges(target_id=current_id)
                for edge in edges:
                    if relation_types and edge["relation_type"] not in relation_types:
                        continue
                    collected_edges.append(edge)
                    next_id = (
                        edge["target_id"]
                        if edge["source_id"] == current_id
                        else edge["source_id"]
                    )
                    queue.append((next_id, depth + 1))

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
                entity = await self.get_entity(current_id)
                if entity:
                    results.append({
                        "entity": entity,
                        "depth": depth,
                        "path": list(path),
                        "cumulative_weight": cumulative_weight,
                    })

            if depth < max_depth:
                edges = await self.find_edges(source_id=current_id)
                for edge in edges:
                    if relation_types and edge["relation_type"] not in relation_types:
                        continue
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

    # ── Search ──

    async def search(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 20,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> list[dict[str, Any]]:
        db = self._ensure_db()
        sql = (
            "SELECT id, entity_type, name, properties FROM entities "
            "WHERE name LIKE ?"
        )
        params: list[Any] = [f"%{query}%"]

        if entity_type:
            sql += " AND entity_type = ?"
            params.append(entity_type)

        sql += " COLLATE NOCASE LIMIT ?"
        params.append(limit)

        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                entity = self._entity_to_dict(row)
                entity["score"] = 1.0
                results.append(entity)
            return results

    # ── Merge ──

    async def merge_entity(
        self,
        entity_type: str,
        match_properties: dict[str, Any],
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        # Try to find existing entity matching all match_properties
        existing_entities = await self.find_entities(entity_type=entity_type)
        for entity in existing_entities:
            if all(entity.get(k) == v for k, v in match_properties.items()):
                # Update existing
                updated = await self.update_entity(entity["id"], properties)
                if updated:
                    return updated

        # No match — create new
        return await self.create_entity(entity_type, properties)

    # ── Ops ──

    async def backup(self, backup_path: str) -> bool:
        db = self._ensure_db()
        await db.commit()  # Flush WAL
        try:
            shutil.copy2(self._db_path, backup_path)
            return True
        except Exception as e:
            logger.error("Backup failed: %s", e)
            return False

    async def health_check(self) -> dict[str, Any]:
        db = self._ensure_db()
        try:
            async with db.execute("SELECT COUNT(*) FROM entities") as cur:
                entity_count = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM edges") as cur:
                edge_count = (await cur.fetchone())[0]
            return {
                "status": "healthy",
                "backend": "sqlite",
                "entity_count": entity_count,
                "edge_count": edge_count,
                "db_path": self._db_path,
            }
        except Exception as e:
            return {"status": "unhealthy", "backend": "sqlite", "error": str(e)}
