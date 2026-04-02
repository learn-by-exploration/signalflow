# mkg/tests/test_phase_d_mirofish_dashboard.py
"""Phase D — MiroFish + Dashboard.

TDD Red tests for:
  D1: MiroFish sidecar interface
  D2: Cross-graph entity resolution
  D3: Event feed bridge
  D4: WebSocket real-time stream
  D5: Graph export (JSON/CSV)
"""

import pytest
import json
from datetime import datetime, timezone

from mkg.infrastructure.sqlite.graph_storage import SQLiteGraphStorage


@pytest.fixture
async def storage():
    s = SQLiteGraphStorage(":memory:")
    await s.initialize()
    yield s
    await s.close()


async def _seed_graph(storage):
    """Create a small test graph."""
    await storage.create_entity("Company", {"name": "TSMC", "canonical_name": "TSMC"}, "tsmc")
    await storage.create_entity("Company", {"name": "NVIDIA", "canonical_name": "NVIDIA"}, "nvidia")
    await storage.create_entity("Sector", {"name": "Semiconductors", "canonical_name": "SEMICONDUCTORS"}, "semi")
    await storage.create_edge("tsmc", "nvidia", "SUPPLIES_TO", {
        "weight": 0.9, "confidence": 0.95, "direction": "positive",
    })
    await storage.create_edge("tsmc", "semi", "OPERATES_IN", {
        "weight": 0.85, "confidence": 1.0, "direction": "positive",
    })


# ── D1: MiroFish Sidecar Interface ──


class TestMiroFishInterface:
    """D1: MiroFish sidecar coordination service."""

    def test_mirofish_client_exists(self):
        """MiroFishClient class exists."""
        from mkg.domain.services.mirofish_client import MiroFishClient
        client = MiroFishClient(base_url="http://localhost:9000")
        assert client is not None

    def test_mirofish_client_has_required_methods(self):
        """Client has submit_propagation, get_status, simulate methods."""
        from mkg.domain.services.mirofish_client import MiroFishClient
        client = MiroFishClient(base_url="http://localhost:9000")
        assert hasattr(client, "submit_propagation")
        assert hasattr(client, "get_status")
        assert hasattr(client, "simulate")

    @pytest.mark.asyncio
    async def test_submit_propagation_format(self):
        """submit_propagation accepts trigger + results and formats them."""
        from mkg.domain.services.mirofish_client import MiroFishClient
        client = MiroFishClient(base_url="http://localhost:9000")
        payload = client.format_propagation(
            trigger_entity_id="tsmc",
            trigger_event="Earthquake in Taiwan",
            impact_score=0.9,
            results=[
                {"entity_id": "nvidia", "impact": 0.72, "depth": 1, "direction": "negative"},
            ],
        )
        assert payload["trigger"]["entity_id"] == "tsmc"
        assert len(payload["affected"]) == 1
        assert payload["affected"][0]["entity_id"] == "nvidia"

    def test_mirofish_client_configurable_timeout(self):
        """Client timeout is configurable."""
        from mkg.domain.services.mirofish_client import MiroFishClient
        client = MiroFishClient(base_url="http://localhost:9000", timeout_seconds=60)
        assert client._timeout == 60


# ── D2: Cross-Graph Entity Resolution ──


class TestCrossGraphEntityResolution:
    """D2: Map MKG entities to external system identifiers."""

    def test_entity_resolver_exists(self):
        """EntityResolver class exists."""
        from mkg.domain.services.entity_resolver import EntityResolver
        resolver = EntityResolver()
        assert resolver is not None

    def test_register_external_mapping(self):
        """Can register MKG entity -> external system mapping."""
        from mkg.domain.services.entity_resolver import EntityResolver
        resolver = EntityResolver()
        resolver.register("tsmc", "bloomberg", "TSM:US")
        result = resolver.resolve("tsmc", "bloomberg")
        assert result == "TSM:US"

    def test_reverse_lookup(self):
        """Can look up MKG entity from external ID."""
        from mkg.domain.services.entity_resolver import EntityResolver
        resolver = EntityResolver()
        resolver.register("tsmc", "bloomberg", "TSM:US")
        result = resolver.reverse_lookup("bloomberg", "TSM:US")
        assert result == "tsmc"

    def test_multiple_external_systems(self):
        """Same entity can map to multiple external systems."""
        from mkg.domain.services.entity_resolver import EntityResolver
        resolver = EntityResolver()
        resolver.register("tsmc", "bloomberg", "TSM:US")
        resolver.register("tsmc", "reuters", "2330.TW")
        resolver.register("tsmc", "yahoo", "TSM")
        assert resolver.resolve("tsmc", "bloomberg") == "TSM:US"
        assert resolver.resolve("tsmc", "reuters") == "2330.TW"
        assert resolver.resolve("tsmc", "yahoo") == "TSM"

    def test_resolve_unknown_returns_none(self):
        """Unknown entity/system returns None."""
        from mkg.domain.services.entity_resolver import EntityResolver
        resolver = EntityResolver()
        assert resolver.resolve("unknown", "bloomberg") is None

    def test_list_mappings(self):
        """Can list all external mappings for an entity."""
        from mkg.domain.services.entity_resolver import EntityResolver
        resolver = EntityResolver()
        resolver.register("tsmc", "bloomberg", "TSM:US")
        resolver.register("tsmc", "yahoo", "TSM")
        mappings = resolver.list_mappings("tsmc")
        assert len(mappings) == 2


# ── D3: Event Feed Bridge ──


class TestEventFeedBridge:
    """D3: Event subscription and feed for external consumers."""

    def test_event_feed_exists(self):
        """EventFeed class exists."""
        from mkg.domain.services.event_feed import EventFeed
        feed = EventFeed()
        assert feed is not None

    def test_subscribe_to_events(self):
        """Can subscribe to events with type filter."""
        from mkg.domain.services.event_feed import EventFeed
        feed = EventFeed()
        sub_id = feed.subscribe(
            callback_url="https://example.com/webhook",
            event_types=["propagation", "entity_created"],
            min_impact=0.5,
        )
        assert sub_id is not None

    def test_publish_event(self):
        """Publishing an event delivers to matching subscribers."""
        from mkg.domain.services.event_feed import EventFeed
        feed = EventFeed()
        delivered: list = []

        feed.subscribe(
            callback_url=None,
            event_types=["propagation"],
            min_impact=0.0,
            handler=lambda e: delivered.append(e),
        )

        feed.publish({
            "event_type": "propagation",
            "entity_id": "tsmc",
            "impact": 0.8,
        })
        assert len(delivered) == 1
        assert delivered[0]["entity_id"] == "tsmc"

    def test_filter_by_impact_threshold(self):
        """Events below min_impact aren't delivered."""
        from mkg.domain.services.event_feed import EventFeed
        feed = EventFeed()
        delivered: list = []

        feed.subscribe(
            callback_url=None,
            event_types=["propagation"],
            min_impact=0.7,
            handler=lambda e: delivered.append(e),
        )

        feed.publish({"event_type": "propagation", "entity_id": "a", "impact": 0.3})
        feed.publish({"event_type": "propagation", "entity_id": "b", "impact": 0.9})
        assert len(delivered) == 1
        assert delivered[0]["entity_id"] == "b"

    def test_unsubscribe(self):
        """After unsubscribing, events are not delivered."""
        from mkg.domain.services.event_feed import EventFeed
        feed = EventFeed()
        delivered: list = []

        sub_id = feed.subscribe(
            callback_url=None,
            event_types=["propagation"],
            handler=lambda e: delivered.append(e),
        )
        feed.unsubscribe(sub_id)
        feed.publish({"event_type": "propagation", "entity_id": "a", "impact": 0.5})
        assert len(delivered) == 0


# ── D5: Graph Export ──


class TestGraphExport:
    """D5: Export graph as JSON or CSV."""

    @pytest.mark.asyncio
    async def test_export_json(self, storage):
        """Export graph as JSON with nodes and edges."""
        from mkg.domain.services.graph_exporter import GraphExporter

        await _seed_graph(storage)
        exporter = GraphExporter(storage)
        data = await exporter.export_json()

        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 3
        assert len(data["edges"]) == 2

    @pytest.mark.asyncio
    async def test_export_json_filtered(self, storage):
        """Export filtered by entity type."""
        from mkg.domain.services.graph_exporter import GraphExporter

        await _seed_graph(storage)
        exporter = GraphExporter(storage)
        data = await exporter.export_json(entity_types=["Company"])

        assert len(data["nodes"]) == 2  # only companies

    @pytest.mark.asyncio
    async def test_export_csv(self, storage):
        """Export edges as CSV string."""
        from mkg.domain.services.graph_exporter import GraphExporter

        await _seed_graph(storage)
        exporter = GraphExporter(storage)
        csv_text = await exporter.export_csv()

        lines = [l.strip() for l in csv_text.strip().split("\n")]
        assert lines[0] == "source_id,target_id,relation_type,weight,confidence,direction"
        assert len(lines) == 3  # header + 2 edges

    @pytest.mark.asyncio
    async def test_export_json_with_metadata(self, storage):
        """JSON export includes metadata (timestamp, counts)."""
        from mkg.domain.services.graph_exporter import GraphExporter

        await _seed_graph(storage)
        exporter = GraphExporter(storage)
        data = await exporter.export_json()

        assert "metadata" in data
        assert "exported_at" in data["metadata"]
        assert data["metadata"]["node_count"] == 3
        assert data["metadata"]["edge_count"] == 2

    @pytest.mark.asyncio
    async def test_export_empty_graph(self, storage):
        """Export of empty graph returns empty lists."""
        from mkg.domain.services.graph_exporter import GraphExporter

        exporter = GraphExporter(storage)
        data = await exporter.export_json()

        assert data["nodes"] == []
        assert data["edges"] == []
        assert data["metadata"]["node_count"] == 0
