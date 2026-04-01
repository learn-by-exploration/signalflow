# mkg/tests/test_provenance_tracker.py
"""Tests for ProvenanceTracker — article-to-signal traceability.

Iterations 1-5: Every pipeline step must be traceable. Given any output
(entity, edge, signal enrichment), you must be able to trace back to
which article(s) produced it and through which pipeline steps.
"""

import pytest
from datetime import datetime, timezone


class TestProvenanceRecording:
    """Recording pipeline steps with inputs/outputs."""

    def test_record_step(self):
        from mkg.domain.services.provenance_tracker import ProvenanceTracker

        pt = ProvenanceTracker()
        pt.record_step(
            article_id="art-001",
            step="extraction",
            inputs={"text_length": 500, "tier": "tier_1_cloud"},
            outputs={"entities_count": 3, "relations_count": 2},
        )
        records = pt.get_records(article_id="art-001")
        assert len(records) == 1
        assert records[0]["step"] == "extraction"
        assert records[0]["article_id"] == "art-001"

    def test_record_multiple_steps(self):
        from mkg.domain.services.provenance_tracker import ProvenanceTracker

        pt = ProvenanceTracker()
        pt.record_step("art-001", "dedup", {"url": "https://x.com"}, {"is_duplicate": False})
        pt.record_step("art-001", "extraction", {"tier": "tier_1"}, {"entities_count": 4})
        pt.record_step("art-001", "verification", {"entities_count": 4}, {"verified_count": 3})
        pt.record_step("art-001", "mutation", {"verified_count": 3}, {"created": 3, "updated": 0})
        records = pt.get_records(article_id="art-001")
        assert len(records) == 4

    def test_records_have_timestamps(self):
        from mkg.domain.services.provenance_tracker import ProvenanceTracker

        pt = ProvenanceTracker()
        pt.record_step("art-001", "extraction", {}, {})
        records = pt.get_records(article_id="art-001")
        assert "timestamp" in records[0]

    def test_record_entity_provenance(self):
        """Track which article created which entity."""
        from mkg.domain.services.provenance_tracker import ProvenanceTracker

        pt = ProvenanceTracker()
        pt.record_entity_origin(
            entity_id="nvidia-001",
            entity_name="NVIDIA",
            article_id="art-001",
            extraction_tier="tier_1_cloud",
            confidence=0.95,
        )
        origin = pt.get_entity_origin("nvidia-001")
        assert origin is not None
        assert origin["article_id"] == "art-001"
        assert origin["extraction_tier"] == "tier_1_cloud"

    def test_record_edge_provenance(self):
        """Track which article created which edge."""
        from mkg.domain.services.provenance_tracker import ProvenanceTracker

        pt = ProvenanceTracker()
        pt.record_edge_origin(
            edge_id="edge-001",
            source_entity="TSMC",
            target_entity="NVIDIA",
            relation_type="SUPPLIES_TO",
            article_id="art-001",
            confidence=0.9,
        )
        origin = pt.get_edge_origin("edge-001")
        assert origin is not None
        assert origin["article_id"] == "art-001"
        assert origin["relation_type"] == "SUPPLIES_TO"


class TestLineageTraversal:
    """Trace from signal enrichment back to source articles."""

    def test_get_article_lineage(self):
        """Full lineage: article → entities → edges created."""
        from mkg.domain.services.provenance_tracker import ProvenanceTracker

        pt = ProvenanceTracker()
        # Record full pipeline
        pt.record_step("art-001", "dedup", {}, {"is_duplicate": False})
        pt.record_step("art-001", "extraction", {}, {"entities_count": 2})
        pt.record_step("art-001", "verification", {}, {"verified_count": 2})
        pt.record_step("art-001", "mutation", {}, {"entities_created": 2, "edges_created": 1})

        pt.record_entity_origin("nvidia-001", "NVIDIA", "art-001", "tier_1_cloud", 0.95)
        pt.record_entity_origin("tsmc-001", "TSMC", "art-001", "tier_1_cloud", 0.92)
        pt.record_edge_origin("edge-001", "TSMC", "NVIDIA", "SUPPLIES_TO", "art-001", 0.9)

        lineage = pt.get_article_lineage("art-001")
        assert lineage["article_id"] == "art-001"
        assert len(lineage["steps"]) == 4
        assert len(lineage["entities_created"]) == 2
        assert len(lineage["edges_created"]) == 1

    def test_get_entity_articles(self):
        """Given an entity, find all articles that contributed to it."""
        from mkg.domain.services.provenance_tracker import ProvenanceTracker

        pt = ProvenanceTracker()
        pt.record_entity_origin("nvidia-001", "NVIDIA", "art-001", "tier_1_cloud", 0.95)
        pt.record_entity_origin("nvidia-001", "NVIDIA", "art-002", "tier_3_regex", 0.8)

        articles = pt.get_entity_articles("nvidia-001")
        assert len(articles) == 2
        assert {a["article_id"] for a in articles} == {"art-001", "art-002"}

    def test_get_propagation_provenance(self):
        """Record which propagation produced which impacts."""
        from mkg.domain.services.provenance_tracker import ProvenanceTracker

        pt = ProvenanceTracker()
        pt.record_propagation(
            trigger_entity_id="tsmc-001",
            trigger_event="fab fire",
            article_id="art-001",
            impacts_count=5,
            max_depth=3,
            chains_count=4,
        )
        prop = pt.get_propagation_records(trigger_entity_id="tsmc-001")
        assert len(prop) == 1
        assert prop[0]["trigger_event"] == "fab fire"
        assert prop[0]["impacts_count"] == 5


class TestComplianceMetadata:
    """Compliance metadata attached to provenance."""

    def test_record_includes_data_source_disclosure(self):
        """Every provenance record must track the data source."""
        from mkg.domain.services.provenance_tracker import ProvenanceTracker

        pt = ProvenanceTracker()
        pt.record_step(
            "art-001", "extraction",
            inputs={"source": "reuters", "url": "https://reuters.com/article"},
            outputs={"entities_count": 2},
        )
        records = pt.get_records(article_id="art-001")
        assert records[0]["inputs"]["source"] == "reuters"

    def test_get_data_sources_for_enrichment(self):
        """Given a pipeline run, list all data sources used."""
        from mkg.domain.services.provenance_tracker import ProvenanceTracker

        pt = ProvenanceTracker()
        pt.record_step("art-001", "extraction",
                        {"source": "reuters", "url": "https://reuters.com/1"}, {})
        pt.record_step("art-002", "extraction",
                        {"source": "bloomberg", "url": "https://bloomberg.com/2"}, {})

        sources = pt.get_all_data_sources()
        assert len(sources) >= 2

    def test_provenance_summary(self):
        """Summary report for compliance audit."""
        from mkg.domain.services.provenance_tracker import ProvenanceTracker

        pt = ProvenanceTracker()
        pt.record_step("art-001", "extraction", {}, {"entities_count": 3})
        pt.record_step("art-001", "mutation", {}, {"entities_created": 3})
        pt.record_entity_origin("e1", "TSMC", "art-001", "tier_1_cloud", 0.95)

        summary = pt.get_summary()
        assert summary["total_articles_processed"] >= 1
        assert summary["total_entities_tracked"] >= 1
        assert summary["total_steps_recorded"] >= 2
