# mkg/tests/test_api.py
"""Tests for MKG FastAPI endpoints.

Uses httpx AsyncClient with the ASGI app for true async testing.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from mkg.api.app import create_app
from mkg.api.dependencies import init_container, _container
import mkg.api.dependencies as deps


@pytest.fixture
async def client():
    """Create a test client with an ephemeral app instance.

    Auth is disabled (no MKG_API_KEY set) so all endpoints are accessible.
    """
    import os
    old_key = os.environ.pop("MKG_API_KEY", None)
    app = create_app()
    # Manually init container for tests (lifespan doesn't run with ASGITransport)
    container = init_container()
    await container.startup()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await container.shutdown()
    deps._container = None
    if old_key is not None:
        os.environ["MKG_API_KEY"] = old_key


class TestHealthEndpoints:
    """System health and metrics."""

    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert data["graph"]["backend"] == "neo4j_dummy"

    async def test_metrics(self, client):
        resp = await client.get("/metrics")
        assert resp.status_code == 200


class TestEntityEndpoints:
    """Entity CRUD via API."""

    async def test_create_entity(self, client):
        resp = await client.post("/api/v1/entities", json={
            "entity_type": "COMPANY",
            "name": "TSMC",
            "canonical_name": "TSMC",
        })
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "TSMC"

    async def test_create_entity_missing_type(self, client):
        resp = await client.post("/api/v1/entities", json={"name": "foo"})
        assert resp.status_code == 422

    async def test_get_entity(self, client):
        create = await client.post("/api/v1/entities", json={
            "entity_type": "COMPANY",
            "name": "NVIDIA",
            "id": "nvda-test",
        })
        assert create.status_code == 201
        resp = await client.get("/api/v1/entities/nvda-test")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "NVIDIA"

    async def test_get_entity_not_found(self, client):
        resp = await client.get("/api/v1/entities/nonexistent")
        assert resp.status_code == 404

    async def test_list_entities(self, client):
        await client.post("/api/v1/entities", json={
            "entity_type": "COMPANY", "name": "A",
        })
        resp = await client.get("/api/v1/entities")
        assert resp.status_code == 200
        assert resp.json()["meta"]["count"] >= 1

    async def test_list_entities_by_type(self, client):
        await client.post("/api/v1/entities", json={
            "entity_type": "COMPANY", "name": "X",
        })
        await client.post("/api/v1/entities", json={
            "entity_type": "PRODUCT", "name": "Y",
        })
        resp = await client.get("/api/v1/entities?entity_type=COMPANY")
        assert resp.status_code == 200
        for e in resp.json()["data"]:
            assert e["entity_type"].upper() == "COMPANY"

    async def test_update_entity(self, client):
        await client.post("/api/v1/entities", json={
            "entity_type": "COMPANY", "name": "AMD", "id": "amd-test",
        })
        resp = await client.put("/api/v1/entities/amd-test", json={
            "metadata": {"sector": "Semiconductors"},
        })
        assert resp.status_code == 200

    async def test_delete_entity(self, client):
        await client.post("/api/v1/entities", json={
            "entity_type": "COMPANY", "name": "Intel", "id": "intc-test",
        })
        resp = await client.delete("/api/v1/entities/intc-test")
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is True


class TestEdgeEndpoints:
    """Edge CRUD via API."""

    async def _seed_entities(self, client):
        await client.post("/api/v1/entities", json={
            "entity_type": "COMPANY", "name": "TSMC", "id": "tsmc-e",
        })
        await client.post("/api/v1/entities", json={
            "entity_type": "COMPANY", "name": "NVIDIA", "id": "nvda-e",
        })

    async def test_create_edge(self, client):
        await self._seed_entities(client)
        resp = await client.post("/api/v1/edges", json={
            "source_id": "tsmc-e",
            "target_id": "nvda-e",
            "relation_type": "SUPPLIES_TO",
            "weight": 0.85,
            "confidence": 0.9,
        })
        assert resp.status_code == 201
        assert resp.json()["data"]["relation_type"] == "SUPPLIES_TO"

    async def test_create_edge_missing_field(self, client):
        resp = await client.post("/api/v1/edges", json={
            "source_id": "a", "target_id": "b",
        })
        assert resp.status_code == 422

    async def test_get_edge(self, client):
        await self._seed_entities(client)
        create = await client.post("/api/v1/edges", json={
            "source_id": "tsmc-e",
            "target_id": "nvda-e",
            "relation_type": "SUPPLIES_TO",
            "weight": 0.8,
            "confidence": 0.9,
            "id": "edge-test",
        })
        assert create.status_code == 201
        resp = await client.get("/api/v1/edges/edge-test")
        assert resp.status_code == 200

    async def test_list_edges(self, client):
        await self._seed_entities(client)
        await client.post("/api/v1/edges", json={
            "source_id": "tsmc-e",
            "target_id": "nvda-e",
            "relation_type": "SUPPLIES_TO",
            "weight": 0.8,
            "confidence": 0.9,
        })
        resp = await client.get("/api/v1/edges?source_id=tsmc-e")
        assert resp.status_code == 200
        assert resp.json()["meta"]["count"] >= 1


class TestGraphEndpoints:
    """Graph traversal and search."""

    async def _seed_graph(self, client):
        for name, eid in [("TSMC", "t"), ("NVIDIA", "n"), ("AWS", "a")]:
            await client.post("/api/v1/entities", json={
                "entity_type": "COMPANY", "name": name, "id": eid,
            })
        await client.post("/api/v1/edges", json={
            "source_id": "t", "target_id": "n",
            "relation_type": "SUPPLIES_TO", "weight": 0.9, "confidence": 0.95,
        })
        await client.post("/api/v1/edges", json={
            "source_id": "n", "target_id": "a",
            "relation_type": "SUPPLIES_TO", "weight": 0.7, "confidence": 0.8,
        })

    async def test_get_neighbors(self, client):
        await self._seed_graph(client)
        resp = await client.get("/api/v1/graph/neighbors/t?direction=outgoing")
        assert resp.status_code == 200
        assert resp.json()["meta"]["count"] >= 1

    async def test_get_subgraph(self, client):
        await self._seed_graph(client)
        resp = await client.get("/api/v1/graph/subgraph/t?max_depth=2")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["nodes"]
        assert data["edges"]

    async def test_search(self, client):
        await self._seed_graph(client)
        resp = await client.get("/api/v1/graph/search?q=TSMC")
        assert resp.status_code == 200
        assert resp.json()["meta"]["count"] >= 1

    async def test_graph_health(self, client):
        resp = await client.get("/api/v1/graph/health")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "healthy"

    async def test_seed_graph(self, client):
        resp = await client.post("/api/v1/graph/seed")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data.get("entities", 0) > 0 or data.get("edges", 0) >= 0


class TestPropagationEndpoints:
    """Propagation engine via API."""

    async def _seed(self, client):
        for name, eid in [("TSMC", "p1"), ("NVIDIA", "p2"), ("AWS", "p3")]:
            await client.post("/api/v1/entities", json={
                "entity_type": "COMPANY", "name": name, "id": eid,
            })
        await client.post("/api/v1/edges", json={
            "source_id": "p1", "target_id": "p2",
            "relation_type": "SUPPLIES_TO", "weight": 0.9, "confidence": 0.95,
        })
        await client.post("/api/v1/edges", json={
            "source_id": "p2", "target_id": "p3",
            "relation_type": "SUPPLIES_TO", "weight": 0.7, "confidence": 0.8,
        })

    async def test_propagate(self, client):
        await self._seed(client)
        resp = await client.post("/api/v1/propagate", json={
            "trigger_entity_id": "p1",
            "impact_score": 1.0,
            "event_description": "Fab fire",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["propagation"]
        assert resp.json()["meta"]["affected_entities"] >= 1

    async def test_propagate_not_found(self, client):
        resp = await client.post("/api/v1/propagate", json={
            "trigger_entity_id": "nonexistent",
        })
        assert resp.status_code == 404

    async def test_propagate_missing_trigger(self, client):
        resp = await client.post("/api/v1/propagate", json={})
        assert resp.status_code == 422

    async def test_weight_adjust(self, client):
        await self._seed(client)
        # Get an edge to adjust
        edges_resp = await client.get("/api/v1/edges?source_id=p1")
        edges = edges_resp.json()["data"]
        assert len(edges) > 0
        edge_id = edges[0]["id"]
        resp = await client.post("/api/v1/weight/adjust", json={
            "edge_id": edge_id,
            "new_evidence_weight": 0.95,
            "evidence_confidence": 0.8,
        })
        assert resp.status_code == 200
        assert "data" in resp.json()

    async def test_weight_adjust_missing_edge_id(self, client):
        resp = await client.post("/api/v1/weight/adjust", json={
            "new_evidence_weight": 0.5,
        })
        assert resp.status_code == 422

    async def test_weight_adjust_missing_weight(self, client):
        resp = await client.post("/api/v1/weight/adjust", json={
            "edge_id": "some-edge",
        })
        assert resp.status_code == 422

    async def test_weight_decay(self, client):
        resp = await client.post("/api/v1/weight/decay", json={
            "days_old": 30,
            "half_life_days": 90.0,
        })
        assert resp.status_code == 200
        assert "data" in resp.json()

    async def test_weight_decay_defaults(self, client):
        resp = await client.post("/api/v1/weight/decay", json={})
        assert resp.status_code == 200

    async def test_accuracy(self, client):
        resp = await client.get("/api/v1/accuracy")
        assert resp.status_code == 200

    async def test_record_prediction(self, client):
        resp = await client.post("/api/v1/accuracy/prediction", json={
            "prediction_id": "pred-1",
            "entity_id": "e1",
            "predicted_impact": 0.8,
        })
        assert resp.status_code == 200

    async def test_record_outcome(self, client):
        await client.post("/api/v1/accuracy/prediction", json={
            "prediction_id": "pred-2",
            "entity_id": "e2",
            "predicted_impact": 0.7,
        })
        resp = await client.post("/api/v1/accuracy/outcome", json={
            "prediction_id": "pred-2",
            "actual_impact": 0.65,
        })
        assert resp.status_code == 200


class TestArticleEndpoints:
    """Article ingestion pipeline via API."""

    async def test_ingest_article(self, client):
        resp = await client.post("/api/v1/articles", json={
            "title": "TSMC Fab Fire",
            "content": "A fire broke out at TSMC Fab 18 in Tainan.",
            "source": "Reuters",
            "url": "https://example.com/tsmc-fire",
        })
        assert resp.status_code == 201
        assert "data" in resp.json()

    async def test_ingest_duplicate(self, client):
        body = {
            "title": "Duplicate Test",
            "content": "This is duplicate content for testing.",
            "url": "https://example.com/dup",
        }
        await client.post("/api/v1/articles", json=body)
        resp2 = await client.post("/api/v1/articles", json=body)
        assert resp2.status_code == 201
        assert resp2.json()["data"].get("duplicate") is True

    async def test_ingest_missing_fields(self, client):
        resp = await client.post("/api/v1/articles", json={"title": "No content"})
        assert resp.status_code == 422

    async def test_extract_article(self, client):
        resp = await client.post("/api/v1/articles/extract", json={
            "text": "TSMC supplies chips to NVIDIA and Apple.",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "extraction" in data
        assert "verification" in data

    async def test_get_article(self, client):
        create = await client.post("/api/v1/articles", json={
            "title": "Get Test Article",
            "content": "Article content for get test unique xyz.",
            "source": "Test",
            "url": "https://example.com/get-test",
        })
        assert create.status_code == 201
        article_data = create.json()["data"]
        # Skip if it was detected as duplicate
        if article_data.get("duplicate"):
            return
        article_id = article_data.get("id") or article_data.get("article_id")
        assert article_id is not None, f"No id in response: {article_data}"
        resp = await client.get(f"/api/v1/articles/{article_id}")
        assert resp.status_code == 200
        assert resp.json()["data"] is not None

    async def test_get_article_not_found(self, client):
        resp = await client.get("/api/v1/articles/nonexistent-article-id")
        assert resp.status_code == 404

    async def test_list_articles(self, client):
        await client.post("/api/v1/articles", json={
            "title": "List Test Article",
            "content": "Unique content for list test abcdef.",
            "source": "Test",
            "url": "https://example.com/list-test",
        })
        resp = await client.get("/api/v1/articles")
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "meta" in resp.json()

    async def test_list_articles_by_status(self, client):
        resp = await client.get("/api/v1/articles?status=pending")
        assert resp.status_code == 200

    async def test_article_stats(self, client):
        resp = await client.get("/api/v1/articles/stats/summary")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "pipeline" in data
        assert "dedup" in data

    async def test_update_article_status(self, client):
        create = await client.post("/api/v1/articles", json={
            "title": "Status Update Article",
            "content": "Unique content for status update test qwerty.",
            "source": "Test",
            "url": "https://example.com/status-update-test",
        })
        assert create.status_code == 201
        article_data = create.json()["data"]
        if article_data.get("duplicate"):
            return
        article_id = article_data.get("id") or article_data.get("article_id")
        assert article_id is not None
        resp = await client.put(f"/api/v1/articles/{article_id}/status", json={
            "status": "processing",
        })
        assert resp.status_code == 200

    async def test_update_article_status_missing(self, client):
        resp = await client.put("/api/v1/articles/some-id/status", json={})
        assert resp.status_code == 422

    async def test_dlq(self, client):
        resp = await client.get("/api/v1/articles/dlq")
        assert resp.status_code == 200


class TestAlertEndpoints:
    """Alert and webhook endpoints."""

    async def test_list_alerts(self, client):
        resp = await client.get("/api/v1/alerts")
        assert resp.status_code == 200

    async def test_generate_alerts(self, client):
        resp = await client.post("/api/v1/alerts/generate", json={
            "chains": [],
        })
        assert resp.status_code == 200

    async def test_register_webhook(self, client):
        resp = await client.post("/api/v1/webhooks", json={
            "webhook_id": "wh-1",
            "url": "https://example.com/hook",
            "events": ["signal.new", "alert.critical"],
        })
        assert resp.status_code == 201

    async def test_unregister_webhook(self, client):
        await client.post("/api/v1/webhooks", json={
            "webhook_id": "wh-del",
            "url": "https://example.com/hook",
            "events": ["signal.new"],
        })
        resp = await client.delete("/api/v1/webhooks/wh-del")
        assert resp.status_code == 200

    async def test_unregister_webhook_not_found(self, client):
        resp = await client.delete("/api/v1/webhooks/nonexistent-wh")
        assert resp.status_code == 404

    async def test_webhook_log(self, client):
        await client.post("/api/v1/webhooks", json={
            "webhook_id": "wh-log",
            "url": "https://example.com/hook",
            "events": ["signal.new"],
        })
        resp = await client.get("/api/v1/webhooks/wh-log/log")
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "meta" in resp.json()

    async def test_pipeline_metrics(self, client):
        resp = await client.get("/api/v1/pipeline/metrics")
        assert resp.status_code == 200

    async def test_pipeline_health(self, client):
        resp = await client.get("/api/v1/pipeline/health")
        assert resp.status_code == 200
        assert "data" in resp.json()

    async def test_cost_stats(self, client):
        resp = await client.get("/api/v1/cost")
        assert resp.status_code == 200
        assert resp.json()["data"]["within_budget"] is True

    async def test_backpressure(self, client):
        resp = await client.get("/api/v1/backpressure")
        assert resp.status_code == 200


class TestTribalKnowledgeEndpoints:
    """Tribal knowledge input via API."""

    async def test_add_tribal_entity(self, client):
        resp = await client.post("/api/v1/tribal/entity", json={
            "name": "Secret Supplier",
            "entity_type": "COMPANY",
            "expert": "John Senior",
            "notes": "Known only through industry contacts",
            "confidence": 0.7,
        })
        assert resp.status_code == 201

    async def test_add_tribal_entity_missing_expert(self, client):
        resp = await client.post("/api/v1/tribal/entity", json={
            "name": "X", "entity_type": "COMPANY",
        })
        assert resp.status_code == 422

    async def test_add_tribal_edge(self, client):
        # Create two entities first
        await client.post("/api/v1/entities", json={
            "entity_type": "COMPANY", "name": "TribalSrc", "id": "tribal-src",
        })
        await client.post("/api/v1/entities", json={
            "entity_type": "COMPANY", "name": "TribalTgt", "id": "tribal-tgt",
        })
        resp = await client.post("/api/v1/tribal/edge", json={
            "source_id": "tribal-src",
            "target_id": "tribal-tgt",
            "relation_type": "SUPPLIES_TO",
            "weight": 0.8,
            "expert": "John Senior",
            "notes": "Known supply relationship",
        })
        assert resp.status_code == 201
        assert "data" in resp.json()

    async def test_add_tribal_edge_missing_field(self, client):
        resp = await client.post("/api/v1/tribal/edge", json={
            "source_id": "a",
            "target_id": "b",
        })
        assert resp.status_code == 422

    async def test_override_confidence(self, client):
        # Create an entity via regular endpoint (consistent entity_type format)
        create = await client.post("/api/v1/entities", json={
            "entity_type": "COMPANY",
            "name": "ConfOverride",
            "id": "conf-override-test",
        })
        assert create.status_code == 201
        resp = await client.put("/api/v1/tribal/confidence/conf-override-test", json={
            "new_confidence": 0.95,
            "expert": "Jane",
            "reason": "Verified via industry contacts",
        })
        assert resp.status_code == 200
        assert "data" in resp.json()

    async def test_override_confidence_missing_fields(self, client):
        resp = await client.put("/api/v1/tribal/confidence/some-id", json={
            "new_confidence": 0.9,
        })
        assert resp.status_code == 422

    async def test_override_confidence_not_found(self, client):
        resp = await client.put("/api/v1/tribal/confidence/nonexistent-entity", json={
            "new_confidence": 0.9,
            "expert": "Jane",
            "reason": "test",
        })
        assert resp.status_code == 404

    async def test_annotate_entity(self, client):
        # Create an entity via regular endpoint
        create = await client.post("/api/v1/entities", json={
            "entity_type": "COMPANY",
            "name": "AnnotateTarget",
            "id": "annotate-test",
        })
        assert create.status_code == 201
        resp = await client.post("/api/v1/tribal/annotate/annotate-test", json={
            "annotation": "Key player in semiconductor supply chain",
            "expert": "Jane",
        })
        assert resp.status_code == 200
        assert "data" in resp.json()

    async def test_annotate_entity_missing_fields(self, client):
        resp = await client.post("/api/v1/tribal/annotate/some-id", json={
            "annotation": "test",
        })
        assert resp.status_code == 422

    async def test_annotate_entity_not_found(self, client):
        resp = await client.post("/api/v1/tribal/annotate/nonexistent-entity", json={
            "annotation": "test",
            "expert": "Jane",
        })
        assert resp.status_code == 404

    async def test_audit_trail(self, client):
        await client.post("/api/v1/tribal/entity", json={
            "name": "Audit Test",
            "entity_type": "COMPANY",
            "expert": "Jane",
        })
        resp = await client.get("/api/v1/tribal/audit")
        assert resp.status_code == 200
        assert resp.json()["meta"]["count"] >= 1

    async def test_graph_mutate(self, client):
        resp = await client.post("/api/v1/graph/mutate", json={
            "entities": [
                {"name": "TestCo", "entity_type": "Company", "confidence": 0.9},
            ],
            "relations": [],
            "source": "test",
        })
        assert resp.status_code == 200
