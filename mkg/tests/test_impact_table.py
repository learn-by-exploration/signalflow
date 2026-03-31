# mkg/tests/test_impact_table.py
"""Tests for ImpactTableBuilder — builds ranked impact table data for the UI.

R-UI1 through R-UI5: Ranks affected entities by impact, enriches with
metadata, formats for frontend rendering.
"""

import pytest


class TestImpactTableBuilder:

    @pytest.fixture
    async def builder(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.impact_table import ImpactTableBuilder
        store = InMemoryGraphStorage()
        await store.create_entity("Company", {"name": "TSMC", "canonical_name": "TSMC"}, entity_id="tsmc")
        await store.create_entity("Company", {"name": "NVIDIA", "canonical_name": "NVIDIA"}, entity_id="nvidia")
        await store.create_entity("Company", {"name": "AMD", "canonical_name": "AMD"}, entity_id="amd")
        return ImpactTableBuilder(store), store

    @pytest.mark.asyncio
    async def test_build_from_propagation(self, builder):
        bld, _ = builder
        results = [
            {"entity_id": "nvidia", "impact": 0.9, "depth": 1, "path": ["tsmc", "nvidia"]},
            {"entity_id": "amd", "impact": 0.5, "depth": 1, "path": ["tsmc", "amd"]},
        ]
        table = await bld.build(results)
        assert len(table["rows"]) == 2

    @pytest.mark.asyncio
    async def test_rows_ranked_by_impact(self, builder):
        bld, _ = builder
        results = [
            {"entity_id": "amd", "impact": 0.5, "depth": 1, "path": ["tsmc", "amd"]},
            {"entity_id": "nvidia", "impact": 0.9, "depth": 1, "path": ["tsmc", "nvidia"]},
        ]
        table = await bld.build(results)
        assert table["rows"][0]["entity_name"] == "NVIDIA"
        assert table["rows"][1]["entity_name"] == "AMD"

    @pytest.mark.asyncio
    async def test_row_has_required_fields(self, builder):
        bld, _ = builder
        results = [
            {"entity_id": "nvidia", "impact": 0.9, "depth": 1, "path": ["tsmc", "nvidia"]},
        ]
        table = await bld.build(results)
        row = table["rows"][0]
        assert "rank" in row
        assert "entity_id" in row
        assert "entity_name" in row
        assert "entity_type" in row
        assert "impact_score" in row
        assert "impact_pct" in row
        assert "depth" in row

    @pytest.mark.asyncio
    async def test_impact_pct_is_percentage(self, builder):
        bld, _ = builder
        results = [
            {"entity_id": "nvidia", "impact": 0.85, "depth": 1, "path": ["tsmc", "nvidia"]},
        ]
        table = await bld.build(results)
        assert table["rows"][0]["impact_pct"] == 85

    @pytest.mark.asyncio
    async def test_empty_results(self, builder):
        bld, _ = builder
        table = await bld.build([])
        assert table["rows"] == []
        assert table["total"] == 0

    @pytest.mark.asyncio
    async def test_table_metadata(self, builder):
        bld, _ = builder
        results = [
            {"entity_id": "nvidia", "impact": 0.9, "depth": 1, "path": ["tsmc", "nvidia"]},
        ]
        table = await bld.build(results, trigger_name="TSMC fire")
        assert table["trigger"] == "TSMC fire"
        assert table["total"] == 1

    @pytest.mark.asyncio
    async def test_table_with_unknown_entity(self, builder):
        """Entity not in storage should use entity_id as name."""
        bld, _ = builder
        results = [
            {"entity_id": "unknown-x", "impact": 0.7, "depth": 1, "path": ["tsmc", "unknown-x"]},
        ]
        table = await bld.build(results)
        assert table["rows"][0]["entity_name"] == "unknown-x"
        assert table["rows"][0]["entity_type"] == "Unknown"

    @pytest.mark.asyncio
    async def test_table_rows_have_sequential_ranks(self, builder):
        bld, _ = builder
        results = [
            {"entity_id": "nvidia", "impact": 0.9, "depth": 1, "path": ["tsmc", "nvidia"]},
            {"entity_id": "amd", "impact": 0.5, "depth": 1, "path": ["tsmc", "amd"]},
        ]
        table = await bld.build(results)
        ranks = [row["rank"] for row in table["rows"]]
        assert ranks == [1, 2]

    @pytest.mark.asyncio
    async def test_table_trigger_defaults_to_none(self, builder):
        bld, _ = builder
        table = await bld.build([])
        assert table["trigger"] is None
