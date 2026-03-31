# mkg/tests/test_llm_extractor_interface.py
"""Tests for LLMExtractor — abstract interface for NER/RE extraction."""

import inspect
from abc import ABC

import pytest


class TestLLMExtractorInterface:

    def _get_interface(self):
        from mkg.domain.interfaces.llm_extractor import LLMExtractor
        return LLMExtractor

    def test_is_abstract_base_class(self):
        cls = self._get_interface()
        assert issubclass(cls, ABC)

    def test_has_extract_entities_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "extract_entities")
        assert getattr(cls.extract_entities, "__isabstractmethod__", False)

    def test_has_extract_relations_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "extract_relations")
        assert getattr(cls.extract_relations, "__isabstractmethod__", False)

    def test_has_extract_all_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "extract_all")
        assert getattr(cls.extract_all, "__isabstractmethod__", False)

    def test_has_get_tier_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "get_tier")

    def test_has_get_cost_estimate_method(self):
        cls = self._get_interface()
        assert hasattr(cls, "get_cost_estimate")

    def test_all_abstract_methods_are_async(self):
        cls = self._get_interface()
        for name in ["extract_entities", "extract_relations", "extract_all"]:
            method = getattr(cls, name)
            assert inspect.iscoroutinefunction(method), f"{name} must be async"

    def test_extract_entities_signature(self):
        cls = self._get_interface()
        sig = inspect.signature(cls.extract_entities)
        params = list(sig.parameters.keys())
        assert "text" in params

    def test_extract_relations_signature(self):
        cls = self._get_interface()
        sig = inspect.signature(cls.extract_relations)
        params = list(sig.parameters.keys())
        assert "text" in params
        assert "entities" in params

    def test_cannot_instantiate(self):
        cls = self._get_interface()
        with pytest.raises(TypeError):
            cls()


class TestExtractionTier:

    def test_tier_enum_has_three_levels(self):
        from mkg.domain.interfaces.llm_extractor import ExtractionTier
        assert ExtractionTier.TIER_1.value == "tier_1_cloud"
        assert ExtractionTier.TIER_2.value == "tier_2_local"
        assert ExtractionTier.TIER_3.value == "tier_3_regex"
