# mkg/tests/test_weight_adjustment.py
"""Tests for WeightAdjustmentService — Weighted Adjacency Network management.

R-WAN-1 through R-WAN-5: Edge weight decay, temporal adjustment,
confidence-weighted updates, and batch recalculation.
"""

import pytest
from datetime import datetime, timezone, timedelta


class TestWeightAdjustmentService:

    @pytest.fixture
    async def service(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.weight_adjustment import WeightAdjustmentService
        store = InMemoryGraphStorage()
        # Create two entities + an edge
        await store.create_entity("Company", {"name": "TSMC", "canonical_name": "TSMC"}, entity_id="tsmc")
        await store.create_entity("Company", {"name": "NVIDIA", "canonical_name": "NVIDIA"}, entity_id="nvidia")
        await store.create_edge(
            source_id="tsmc", target_id="nvidia",
            relation_type="SUPPLIES_TO",
            properties={"weight": 0.9, "confidence": 0.8},
            edge_id="edge-1",
        )
        return WeightAdjustmentService(store), store

    @pytest.mark.asyncio
    async def test_apply_time_decay(self, service):
        svc, store = service
        original = await store.get_edge("edge-1")
        decayed = svc.apply_time_decay(original["weight"], days_old=30, half_life_days=90)
        assert 0 < decayed < original["weight"]

    @pytest.mark.asyncio
    async def test_time_decay_zero_days_no_change(self, service):
        svc, _ = service
        result = svc.apply_time_decay(0.9, days_old=0, half_life_days=90)
        assert abs(result - 0.9) < 1e-6

    @pytest.mark.asyncio
    async def test_confidence_weighted_update(self, service):
        svc, store = service
        await svc.update_edge_weight(
            edge_id="edge-1",
            new_evidence_weight=0.7,
            evidence_confidence=0.95,
        )
        updated = await store.get_edge("edge-1")
        assert updated["weight"] != 0.9  # Changed from original

    @pytest.mark.asyncio
    async def test_weight_clamped_to_01(self, service):
        svc, store = service
        await svc.update_edge_weight(
            edge_id="edge-1",
            new_evidence_weight=1.5,
            evidence_confidence=1.0,
        )
        updated = await store.get_edge("edge-1")
        assert 0.0 <= updated["weight"] <= 1.0

    @pytest.mark.asyncio
    async def test_batch_decay_all_edges(self, service):
        svc, store = service
        # Add another edge
        await store.create_entity("Company", {"name": "AMD"}, entity_id="amd")
        await store.create_edge(
            source_id="nvidia", target_id="amd",
            relation_type="COMPETES_WITH",
            properties={"weight": 0.6, "confidence": 0.7},
            edge_id="edge-2",
        )
        results = await svc.batch_decay(days_old=60, half_life_days=90)
        assert results["edges_updated"] == 2

    @pytest.mark.asyncio
    async def test_decay_does_not_go_below_floor(self, service):
        svc, _ = service
        result = svc.apply_time_decay(0.1, days_old=3650, half_life_days=90)
        assert result >= svc.weight_floor

    @pytest.mark.asyncio
    async def test_get_edge_age_days(self, service):
        svc, store = service
        edge = await store.get_edge("edge-1")
        days = svc.get_edge_age_days(edge)
        assert days >= 0

    def test_weight_floor_validation_negative(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.weight_adjustment import WeightAdjustmentService
        with pytest.raises(ValueError, match="weight_floor must be in"):
            WeightAdjustmentService(InMemoryGraphStorage(), weight_floor=-0.1)

    def test_weight_floor_validation_one(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.weight_adjustment import WeightAdjustmentService
        with pytest.raises(ValueError, match="weight_floor must be in"):
            WeightAdjustmentService(InMemoryGraphStorage(), weight_floor=1.0)

    def test_weight_floor_validation_above_one(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.weight_adjustment import WeightAdjustmentService
        with pytest.raises(ValueError, match="weight_floor must be in"):
            WeightAdjustmentService(InMemoryGraphStorage(), weight_floor=2.5)

    def test_weight_floor_zero_is_valid(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.weight_adjustment import WeightAdjustmentService
        svc = WeightAdjustmentService(InMemoryGraphStorage(), weight_floor=0.0)
        assert svc.weight_floor == 0.0

    @pytest.mark.asyncio
    async def test_edge_age_with_z_suffix_timestamp(self, service):
        svc, store = service
        edge = {"created_at": "2020-01-01T00:00:00Z"}
        days = svc.get_edge_age_days(edge)
        assert days > 365  # Should be several years old

    @pytest.mark.asyncio
    async def test_edge_age_with_offset_timestamp(self, service):
        svc, store = service
        edge = {"created_at": "2020-01-01T00:00:00+05:30"}
        days = svc.get_edge_age_days(edge)
        assert days > 365

    @pytest.mark.asyncio
    async def test_edge_age_with_datetime_object(self, service):
        svc, _ = service
        past = datetime.now(timezone.utc) - timedelta(days=10)
        edge = {"created_at": past}
        days = svc.get_edge_age_days(edge)
        assert 9.9 < days < 10.1

    @pytest.mark.asyncio
    async def test_edge_age_with_naive_datetime(self, service):
        svc, _ = service
        past = datetime.utcnow() - timedelta(days=5)
        edge = {"created_at": past}
        days = svc.get_edge_age_days(edge)
        assert 4.9 < days < 5.1

    @pytest.mark.asyncio
    async def test_edge_age_with_none_created_at(self, service):
        svc, _ = service
        edge = {"created_at": None}
        assert svc.get_edge_age_days(edge) == 0.0

    @pytest.mark.asyncio
    async def test_edge_age_missing_created_at(self, service):
        svc, _ = service
        edge = {}
        assert svc.get_edge_age_days(edge) == 0.0

    @pytest.mark.asyncio
    async def test_edge_age_non_string_type(self, service):
        svc, _ = service
        edge = {"created_at": 12345}  # Integer, not string or datetime
        assert svc.get_edge_age_days(edge) == 0.0
