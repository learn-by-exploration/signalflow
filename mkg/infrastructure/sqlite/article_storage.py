# mkg/infrastructure/sqlite/article_storage.py
"""SQLiteArticleStorage — persistent article storage via aiosqlite.

Implements the ArticleStorage interface using SQLite for persistence.
"""

import json
import logging
from typing import Any, Optional

import aiosqlite

from mkg.domain.interfaces.article_storage import ArticleStorage

logger = logging.getLogger(__name__)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'unknown',
    url TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    published_at TEXT,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
"""


class SQLiteArticleStorage(ArticleStorage):
    """Persistent article storage backed by SQLite via aiosqlite."""

    def __init__(self, db_path: str = "mkg_articles.db") -> None:
        self._db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Open database and create schema."""
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.executescript(_SCHEMA_SQL)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    def _ensure_db(self) -> aiosqlite.Connection:
        if not self._db:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._db

    def _row_to_dict(self, row: tuple) -> dict[str, Any]:
        metadata = json.loads(row[7]) if row[7] else {}
        return {
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "source": row[3],
            "url": row[4],
            "status": row[5],
            "published_at": row[6],
            "metadata": metadata,
        }

    async def store(self, article: dict[str, Any]) -> dict[str, Any]:
        db = self._ensure_db()
        article_id = article.get("id", "")
        metadata_json = json.dumps(article.get("metadata", {}))

        await db.execute(
            "INSERT OR REPLACE INTO articles "
            "(id, title, content, source, url, status, published_at, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                article_id,
                article.get("title", ""),
                article.get("content", ""),
                article.get("source", "unknown"),
                article.get("url"),
                article.get("status", "pending"),
                article.get("published_at"),
                metadata_json,
            ),
        )
        await db.commit()
        return {**article, "id": article_id}

    async def get(self, article_id: str) -> Optional[dict[str, Any]]:
        db = self._ensure_db()
        async with db.execute(
            "SELECT id, title, content, source, url, status, published_at, metadata "
            "FROM articles WHERE id = ?",
            (article_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return self._row_to_dict(row) if row else None

    async def update_status(
        self, article_id: str, status: str
    ) -> Optional[dict[str, Any]]:
        db = self._ensure_db()
        cursor = await db.execute(
            "UPDATE articles SET status = ? WHERE id = ?",
            (status, article_id),
        )
        await db.commit()
        if cursor.rowcount == 0:
            return None
        return await self.get(article_id)

    async def delete(self, article_id: str) -> bool:
        db = self._ensure_db()
        cursor = await db.execute(
            "DELETE FROM articles WHERE id = ?", (article_id,)
        )
        await db.commit()
        return cursor.rowcount > 0

    async def list_by_status(
        self, status: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        db = self._ensure_db()
        async with db.execute(
            "SELECT id, title, content, source, url, status, published_at, metadata "
            "FROM articles WHERE status = ? LIMIT ?",
            (status, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    async def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        db = self._ensure_db()
        async with db.execute(
            "SELECT id, title, content, source, url, status, published_at, metadata "
            "FROM articles WHERE title LIKE ? OR content LIKE ? COLLATE NOCASE LIMIT ?",
            (f"%{query}%", f"%{query}%", limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    async def count_by_status(self) -> dict[str, int]:
        db = self._ensure_db()
        async with db.execute(
            "SELECT status, COUNT(*) FROM articles GROUP BY status"
        ) as cursor:
            rows = await cursor.fetchall()
            return {row[0]: row[1] for row in rows}
