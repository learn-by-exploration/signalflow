# mkg/domain/services/article_pipeline.py
"""ArticleIngestionPipeline — ingests and tracks articles for NER/RE extraction.

R-IA1 through R-IA5: Article ingestion, validation, status tracking.
"""

import uuid
from typing import Any, Optional

from mkg.domain.entities.article import Article, ArticleStatus


class ArticleIngestionPipeline:
    """Pipeline for ingesting and tracking articles.

    Stores articles in memory with status tracking.
    Articles flow: pending → processing → completed/failed.
    """

    def __init__(self) -> None:
        self._articles: dict[str, Article] = {}

    async def ingest(self, data: dict[str, Any]) -> dict[str, Any]:
        """Ingest a new article into the pipeline."""
        title = data.get("title")
        content = data.get("content")
        if not title:
            raise ValueError("Article must have a title")
        if not content:
            raise ValueError("Article must have content")

        article = Article(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            source=data.get("source", "unknown"),
            url=data.get("url"),
        )
        self._articles[article.id] = article
        return article.to_dict()

    async def get_article(self, article_id: str) -> Optional[dict[str, Any]]:
        """Get an article by ID."""
        article = self._articles.get(article_id)
        return article.to_dict() if article else None

    async def update_status(
        self, article_id: str, status: str
    ) -> dict[str, Any]:
        """Update an article's processing status."""
        article = self._articles.get(article_id)
        if not article:
            raise ValueError(f"Article {article_id} not found")
        article.status = ArticleStatus(status)
        return article.to_dict()

    async def get_pending(self) -> list[dict[str, Any]]:
        """Get all articles with pending status."""
        return await self.get_by_status("pending")

    async def get_by_status(self, status: str) -> list[dict[str, Any]]:
        """Get articles by status."""
        target = ArticleStatus(status)
        return [
            a.to_dict() for a in self._articles.values()
            if a.status == target
        ]

    async def get_stats(self) -> dict[str, int]:
        """Get pipeline statistics."""
        stats: dict[str, int] = {"total": len(self._articles)}
        for status in ArticleStatus:
            stats[status.value] = sum(
                1 for a in self._articles.values() if a.status == status
            )
        return stats
