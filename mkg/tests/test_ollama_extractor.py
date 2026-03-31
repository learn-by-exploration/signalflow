# mkg/tests/test_ollama_extractor.py
"""Tests for OllamaExtractor — Tier 2 local NER/RE via Ollama."""

import pytest
from mkg.domain.interfaces.llm_extractor import ExtractionTier


class TestOllamaExtractor:

    @pytest.fixture
    def extractor(self):
        from mkg.infrastructure.llm.ollama_extractor import OllamaExtractor
        return OllamaExtractor(model="llama3.1:8b", base_url="http://localhost:11434")

    def test_is_llm_extractor(self):
        from mkg.infrastructure.llm.ollama_extractor import OllamaExtractor
        from mkg.domain.interfaces.llm_extractor import LLMExtractor
        assert issubclass(OllamaExtractor, LLMExtractor)

    def test_tier_is_2(self, extractor):
        assert extractor.get_tier() == ExtractionTier.TIER_2

    def test_cost_estimate_is_zero(self, extractor):
        assert extractor.get_cost_estimate(1000) == 0.0

    @pytest.mark.asyncio
    async def test_extract_entities_returns_list(self, extractor):
        extractor._call_api = _mock_response
        result = await extractor.extract_entities("TSMC announced record revenue")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_extract_all_returns_dict(self, extractor):
        extractor._call_api = _mock_all_response
        result = await extractor.extract_all("TSMC supplies NVIDIA")
        assert "entities" in result
        assert "relations" in result

async def _mock_response(prompt, **kwargs):
    return '{"entities": [{"name": "TSMC", "entity_type": "Company", "confidence": 0.8}]}'

async def _mock_all_response(prompt, **kwargs):
    return '{"entities": [{"name": "TSMC", "entity_type": "Company", "confidence": 0.8}], "relations": []}'
