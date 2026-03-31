# mkg/tests/test_claude_extractor.py
"""Tests for ClaudeExtractor — Tier 1 cloud NER/RE via Claude API."""

import pytest

from mkg.domain.interfaces.llm_extractor import ExtractionTier


class TestClaudeExtractor:

    @pytest.fixture
    def extractor(self):
        from mkg.infrastructure.llm.claude_extractor import ClaudeExtractor
        return ClaudeExtractor(api_key="test-key", model="claude-sonnet-4-20250514")

    def test_is_llm_extractor(self):
        from mkg.infrastructure.llm.claude_extractor import ClaudeExtractor
        from mkg.domain.interfaces.llm_extractor import LLMExtractor
        assert issubclass(ClaudeExtractor, LLMExtractor)

    def test_tier_is_1(self, extractor):
        assert extractor.get_tier() == ExtractionTier.TIER_1

    def test_cost_estimate_positive(self, extractor):
        cost = extractor.get_cost_estimate(1000)
        assert cost > 0

    @pytest.mark.asyncio
    async def test_extract_entities_returns_list(self, extractor):
        # Mock the API call
        extractor._call_api = _mock_entity_response
        result = await extractor.extract_entities("TSMC announced record revenue")
        assert isinstance(result, list)
        assert len(result) >= 1
        assert "name" in result[0]
        assert "entity_type" in result[0]

    @pytest.mark.asyncio
    async def test_extract_relations_returns_list(self, extractor):
        extractor._call_api = _mock_relation_response
        entities = [{"name": "TSMC", "entity_type": "Company"}, {"name": "NVIDIA", "entity_type": "Company"}]
        result = await extractor.extract_relations("TSMC supplies chips to NVIDIA", entities)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_extract_all_returns_dict(self, extractor):
        extractor._call_api = _mock_all_response
        result = await extractor.extract_all("TSMC supplies chips to NVIDIA for AI GPUs")
        assert "entities" in result
        assert "relations" in result

    @pytest.mark.asyncio
    async def test_extract_entities_handles_empty_text(self, extractor):
        extractor._call_api = _mock_empty_response
        result = await extractor.extract_entities("")
        assert result == []

    def test_prompt_contains_entity_types(self, extractor):
        prompt = extractor._build_entity_prompt("TSMC announced revenue")
        assert "Company" in prompt
        assert "Person" in prompt


# Mock helpers
async def _mock_entity_response(prompt: str, **kwargs):
    return '{"entities": [{"name": "TSMC", "entity_type": "Company", "confidence": 0.95}]}'

async def _mock_relation_response(prompt: str, **kwargs):
    return '{"relations": [{"source": "TSMC", "target": "NVIDIA", "relation_type": "SUPPLIES_TO", "weight": 0.85, "confidence": 0.9}]}'

async def _mock_all_response(prompt: str, **kwargs):
    return '{"entities": [{"name": "TSMC", "entity_type": "Company", "confidence": 0.95}], "relations": [{"source": "TSMC", "target": "NVIDIA", "relation_type": "SUPPLIES_TO", "weight": 0.85, "confidence": 0.9}]}'

async def _mock_empty_response(prompt: str, **kwargs):
    return '{"entities": [], "relations": []}'
