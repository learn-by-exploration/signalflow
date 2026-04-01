# mkg/api/routes/entities.py
"""Entity & Edge CRUD endpoints.

All request bodies use typed Pydantic models for automatic validation.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from mkg.api.dependencies import get_container
from mkg.api.schemas import (
    CreateEdgeRequest,
    CreateEntityRequest,
    UpdateEntityRequest,
)
from mkg.domain.entities.edge import RelationType
from mkg.domain.entities.node import EntityType

router = APIRouter()


def _resolve_entity_type(raw: str) -> EntityType:
    """Resolve entity type from user input (case-insensitive)."""
    for et in EntityType:
        if et.value == raw or et.value.upper() == raw.upper() or et.name == raw.upper():
            return et
    raise ValueError(f"Invalid entity_type: {raw}")


# --- Entity CRUD ---


@router.post("/entities", status_code=201)
async def create_entity(body: CreateEntityRequest) -> dict[str, Any]:
    """Create a new entity node."""
    c = get_container()
    try:
        et = _resolve_entity_type(body.entity_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid entity_type: {body.entity_type}")
    entity = await c.entity_service.create_entity(
        entity_type=et,
        name=body.name,
        canonical_name=body.canonical_name or body.name,
        entity_id=body.id,
        metadata=body.metadata,
        confidence=body.confidence,
        source=body.source,
    )
    return {"data": entity.to_dict()}


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str) -> dict[str, Any]:
    """Get an entity by ID."""
    c = get_container()
    entity = await c.entity_service.get_entity(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"data": entity.to_dict()}


@router.get("/entities")
async def list_entities(
    entity_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """List entities with optional type filter."""
    c = get_container()
    et = None
    if entity_type:
        try:
            et = _resolve_entity_type(entity_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid entity_type: {entity_type}")
    entities = await c.entity_service.find_entities(
        entity_type=et, limit=limit, offset=offset
    )
    return {
        "data": [e.to_dict() for e in entities],
        "meta": {"count": len(entities), "limit": limit, "offset": offset},
    }


@router.put("/entities/{entity_id}")
async def update_entity(entity_id: str, body: UpdateEntityRequest) -> dict[str, Any]:
    """Update an entity's properties."""
    c = get_container()
    entity = await c.entity_service.update_entity(
        entity_id,
        name=body.name,
        metadata=body.metadata,
        confidence=body.confidence,
    )
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"data": entity.to_dict()}


@router.delete("/entities/{entity_id}")
async def delete_entity(entity_id: str) -> dict[str, Any]:
    """Delete an entity and its connected edges."""
    c = get_container()
    deleted = await c.entity_service.delete_entity(entity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"data": {"deleted": True, "id": entity_id}}


# --- Edge CRUD ---


@router.post("/edges", status_code=201)
async def create_edge(body: CreateEdgeRequest) -> dict[str, Any]:
    """Create a relationship edge between two entities."""
    c = get_container()
    try:
        rt = RelationType(body.relation_type.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid relation_type: {body.relation_type}")
    try:
        edge = await c.entity_service.create_edge(
            source_id=body.source_id,
            target_id=body.target_id,
            relation_type=rt,
            weight=body.weight,
            confidence=body.confidence,
            edge_id=body.id,
            metadata=body.metadata,
            source=body.source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"data": edge.to_dict()}


@router.get("/edges/{edge_id}")
async def get_edge(edge_id: str) -> dict[str, Any]:
    """Get an edge by ID."""
    c = get_container()
    edge = await c.entity_service.get_edge(edge_id)
    if edge is None:
        raise HTTPException(status_code=404, detail="Edge not found")
    return {"data": edge.to_dict()}


@router.get("/edges")
async def list_edges(
    source_id: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    relation_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """List edges with optional filters."""
    c = get_container()
    rt = None
    if relation_type:
        try:
            rt = RelationType(relation_type.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid relation_type: {relation_type}")
    edges = await c.entity_service.find_edges(
        source_id=source_id, target_id=target_id, relation_type=rt, limit=limit
    )
    return {
        "data": [e.to_dict() for e in edges],
        "meta": {"count": len(edges)},
    }
