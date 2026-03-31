# mkg/tests/test_hallucination_verifier.py
"""Tests for HallucinationVerifier — validates extraction results against source text."""

import pytest


class TestHallucinationVerifier:

    @pytest.fixture
    def verifier(self):
        from mkg.domain.services.hallucination_verifier import HallucinationVerifier
        return HallucinationVerifier()

    def test_entity_present_in_text(self, verifier):
        text = "TSMC announced record revenue of $23.5 billion"
        entity = {"name": "TSMC", "entity_type": "Company", "confidence": 0.95}
        assert verifier.verify_entity(entity, text) is True

    def test_entity_not_in_text(self, verifier):
        text = "TSMC announced record revenue"
        entity = {"name": "Samsung", "entity_type": "Company", "confidence": 0.95}
        assert verifier.verify_entity(entity, text) is False

    def test_entity_case_insensitive(self, verifier):
        text = "tsmc announced record revenue"
        entity = {"name": "TSMC", "entity_type": "Company", "confidence": 0.95}
        assert verifier.verify_entity(entity, text) is True

    def test_relation_source_in_text(self, verifier):
        text = "TSMC supplies advanced chips to NVIDIA for GPU production"
        relation = {"source": "TSMC", "target": "NVIDIA", "relation_type": "SUPPLIES_TO"}
        assert verifier.verify_relation(relation, text) is True

    def test_relation_missing_entity_fails(self, verifier):
        text = "TSMC supplies chips to customers"
        relation = {"source": "TSMC", "target": "AMD", "relation_type": "SUPPLIES_TO"}
        assert verifier.verify_relation(relation, text) is False

    def test_verify_result_filters_hallucinations(self, verifier):
        text = "TSMC and NVIDIA announced a new AI chip partnership"
        result = {
            "entities": [
                {"name": "TSMC", "entity_type": "Company", "confidence": 0.95},
                {"name": "NVIDIA", "entity_type": "Company", "confidence": 0.90},
                {"name": "Samsung", "entity_type": "Company", "confidence": 0.80},
            ],
            "relations": [
                {"source": "TSMC", "target": "NVIDIA", "relation_type": "SUPPLIES_TO"},
                {"source": "TSMC", "target": "Samsung", "relation_type": "COMPETES_WITH"},
            ],
        }
        verified = verifier.verify_result(result, text)
        assert len(verified["entities"]) == 2  # Samsung filtered out
        assert len(verified["relations"]) == 1  # Samsung relation filtered

    def test_verify_returns_stats(self, verifier):
        text = "TSMC announced revenue"
        result = {
            "entities": [
                {"name": "TSMC", "entity_type": "Company"},
                {"name": "Intel", "entity_type": "Company"},
            ],
            "relations": [],
        }
        verified = verifier.verify_result(result, text)
        assert verified["stats"]["entities_total"] == 2
        assert verified["stats"]["entities_verified"] == 1
        assert verified["stats"]["entities_rejected"] == 1

    def test_verify_empty_result(self, verifier):
        verified = verifier.verify_result({"entities": [], "relations": []}, "text")
        assert verified["entities"] == []
        assert verified["relations"] == []
        assert verified["stats"]["entities_total"] == 0

    def test_verify_entity_empty_name(self, verifier):
        text = "TSMC makes chips"
        entity = {"name": "", "entity_type": "Company"}
        assert verifier.verify_entity(entity, text) is True  # empty string in text

    def test_verify_entity_partial_match(self, verifier):
        text = "TSMC is the largest chipmaker"
        entity = {"name": "TSM", "entity_type": "Company"}
        # TSM is a substring of TSMC
        assert verifier.verify_entity(entity, text) is True

    def test_relation_with_hallucinated_entity_filtered(self, verifier):
        text = "TSMC and NVIDIA are chip companies"
        result = {
            "entities": [
                {"name": "TSMC", "entity_type": "Company"},
                {"name": "NVIDIA", "entity_type": "Company"},
            ],
            "relations": [
                {"source": "TSMC", "target": "Samsung", "relation_type": "X"},  # Samsung not in text
            ],
        }
        verified = verifier.verify_result(result, text)
        assert len(verified["relations"]) == 0

    def test_verify_result_preserves_order(self, verifier):
        text = "Apple Microsoft Google"
        result = {
            "entities": [
                {"name": "Apple"},
                {"name": "Microsoft"},
                {"name": "Google"},
            ],
            "relations": [],
        }
        verified = verifier.verify_result(result, text)
        names = [e["name"] for e in verified["entities"]]
        assert names == ["Apple", "Microsoft", "Google"]

    def test_relation_requires_both_entities_verified(self, verifier):
        """Relation source/target must both be in verified entity set."""
        text = "TSMC and Intel partnership with NVIDIA"
        result = {
            "entities": [
                {"name": "TSMC"},
                {"name": "Intel"},
            ],
            "relations": [
                # Both in text but NVIDIA entity not extracted
                {"source": "TSMC", "target": "NVIDIA", "relation_type": "X"},
            ],
        }
        verified = verifier.verify_result(result, text)
        assert len(verified["relations"]) == 0  # NVIDIA not in verified entities set
