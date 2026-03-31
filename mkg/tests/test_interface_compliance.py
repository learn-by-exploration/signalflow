# mkg/tests/test_interface_compliance.py
"""Interface compliance tests — verify all implementations satisfy their contracts.

Iterations 26-30: Every abstract method must be implemented, return correct types,
and handle edge cases according to the interface specification.
"""

import inspect
from abc import abstractmethod

import pytest

from mkg.domain.interfaces.graph_storage import GraphStorage
from mkg.domain.interfaces.llm_extractor import LLMExtractor, ExtractionTier
from mkg.domain.interfaces.article_storage import ArticleStorage


class TestGraphStorageCompliance:
    """Verify InMemoryGraphStorage implements all GraphStorage methods."""

    def _get_impl(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        return InMemoryGraphStorage

    def test_is_subclass(self):
        assert issubclass(self._get_impl(), GraphStorage)

    def test_all_abstract_methods_implemented(self):
        cls = self._get_impl()
        abstract_methods = {
            name for name, method in inspect.getmembers(GraphStorage)
            if getattr(method, "__isabstractmethod__", False)
        }
        for method_name in abstract_methods:
            impl = getattr(cls, method_name, None)
            assert impl is not None, f"Missing implementation: {method_name}"
            assert not getattr(impl, "__isabstractmethod__", False), \
                f"Method {method_name} still abstract in implementation"

    def test_all_methods_are_async(self):
        cls = self._get_impl()
        abstract_methods = {
            name for name, method in inspect.getmembers(GraphStorage)
            if getattr(method, "__isabstractmethod__", False)
        }
        for method_name in abstract_methods:
            impl = getattr(cls, method_name)
            assert inspect.iscoroutinefunction(impl), \
                f"Method {method_name} must be async"

    @pytest.mark.asyncio
    async def test_create_entity_returns_dict_with_id(self):
        store = self._get_impl()()
        result = await store.create_entity("Company", {"name": "Test"})
        assert isinstance(result, dict)
        assert "id" in result
        assert result["name"] == "Test"

    @pytest.mark.asyncio
    async def test_get_entity_returns_none_for_missing(self):
        store = self._get_impl()()
        result = await store.get_entity("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_entity_returns_none_for_missing(self):
        store = self._get_impl()()
        result = await store.update_entity("nonexistent", {"name": "X"})
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_entity_returns_false_for_missing(self):
        store = self._get_impl()()
        result = await store.delete_entity("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_find_entities_returns_list(self):
        store = self._get_impl()()
        result = await store.find_entities()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_create_edge_returns_dict_with_id(self):
        store = self._get_impl()()
        e1 = await store.create_entity("Company", {"name": "A"})
        e2 = await store.create_entity("Company", {"name": "B"})
        edge = await store.create_edge(e1["id"], e2["id"], "SUPPLIES_TO",
                                       {"weight": 0.5})
        assert isinstance(edge, dict)
        assert "id" in edge

    @pytest.mark.asyncio
    async def test_get_edge_returns_none_for_missing(self):
        store = self._get_impl()()
        result = await store.get_edge("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_edge_returns_false_for_missing(self):
        store = self._get_impl()()
        result = await store.delete_edge("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_find_edges_returns_list(self):
        store = self._get_impl()()
        result = await store.find_edges()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_neighbors_returns_list(self):
        store = self._get_impl()()
        e1 = await store.create_entity("Company", {"name": "A"})
        result = await store.get_neighbors(e1["id"])
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_subgraph_returns_dict(self):
        store = self._get_impl()()
        e1 = await store.create_entity("Company", {"name": "A"})
        result = await store.get_subgraph(e1["id"])
        assert isinstance(result, dict)
        assert "nodes" in result
        assert "edges" in result

    @pytest.mark.asyncio
    async def test_health_check_returns_dict(self):
        store = self._get_impl()()
        result = await store.health_check()
        assert isinstance(result, dict)
        assert "status" in result or "healthy" in result


class TestLLMExtractorCompliance:
    """Verify all LLMExtractor implementations satisfy the interface."""

    def _get_implementations(self):
        from mkg.infrastructure.llm.regex_extractor import RegexExtractor
        from mkg.infrastructure.llm.claude_extractor import ClaudeExtractor
        from mkg.infrastructure.llm.ollama_extractor import OllamaExtractor
        return [RegexExtractor, ClaudeExtractor, OllamaExtractor]

    def test_all_are_subclasses(self):
        for cls in self._get_implementations():
            assert issubclass(cls, LLMExtractor), f"{cls.__name__} is not a LLMExtractor"

    def test_all_have_extract_entities(self):
        for cls in self._get_implementations():
            assert hasattr(cls, "extract_entities"), f"{cls.__name__} missing extract_entities"
            assert inspect.iscoroutinefunction(getattr(cls, "extract_entities"))

    def test_all_have_extract_relations(self):
        for cls in self._get_implementations():
            assert hasattr(cls, "extract_relations"), f"{cls.__name__} missing extract_relations"
            assert inspect.iscoroutinefunction(getattr(cls, "extract_relations"))

    def test_all_have_extract_all(self):
        for cls in self._get_implementations():
            assert hasattr(cls, "extract_all"), f"{cls.__name__} missing extract_all"
            assert inspect.iscoroutinefunction(getattr(cls, "extract_all"))

    def test_all_have_get_tier(self):
        for cls in self._get_implementations():
            assert hasattr(cls, "get_tier"), f"{cls.__name__} missing get_tier"

    def test_all_have_get_cost_estimate(self):
        for cls in self._get_implementations():
            assert hasattr(cls, "get_cost_estimate"), f"{cls.__name__} missing get_cost_estimate"

    def test_regex_extractor_tier(self):
        from mkg.infrastructure.llm.regex_extractor import RegexExtractor
        ext = RegexExtractor()
        assert ext.get_tier() == ExtractionTier.TIER_3

    def test_regex_extractor_cost_is_zero(self):
        from mkg.infrastructure.llm.regex_extractor import RegexExtractor
        ext = RegexExtractor()
        assert ext.get_cost_estimate(1000) == 0.0

    @pytest.mark.asyncio
    async def test_regex_extract_entities_returns_list(self):
        from mkg.infrastructure.llm.regex_extractor import RegexExtractor
        ext = RegexExtractor()
        result = await ext.extract_entities("TSMC and NVIDIA")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_regex_extract_all_returns_dict(self):
        from mkg.infrastructure.llm.regex_extractor import RegexExtractor
        ext = RegexExtractor()
        result = await ext.extract_all("TSMC supplies to NVIDIA")
        assert isinstance(result, dict)
        assert "entities" in result
        assert "relations" in result


class TestArticleStorageCompliance:
    """Verify InMemoryArticleStorage implements all ArticleStorage methods."""

    def _get_impl(self):
        from mkg.infrastructure.in_memory.article_storage import InMemoryArticleStorage
        return InMemoryArticleStorage

    def test_is_subclass(self):
        assert issubclass(self._get_impl(), ArticleStorage)

    def test_all_abstract_methods_implemented(self):
        cls = self._get_impl()
        abstract_methods = {
            name for name, method in inspect.getmembers(ArticleStorage)
            if getattr(method, "__isabstractmethod__", False)
        }
        for method_name in abstract_methods:
            impl = getattr(cls, method_name, None)
            assert impl is not None, f"Missing implementation: {method_name}"
            assert not getattr(impl, "__isabstractmethod__", False), \
                f"Method {method_name} still abstract in implementation"

    def test_all_methods_are_async(self):
        cls = self._get_impl()
        abstract_methods = {
            name for name, method in inspect.getmembers(ArticleStorage)
            if getattr(method, "__isabstractmethod__", False)
        }
        for method_name in abstract_methods:
            impl = getattr(cls, method_name)
            assert inspect.iscoroutinefunction(impl), \
                f"Method {method_name} must be async"

    @pytest.mark.asyncio
    async def test_store_and_get(self):
        store = self._get_impl()()
        article = await store.store({
            "id": "art-1",
            "title": "Test",
            "content": "Content",
            "status": "pending",
        })
        result = await store.get(article["id"])
        assert result is not None
        assert result["title"] == "Test"

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing(self):
        store = self._get_impl()()
        result = await store.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_returns_false_for_missing(self):
        store = self._get_impl()()
        result = await store.delete("nonexistent")
        assert result is False
