# mkg/infrastructure/persistent/provenance_tracker.py
"""PersistentProvenanceTracker — sync ProvenanceTracker backed by SQLite.

Extends the in-memory ProvenanceTracker with SQLite persistence.
Same sync API as the domain service but data survives restarts.
Uses sqlite3 (not aiosqlite) for synchronous operation.
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

from mkg.domain.services.provenance_tracker import ProvenanceTracker

logger = logging.getLogger(__name__)


class PersistentProvenanceTracker(ProvenanceTracker):
    """ProvenanceTracker that persists records to SQLite.

    Inherits all in-memory behavior from ProvenanceTracker and additionally
    writes every record to a SQLite database. On construction, existing
    records are loaded from disk into the in-memory cache.
    """

    def __init__(self, db_path: str) -> None:
        super().__init__()
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, timeout=30.0)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.executescript("""
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
        self._conn.commit()

        # Load existing records into in-memory cache
        self._load_existing()

    def _load_existing(self) -> None:
        """Load existing records from SQLite into in-memory cache."""
        # Load steps
        cursor = self._conn.execute(
            "SELECT article_id, step, inputs_json, outputs_json, timestamp "
            "FROM provenance_steps ORDER BY id"
        )
        for row in cursor:
            record = {
                "article_id": row[0],
                "step": row[1],
                "inputs": json.loads(row[2]),
                "outputs": json.loads(row[3]),
                "timestamp": row[4],
            }
            self._steps.setdefault(row[0], []).append(record)

        # Load entity origins
        cursor = self._conn.execute(
            "SELECT entity_id, entity_name, article_id, extraction_tier, confidence, timestamp "
            "FROM entity_origins ORDER BY id"
        )
        for row in cursor:
            record = {
                "entity_id": row[0],
                "entity_name": row[1],
                "article_id": row[2],
                "extraction_tier": row[3],
                "confidence": row[4],
                "timestamp": row[5],
            }
            self._entity_origins.setdefault(row[0], []).append(record)

        # Load edge origins
        cursor = self._conn.execute(
            "SELECT edge_id, source_entity, target_entity, relation_type, article_id, confidence, timestamp "
            "FROM edge_origins ORDER BY id"
        )
        for row in cursor:
            self._edge_origins[row[0]] = {
                "edge_id": row[0],
                "source_entity": row[1],
                "target_entity": row[2],
                "relation_type": row[3],
                "article_id": row[4],
                "confidence": row[5],
                "timestamp": row[6],
            }

    def record_step(
        self,
        article_id: str,
        step: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
    ) -> None:
        """Record a pipeline step — persists to SQLite and in-memory."""
        # Call parent for in-memory storage
        super().record_step(article_id, step, inputs, outputs)

        # Get the timestamp from the just-added record
        ts = self._steps[article_id][-1]["timestamp"]

        # Also persist to SQLite
        self._conn.execute(
            "INSERT INTO provenance_steps (article_id, step, inputs_json, outputs_json, timestamp) "
            "VALUES (?, ?, ?, ?, ?)",
            (article_id, step, json.dumps(inputs), json.dumps(outputs), ts),
        )
        self._conn.commit()

    def record_entity_origin(
        self,
        entity_id: str,
        entity_name: str,
        article_id: str,
        extraction_tier: str,
        confidence: float,
    ) -> None:
        """Record entity origin — persists to SQLite and in-memory."""
        super().record_entity_origin(entity_id, entity_name, article_id, extraction_tier, confidence)

        ts = self._entity_origins[entity_id][-1]["timestamp"]

        self._conn.execute(
            "INSERT INTO entity_origins (entity_id, entity_name, article_id, extraction_tier, confidence, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (entity_id, entity_name, article_id, extraction_tier, confidence, ts),
        )
        self._conn.commit()

    def record_edge_origin(
        self,
        edge_id: str,
        source_entity: str,
        target_entity: str,
        relation_type: str,
        article_id: str,
        confidence: float,
    ) -> None:
        """Record edge origin — persists to SQLite and in-memory."""
        super().record_edge_origin(edge_id, source_entity, target_entity, relation_type, article_id, confidence)

        ts = self._edge_origins[edge_id]["timestamp"]

        self._conn.execute(
            "INSERT OR REPLACE INTO edge_origins "
            "(edge_id, source_entity, target_entity, relation_type, article_id, confidence, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (edge_id, source_entity, target_entity, relation_type, article_id, confidence, ts),
        )
        self._conn.commit()

    def get_summary(self) -> dict[str, Any]:
        """Get summary from SQLite for persistent accuracy."""
        cursor = self._conn.execute(
            "SELECT COUNT(DISTINCT article_id) FROM provenance_steps"
        )
        total_articles = cursor.fetchone()[0]

        cursor = self._conn.execute("SELECT COUNT(*) FROM provenance_steps")
        total_steps = cursor.fetchone()[0]

        cursor = self._conn.execute(
            "SELECT COUNT(DISTINCT entity_id) FROM entity_origins"
        )
        total_entities = cursor.fetchone()[0]

        cursor = self._conn.execute(
            "SELECT COUNT(DISTINCT edge_id) FROM edge_origins"
        )
        total_edges = cursor.fetchone()[0]

        # Propagations are still in-memory only
        total_propagations = sum(
            len(props) for props in self._propagations.values()
        )

        return {
            "total_articles_processed": total_articles,
            "total_steps_recorded": total_steps,
            "total_entities_tracked": total_entities,
            "total_edges_tracked": total_edges,
            "total_propagations": total_propagations,
        }

    def close(self) -> None:
        """Close the SQLite connection."""
        if self._conn:
            self._conn.close()
