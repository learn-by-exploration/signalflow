# mkg/api/routes/graph.py
"""Graph traversal, search, and subgraph endpoints."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from mkg.api.dependencies import get_container

router = APIRouter()


@router.get("/graph/neighbors/{entity_id}")
async def get_neighbors(
    entity_id: str,
    relation_type: Optional[str] = Query(None),
    direction: str = Query("both", pattern="^(outgoing|incoming|both)$"),
) -> dict[str, Any]:
    """Get immediate neighbors of an entity."""
    c = get_container()
    entity = await c.graph_storage.get_entity(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    neighbors = await c.graph_storage.get_neighbors(entity_id, relation_type, direction)
    return {"data": neighbors, "meta": {"count": len(neighbors)}}


@router.get("/graph/subgraph/{entity_id}")
async def get_subgraph(
    entity_id: str,
    max_depth: int = Query(2, ge=1, le=6),
    relation_types: Optional[str] = Query(None, description="Comma-separated relation types"),
) -> dict[str, Any]:
    """Get a subgraph centered on an entity up to max_depth hops."""
    c = get_container()
    entity = await c.graph_storage.get_entity(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    rt_list = relation_types.split(",") if relation_types else None
    subgraph = await c.graph_storage.get_subgraph(entity_id, max_depth, rt_list)
    return {
        "data": subgraph,
        "meta": {
            "node_count": len(subgraph.get("nodes", [])),
            "edge_count": len(subgraph.get("edges", [])),
        },
    }


@router.get("/graph/search")
async def search_graph(
    q: str = Query(..., min_length=1, description="Search query"),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """Hybrid search across entities (vector + keyword)."""
    c = get_container()
    results = await c.graph_storage.search(q, entity_type=entity_type, limit=limit)
    return {"data": results, "meta": {"count": len(results)}}


@router.post("/graph/seed")
async def seed_graph(body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Seed the graph with default semiconductor data or custom data."""
    c = get_container()
    if body:
        counts = await c.seed_loader.load(body)
    else:
        from mkg.domain.services.seed_loader import get_default_seed_data

        counts = await c.seed_loader.load(get_default_seed_data())
    return {"data": counts}


@router.get("/graph/health")
async def graph_health() -> dict[str, Any]:
    """Graph storage health check."""
    c = get_container()
    return {"data": await c.graph_storage.health_check()}
