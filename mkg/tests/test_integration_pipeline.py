# mkg/tests/test_integration_pipeline.py
"""Integration tests — end-to-end pipeline exercising multiple components.

Iterations 21-25: Tests that verify components work together correctly,
from article ingestion through to alert generation.
"""

import pytest


class TestArticleToGraphPipeline:
    """Integration: Article → Extraction → Graph Mutation → Verification."""

    @pytest.fixture
    async def pipeline(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.infrastructure.llm.regex_extractor import RegexExtractor
        from mkg.domain.services.graph_mutation import GraphMutationService
        from mkg.domain.services.canonical_registry import CanonicalEntityRegistry
        from mkg.domain.services.hallucination_verifier import HallucinationVerifier
        from mkg.domain.services.article_pipeline import ArticleIngestionPipeline
        from mkg.domain.services.article_dedup import ArticleDedup

        store = InMemoryGraphStorage()
        registry = CanonicalEntityRegistry(load_defaults=True)
        extractor = RegexExtractor()
        mutation = GraphMutationService(store, registry)
        verifier = HallucinationVerifier()
        pipeline = ArticleIngestionPipeline()
        dedup = ArticleDedup()

        return {
            "store": store,
            "extractor": extractor,
            "mutation": mutation,
            "verifier": verifier,
            "pipeline": pipeline,
            "dedup": dedup,
        }

    @pytest.mark.asyncio
    async def test_full_article_to_graph_flow(self, pipeline):
        """Ingest article → extract → verify → mutate graph."""
        p = pipeline
        text = "TSMC supplies advanced 3nm chips to NVIDIA for GPU production"

        # Step 1: Ingest article
        article = await p["pipeline"].ingest({
            "title": "TSMC-NVIDIA Partnership",
            "content": text,
            "source": "reuters",
            "url": "https://reuters.com/test-article-1",
        })
        assert article["id"] is not None

        # Step 2: Check dedup
        dedup_result = p["dedup"].check_article(
            url="https://reuters.com/test-article-1", content=text
        )
        assert dedup_result["is_duplicate"] is False
        p["dedup"].mark_seen_url("https://reuters.com/test-article-1")
        p["dedup"].mark_seen_content(text)

        # Step 3: Extract entities + relations
        extraction = await p["extractor"].extract_all(text)
        assert len(extraction["entities"]) >= 2

        # Step 4: Verify against source text
        verified = p["verifier"].verify_result(extraction, text)
        assert verified["stats"]["entities_verified"] >= 2

        # Step 5: Mutate graph
        result = await p["mutation"].apply(verified, source=article["id"])
        assert result["entities"]["created"] >= 2

        # Step 6: Verify graph state
        entities = await p["store"].find_entities(entity_type="Company")
        names = [e.get("canonical_name", e.get("name")) for e in entities]
        assert "TSMC" in names
        assert "NVIDIA" in names

    @pytest.mark.asyncio
    async def test_duplicate_article_rejected(self, pipeline):
        p = pipeline
        text = "TSMC announces quarterly earnings"
        url = "https://reuters.com/tsmc-earnings"

        # First check should pass
        result1 = p["dedup"].check_article(url, text)
        assert result1["is_duplicate"] is False
        p["dedup"].mark_seen_url(url)
        p["dedup"].mark_seen_content(text)

        # Second check should detect duplicate
        result2 = p["dedup"].check_article(url, text)
        assert result2["is_duplicate"] is True

    @pytest.mark.asyncio
    async def test_hallucination_filtering_in_pipeline(self, pipeline):
        """Entities not in source text should be filtered out."""
        p = pipeline
        text = "TSMC reported strong quarterly results"

        extraction = await p["extractor"].extract_all(text)
        # Manually inject a hallucinated entity
        extraction["entities"].append({
            "name": "FakeCompany123",
            "entity_type": "Company",
            "confidence": 0.9,
        })

        verified = p["verifier"].verify_result(extraction, text)
        names = [e["name"] for e in verified["entities"]]
        assert "FakeCompany123" not in names


class TestPropagationToAlertPipeline:
    """Integration: Graph Event → Propagation → Chain Building → Alert."""

    @pytest.fixture
    async def system(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.propagation_engine import PropagationEngine
        from mkg.domain.services.causal_chain_builder import CausalChainBuilder
        from mkg.domain.services.alert_system import AlertSystem
        from mkg.domain.services.impact_table import ImpactTableBuilder

        store = InMemoryGraphStorage()
        # Build supply chain: TSMC -> NVIDIA -> AMD
        await store.create_entity("Company", {"name": "TSMC"}, entity_id="tsmc")
        await store.create_entity("Company", {"name": "NVIDIA"}, entity_id="nvidia")
        await store.create_entity("Company", {"name": "AMD"}, entity_id="amd")
        await store.create_entity("Sector", {"name": "AI Chips"}, entity_id="ai-chips")
        await store.create_edge("tsmc", "nvidia", "SUPPLIES_TO",
                                {"weight": 0.9, "confidence": 0.9})
        await store.create_edge("tsmc", "amd", "SUPPLIES_TO",
                                {"weight": 0.7, "confidence": 0.8})
        await store.create_edge("nvidia", "ai-chips", "OPERATES_IN",
                                {"weight": 0.6, "confidence": 0.7})

        engine = PropagationEngine(store)
        chain_builder = CausalChainBuilder(store)
        alert_system = AlertSystem()
        impact_table = ImpactTableBuilder(store)

        return {
            "store": store,
            "engine": engine,
            "chain_builder": chain_builder,
            "alert_system": alert_system,
            "impact_table": impact_table,
        }

    @pytest.mark.asyncio
    async def test_full_event_to_alert_flow(self, system):
        """Trigger event → propagate → build chains → generate alerts."""
        s = system

        # Step 1: Propagate impact
        results = await s["engine"].propagate(
            trigger_entity_id="tsmc",
            impact_score=1.0,
        )
        assert len(results) >= 2  # NVIDIA + AMD at minimum

        # Step 2: Build causal chains
        chains = await s["chain_builder"].build_chains(
            trigger_entity_id="tsmc",
            trigger_event="TSMC factory fire",
            propagation_results=results,
        )
        assert len(chains) >= 2
        for chain in chains:
            assert "narrative" in chain
            assert chain["impact_score"] > 0

        # Step 3: Generate alerts
        alerts = s["alert_system"].generate_alerts(chains)
        assert len(alerts) >= 1
        for alert in alerts:
            assert alert["severity"] in ("critical", "high", "medium", "low")

        # Step 4: Build impact table
        table = await s["impact_table"].build(results, trigger_name="TSMC fire")
        assert table["total"] >= 2
        assert table["rows"][0]["impact_score"] >= table["rows"][-1]["impact_score"]

    @pytest.mark.asyncio
    async def test_minor_event_produces_no_alerts(self, system):
        """Low-impact event should not generate high-severity alerts."""
        s = system

        results = await s["engine"].propagate(
            trigger_entity_id="tsmc",
            impact_score=0.1,  # Low impact
        )

        chains = await s["chain_builder"].build_chains(
            trigger_entity_id="tsmc",
            trigger_event="Minor TSMC scheduling change",
            propagation_results=results,
        )

        # Filter for high-severity only
        alerts = s["alert_system"].generate_alerts(chains, min_severity="critical")
        assert len(alerts) == 0  # Minor event shouldn't generate critical alerts

    @pytest.mark.asyncio
    async def test_chain_narratives_are_readable(self, system):
        s = system
        results = await s["engine"].propagate("tsmc", impact_score=1.0)
        chains = await s["chain_builder"].build_chains(
            "tsmc", "TSMC production halt", results
        )
        for chain in chains:
            narrative = chain["narrative"]
            assert "TSMC" in narrative
            assert "%" in narrative  # Impact percentage
            assert len(narrative) > 20  # Meaningful text


class TestWeightAdjustmentWithPropagation:
    """Integration: Weight decay affects propagation results."""

    @pytest.fixture
    async def system(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.weight_adjustment import WeightAdjustmentService
        from mkg.domain.services.propagation_engine import PropagationEngine

        store = InMemoryGraphStorage()
        await store.create_entity("Company", {"name": "A"}, entity_id="a")
        await store.create_entity("Company", {"name": "B"}, entity_id="b")
        await store.create_edge("a", "b", "SUPPLIES_TO",
                                {"weight": 0.9, "confidence": 0.9}, edge_id="e1")

        weight_svc = WeightAdjustmentService(store)
        engine = PropagationEngine(store)

        return {
            "store": store,
            "weight_svc": weight_svc,
            "engine": engine,
        }

    @pytest.mark.asyncio
    async def test_weight_decay_reduces_propagation_impact(self, system):
        s = system

        # Propagate before decay
        before = await s["engine"].propagate("a", impact_score=1.0)
        impact_before = before[0]["impact"]

        # Apply weight update (reduce weight)
        await s["weight_svc"].update_edge_weight(
            edge_id="e1",
            new_evidence_weight=0.3,
            evidence_confidence=0.95,
        )

        # Propagate after decay
        after = await s["engine"].propagate("a", impact_score=1.0)
        impact_after = after[0]["impact"]

        assert impact_after < impact_before


class TestDLQWithArticlePipeline:
    """Integration: Failed articles go to DLQ and can be retried."""

    @pytest.mark.asyncio
    async def test_failed_article_to_dlq_flow(self):
        from mkg.domain.services.article_pipeline import ArticleIngestionPipeline
        from mkg.domain.services.dlq import DeadLetterQueue

        pipeline = ArticleIngestionPipeline()
        dlq = DeadLetterQueue(max_retries=3)

        # Ingest article
        article = await pipeline.ingest({
            "title": "Test Article",
            "content": "Some content about TSMC",
            "source": "test",
        })

        # Simulate extraction failure → add to DLQ
        await dlq.add(article["id"], "extraction_timeout", {"error": "timeout"})

        # DLQ should have the item
        stats = await dlq.get_stats()
        assert stats["total"] == 1
        assert stats["retriable"] == 1

        # After max retries, item is exhausted
        for _ in range(3):
            await dlq.increment_retry(article["id"])
        assert await dlq.is_exhausted(article["id"]) is True

        # On successful retry, remove from DLQ
        await dlq.remove(article["id"])
        stats = await dlq.get_stats()
        assert stats["total"] == 0
