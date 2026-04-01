# mkg/domain/services/signal_bridge.py
"""SignalBridge — connects MKG analysis to SignalFlow signal reasoning.

Bridges MKG's causal chain & impact propagation results into structured
signal enrichment data that the backend's SignalGenerator can consume.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SignalBridge:
    """Bridges MKG causal analysis to SignalFlow signal enrichment.

    Takes pipeline results (impacts, causal chains, impact table) and
    produces structured data for:
    - AI reasoning enrichment (context for Claude prompt)
    - Confidence adjustment (amplify/dampen based on supply chain risk)
    - Risk factor summary (for signal cards)

    Optionally wraps output with compliance metadata (disclaimers,
    classification, data sources) when compliance_manager is provided.
    """

    # Minimum impact score to include in signal enrichment
    MIN_IMPACT_THRESHOLD = 0.05
    # Maximum MKG-based confidence adjustment
    MAX_CONFIDENCE_ADJUSTMENT = 15

    def __init__(
        self,
        compliance_manager: Any = None,
        lineage_tracer: Any = None,
    ) -> None:
        self._compliance = compliance_manager
        self._lineage = lineage_tracer

    def enrich_signal(
        self,
        symbol: str,
        pipeline_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Produce signal enrichment from MKG pipeline output.

        Args:
            symbol: The trading symbol being evaluated (e.g., "NVDA", "AAPL").
            pipeline_result: Output from PipelineOrchestrator.process_article().

        Returns:
            Enrichment dict with:
            - supply_chain_risk: overall risk score [0, 1]
            - confidence_adjustment: signed int for signal confidence
            - risk_factors: list of plain-English risk factors
            - affected_companies: list of impacted entities with scores
            - reasoning_context: string for AI prompt injection
            - has_material_impact: bool — whether MKG found actionable data
        """
        if not pipeline_result or pipeline_result.get("status") != "completed":
            return self._empty_enrichment()

        impacts = pipeline_result.get("impacts", [])
        chains = pipeline_result.get("causal_chains", [])
        table = pipeline_result.get("impact_table", {})

        if not impacts:
            return self._empty_enrichment()

        # Filter to material impacts
        material_impacts = [
            imp for imp in impacts
            if imp.get("impact", 0) >= self.MIN_IMPACT_THRESHOLD
        ]

        if not material_impacts:
            return self._empty_enrichment()

        # Find impact for the target symbol
        symbol_impact = self._find_symbol_impact(symbol, chains)
        supply_chain_risk = self._compute_supply_chain_risk(material_impacts)
        confidence_adj = self._compute_confidence_adjustment(
            symbol_impact, supply_chain_risk
        )
        risk_factors = self._extract_risk_factors(chains, symbol)
        affected = self._extract_affected_companies(table)
        reasoning_ctx = self._build_reasoning_context(chains, symbol)

        return {
            "supply_chain_risk": round(supply_chain_risk, 3),
            "confidence_adjustment": confidence_adj,
            "risk_factors": risk_factors,
            "affected_companies": affected,
            "reasoning_context": reasoning_ctx,
            "has_material_impact": True,
            "impact_count": len(material_impacts),
            "max_impact": max(imp["impact"] for imp in material_impacts),
        }

    def _empty_enrichment(self) -> dict[str, Any]:
        """Return empty enrichment when MKG has no data."""
        return {
            "supply_chain_risk": 0.0,
            "confidence_adjustment": 0,
            "risk_factors": [],
            "affected_companies": [],
            "reasoning_context": "",
            "has_material_impact": False,
            "impact_count": 0,
            "max_impact": 0.0,
        }

    def enrich_signal_with_compliance(
        self,
        symbol: str,
        pipeline_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Produce signal enrichment wrapped with compliance metadata.

        Combines standard enrichment with:
        - Regulatory disclaimers (NOT_FINANCIAL_ADVICE, AI_GENERATED, etc.)
        - Risk classification (high/medium/low)
        - Data source disclosure
        - Lineage references

        Args:
            symbol: The trading symbol being evaluated.
            pipeline_result: Output from PipelineOrchestrator.process_article().

        Returns:
            Enrichment dict with all standard fields PLUS:
            - disclaimers: list of disclaimer texts
            - classification: {risk_level, requires_disclosure, reason}
            - data_sources: list of attributed sources
        """
        # Get standard enrichment
        enrichment = self.enrich_signal(symbol, pipeline_result)

        # Build disclaimers
        disclaimers = self._build_disclaimers(enrichment)

        # Classify regulatory risk
        classification = self._classify_enrichment(enrichment)

        # Get data sources from lineage
        data_sources = self._get_data_sources()

        # Merge compliance into enrichment
        enrichment["disclaimers"] = disclaimers
        enrichment["classification"] = classification
        enrichment["data_sources"] = data_sources

        return enrichment

    def _build_disclaimers(self, enrichment: dict[str, Any]) -> list[str]:
        """Build list of applicable disclaimer texts."""
        if not self._compliance:
            from mkg.domain.services.compliance_manager import ComplianceManager, DisclaimerType
            cm = ComplianceManager()
        else:
            from mkg.domain.services.compliance_manager import DisclaimerType
            cm = self._compliance

        disclaimers = [
            cm.get_disclaimer(DisclaimerType.NOT_FINANCIAL_ADVICE),
            cm.get_disclaimer(DisclaimerType.AI_GENERATED),
        ]

        if enrichment.get("has_material_impact"):
            disclaimers.append(cm.get_disclaimer(DisclaimerType.RISK_WARNING))

        return disclaimers

    def _classify_enrichment(self, enrichment: dict[str, Any]) -> dict[str, Any]:
        """Classify enrichment for regulatory risk level."""
        if not self._compliance:
            from mkg.domain.services.compliance_manager import ComplianceManager
            cm = ComplianceManager()
        else:
            cm = self._compliance

        return cm.classify_impact(
            supply_chain_risk=enrichment.get("supply_chain_risk", 0.0),
            confidence_adjustment=enrichment.get("confidence_adjustment", 0),
            has_material_impact=enrichment.get("has_material_impact", False),
        )

    def _get_data_sources(self) -> list[dict[str, Any]]:
        """Get data sources from lineage tracer."""
        if self._lineage and hasattr(self._lineage, '_provenance'):
            return self._lineage._provenance.get_all_data_sources()
        return []

    def _find_symbol_impact(
        self, symbol: str, chains: list[dict[str, Any]]
    ) -> float:
        """Find the impact score for the target symbol in causal chains."""
        symbol_upper = symbol.upper()
        for chain in chains:
            affected_name = chain.get("affected_name", "").upper()
            if symbol_upper in affected_name or affected_name in symbol_upper:
                return chain.get("impact_score", 0.0)
        return 0.0

    def _compute_supply_chain_risk(
        self, impacts: list[dict[str, Any]]
    ) -> float:
        """Compute overall supply chain risk from material impacts.

        Average of top-3 impacts (by score), capped at 1.0.
        """
        sorted_impacts = sorted(
            impacts, key=lambda x: x.get("impact", 0), reverse=True
        )
        top_n = sorted_impacts[:3]
        avg = sum(imp.get("impact", 0) for imp in top_n) / len(top_n)
        return min(avg, 1.0)

    def _compute_confidence_adjustment(
        self, symbol_impact: float, supply_chain_risk: float
    ) -> int:
        """Compute confidence adjustment for the signal.

        Negative adjustment = risk dampens confidence (supply chain disruption).
        Positive adjustment = positive chain effect boosts confidence.
        """
        if symbol_impact <= 0:
            return 0

        # Scale impact to adjustment range
        raw_adj = symbol_impact * self.MAX_CONFIDENCE_ADJUSTMENT
        # Supply chain risk > 0.5 means negative event → negative adjustment
        if supply_chain_risk > 0.5:
            return -min(int(raw_adj), self.MAX_CONFIDENCE_ADJUSTMENT)
        return min(int(raw_adj), self.MAX_CONFIDENCE_ADJUSTMENT)

    def _extract_risk_factors(
        self, chains: list[dict[str, Any]], symbol: str
    ) -> list[str]:
        """Extract plain-English risk factors from causal chains."""
        factors: list[str] = []
        symbol_upper = symbol.upper()

        for chain in chains:
            narrative = chain.get("narrative", "")
            if not narrative:
                continue

            affected = chain.get("affected_name", "").upper()
            trigger = chain.get("trigger_name", "").upper()

            # Include if symbol is directly mentioned or is upstream
            if symbol_upper in affected or symbol_upper in trigger:
                factors.append(narrative)
            elif chain.get("impact_score", 0) >= 0.5:
                # High-impact chains are always relevant
                factors.append(narrative)

        return factors[:5]  # Cap at 5 risk factors

    def _extract_affected_companies(
        self, table: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract affected companies from impact table for UI display."""
        rows = table.get("rows", [])
        return [
            {
                "name": row.get("entity_name", ""),
                "impact_pct": row.get("impact_pct", 0),
                "entity_type": row.get("entity_type", ""),
            }
            for row in rows[:10]  # Top 10 affected
        ]

    def _build_reasoning_context(
        self, chains: list[dict[str, Any]], symbol: str
    ) -> str:
        """Build context string for AI reasoning prompt injection.

        This context is added to the Claude prompt when generating
        signal explanations, giving the AI supply-chain awareness.
        """
        if not chains:
            return ""

        lines: list[str] = []
        lines.append("Supply Chain Analysis (MKG):")

        for chain in chains[:5]:
            trigger = chain.get("trigger_name", "?")
            affected = chain.get("affected_name", "?")
            event = chain.get("trigger_event", "event")
            impact = chain.get("impact_score", 0)
            hops = chain.get("hops", 0)

            lines.append(
                f"- {trigger} → {affected}: {event} "
                f"(impact: {impact:.0%}, {hops} hop{'s' if hops != 1 else ''})"
            )

        return "\n".join(lines)
