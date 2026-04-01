# mkg/tests/test_compliance_manager.py
"""Tests for ComplianceManager — regulatory compliance for signal recommendations.

Iterations 6-10: Every signal enrichment must carry appropriate disclaimers,
data source disclosures, and regulatory classifications per SEBI IA
Regulations 2013 and general financial advisory compliance requirements.
"""

import pytest


class TestDisclaimerGeneration:
    """Disclaimer text generation for signal outputs."""

    def test_not_financial_advice_disclaimer(self):
        from mkg.domain.services.compliance_manager import ComplianceManager, DisclaimerType

        cm = ComplianceManager()
        d = cm.get_disclaimer(DisclaimerType.NOT_FINANCIAL_ADVICE)
        assert "not" in d.lower() and "financial advice" in d.lower()

    def test_sebi_disclaimer(self):
        from mkg.domain.services.compliance_manager import ComplianceManager, DisclaimerType

        cm = ComplianceManager()
        d = cm.get_disclaimer(DisclaimerType.SEBI_DISCLAIMER)
        assert "SEBI" in d or "Securities" in d

    def test_data_source_disclosure(self):
        from mkg.domain.services.compliance_manager import ComplianceManager, DisclaimerType

        cm = ComplianceManager()
        d = cm.get_disclaimer(DisclaimerType.DATA_SOURCE_DISCLOSURE)
        assert len(d) > 0

    def test_ai_generated_disclaimer(self):
        from mkg.domain.services.compliance_manager import ComplianceManager, DisclaimerType

        cm = ComplianceManager()
        d = cm.get_disclaimer(DisclaimerType.AI_GENERATED)
        assert "AI" in d or "artificial intelligence" in d.lower() or "machine" in d.lower()

    def test_all_disclaimers_are_non_empty(self):
        from mkg.domain.services.compliance_manager import ComplianceManager, DisclaimerType

        cm = ComplianceManager()
        for dt in DisclaimerType:
            d = cm.get_disclaimer(dt)
            assert len(d) > 10, f"Disclaimer {dt.name} is too short: '{d}'"


class TestComplianceEnvelope:
    """Compliance envelope wraps every signal enrichment."""

    def test_wrap_enrichment_adds_disclaimers(self):
        from mkg.domain.services.compliance_manager import ComplianceManager

        cm = ComplianceManager()
        enrichment = {
            "supply_chain_risk": 0.75,
            "confidence_adjustment": -10,
            "risk_factors": ["TSMC fab fire affects NVIDIA supply"],
            "has_material_impact": True,
        }
        wrapped = cm.wrap_enrichment(
            enrichment,
            data_sources=[{"source": "reuters", "url": "https://reuters.com/1"}],
        )
        assert "disclaimers" in wrapped
        assert "data_sources" in wrapped
        assert "compliance_timestamp" in wrapped
        assert "enrichment" in wrapped
        # Original enrichment is preserved
        assert wrapped["enrichment"]["supply_chain_risk"] == 0.75

    def test_wrap_enrichment_includes_all_required_disclaimers(self):
        from mkg.domain.services.compliance_manager import ComplianceManager

        cm = ComplianceManager()
        wrapped = cm.wrap_enrichment({"has_material_impact": True}, data_sources=[])
        disclaimers = wrapped["disclaimers"]
        # Must have at least NOT_FINANCIAL_ADVICE and AI_GENERATED
        assert any("not" in d.lower() and "advice" in d.lower() for d in disclaimers)
        assert any("AI" in d or "generated" in d.lower() for d in disclaimers)

    def test_wrap_enrichment_includes_data_source_list(self):
        from mkg.domain.services.compliance_manager import ComplianceManager

        cm = ComplianceManager()
        sources = [
            {"source": "reuters", "url": "https://reuters.com/1", "article_id": "a1"},
            {"source": "bloomberg", "url": "https://bbg.com/2", "article_id": "a2"},
        ]
        wrapped = cm.wrap_enrichment({"test": True}, data_sources=sources)
        assert len(wrapped["data_sources"]) == 2

    def test_wrap_empty_enrichment(self):
        from mkg.domain.services.compliance_manager import ComplianceManager

        cm = ComplianceManager()
        wrapped = cm.wrap_enrichment({}, data_sources=[])
        assert "disclaimers" in wrapped
        assert "compliance_timestamp" in wrapped


class TestRegulatoryClassification:
    """Classify enrichment output by regulatory category."""

    def test_classify_high_impact(self):
        from mkg.domain.services.compliance_manager import ComplianceManager

        cm = ComplianceManager()
        classification = cm.classify_impact(
            supply_chain_risk=0.8,
            confidence_adjustment=-12,
            has_material_impact=True,
        )
        assert classification["risk_level"] == "high"
        assert classification["requires_disclosure"] is True

    def test_classify_low_impact(self):
        from mkg.domain.services.compliance_manager import ComplianceManager

        cm = ComplianceManager()
        classification = cm.classify_impact(
            supply_chain_risk=0.1,
            confidence_adjustment=0,
            has_material_impact=False,
        )
        assert classification["risk_level"] == "low"

    def test_classify_medium_impact(self):
        from mkg.domain.services.compliance_manager import ComplianceManager

        cm = ComplianceManager()
        classification = cm.classify_impact(
            supply_chain_risk=0.5,
            confidence_adjustment=-5,
            has_material_impact=True,
        )
        assert classification["risk_level"] == "medium"

    def test_classification_includes_reasoning(self):
        from mkg.domain.services.compliance_manager import ComplianceManager

        cm = ComplianceManager()
        classification = cm.classify_impact(
            supply_chain_risk=0.9,
            confidence_adjustment=-15,
            has_material_impact=True,
        )
        assert "reason" in classification
        assert len(classification["reason"]) > 0


class TestComplianceReport:
    """Generate compliance reports for audit."""

    def test_generate_report(self):
        from mkg.domain.services.compliance_manager import ComplianceManager

        cm = ComplianceManager()
        cm.wrap_enrichment({"has_material_impact": True},
                           data_sources=[{"source": "reuters"}])
        cm.wrap_enrichment({"has_material_impact": False}, data_sources=[])

        report = cm.get_compliance_report()
        assert report["total_enrichments_processed"] == 2
        assert "generated_at" in report

    def test_report_tracks_high_risk_count(self):
        from mkg.domain.services.compliance_manager import ComplianceManager

        cm = ComplianceManager()
        cm.wrap_enrichment(
            {"supply_chain_risk": 0.9, "has_material_impact": True},
            data_sources=[{"source": "reuters"}],
            supply_chain_risk=0.9,
            confidence_adjustment=-12,
        )
        report = cm.get_compliance_report()
        assert report["high_risk_count"] >= 1
