# mkg/infrastructure/sqlite/provenance_storage.py
"""SQLite-backed ProvenanceTracker — persistent provenance records.

Stores all pipeline step records, entity origins, and edge origins
in SQLite so they survive process restarts.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import aiosqlite

logger = logging.getLogger(__name__)


class SQLiteProvenanceStorage:
    """Persistent provenance storage backed by SQLite.

    Tables:
        provenance_steps — pipeline step records
        entity_origins — entity → article attribution
        edge_origins — edge → article attribution
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Create tables if they don't exist."""
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS provenance_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL,
                step TEXT NOT NULL,
                inputs_json TEXT NOT NULL DEFAULT '{}',
                outputs_json TEXT NOT NULL DEFAULT '{}',
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS entity_origins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT NOT NULL,
                entity_name TEXT NOT NULL,
                article_id TEXT NOT NULL,
                extraction_tier TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS edge_origins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                edge_id TEXT NOT NULL,
                source_entity TEXT NOT NULL,
                target_entity TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                article_id TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_prov_article ON provenance_steps(article_id);
            CREATE INDEX IF NOT EXISTS idx_eo_entity ON entity_origins(entity_id);
            CREATE INDEX IF NOT EXISTS idx_eo_article ON entity_origins(article_id);
            CREATE INDEX IF NOT EXISTS idx_edg_edge ON edge_origins(edge_id);
        """)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    async def record_step(
        self,
        article_id: str,
        step: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
    ) -> None:
        """Record a pipeline processing step."""
        ts = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "INSERT INTO provenance_steps (article_id, step, inputs_json, outputs_json, timestamp) "
            "VALUES (?, ?, ?, ?, ?)",
            (article_id, step, json.dumps(inputs), json.dumps(outputs), ts),
        )
        await self._db.commit()

    async def get_records(self, article_id: str) -> list[dict[str, Any]]:
        """Get all pipeline step records for an article."""
        cursor = await self._db.execute(
            "SELECT article_id, step, inputs_json, outputs_json, timestamp "
            "FROM provenance_steps WHERE article_id = ? ORDER BY id",
            (article_id,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "article_id": row[0],
                "step": row[1],
                "inputs": json.loads(row[2]),
                "outputs": json.loads(row[3]),
                "timestamp": row[4],
            }
            for row in rows
        ]

    async def record_entity_origin(
        self,
        entity_id: str,
        entity_name: str,
        article_id: str,
        extraction_tier: str,
        confidence: float,
    ) -> None:
        """Record entity origin — which article created it."""
        ts = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "INSERT INTO entity_origins (entity_id, entity_name, article_id, extraction_tier, confidence, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (entity_id, entity_name, article_id, extraction_tier, confidence, ts),
        )
        await self._db.commit()

    async def get_entity_articles(self, entity_id: str) -> list[dict[str, Any]]:
        """Get all articles that contributed to an entity."""
        cursor = await self._db.execute(
            "SELECT entity_id, entity_name, article_id, extraction_tier, confidence, timestamp "
            "FROM entity_origins WHERE entity_id = ? ORDER BY id",
            (entity_id,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "entity_id": row[0],
                "entity_name": row[1],
                "article_id": row[2],
                "extraction_tier": row[3],
                "confidence": row[4],
                "timestamp": row[5],
            }
            for row in rows
        ]

    async def get_article_lineage(self, article_id: str) -> dict[str, Any]:
        """Full lineage for an article — steps, entities, edges."""
        steps = await self.get_records(article_id)

        cursor = await self._db.execute(
            "SELECT entity_id, entity_name, article_id, extraction_tier, confidence, timestamp "
            "FROM entity_origins WHERE article_id = ? ORDER BY id",
            (article_id,),
        )
        entity_rows = await cursor.fetchall()
        entities = [
            {
                "entity_id": r[0], "entity_name": r[1], "article_id": r[2],
                "extraction_tier": r[3], "confidence": r[4], "timestamp": r[5],
            }
            for r in entity_rows
        ]

        cursor = await self._db.execute(
            "SELECT edge_id, source_entity, target_entity, relation_type, article_id, confidence, timestamp "
            "FROM edge_origins WHERE article_id = ? ORDER BY id",
            (article_id,),
        )
        edge_rows = await cursor.fetchall()
        edges = [
            {
                "edge_id": r[0], "source_entity": r[1], "target_entity": r[2],
                "relation_type": r[3], "article_id": r[4], "confidence": r[5],
                "timestamp": r[6],
            }
            for r in edge_rows
        ]

        return {
            "article_id": article_id,
            "steps": steps,
            "entities_created": entities,
            "edges_created": edges,
        }

    async def get_summary(self) -> dict[str, Any]:
        """Aggregate summary for audit."""
        cursor = await self._db.execute(
            "SELECT COUNT(DISTINCT article_id) FROM provenance_steps"
        )
        total_articles = (await cursor.fetchone())[0]

        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM provenance_steps"
        )
        total_steps = (await cursor.fetchone())[0]

        cursor = await self._db.execute(
            "SELECT COUNT(DISTINCT entity_id) FROM entity_origins"
        )
        total_entities = (await cursor.fetchone())[0]

        cursor = await self._db.execute(
            "SELECT COUNT(DISTINCT edge_id) FROM edge_origins"
        )
        total_edges = (await cursor.fetchone())[0]

        return {
            "total_articles_processed": total_articles,
            "total_steps_recorded": total_steps,
            "total_entities_tracked": total_entities,
            "total_edges_tracked": total_edges,
        }
