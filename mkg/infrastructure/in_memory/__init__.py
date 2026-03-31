# mkg/infrastructure/in_memory/__init__.py
"""In-memory implementations for testing."""

from mkg.infrastructure.in_memory.article_storage import InMemoryArticleStorage
from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage

__all__ = [
    "InMemoryArticleStorage",
    "InMemoryGraphStorage",
]
