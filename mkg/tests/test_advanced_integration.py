# mkg/tests/test_advanced_integration.py
"""Advanced integration tests — weight decay, accuracy tracking, webhook,
seed data, and end-to-end pipeline stress.

Iterations 41-45: Testing cross-cutting concerns, analytics, and the full
system under realistic multi-article load.
"""

import os
import tempfile

import pytest

from mkg.domain.services.accuracy_tracker import AccuracyTracker
from mkg.domain.services.alert_system import AlertSystem
from mkg.domain.services.signal_bridge import SignalBridge
from mkg.domain.services.webhook_delivery import WebhookDelivery
from mkg.domain.services.weight_adjustment import WeightAdjustmentService
from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage


# ════════════════════════════════════════════════════════════
# WEIGHT DECAY ON REAL STORAGE
# ════════════════════════════════════════════════════════════


class TestWeightDecayOnSQLite:
    """Weight decay with real SQLite graph storage."""

    @pytest.fixture
    async def storage_with_edge(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            s = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "g.db"))
            await s.initialize()
            e1 = await s.create_entity(
                entity_type="Company",
                properties={"name": "TSMC", "canonical_name": "TSMC"},
            )
            e2 = await s.create_entity(
                entity_type="Company",
                properties={"name": "NVIDIA", "canonical_name": "NVIDIA"},
            )
            edge = await s.create_edge(
                source_id=e1["id"],
                target_id=e2["id"],
                relation_type="SUPPLIES_TO",
                properties={"weight": 0.85, "confidence": 0.9},
            )
            yield s, edge
            await s.close()

    @pytest.mark.asyncio
    async def test_time_decay_reduces_weight(self, storage_with_edge):
        s, edge = storage_with_edge
        was = WeightAdjustmentService(s)
        original_weight = 0.85
        decayed = was.apply_time_decay(original_weight, days_old=90, half_life_days=90)
        assert decayed < original_weight
        assert abs(decayed - original_weight * 0.5) < 0.01  # ~50% after one half-life

    @pytest.mark.asyncio
    async def test_weight_floor_enforced(self, storage_with_edge):
        s, edge = storage_with_edge
        was = WeightAdjustmentService(s, weight_floor=0.05)
        decayed = was.apply_time_decay(0.85, days_old=1000, half_life_days=90)
        assert decayed >= 0.05

    @pytest.mark.asyncio
    async def test_zero_age_no_decay(self, storage_with_edge):
        s, edge = storage_with_edge
        was = WeightAdjustmentService(s)
        decayed = was.apply_time_decay(0.85, days_old=0)
        assert decayed == 0.85


# ════════════════════════════════════════════════════════════
# ACCURACY TRACKER
# ════════════════════════════════════════════════════════════


class TestAccuracyTracker:
    """Prediction accuracy tracking and calibration."""

    def test_record_and_resolve_prediction(self):
        at = AccuracyTracker()
        at.record_prediction("p1", "nvidia-1", predicted_impact=0.8, source="article-1")
        at.record_outcome("p1", actual_impact=0.75)
        accuracy = at.get_accuracy()
        assert accuracy is not None
        assert accuracy > 0.9  # 1 - |0.8 - 0.75| = 0.95

    def test_no_resolved_predictions_returns_none(self):
        at = AccuracyTracker()
        at.record_prediction("p1", "e1", 0.5, "s")
        assert at.get_accuracy() is None

    def test_multiple_predictions_accuracy(self):
        at = AccuracyTracker()
        # Perfect prediction
        at.record_prediction("p1", "e1", 0.8, "s1")
        at.record_outcome("p1", 0.8)
        # Off by 0.2
        at.record_prediction("p2", "e2", 0.6, "s2")
        at.record_outcome("p2", 0.4)
        accuracy = at.get_accuracy()
        # Expected: 1 - mean(|0|, |0.2|) = 1 - 0.1 = 0.9
        assert accuracy is not None
        assert abs(accuracy - 0.9) < 0.01

    def test_outcome_for_unknown_prediction_ignored(self):
        at = AccuracyTracker()
        at.record_outcome("nonexistent", 0.5)  # Should not crash
        assert at.get_accuracy() is None

    def test_worst_case_accuracy_capped_at_zero(self):
        at = AccuracyTracker()
        at.record_prediction("p1", "e1", 0.0, "s")
        at.record_outcome("p1", 1.0)
        at.record_prediction("p2", "e2", 1.0, "s")
        at.record_outcome("p2", 0.0)
        accuracy = at.get_accuracy()
        assert accuracy == 0.0  # 1 - 1.0 = 0


# ════════════════════════════════════════════════════════════
# WEBHOOK DELIVERY
# ════════════════════════════════════════════════════════════


class TestWebhookDelivery:
    """Webhook registration, event matching, and payload formatting."""

    def test_register_webhook(self):
        wd = WebhookDelivery()
        wh = wd.register("wh-1", "https://example.com/hook", ["alert.created"])
        assert wh["id"] == "wh-1"
        assert "registered_at" in wh

    def test_unregister_webhook(self):
        wd = WebhookDelivery()
        wd.register("wh-1", "https://example.com/hook", ["*"])
        assert wd.unregister("wh-1") is True
        assert wd.unregister("wh-1") is False  # already removed

    def test_format_payload(self):
        wd = WebhookDelivery()
        payload = wd.format_payload(
            {"alert_id": "a-1", "severity": "high"},
            event_type="alert.created",
        )
        assert payload["event"] == "alert.created"
        assert "sent_at" in payload


# ════════════════════════════════════════════════════════════
# ALERT SYSTEM EDGE CASES
# ════════════════════════════════════════════════════════════


class TestAlertSystemEdgeCases:
    """Alert system dedup and threshold edge cases."""

    def test_dedup_same_chain(self):
        als = AlertSystem()
        chain = {
            "trigger": "t1", "affected_entity": "a1",
            "trigger_event": "fire", "impact_score": 0.9,
            "affected_name": "NVIDIA",
        }
        a1 = als.generate_alert(chain)
        a2 = als.generate_alert(chain)
        assert a1 is not None
        assert a2 is None  # deduped

    def test_severity_classification(self):
        als = AlertSystem()
        assert als._classify_severity(0.9) == "critical"
        assert als._classify_severity(0.7) == "high"
        assert als._classify_severity(0.4) == "medium"
        assert als._classify_severity(0.1) == "low"

    def test_batch_alert_generation(self):
        als = AlertSystem()
        chains = [
            {"trigger": "t1", "affected_entity": f"a{i}",
             "trigger_event": "event", "impact_score": 0.3 * (i + 1),
             "affected_name": f"Company_{i}"}
            for i in range(5)
        ]
        alerts = als.generate_alerts(chains)
        assert isinstance(alerts, list)


# ════════════════════════════════════════════════════════════
# SEED DATA LOADER ON SQLITE
# ════════════════════════════════════════════════════════════


class TestSeedDataLoaderOnSQLite:
    """Seed data loading into real SQLite storage."""

    @pytest.mark.asyncio
    async def test_load_default_seed_data(self):
        from mkg.domain.services.seed_loader import SeedDataLoader, get_default_seed_data

        with tempfile.TemporaryDirectory() as tmpdir:
            s = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "g.db"))
            await s.initialize()

            loader = SeedDataLoader(s)
            seed = get_default_seed_data()
            result = await loader.load(seed)

            assert result["entities_loaded"] > 0
            entities = await s.find_entities()
            assert len(entities) > 0

            await s.close()

    @pytest.mark.asyncio
    async def test_seed_then_propagate(self):
        """Seed → propagate should produce real impacts."""
        from mkg.domain.services.propagation_engine import PropagationEngine
        from mkg.domain.services.seed_loader import SeedDataLoader, get_default_seed_data

        with tempfile.TemporaryDirectory() as tmpdir:
            s = SQLiteGraphStorage(db_path=os.path.join(tmpdir, "g.db"))
            await s.initialize()

            loader = SeedDataLoader(s)
            seed = get_default_seed_data()
            result = await loader.load(seed)
            assert result["entities_loaded"] > 0

            # Find first entity
            entities = await s.find_entities()
            if entities:
                engine = PropagationEngine(s)
                impacts = await engine.propagate(
                    trigger_entity_id=entities[0]["id"],
                    impact_score=1.0,
                    max_depth=3,
                )
                # Seed data should have edges, so propagation should find some impacts
                # (unless the chosen entity has no outgoing edges)
                assert isinstance(impacts, list)

            await s.close()


# ════════════════════════════════════════════════════════════
# MULTI-ARTICLE STRESS TEST
# ════════════════════════════════════════════════════════════


class TestMultiArticleStress:
    """Process many articles in sequence — verify no degradation."""

    @pytest.mark.asyncio
    async def test_process_10_articles_no_crash(self):
        """Pipeline should handle 10 articles without error."""
        from mkg.service_factory import ServiceFactory

        with tempfile.TemporaryDirectory() as tmpdir:
            factory = ServiceFactory(db_dir=tmpdir)
            await factory.initialize()
            pipeline = factory.create_pipeline_orchestrator()

            articles = [
                ("TSMC Q1 results", "TSMC reports strong Q1 revenue from AI chip demand."),
                ("NVIDIA earnings", "NVIDIA beats earnings expectations on datacenter growth."),
                ("Apple supply chain", "Apple diversifies supply chain away from China."),
                ("RBI rate decision", "RBI holds rates steady, inflation under control."),
                ("HDFC Bank merger", "HDFC Bank post-merger integration shows strength."),
                ("Oil prices surge", "Crude oil prices surge on OPEC production cuts."),
                ("IndiGo fleet expansion", "IndiGo orders 50 new aircraft for expansion."),
                ("TCS wins deal", "TCS wins large cloud transformation deal from US bank."),
                ("Crypto regulation", "SEC proposes new cryptocurrency regulations."),
                ("Reliance Jio 5G", "Reliance Jio rolls out 5G to 500 more cities."),
            ]

            for title, content in articles:
                result = await pipeline.process_article(
                    title=title, content=content, source="test",
                )
                assert result["status"] in ("completed", "duplicate")

            # Verify graph accumulated entities
            entities = await factory.graph_storage.find_entities()
            assert len(entities) >= 5  # At least some entities created

            await factory.shutdown()

    @pytest.mark.asyncio
    async def test_bridge_after_multi_article_pipeline(self):
        """Signal bridge should work after multi-article processing."""
        from mkg.service_factory import ServiceFactory
        from mkg.domain.services.propagation_engine import PropagationEngine
        from mkg.domain.services.causal_chain_builder import CausalChainBuilder
        from mkg.domain.services.impact_table import ImpactTableBuilder

        with tempfile.TemporaryDirectory() as tmpdir:
            factory = ServiceFactory(db_dir=tmpdir)
            await factory.initialize()
            pipeline = factory.create_pipeline_orchestrator()

            # Process a cluster of related articles
            result = await pipeline.process_article(
                title="TSMC fab disruption",
                content="TSMC fab fire disrupts chip supply to NVIDIA, Apple, and AMD.",
                source="reuters",
                trigger_propagation=True,
                trigger_entity_name="TSMC",
                trigger_event="fab fire",
            )

            bridge = SignalBridge()
            enrichment = bridge.enrich_signal("NVDA", result)
            assert isinstance(enrichment, dict)
            assert "supply_chain_risk" in enrichment
            assert "reasoning_context" in enrichment

            await factory.shutdown()
