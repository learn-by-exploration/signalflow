# mkg/infrastructure/persistent/audit_logger.py
"""PersistentAuditLogger — sync AuditLogger backed by SQLite.

Extends the in-memory AuditLogger with SQLite persistence.
Same sync API as the domain service but data survives restarts.
Uses sqlite3 (not aiosqlite) for synchronous operation.
"""

import json
import logging
import sqlite3
from typing import Any, Optional

from mkg.domain.services.audit_logger import AuditAction, AuditLogger

logger = logging.getLogger(__name__)


class PersistentAuditLogger(AuditLogger):
    """AuditLogger that persists entries to SQLite.

    Inherits all in-memory behavior from AuditLogger and additionally
    writes every entry to a SQLite database. On construction, existing
    entries are loaded from disk into the in-memory cache.
    """

    def __init__(self, db_path: str) -> None:
        super().__init__()
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, timeout=30.0)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                target_id TEXT NOT NULL,
                target_type TEXT NOT NULL,
                details_json TEXT NOT NULL DEFAULT '{}',
                timestamp TEXT NOT NULL
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_log(target_id)"
        )
        self._conn.commit()

        # Load existing entries into in-memory cache
        self._load_existing()

    def _load_existing(self) -> None:
        """Load existing entries from SQLite into in-memory cache."""
        cursor = self._conn.execute(
            "SELECT action, actor, target_id, target_type, details_json, timestamp "
            "FROM audit_log ORDER BY id"
        )
        for row in cursor:
            entry = {
                "action": row[0],
                "actor": row[1],
                "target_id": row[2],
                "target_type": row[3],
                "details": json.loads(row[4]),
                "timestamp": row[5],
            }
            self._entries.append(entry)

    def log(
        self,
        action: AuditAction,
        actor: str,
        target_id: str,
        target_type: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Log an audit entry — persists to SQLite and in-memory."""
        # Call parent to get the in-memory entry
        entry = super().log(action, actor, target_id, target_type, details)

        # Also persist to SQLite
        action_str = action.value if hasattr(action, "value") else str(action)
        details_json = json.dumps(details or {})
        self._conn.execute(
            "INSERT INTO audit_log (action, actor, target_id, target_type, details_json, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (action_str, actor, target_id, target_type, details_json, entry["timestamp"]),
        )
        self._conn.commit()

        return entry

    def get_entries(
        self,
        action: Optional[AuditAction] = None,
        target_id: Optional[str] = None,
        actor: Optional[str] = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Query entries from SQLite for persistence-safe reads."""
        query = "SELECT action, actor, target_id, target_type, details_json, timestamp FROM audit_log WHERE 1=1"
        params: list[Any] = []

        if action is not None:
            action_str = action.value if hasattr(action, "value") else str(action)
            query += " AND action = ?"
            params.append(action_str)
        if target_id is not None:
            query += " AND target_id = ?"
            params.append(target_id)
        if actor is not None:
            query += " AND actor = ?"
            params.append(actor)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        cursor = self._conn.execute(query, params)
        return [
            {
                "action": row[0],
                "actor": row[1],
                "target_id": row[2],
                "target_type": row[3],
                "details": json.loads(row[4]),
                "timestamp": row[5],
            }
            for row in cursor
        ]

    def export_report(self) -> dict[str, Any]:
        """Generate audit summary from SQLite."""
        cursor = self._conn.execute("SELECT COUNT(*) FROM audit_log")
        total = cursor.fetchone()[0]

        cursor = self._conn.execute(
            "SELECT action, COUNT(*) FROM audit_log GROUP BY action"
        )
        breakdown = {row[0]: row[1] for row in cursor}

        return {
            "total_entries": total,
            "actions_breakdown": breakdown,
        }

    def close(self) -> None:
        """Close the SQLite connection."""
        if self._conn:
            self._conn.close()
