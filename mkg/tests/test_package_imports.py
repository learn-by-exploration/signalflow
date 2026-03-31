# mkg/tests/test_package_imports.py
"""Tests for package-level imports and exports.

Iterations 36-40: All __init__.py files should export their public API cleanly.
"""

import pytest


class TestPackageImports:
    """Verify all package-level imports work correctly."""

    def test_import_mkg(self):
        import mkg
        assert hasattr(mkg, "__version__")

    def test_import_domain_entities(self):
        from mkg.domain.entities import (
            Article, ArticleStatus,
            Edge, RelationType,
            Entity, EntityType,
            ExtractionResult,
        )
        assert Article is not None
        assert Entity is not None
        assert Edge is not None

    def test_import_domain_interfaces(self):
        from mkg.domain.interfaces import (
            ArticleStorage,
            GraphStorage,
            LLMExtractor,
            ExtractionTier,
        )
        assert GraphStorage is not None
        assert LLMExtractor is not None

    def test_import_infrastructure_in_memory(self):
        from mkg.infrastructure.in_memory import (
            InMemoryGraphStorage,
            InMemoryArticleStorage,
        )
        assert InMemoryGraphStorage is not None
        assert InMemoryArticleStorage is not None

    def test_import_infrastructure_llm(self):
        from mkg.infrastructure.llm import (
            ClaudeExtractor,
            OllamaExtractor,
            RegexExtractor,
        )
        assert RegexExtractor is not None

    def test_entity_types_are_enums(self):
        from mkg.domain.entities import EntityType
        assert "Company" in [e.value for e in EntityType]

    def test_relation_types_are_enums(self):
        from mkg.domain.entities import RelationType
        assert "SUPPLIES_TO" in [e.value for e in RelationType]

    def test_extraction_tiers_are_enums(self):
        from mkg.domain.interfaces import ExtractionTier
        assert len(list(ExtractionTier)) == 3

    def test_all_exports_are_listed(self):
        from mkg.domain import entities
        assert hasattr(entities, "__all__")
        assert len(entities.__all__) >= 5

    def test_version_format(self):
        import mkg
        parts = mkg.__version__.split(".")
        assert len(parts) >= 2  # At least major.minor
