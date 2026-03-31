# mkg/domain/interfaces/__init__.py
"""Domain interfaces — ports for dependency inversion."""

from mkg.domain.interfaces.article_storage import ArticleStorage
from mkg.domain.interfaces.graph_storage import GraphStorage
from mkg.domain.interfaces.llm_extractor import ExtractionTier, LLMExtractor

__all__ = [
    "ArticleStorage",
    "ExtractionTier",
    "GraphStorage",
    "LLMExtractor",
]