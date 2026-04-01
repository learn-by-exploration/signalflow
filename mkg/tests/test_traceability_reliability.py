# mkg/tests/test_traceability_reliability.py
"""Reliability Hardening Tests — Iterations 41-45.

Tests for edge cases, error conditions, and concurrent operations:
1. Provenance under error conditions (extraction failures, empty data)
2. Audit logger resilience (large volumes, malformed data)
3. Compliance manager edge cases (boundary values, missing fields)
4. PII detector edge cases (unicode, mixed content, empty strings)
5. LineageTracer with missing provenance data
"""

import pytest
from datetime import datetime, timezone


class TestProvenanceResilience:
    """ProvenanceTracker must handle edge cases gracefully."""

    def test_record_step_with_none_inputs(self):
        from mkg.domain.services.provenance_tracker import ProvenanceTracker
        pt = ProvenanceTracker()
        # Should not raise even with edge-case inputs
        pt.record_step("art-001", "extraction", {}, {})
        records = pt.get_records("art-001")
        assert len(records) == 1

    def test_get_records_nonexistent_article(self):
        from mkg.domain.services.provenance_tracker import ProvenanceTracker
        pt = ProvenanceTracker()
        records = pt.get_records("nonexistent")
        assert records == []

    def test_entity_origin_lookup_nonexistent(self):
        from mkg.domain.services.provenance_tracker import ProvenanceTracker
        pt = ProvenanceTracker()
        origin = pt.get_entity_origin("nonexistent")
        assert origin is None

    def test_edge_origin_lookup_nonexistent(self):
        from mkg.domain.services.provenance_tracker import ProvenanceTracker
        pt = ProvenanceTracker()
        origin = pt.get_edge_origin("nonexistent")
        assert origin is None

    def test_large_volume_provenance(self):
        from mkg.domain.services.provenance_tracker import ProvenanceTracker
        pt = ProvenanceTracker()
        for i in range(1000):
            pt.record_step(f"art-{i}", "extraction", {"i": i}, {"count": 1})
            pt.record_entity_origin(f"e-{i}", f"Entity-{i}", f"art-{i}", "tier_3", 0.5)
        summary = pt.get_summary()
        assert summary["total_articles_processed"] == 1000
        assert summary["total_entities_tracked"] == 1000

    def test_duplicate_entity_origins(self):
        from mkg.domain.services.provenance_tracker import ProvenanceTracker
        pt = ProvenanceTracker()
        # Same entity from multiple articles
        pt.record_entity_origin("e1", "TSMC", "art-001", "tier_1", 0.95)
        pt.record_entity_origin("e1", "TSMC", "art-002", "tier_3", 0.80)
        pt.record_entity_origin("e1", "TSMC", "art-003", "tier_1", 0.90)
        articles = pt.get_entity_articles("e1")
        assert len(articles) == 3  # All three recorded


class TestAuditLoggerResilience:
    """AuditLogger must handle edge cases and high volumes."""

    def test_large_volume_audit(self):
        from mkg.domain.services.audit_logger import AuditLogger, AuditAction
        al = AuditLogger()
        for i in range(500):
            al.log(AuditAction.ENTITY_CREATED, "pipeline", f"e-{i}", "entity", {"i": i})
        entries = al.get_entries()
        assert len(entries) == 500

    def test_query_with_no_matching_entries(self):
        from mkg.domain.services.audit_logger import AuditLogger, AuditAction
        al = AuditLogger()
        al.log(AuditAction.ENTITY_CREATED, "pipeline", "e1", "entity", {})
        entries = al.get_entries(action=AuditAction.EDGE_DELETED)
        assert len(entries) == 0

    def test_export_report_with_mixed_actions(self):
        from mkg.domain.services.audit_logger import AuditLogger, AuditAction
        al = AuditLogger()
        al.log(AuditAction.ENTITY_CREATED, "pipeline", "e1", "entity", {})
        al.log(AuditAction.EDGE_CREATED, "pipeline", "ed1", "edge", {})
        al.log(AuditAction.ENTITY_UPDATED, "pipeline", "e1", "entity", {})
        al.log(AuditAction.PROPAGATION_RUN, "pipeline", "prop1", "propagation", {})
        report = al.export_report()
        assert report["total_entries"] == 4
        assert len(report["actions_breakdown"]) == 4

    def test_audit_entry_timestamps_are_ordered(self):
        from mkg.domain.services.audit_logger import AuditLogger, AuditAction
        al = AuditLogger()
        for i in range(100):
            al.log(AuditAction.ENTITY_CREATED, "pipeline", f"e-{i}", "entity", {})
        entries = al.get_entries()
        timestamps = [e["timestamp"] for e in entries]
        assert timestamps == sorted(timestamps)


class TestComplianceEdgeCases:
    """ComplianceManager boundary and edge cases."""

    def test_classify_zero_values(self):
        from mkg.domain.services.compliance_manager import ComplianceManager
        cm = ComplianceManager()
        result = cm.classify_impact(
            supply_chain_risk=0.0,
            confidence_adjustment=0,
            has_material_impact=False,
        )
        assert result["risk_level"] == "low"
        assert result["requires_disclosure"] is False

    def test_classify_boundary_values(self):
        from mkg.domain.services.compliance_manager import ComplianceManager
        cm = ComplianceManager()
        # Exactly at boundary
        result = cm.classify_impact(
            supply_chain_risk=0.3,
            confidence_adjustment=0,
            has_material_impact=False,
        )
        assert result["risk_level"] in ("medium", "low")

    def test_wrap_enrichment_empty_sources(self):
        from mkg.domain.services.compliance_manager import ComplianceManager
        cm = ComplianceManager()
        wrapped = cm.wrap_enrichment(
            enrichment={"value": 1},
            data_sources=[],
            supply_chain_risk=0.1,
        )
        assert "disclaimers" in wrapped
        assert "enrichment" in wrapped

    def test_compliance_report_after_many_wraps(self):
        from mkg.domain.services.compliance_manager import ComplianceManager
        cm = ComplianceManager()
        for i in range(100):
            cm.wrap_enrichment(
                enrichment={"i": i},
                data_sources=[{"source": "test"}],
                supply_chain_risk=i / 100.0,
            )
        report = cm.get_compliance_report()
        assert report["total_enrichments_processed"] == 100


class TestPIIDetectorEdgeCases:
    """PII detector robustness."""

    def test_empty_string(self):
        from mkg.domain.services.pii_detector import PIIDetector
        d = PIIDetector()
        result = d.scan("")
        assert result["has_pii"] is False
        assert result["pii_count"] == 0

    def test_unicode_text(self):
        from mkg.domain.services.pii_detector import PIIDetector
        d = PIIDetector()
        result = d.scan("टीएसएमसी ने मजबूत राजस्व की रिपोर्ट दी")
        assert result["has_pii"] is False

    def test_mixed_pii_content(self):
        from mkg.domain.services.pii_detector import PIIDetector
        d = PIIDetector()
        text = "Email: john@example.com, PAN: ABCDE1234F, Phone: +91-9876543210"
        result = d.scan(text)
        assert result["has_pii"] is True
        assert len(result["pii_types"]) >= 3

    def test_redact_preserves_non_pii(self):
        from mkg.domain.services.pii_detector import PIIDetector
        d = PIIDetector()
        text = "TSMC reported strong revenue. Contact: ceo@tsmc.com"
        redacted = d.redact(text)
        assert "TSMC reported strong revenue" in redacted
        assert "ceo@tsmc.com" not in redacted

    def test_very_long_text(self):
        from mkg.domain.services.pii_detector import PIIDetector
        d = PIIDetector()
        text = "Normal financial text. " * 10000 + "email@test.com"
        result = d.scan(text)
        assert result["has_pii"] is True
        assert result["pii_count"] == 1


class TestLineageTracerEdgeCases:
    """LineageTracer with missing or partial data."""

    def test_trace_entity_no_data(self):
        from mkg.domain.services.lineage_tracer import LineageTracer
        from mkg.domain.services.provenance_tracker import ProvenanceTracker
        from mkg.domain.services.compliance_manager import ComplianceManager
        lt = LineageTracer(ProvenanceTracker(), ComplianceManager())
        result = lt.trace_entity("nonexistent")
        assert result["entity_id"] == "nonexistent"
        assert len(result["source_articles"]) == 0
        assert result["highest_confidence"] == 0.0

    def test_trace_chain_no_origin(self):
        from mkg.domain.services.lineage_tracer import LineageTracer
        from mkg.domain.services.provenance_tracker import ProvenanceTracker
        from mkg.domain.services.compliance_manager import ComplianceManager
        lt = LineageTracer(ProvenanceTracker(), ComplianceManager())
        chain = {
            "trigger": "unknown_entity",
            "trigger_name": "Unknown",
            "affected_entity": "other",
            "affected_name": "Other",
            "impact_score": 0.5,
        }
        result = lt.trace_chain(chain)
        assert result["trigger_article"] is None
        assert result["trigger_confidence"] == 0.0

    def test_trace_enrichment_empty_context(self):
        from mkg.domain.services.lineage_tracer import LineageTracer
        from mkg.domain.services.provenance_tracker import ProvenanceTracker
        from mkg.domain.services.compliance_manager import ComplianceManager
        lt = LineageTracer(ProvenanceTracker(), ComplianceManager())
        result = lt.trace_enrichment({"entity_ids": [], "article_ids": []})
        assert len(result["source_articles"]) == 0
        assert len(result["entities_involved"]) == 0


class TestRetentionPolicyEdgeCases:
    """RetentionPolicy boundary conditions."""

    def test_exact_boundary_date(self):
        from mkg.domain.services.retention_policy import RetentionPolicy
        from datetime import timedelta
        rp = RetentionPolicy(article_retention_days=30)
        # Exactly 30 days ago — should still be valid (not expired)
        boundary = datetime.now(timezone.utc) - timedelta(days=30, seconds=-1)
        assert rp.is_expired("article", boundary) is False

    def test_zero_retention_everything_expired(self):
        from mkg.domain.services.retention_policy import RetentionPolicy
        from datetime import timedelta
        rp = RetentionPolicy(article_retention_days=0)
        recent = datetime.now(timezone.utc) - timedelta(seconds=1)
        assert rp.is_expired("article", recent) is True
