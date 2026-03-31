# mkg/domain/entities/__init__.py
"""Domain entities — value objects and data models."""

from mkg.domain.entities.article import Article, ArticleStatus
from mkg.domain.entities.edge import Edge, RelationType
from mkg.domain.entities.extraction_result import ExtractionResult
from mkg.domain.entities.node import Entity, EntityType

__all__ = [
    "Article",
    "ArticleStatus",
    "Edge",
    "Entity",
    "EntityType",
    "ExtractionResult",
    "RelationType",
]