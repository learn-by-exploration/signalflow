# mkg/domain/interfaces/article_storage.py
"""ArticleStorage — abstract interface for persistent article storage.

R-AS1: Port interface for article persistence, decoupled from
infrastructure (PostgreSQL, in-memory, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class ArticleStorage(ABC):
    """Abstract interface for article persistence."""

    @abstractmethod
    async def store(self, article: dict[str, Any]) -> dict[str, Any]:
        """Store an article."""
        ...

    @abstractmethod
    async def get(self, article_id: str) -> Optional[dict[str, Any]]:
        """Get an article by ID."""
        ...

    @abstractmethod
    async def update_status(self, article_id: str, status: str) -> Optional[dict[str, Any]]:
        """Update an article's processing status."""
        ...

    @abstractmethod
    async def delete(self, article_id: str) -> bool:
        """Delete an article."""
        ...

    @abstractmethod
    async def list_by_status(self, status: str, limit: int = 100) -> list[dict[str, Any]]:
        """List articles by status."""
        ...

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search articles by keyword."""
        ...

    @abstractmethod
    async def count_by_status(self) -> dict[str, int]:
        """Count articles grouped by status."""
        ...
