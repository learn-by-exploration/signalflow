# mkg/domain/services/lineage_tracer.py
"""LineageTracer — full signal-to-article traceability chain.

Given a signal enrichment result, traces the complete chain:
  enrichment → causal chains → entities → articles → data sources

Combines ProvenanceTracker (raw records) with ComplianceManager
(disclaimers + classification) to produce auditable lineage reports.

SEBI IA Regulations 2013 require that any output influencing investment
decisions must be traceable to its source data. This service provides
that traceability.
"""

import logging
from typing import Any

from mkg.domain.services.compliance_manager import ComplianceManager, DisclaimerType
from mkg.domain.services.provenance_tracker import ProvenanceTracker

logger = logging.getLogger(__name__)


class LineageTracer:
    """Traces signal enrichment outputs back to source articles.

    Given entity IDs and article IDs from an enrichment result,
    queries ProvenanceTracker for the full lineage chain and
    optionally wraps it with ComplianceManager disclaimers.
    """

    def __init__(
        self,
        provenance_tracker: ProvenanceTracker,
        compliance_manager: ComplianceManager,
    ) -> None:
        self._provenance = provenance_tracker
        self._compliance = compliance_manager

    def trace_enrichment(self, enrichment_context: dict[str, Any]) -> dict[str, Any]:
        """Trace an enrichment result back to its source articles.

        Args:
            enrichment_context: Must contain:
                - entity_ids: list[str] — entities involved in enrichment
                - article_ids: list[str] — articles that fed the pipeline

        Returns:
            Structured lineage report with source_articles, entities_involved,
            edges, and propagation events.
        """
        entity_ids: list[str] = enrichment_context.get("entity_ids", [])
        article_ids: list[str] = enrichment_context.get("article_ids", [])

        # Gather article-level lineage
        source_articles: list[dict[str, Any]] = []
        for article_id in article_ids:
            lineage = self._provenance.get_article_lineage(article_id)
            source_articles.append(lineage)

        # Gather entity-level lineage
        entities_involved: list[dict[str, Any]] = []
        for entity_id in entity_ids:
            articles = self._provenance.get_entity_articles(entity_id)
            entity_info = {
                "entity_id": entity_id,
                "contributing_articles": articles,
            }
            entities_involved.append(entity_info)

        return {
            "source_articles": source_articles,
            "entities_involved": entities_involved,
        }

    def trace_entity(self, entity_id: str) -> dict[str, Any]:
        """Trace a single entity back to its source articles.

        Returns entity lineage including all contributing articles,
        highest confidence, and extraction tiers used.
        """
        articles = self._provenance.get_entity_articles(entity_id)

        # Collect data sources for each contributing article
        data_sources: list[dict[str, Any]] = []
        for article_record in articles:
            aid = article_record["article_id"]
            steps = self._provenance.get_records(aid)
            for step in steps:
                source = step.get("inputs", {}).get("source")
                if source:
                    data_sources.append({
                        "source": source,
                        "article_id": aid,
                        "url": step.get("inputs", {}).get("url"),
                    })

        highest_confidence = max(
            (a["confidence"] for a in articles), default=0.0
        )
        tiers_used = {a["extraction_tier"] for a in articles}
        source_article_ids = [a["article_id"] for a in articles]

        return {
            "entity_id": entity_id,
            "source_articles": source_article_ids,
            "highest_confidence": highest_confidence,
            "extraction_tiers_used": tiers_used,
            "data_sources": data_sources,
        }

    def trace_chain(self, chain: dict[str, Any]) -> dict[str, Any]:
        """Trace a causal chain back to its source data.

        Args:
            chain: Must contain:
                - trigger: str — trigger entity ID
                - trigger_name: str — trigger entity display name
                - affected_entity: str — affected entity ID
                - affected_name: str — affected entity display name
                - impact_score: float

        Returns:
            Chain lineage including trigger article, confidence scores.
        """
        trigger_id = chain["trigger"]
        trigger_origin = self._provenance.get_entity_origin(trigger_id)
        propagation_records = self._provenance.get_propagation_records(trigger_id)

        trigger_article = trigger_origin["article_id"] if trigger_origin else None
        trigger_confidence = trigger_origin["confidence"] if trigger_origin else 0.0

        return {
            "chain": chain,
            "trigger_article": trigger_article,
            "trigger_confidence": trigger_confidence,
            "propagation_events": propagation_records,
        }

    def trace_enrichment_with_compliance(
        self, enrichment_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Trace enrichment AND wrap with compliance metadata.

        Combines lineage tracing with ComplianceManager disclaimers
        and regulatory classification. This is the full audit-ready output.

        Args:
            enrichment_context: Must contain entity_ids, article_ids,
                and optionally supply_chain_risk, confidence_adjustment,
                has_material_impact for classification.

        Returns:
            Dict with lineage, disclaimers, and classification.
        """
        lineage = self.trace_enrichment(enrichment_context)

        # Classify impact
        supply_chain_risk = enrichment_context.get("supply_chain_risk", 0.0)
        confidence_adjustment = enrichment_context.get("confidence_adjustment", 0)
        has_material_impact = enrichment_context.get("has_material_impact", False)

        classification = self._compliance.classify_impact(
            supply_chain_risk=supply_chain_risk,
            confidence_adjustment=confidence_adjustment,
            has_material_impact=has_material_impact,
        )

        # Build disclaimer list
        disclaimers = [
            self._compliance.get_disclaimer(DisclaimerType.NOT_FINANCIAL_ADVICE),
            self._compliance.get_disclaimer(DisclaimerType.AI_GENERATED),
        ]
        if has_material_impact:
            disclaimers.append(
                self._compliance.get_disclaimer(DisclaimerType.RISK_WARNING)
            )

        return {
            "lineage": lineage,
            "disclaimers": disclaimers,
            "classification": classification,
        }

    def get_summary(self) -> dict[str, Any]:
        """Summary of all lineage data for audit dashboards.

        Returns aggregate stats about traced entities and referenced articles.
        """
        prov_summary = self._provenance.get_summary()
        total_entities = prov_summary["total_entities_tracked"]

        # Count unique articles referenced by entities
        referenced_articles: set[str] = set()
        # Access provenance internals for summary
        for origins in self._provenance._entity_origins.values():
            for origin in origins:
                referenced_articles.add(origin["article_id"])

        # Tier distribution
        tier_distribution: dict[str, int] = {}
        for origins in self._provenance._entity_origins.values():
            for origin in origins:
                tier = origin["extraction_tier"]
                tier_distribution[tier] = tier_distribution.get(tier, 0) + 1

        return {
            "total_entities_traced": total_entities,
            "total_articles_referenced": len(referenced_articles),
            "tier_distribution": tier_distribution,
        }
