# mkg/infrastructure/in_memory/article_storage.py
"""InMemoryArticleStorage — test double for article persistence.

Implements ArticleStorage using plain Python dicts.
"""

from typing import Any, Optional

from mkg.domain.interfaces.article_storage import ArticleStorage


class InMemoryArticleStorage(ArticleStorage):
    """In-memory article storage for testing."""

    def __init__(self) -> None:
        self._articles: dict[str, dict[str, Any]] = {}

    async def store(self, article: dict[str, Any]) -> dict[str, Any]:
        article_id = article.get("id", str(len(self._articles)))
        stored = dict(article)
        stored["id"] = article_id
        self._articles[article_id] = stored
        return stored

    async def get(self, article_id: str) -> Optional[dict[str, Any]]:
        return self._articles.get(article_id)

    async def update_status(self, article_id: str, status: str) -> Optional[dict[str, Any]]:
        if article_id not in self._articles:
            return None
        self._articles[article_id]["status"] = status
        return self._articles[article_id]

    async def delete(self, article_id: str) -> bool:
        if article_id in self._articles:
            del self._articles[article_id]
            return True
        return False

    async def list_by_status(self, status: str, limit: int = 100) -> list[dict[str, Any]]:
        return [
            a for a in self._articles.values()
            if a.get("status") == status
        ][:limit]

    async def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        query_lower = query.lower()
        results: list[dict[str, Any]] = []
        for article in self._articles.values():
            title = article.get("title", "").lower()
            content = article.get("content", "").lower()
            if query_lower in title or query_lower in content:
                results.append(article)
                if len(results) >= limit:
                    break
        return results

    async def count_by_status(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for article in self._articles.values():
            status = article.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return counts
