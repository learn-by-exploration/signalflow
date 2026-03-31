# mkg/tests/test_extraction_result.py
"""Tests for ExtractionResult — structured output from the extraction pipeline."""

import pytest


class TestExtractionResult:

    def test_create_result(self):
        from mkg.domain.entities.extraction_result import ExtractionResult
        result = ExtractionResult(
            article_id="art-001",
            extractor_tier="tier_1_cloud",
            entities=[{"name": "TSMC", "entity_type": "Company", "confidence": 0.95}],
            relations=[{"source": "TSMC", "target": "NVIDIA", "relation_type": "SUPPLIES_TO", "weight": 0.85, "confidence": 0.9}],
        )
        assert result.article_id == "art-001"
        assert len(result.entities) == 1
        assert len(result.relations) == 1

    def test_result_has_metadata(self):
        from mkg.domain.entities.extraction_result import ExtractionResult
        result = ExtractionResult(
            article_id="art-001",
            extractor_tier="tier_1_cloud",
            entities=[], relations=[],
            metadata={"tokens_used": 500, "cost_usd": 0.002},
        )
        assert result.metadata["tokens_used"] == 500

    def test_result_to_dict(self):
        from mkg.domain.entities.extraction_result import ExtractionResult
        result = ExtractionResult(
            article_id="art-001",
            extractor_tier="tier_1_cloud",
            entities=[{"name": "TSMC", "entity_type": "Company", "confidence": 0.95}],
            relations=[],
        )
        d = result.to_dict()
        assert d["article_id"] == "art-001"
        assert d["extractor_tier"] == "tier_1_cloud"
        assert d["entity_count"] == 1

    def test_result_from_dict(self):
        from mkg.domain.entities.extraction_result import ExtractionResult
        d = {
            "article_id": "art-001",
            "extractor_tier": "tier_1_cloud",
            "entities": [{"name": "TSMC", "entity_type": "Company"}],
            "relations": [],
        }
        result = ExtractionResult.from_dict(d)
        assert result.article_id == "art-001"

    def test_result_entity_count(self):
        from mkg.domain.entities.extraction_result import ExtractionResult
        result = ExtractionResult(
            article_id="art-001", extractor_tier="tier_1_cloud",
            entities=[{"name": "A"}, {"name": "B"}, {"name": "C"}],
            relations=[],
        )
        assert result.entity_count == 3

    def test_result_relation_count(self):
        from mkg.domain.entities.extraction_result import ExtractionResult
        result = ExtractionResult(
            article_id="art-001", extractor_tier="tier_1_cloud",
            entities=[], relations=[{"source": "A", "target": "B"}],
        )
        assert result.relation_count == 1

    def test_result_is_empty(self):
        from mkg.domain.entities.extraction_result import ExtractionResult
        result = ExtractionResult(
            article_id="art-001", extractor_tier="tier_1_cloud",
            entities=[], relations=[],
        )
        assert result.is_empty is True

    def test_result_not_empty(self):
        from mkg.domain.entities.extraction_result import ExtractionResult
        result = ExtractionResult(
            article_id="art-001", extractor_tier="tier_1_cloud",
            entities=[{"name": "TSMC"}], relations=[],
        )
        assert result.is_empty is False
