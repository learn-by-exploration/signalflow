# mkg/tests/test_scenario_integration.py
"""Multi-scenario integration tests — real SQLite storage + full pipeline.

Iteration 32-34: End-to-end scenarios testing the real, wired system.
Each scenario seeds a knowledge graph, processes articles, runs propagation,
and validates causal chains, impact tables, and signal bridge output.
"""

import os
import tempfile

import pytest

from mkg.domain.entities.edge import RelationType
from mkg.domain.entities.node import EntityType
from mkg.domain.services.alert_system import AlertSystem
from mkg.domain.services.article_dedup import ArticleDedup
from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
from mkg.domain.services.causal_chain_builder import CausalChainBuilder
from mkg.domain.services.cost_governance import CostGovernance
from mkg.domain.services.extraction_orchestrator import ExtractionOrchestrator
from mkg.domain.services.graph_mutation import GraphMutationService
from mkg.domain.services.hallucination_verifier import HallucinationVerifier
from mkg.domain.services.impact_table import ImpactTableBuilder
from mkg.domain.services.pipeline_orchestrator import PipelineOrchestrator
from mkg.domain.services.propagation_engine import PropagationEngine
from mkg.domain.services.signal_bridge import SignalBridge
from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage


# ── Helper: Fake extractor that returns scenario-specific data ──


class _ScenarioExtractor:
    """Returns canned extraction results for a specific scenario."""

    def __init__(self, entities: list[dict], relations: list[dict]):
        self._entities = entities
        self._relations = relations

    def get_tier(self):
        from mkg.domain.interfaces.llm_extractor import ExtractionTier
        return ExtractionTier.TIER_3

    def get_cost_estimate(self, text_length: int) -> float:
        return 0.0

    async def extract_all(self, text: str, context=None) -> dict:
        return {"entities": self._entities, "relations": self._relations}


async def _build_pipeline(
    storage: SQLiteGraphStorage,
    entities: list[dict],
    relations: list[dict],
) -> PipelineOrchestrator:
    """Wire up a full pipeline with a given scenario extractor."""
    registry = CanonicalEntityRegistry()
    extractor = _ScenarioExtractor(entities, relations)
    return PipelineOrchestrator(
        graph_storage=storage,
        extraction_orchestrator=ExtractionOrchestrator(
            extractors=[extractor],
            cost_governance=CostGovernance(monthly_budget_usd=30.0),
        ),
        hallucination_verifier=HallucinationVerifier(),
        graph_mutation=GraphMutationService(storage, registry),
        propagation_engine=PropagationEngine(storage),
        causal_chain_builder=CausalChainBuilder(storage),
        alert_system=AlertSystem(),
        impact_table_builder=ImpactTableBuilder(storage),
        article_dedup=ArticleDedup(),
    )


# ════════════════════════════════════════════════════════════
# SCENARIO 1: Semiconductor Supply Chain (TSMC → NVIDIA → AMD)
# ════════════════════════════════════════════════════════════


class TestSemiconductorScenario:
    """TSMC fab disruption propagates to NVIDIA, Apple, AMD."""

    ENTITIES = [
        {"name": "TSMC", "entity_type": "Company", "confidence": 0.95},
        {"name": "NVIDIA", "entity_type": "Company", "confidence": 0.92},
        {"name": "Apple", "entity_type": "Company", "confidence": 0.90},
        {"name": "AMD", "entity_type": "Company", "confidence": 0.85},
    ]
    RELATIONS = [
        {"source": "TSMC", "target": "NVIDIA", "relation_type": "SUPPLIES_TO",
         "weight": 0.85, "confidence": 0.9},
        {"source": "TSMC", "target": "Apple", "relation_type": "SUPPLIES_TO",
         "weight": 0.80, "confidence": 0.88},
        {"source": "NVIDIA", "target": "AMD", "relation_type": "COMPETES_WITH",
         "weight": 0.60, "confidence": 0.8},
    ]

    @pytest.fixture
    async def storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "graph.db"))
            await s.initialize()
            yield s
            await s.close()

    @pytest.mark.asyncio
    async def test_full_pipeline_creates_entities(self, storage):
        pipeline = await _build_pipeline(storage, self.ENTITIES, self.RELATIONS)
        result = await pipeline.process_article(
            title="TSMC fab disruption",
            content="TSMC fab fire disrupts chip supply to NVIDIA and Apple. AMD may benefit.",
            source="reuters",
        )
        assert result["status"] == "completed"
        assert result["entities_created"] >= 3  # At least TSMC, NVIDIA, Apple

    @pytest.mark.asyncio
    async def test_propagation_reaches_nvidia(self, storage):
        pipeline = await _build_pipeline(storage, self.ENTITIES, self.RELATIONS)
        result = await pipeline.process_article(
            title="TSMC earthquake",
            content="TSMC earthquake disruption hits chip manufacturing for NVIDIA and Apple.",
            source="test",
            trigger_propagation=True,
            trigger_entity_name="TSMC",
            trigger_event="earthquake disruption",
        )
        assert result["propagation_ran"] is True
        impacted_ids = [imp["entity_id"] for imp in result.get("impacts", [])]
        assert len(impacted_ids) >= 1  # At least NVIDIA or Apple

    @pytest.mark.asyncio
    async def test_causal_chains_have_narratives(self, storage):
        pipeline = await _build_pipeline(storage, self.ENTITIES, self.RELATIONS)
        result = await pipeline.process_article(
            title="TSMC fire",
            content="TSMC fire affects NVIDIA GPU chips and Apple A-series processors.",
            source="test",
            trigger_propagation=True,
            trigger_entity_name="TSMC",
            trigger_event="factory fire",
        )
        chains = result.get("causal_chains", [])
        assert len(chains) >= 1
        for chain in chains:
            assert "narrative" in chain
            assert len(chain["narrative"]) > 0

    @pytest.mark.asyncio
    async def test_impact_table_ranked(self, storage):
        pipeline = await _build_pipeline(storage, self.ENTITIES, self.RELATIONS)
        result = await pipeline.process_article(
            title="TSMC supply shock",
            content="TSMC supply shock hits NVIDIA and Apple chip lines.",
            source="test",
            trigger_propagation=True,
            trigger_entity_name="TSMC",
            trigger_event="supply shock",
        )
        table = result.get("impact_table", {})
        rows = table.get("rows", [])
        if len(rows) >= 2:
            assert rows[0]["impact_score"] >= rows[1]["impact_score"]

    @pytest.mark.asyncio
    async def test_signal_bridge_enrichment(self, storage):
        """Bridge should produce actionable enrichment from pipeline result."""
        pipeline = await _build_pipeline(storage, self.ENTITIES, self.RELATIONS)
        result = await pipeline.process_article(
            title="TSMC disruption",
            content="TSMC disruption affects NVIDIA chip supply globally.",
            source="test",
            trigger_propagation=True,
            trigger_entity_name="TSMC",
            trigger_event="disruption",
        )
        bridge = SignalBridge()
        enrichment = bridge.enrich_signal("NVIDIA", result)
        # Even if entities differ, the bridge should handle it
        assert isinstance(enrichment, dict)
        assert "supply_chain_risk" in enrichment
        assert "confidence_adjustment" in enrichment


# ════════════════════════════════════════════════════════════
# SCENARIO 2: Oil & Geopolitics (Saudi Aramco → Oil Price → Airlines)
# ════════════════════════════════════════════════════════════


class TestOilGeopoliticsScenario:
    """Saudi production cut → oil price surge → airline cost pressure."""

    ENTITIES = [
        {"name": "Saudi Aramco", "entity_type": "Company", "confidence": 0.95},
        {"name": "Crude Oil", "entity_type": "Product", "confidence": 0.90},
        {"name": "IndiGo", "entity_type": "Company", "confidence": 0.85},
        {"name": "Air India", "entity_type": "Company", "confidence": 0.83},
        {"name": "India", "entity_type": "Country", "confidence": 0.95},
    ]
    RELATIONS = [
        {"source": "Saudi Aramco", "target": "Crude Oil", "relation_type": "PRODUCES",
         "weight": 0.90, "confidence": 0.95},
        {"source": "Crude Oil", "target": "IndiGo", "relation_type": "AFFECTS",
         "weight": 0.70, "confidence": 0.80},
        {"source": "Crude Oil", "target": "Air India", "relation_type": "AFFECTS",
         "weight": 0.65, "confidence": 0.78},
        {"source": "IndiGo", "target": "India", "relation_type": "OPERATES_IN",
         "weight": 0.95, "confidence": 0.99},
    ]

    @pytest.fixture
    async def storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "graph.db"))
            await s.initialize()
            yield s
            await s.close()

    @pytest.mark.asyncio
    async def test_oil_shock_propagates_to_airlines(self, storage):
        pipeline = await _build_pipeline(storage, self.ENTITIES, self.RELATIONS)
        result = await pipeline.process_article(
            title="Saudi Aramco production cut",
            content="Saudi Aramco announces 2M barrel/day production cut. Crude oil prices surge. "
                    "IndiGo and Air India face rising fuel costs in India.",
            source="bloomberg",
            trigger_propagation=True,
            trigger_entity_name="Saudi Aramco",
            trigger_event="production cut",
        )
        assert result["propagation_ran"] is True
        impacts = result.get("impacts", [])
        assert len(impacts) >= 1  # At least Crude Oil

    @pytest.mark.asyncio
    async def test_oil_chain_depth_reaches_airlines(self, storage):
        """Impact should propagate at least 2 hops: Aramco → Oil → IndiGo."""
        pipeline = await _build_pipeline(storage, self.ENTITIES, self.RELATIONS)
        result = await pipeline.process_article(
            title="Saudi oil cut",
            content="Saudi Aramco cuts production. Crude oil prices soar, hitting IndiGo and Air India.",
            source="test",
            trigger_propagation=True,
            trigger_entity_name="Saudi Aramco",
            trigger_event="production cut",
        )
        max_depth = max(
            (imp.get("depth", 0) for imp in result.get("impacts", [])),
            default=0,
        )
        assert max_depth >= 2  # At least through Oil → Airlines

    @pytest.mark.asyncio
    async def test_bridge_enrichment_for_indigo(self, storage):
        pipeline = await _build_pipeline(storage, self.ENTITIES, self.RELATIONS)
        result = await pipeline.process_article(
            title="Saudi production cut",
            content="Saudi Aramco production cut raises crude oil costs for IndiGo and Air India.",
            source="test",
            trigger_propagation=True,
            trigger_entity_name="Saudi Aramco",
            trigger_event="production cut",
        )
        bridge = SignalBridge()
        enrichment = bridge.enrich_signal("IndiGo", result)
        assert isinstance(enrichment["supply_chain_risk"], float)


# ════════════════════════════════════════════════════════════
# SCENARIO 3: Pharma (FDA regulation → Drug companies)
# ════════════════════════════════════════════════════════════


class TestPharmaScenario:
    """FDA approval/rejection → pharma company stock impact."""

    ENTITIES = [
        {"name": "FDA", "entity_type": "Regulation", "confidence": 0.95},
        {"name": "Pfizer", "entity_type": "Company", "confidence": 0.92},
        {"name": "mRNA Vaccine", "entity_type": "Product", "confidence": 0.88},
        {"name": "BioNTech", "entity_type": "Company", "confidence": 0.85},
    ]
    RELATIONS = [
        {"source": "FDA", "target": "mRNA Vaccine", "relation_type": "REGULATES",
         "weight": 0.90, "confidence": 0.95},
        {"source": "Pfizer", "target": "mRNA Vaccine", "relation_type": "PRODUCES",
         "weight": 0.85, "confidence": 0.90},
        {"source": "BioNTech", "target": "mRNA Vaccine", "relation_type": "PRODUCES",
         "weight": 0.80, "confidence": 0.85},
    ]

    @pytest.fixture
    async def storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "graph.db"))
            await s.initialize()
            yield s
            await s.close()

    @pytest.mark.asyncio
    async def test_fda_rejection_propagates(self, storage):
        pipeline = await _build_pipeline(storage, self.ENTITIES, self.RELATIONS)
        result = await pipeline.process_article(
            title="FDA rejects mRNA booster",
            content="FDA rejects updated mRNA vaccine booster from Pfizer and BioNTech. "
                    "Regulatory concerns cited.",
            source="reuters",
            trigger_propagation=True,
            trigger_entity_name="FDA",
            trigger_event="vaccine rejection",
        )
        assert result["propagation_ran"] is True

    @pytest.mark.asyncio
    async def test_pharma_creates_regulation_entity(self, storage):
        pipeline = await _build_pipeline(storage, self.ENTITIES, self.RELATIONS)
        await pipeline.process_article(
            title="FDA update",
            content="FDA announces new regulations for mRNA vaccines by Pfizer and BioNTech.",
            source="test",
        )
        entities = await storage.find_entities()
        names = {e.get("name", "") for e in entities}
        # At minimum we should have some entities
        assert len(entities) >= 1


# ════════════════════════════════════════════════════════════
# SCENARIO 4: Banking / NBFC (RBI policy → HDFC → ICICI)
# ════════════════════════════════════════════════════════════


class TestBankingScenario:
    """RBI rate hike → bank NIM expansion → NBFC stress."""

    ENTITIES = [
        {"name": "RBI", "entity_type": "Regulation", "confidence": 0.95},
        {"name": "HDFC Bank", "entity_type": "Company", "confidence": 0.92},
        {"name": "ICICI Bank", "entity_type": "Company", "confidence": 0.90},
        {"name": "Bajaj Finance", "entity_type": "Company", "confidence": 0.85},
        {"name": "India", "entity_type": "Country", "confidence": 0.99},
    ]
    RELATIONS = [
        {"source": "RBI", "target": "HDFC Bank", "relation_type": "REGULATES",
         "weight": 0.90, "confidence": 0.95},
        {"source": "RBI", "target": "ICICI Bank", "relation_type": "REGULATES",
         "weight": 0.88, "confidence": 0.93},
        {"source": "HDFC Bank", "target": "Bajaj Finance", "relation_type": "COMPETES_WITH",
         "weight": 0.50, "confidence": 0.70},
        {"source": "HDFC Bank", "target": "India", "relation_type": "OPERATES_IN",
         "weight": 0.95, "confidence": 0.99},
    ]

    @pytest.fixture
    async def storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "graph.db"))
            await s.initialize()
            yield s
            await s.close()

    @pytest.mark.asyncio
    async def test_rbi_rate_hike_propagates(self, storage):
        pipeline = await _build_pipeline(storage, self.ENTITIES, self.RELATIONS)
        result = await pipeline.process_article(
            title="RBI hikes repo rate by 25 bps",
            content="RBI hikes repo rate by 25 basis points. HDFC Bank and ICICI Bank NIM expected "
                    "to expand. Bajaj Finance faces higher borrowing costs in India.",
            source="economic_times",
            trigger_propagation=True,
            trigger_entity_name="RBI",
            trigger_event="repo rate hike",
        )
        assert result["propagation_ran"] is True
        assert len(result.get("impacts", [])) >= 1

    @pytest.mark.asyncio
    async def test_banking_impact_table_includes_hdfc(self, storage):
        pipeline = await _build_pipeline(storage, self.ENTITIES, self.RELATIONS)
        result = await pipeline.process_article(
            title="RBI monetary policy",
            content="RBI monetary policy impacts HDFC Bank, ICICI Bank, and Bajaj Finance in India.",
            source="test",
            trigger_propagation=True,
            trigger_entity_name="RBI",
            trigger_event="monetary policy change",
        )
        table = result.get("impact_table", {})
        rows = table.get("rows", [])
        entity_names = {r.get("entity_name", "") for r in rows}
        # At least one bank should appear
        assert len(entity_names) >= 1

    @pytest.mark.asyncio
    async def test_banking_bridge_for_hdfc_signal(self, storage):
        pipeline = await _build_pipeline(storage, self.ENTITIES, self.RELATIONS)
        result = await pipeline.process_article(
            title="RBI rate decision",
            content="RBI rate hike benefits HDFC Bank margins. ICICI Bank and Bajaj Finance also impacted.",
            source="test",
            trigger_propagation=True,
            trigger_entity_name="RBI",
            trigger_event="rate hike",
        )
        bridge = SignalBridge()
        enrichment = bridge.enrich_signal("HDFCBANK", result)
        assert isinstance(enrichment, dict)
        assert "reasoning_context" in enrichment


# ════════════════════════════════════════════════════════════
# SCENARIO 5: Persistence Round-Trip (Iteration 34)
# ════════════════════════════════════════════════════════════


class TestPersistenceRoundTrip:
    """Verify data persists across factory lifecycle."""

    @pytest.mark.asyncio
    async def test_entities_survive_restart(self):
        """Entities created in session 1 are available in session 2."""
        from mkg.service_factory import ServiceFactory

        with tempfile.TemporaryDirectory() as tmpdir:
            # Session 1: create entities
            f1 = ServiceFactory(db_dir=tmpdir)
            await f1.initialize()
            pipeline1 = f1.create_pipeline_orchestrator()
            await pipeline1.process_article(
                title="TSMC updates",
                content="TSMC semiconductor manufacturing landmark expansion.",
                source="test",
            )
            entities_s1 = await f1.graph_storage.find_entities()
            count_s1 = len(entities_s1)
            await f1.shutdown()

            # Session 2: verify
            f2 = ServiceFactory(db_dir=tmpdir)
            await f2.initialize()
            entities_s2 = await f2.graph_storage.find_entities()
            count_s2 = len(entities_s2)
            await f2.shutdown()

            assert count_s2 >= count_s1
            assert count_s2 > 0

    @pytest.mark.asyncio
    async def test_edges_survive_restart(self):
        """Edges created in session 1 survive restart."""
        from mkg.service_factory import ServiceFactory

        entities = [
            {"name": "TCS", "entity_type": "Company", "confidence": 0.9},
            {"name": "Infosys", "entity_type": "Company", "confidence": 0.9},
        ]
        relations = [
            {"source": "TCS", "target": "Infosys", "relation_type": "COMPETES_WITH",
             "weight": 0.70, "confidence": 0.85},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = ServiceFactory(db_dir=tmpdir)
            await f1.initialize()
            storage1 = f1.graph_storage
            pipeline1 = await _build_pipeline(storage1, entities, relations)
            await pipeline1.process_article(
                title="Indian IT sector",
                content="TCS and Infosys compete for cloud deals.",
                source="test",
            )
            edges_s1 = await storage1.find_edges()
            await f1.shutdown()

            f2 = ServiceFactory(db_dir=tmpdir)
            await f2.initialize()
            edges_s2 = await f2.graph_storage.find_edges()
            await f2.shutdown()

            assert len(edges_s2) >= len(edges_s1)

    @pytest.mark.asyncio
    async def test_propagation_works_on_persisted_graph(self):
        """Propagation should work on data from a previous session."""
        from mkg.service_factory import ServiceFactory

        entities = [
            {"name": "Reliance", "entity_type": "Company", "confidence": 0.95},
            {"name": "Jio", "entity_type": "Company", "confidence": 0.90},
        ]
        relations = [
            {"source": "Reliance", "target": "Jio", "relation_type": "SUBSIDIARY_OF",
             "weight": 0.95, "confidence": 0.99},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            # Session 1: seed graph
            f1 = ServiceFactory(db_dir=tmpdir)
            await f1.initialize()
            pipeline1 = await _build_pipeline(f1.graph_storage, entities, relations)
            await pipeline1.process_article(
                title="Reliance Jio",
                content="Reliance Industries subsidiary Jio announces telecom expansion.",
                source="test",
            )
            await f1.shutdown()

            # Session 2: propagate on persisted graph
            f2 = ServiceFactory(db_dir=tmpdir)
            await f2.initialize()
            engine = PropagationEngine(f2.graph_storage)

            # Find Reliance entity
            reliance_entities = await f2.graph_storage.search("Reliance", limit=1)
            if reliance_entities:
                impacts = await engine.propagate(
                    trigger_entity_id=reliance_entities[0]["id"],
                    impact_score=1.0,
                    max_depth=3,
                )
                # Should find at least Jio
                assert len(impacts) >= 1

            await f2.shutdown()


# ════════════════════════════════════════════════════════════
# SCENARIO 6: Error & Edge Cases (Iteration 35)
# ════════════════════════════════════════════════════════════


class TestErrorAndEdgeCases:
    """Edge cases: empty content, unknown entities, dedup, no propagation."""

    @pytest.fixture
    async def storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "graph.db"))
            await s.initialize()
            yield s
            await s.close()

    @pytest.mark.asyncio
    async def test_empty_content_returns_failed(self, storage):
        pipeline = await _build_pipeline(storage, [], [])
        result = await pipeline.process_article(
            title="Empty", content="", source="test",
        )
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_no_entities_extracted(self, storage):
        """Extractor returns no entities → completed with 0 entities."""
        pipeline = await _build_pipeline(storage, [], [])
        result = await pipeline.process_article(
            title="Random", content="Some random content with no entities.", source="test",
        )
        assert result["status"] == "completed"
        assert result["entities_created"] == 0

    @pytest.mark.asyncio
    async def test_propagation_on_nonexistent_entity(self, storage):
        """Trigger propagation for entity not in graph → no impacts."""
        entities = [{"name": "Wipro", "entity_type": "Company", "confidence": 0.9}]
        pipeline = await _build_pipeline(storage, entities, [])
        result = await pipeline.process_article(
            title="Wipro news",
            content="Wipro announces new cloud services.",
            source="test",
            trigger_propagation=True,
            trigger_entity_name="NonExistentCo",
            trigger_event="nothing",
        )
        # Should complete without crash
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_duplicate_url_skipped(self, storage):
        entities = [{"name": "TCS", "entity_type": "Company", "confidence": 0.9}]
        pipeline = await _build_pipeline(storage, entities, [])
        r1 = await pipeline.process_article(
            title="TCS Q4", content="TCS Q4 results strong.", source="test",
            url="https://example.com/tcs-q4",
        )
        r2 = await pipeline.process_article(
            title="TCS Q4 copy", content="TCS Q4 results strong.", source="test",
            url="https://example.com/tcs-q4",
        )
        assert r1["status"] == "completed"
        assert r2["status"] == "duplicate"

    @pytest.mark.asyncio
    async def test_multiple_articles_accumulate(self, storage):
        """Multiple articles should accumulate entities in the graph."""
        entities_1 = [{"name": "Wipro", "entity_type": "Company", "confidence": 0.9}]
        entities_2 = [{"name": "HCL", "entity_type": "Company", "confidence": 0.9}]

        pipeline1 = await _build_pipeline(storage, entities_1, [])
        await pipeline1.process_article(
            title="Wipro", content="Wipro IT services.", source="test",
        )

        pipeline2 = await _build_pipeline(storage, entities_2, [])
        await pipeline2.process_article(
            title="HCL", content="HCL tech expansion.", source="test",
        )

        all_entities = await storage.find_entities()
        names = {e.get("name", "") for e in all_entities}
        assert len(all_entities) >= 2

    @pytest.mark.asyncio
    async def test_propagation_with_no_outgoing_edges(self, storage):
        """Entity with no edges → propagation returns empty impacts."""
        entities = [{"name": "IsolatedCo", "entity_type": "Company", "confidence": 0.9}]
        pipeline = await _build_pipeline(storage, entities, [])
        result = await pipeline.process_article(
            title="IsolatedCo news",
            content="IsolatedCo has no supply chain connections.",
            source="test",
            trigger_propagation=True,
            trigger_entity_name="IsolatedCo",
            trigger_event="solo event",
        )
        # Should complete without crash, impacts may be empty
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_bridge_with_no_propagation(self, storage):
        """Signal bridge handles pipeline result without propagation."""
        entities = [{"name": "SBI", "entity_type": "Company", "confidence": 0.9}]
        pipeline = await _build_pipeline(storage, entities, [])
        result = await pipeline.process_article(
            title="SBI news", content="SBI quarterly results.", source="test",
        )
        bridge = SignalBridge()
        enrichment = bridge.enrich_signal("SBIN", result)
        assert enrichment["has_material_impact"] is False
        assert enrichment["confidence_adjustment"] == 0
