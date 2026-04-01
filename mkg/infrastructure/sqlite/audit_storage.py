# mkg/infrastructure/sqlite/audit_storage.py
"""SQLite-backed AuditLogger — persistent audit trail.

Stores all audit entries in SQLite so they survive process restarts.
Provides the same query interface as the in-memory AuditLogger.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import aiosqlite

logger = logging.getLogger(__name__)


class SQLiteAuditStorage:
    """Persistent audit storage backed by SQLite.

    Schema:
        audit_log(id, action, actor, target_id, target_type, details_json, timestamp)
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Create tables if they don't exist."""
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("""
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
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action)"
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_log(target_id)"
        )
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    async def log(
        self,
        action: Any,
        actor: str,
        target_id: str,
        target_type: str,
        details: dict[str, Any],
    ) -> dict[str, Any]:
        """Append an audit entry to persistent storage."""
        action_str = action.value if hasattr(action, "value") else str(action)
        ts = datetime.now(timezone.utc).isoformat()
        details_json = json.dumps(details)

        await self._db.execute(
            "INSERT INTO audit_log (action, actor, target_id, target_type, details_json, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (action_str, actor, target_id, target_type, details_json, ts),
        )
        await self._db.commit()

        entry = {
            "action": action_str,
            "actor": actor,
            "target_id": target_id,
            "target_type": target_type,
            "details": details,
            "timestamp": ts,
        }
        return entry

    async def get_entries(
        self,
        action: Any = None,
        target_id: str | None = None,
        actor: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Query audit entries with optional filters."""
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

        cursor = await self._db.execute(query, params)
        rows = await cursor.fetchall()

        return [
            {
                "action": row[0],
                "actor": row[1],
                "target_id": row[2],
                "target_type": row[3],
                "details": json.loads(row[4]),
                "timestamp": row[5],
            }
            for row in rows
        ]

    async def export_report(self) -> dict[str, Any]:
        """Generate audit summary report."""
        cursor = await self._db.execute("SELECT COUNT(*) FROM audit_log")
        total = (await cursor.fetchone())[0]

        cursor = await self._db.execute(
            "SELECT action, COUNT(*) FROM audit_log GROUP BY action"
        )
        breakdown = {row[0]: row[1] for row in await cursor.fetchall()}

        return {
            "total_entries": total,
            "actions_breakdown": breakdown,
        }
