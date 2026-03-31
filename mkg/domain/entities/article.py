# mkg/domain/entities/article.py
"""Article domain model for the ingestion pipeline.

Represents a news article being processed through the NER/RE extraction pipeline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ArticleStatus(Enum):
    """Processing status of an article in the pipeline."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class Article:
    """Domain model for a news article."""

    __slots__ = (
        "id", "title", "content", "source", "url",
        "published_at", "status", "metadata",
        "created_at", "updated_at",
    )

    def __init__(
        self,
        id: str,
        title: str,
        content: str,
        source: str,
        url: Optional[str] = None,
        published_at: Optional[datetime] = None,
        status: ArticleStatus = ArticleStatus.PENDING,
        metadata: Optional[dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        if not title:
            raise ValueError("Article title cannot be empty")
        if not content:
            raise ValueError("Article content cannot be empty")

        self.id = id
        self.title = title
        self.content = content
        self.source = source
        self.url = url
        self.published_at = published_at
        self.status = status
        self.metadata = metadata or {}
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "url": self.url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "status": self.status.value,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Article:
        """Deserialize from a plain dict."""
        published_at = data.get("published_at")
        if isinstance(published_at, str):
            published_at = datetime.fromisoformat(published_at)
        status = ArticleStatus(data["status"]) if "status" in data else ArticleStatus.PENDING
        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            source=data.get("source", "unknown"),
            url=data.get("url"),
            published_at=published_at,
            status=status,
            metadata=data.get("metadata", {}),
        )
