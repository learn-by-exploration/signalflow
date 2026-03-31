# mkg/tests/test_tribal_knowledge.py
"""Tests for TribalKnowledgeInput — human expert knowledge injection.

R-TK1 through R-TK5: Manual entity/edge creation, confidence overrides,
annotation, and audit trail.
"""

import pytest


class TestTribalKnowledgeInput:

    @pytest.fixture
    async def service(self):
        from mkg.infrastructure.in_memory.graph_storage import InMemoryGraphStorage
        from mkg.domain.services.tribal_knowledge import TribalKnowledgeInput
        store = InMemoryGraphStorage()
        return TribalKnowledgeInput(store), store

    @pytest.mark.asyncio
    async def test_add_expert_entity(self, service):
        svc, store = service
        result = await svc.add_entity(
            name="GlobalFoundries",
            entity_type="Company",
            expert="analyst-1",
            notes="Major chip foundry, TSMC competitor",
        )
        assert result["name"] == "GlobalFoundries"
        assert result.get("source") == "expert:analyst-1"

    @pytest.mark.asyncio
    async def test_add_expert_edge(self, service):
        svc, store = service
        await store.create_entity("Company", {"name": "TSMC"}, entity_id="tsmc")
        await store.create_entity("Company", {"name": "GF"}, entity_id="gf")
        result = await svc.add_edge(
            source_id="tsmc",
            target_id="gf",
            relation_type="COMPETES_WITH",
            weight=0.75,
            expert="analyst-1",
            notes="Direct foundry competition",
        )
        assert result["relation_type"] == "COMPETES_WITH"

    @pytest.mark.asyncio
    async def test_override_confidence(self, service):
        svc, store = service
        await store.create_entity("Company", {"name": "TSMC", "confidence": 0.5}, entity_id="tsmc")
        result = await svc.override_confidence(
            entity_id="tsmc",
            new_confidence=0.95,
            expert="analyst-1",
            reason="Verified primary source",
        )
        assert result["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_add_annotation(self, service):
        svc, store = service
        await store.create_entity("Company", {"name": "TSMC"}, entity_id="tsmc")
        result = await svc.annotate(
            entity_id="tsmc",
            annotation="Key supplier for iPhone chips",
            expert="analyst-1",
        )
        annotations = result.get("annotations", [])
        assert len(annotations) == 1
        assert "Key supplier" in annotations[0]["text"]

    @pytest.mark.asyncio
    async def test_audit_trail(self, service):
        svc, store = service
        await store.create_entity("Company", {"name": "TSMC", "confidence": 0.5}, entity_id="tsmc")
        await svc.override_confidence("tsmc", 0.9, "analyst-1", "Verified")
        trail = svc.get_audit_trail()
        assert len(trail) == 1
        assert trail[0]["action"] == "override_confidence"
        assert trail[0]["expert"] == "analyst-1"

    @pytest.mark.asyncio
    async def test_expert_attribution(self, service):
        svc, store = service
        result = await svc.add_entity(
            name="Intel",
            entity_type="Company",
            expert="analyst-2",
        )
        entity = await store.get_entity(result["id"])
        assert entity["source"] == "expert:analyst-2"
