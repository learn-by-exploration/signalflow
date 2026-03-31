# mkg/tests/test_regex_extractor.py
"""Tests for RegexExtractor — Tier 3 fallback NER/RE via regex patterns."""

import pytest
from mkg.domain.interfaces.llm_extractor import ExtractionTier


class TestRegexExtractor:

    @pytest.fixture
    def extractor(self):
        from mkg.infrastructure.llm.regex_extractor import RegexExtractor
        return RegexExtractor()

    def test_is_llm_extractor(self):
        from mkg.infrastructure.llm.regex_extractor import RegexExtractor
        from mkg.domain.interfaces.llm_extractor import LLMExtractor
        assert issubclass(RegexExtractor, LLMExtractor)

    def test_tier_is_3(self, extractor):
        assert extractor.get_tier() == ExtractionTier.TIER_3

    def test_cost_estimate_is_zero(self, extractor):
        assert extractor.get_cost_estimate(1000) == 0.0

    @pytest.mark.asyncio
    async def test_extract_company_names(self, extractor):
        text = "TSMC and NVIDIA announced a new partnership for AI chip production"
        result = await extractor.extract_entities(text)
        names = [e["name"] for e in result]
        assert "TSMC" in names
        assert "NVIDIA" in names

    @pytest.mark.asyncio
    async def test_extract_money_amounts(self, extractor):
        text = "The deal is worth $23.5 billion for semiconductor equipment"
        result = await extractor.extract_entities(text)
        # Should extract monetary amounts as entities or metadata
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_extract_returns_confidence(self, extractor):
        text = "Apple Inc. launched the new iPhone 16"
        result = await extractor.extract_entities(text)
        for entity in result:
            assert "confidence" in entity
            assert entity["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_extract_all_returns_dict(self, extractor):
        result = await extractor.extract_all("TSMC supplies chips to NVIDIA")
        assert "entities" in result
        assert "relations" in result

    @pytest.mark.asyncio
    async def test_empty_text_returns_empty(self, extractor):
        result = await extractor.extract_entities("")
        assert result == []
