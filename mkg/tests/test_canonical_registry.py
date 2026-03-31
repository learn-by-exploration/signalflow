# mkg/tests/test_canonical_registry.py
"""Tests for CanonicalEntityRegistry — entity dedup via canonical name resolution.

R-KG7: Entity dedup via MERGE on insert. Maps aliases/variants to canonical names.
"""

import pytest

from mkg.domain.entities.node import EntityType


class TestCanonicalNameNormalization:
    """Test canonical name generation from raw text."""

    def test_normalize_simple_name(self):
        from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
        registry = CanonicalEntityRegistry()
        assert registry.normalize("TSMC") == "TSMC"

    def test_normalize_strips_whitespace(self):
        from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
        registry = CanonicalEntityRegistry()
        assert registry.normalize("  TSMC  ") == "TSMC"

    def test_normalize_uppercases(self):
        from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
        registry = CanonicalEntityRegistry()
        assert registry.normalize("tsmc") == "TSMC"

    def test_normalize_removes_legal_suffixes(self):
        from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
        registry = CanonicalEntityRegistry()
        assert registry.normalize("NVIDIA Corporation") == "NVIDIA"

    def test_normalize_removes_inc(self):
        from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
        registry = CanonicalEntityRegistry()
        assert registry.normalize("Apple Inc.") == "APPLE"

    def test_normalize_removes_ltd(self):
        from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
        registry = CanonicalEntityRegistry()
        assert registry.normalize("Samsung Electronics Co., Ltd.") == "SAMSUNG ELECTRONICS"

    def test_normalize_removes_limited(self):
        from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
        registry = CanonicalEntityRegistry()
        assert registry.normalize("Reliance Industries Limited") == "RELIANCE INDUSTRIES"


class TestAliasMapping:
    """Test alias registration and resolution."""

    @pytest.fixture
    def registry(self):
        from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
        return CanonicalEntityRegistry()

    def test_register_alias(self, registry):
        registry.register_alias("Taiwan Semiconductor Manufacturing Company", "TSMC")
        assert registry.resolve("Taiwan Semiconductor Manufacturing Company") == "TSMC"

    def test_resolve_unknown_returns_normalized(self, registry):
        result = registry.resolve("Unknown Company Inc.")
        assert result == "UNKNOWN COMPANY"

    def test_register_multiple_aliases(self, registry):
        registry.register_alias("台積電", "TSMC")
        registry.register_alias("Taiwan Semiconductor", "TSMC")
        registry.register_alias("TSM", "TSMC")
        assert registry.resolve("台積電") == "TSMC"
        assert registry.resolve("Taiwan Semiconductor") == "TSMC"
        assert registry.resolve("TSM") == "TSMC"

    def test_resolve_is_case_insensitive(self, registry):
        registry.register_alias("nvidia", "NVIDIA")
        assert registry.resolve("NVIDIA") == "NVIDIA"
        assert registry.resolve("nvidia") == "NVIDIA"

    def test_get_all_aliases_for_canonical(self, registry):
        registry.register_alias("台積電", "TSMC")
        registry.register_alias("Taiwan Semiconductor", "TSMC")
        aliases = registry.get_aliases("TSMC")
        assert "台積電" in aliases
        assert "Taiwan Semiconductor" in aliases


class TestMergeOrCreate:
    """Test the merge-or-create pattern for entity dedup."""

    @pytest.fixture
    async def registry_with_storage(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
        from mkg.domain.services.entity_service import EntityService
        store = InMemoryGraphStorage()
        svc = EntityService(store)
        registry = CanonicalEntityRegistry()
        return registry, svc, store

    @pytest.mark.asyncio
    async def test_merge_creates_new_when_no_match(self, registry_with_storage):
        registry, svc, store = registry_with_storage
        entity = await registry.merge_or_create(
            storage=store,
            entity_type=EntityType.COMPANY,
            name="TSMC",
        )
        assert entity is not None
        assert entity["canonical_name"] == "TSMC"

    @pytest.mark.asyncio
    async def test_merge_returns_existing_when_matches(self, registry_with_storage):
        registry, svc, store = registry_with_storage
        # Without alias, same normalized name should still merge
        first = await registry.merge_or_create(
            storage=store,
            entity_type=EntityType.COMPANY,
            name="NVIDIA Corporation",
        )
        second = await registry.merge_or_create(
            storage=store,
            entity_type=EntityType.COMPANY,
            name="NVIDIA Corp.",
        )
        # Both normalize to "NVIDIA" so should be same entity
        assert first["id"] == second["id"]

    @pytest.mark.asyncio
    async def test_merge_uses_alias_resolution(self, registry_with_storage):
        registry, svc, store = registry_with_storage
        registry.register_alias("Taiwan Semiconductor Manufacturing Company", "TSMC")
        first = await registry.merge_or_create(
            storage=store,
            entity_type=EntityType.COMPANY,
            name="TSMC",
        )
        second = await registry.merge_or_create(
            storage=store,
            entity_type=EntityType.COMPANY,
            name="Taiwan Semiconductor Manufacturing Company",
        )
        assert first["id"] == second["id"]  # Same entity

    @pytest.mark.asyncio
    async def test_merge_with_additional_properties(self, registry_with_storage):
        registry, svc, store = registry_with_storage
        entity = await registry.merge_or_create(
            storage=store,
            entity_type=EntityType.COMPANY,
            name="NVIDIA",
            properties={"ticker": "NVDA", "sector": "Semiconductors"},
        )
        assert entity["ticker"] == "NVDA"


class TestBuiltinAliases:
    """Test that common aliases are pre-registered."""

    def test_has_semiconductor_aliases(self):
        from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
        registry = CanonicalEntityRegistry(load_defaults=True)
        assert registry.resolve("Taiwan Semiconductor Manufacturing Company") == "TSMC"

    def test_has_tech_company_aliases(self):
        from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
        registry = CanonicalEntityRegistry(load_defaults=True)
        assert registry.resolve("Alphabet Inc.") == "ALPHABET"
