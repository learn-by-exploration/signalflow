# mkg/api/routes/tribal.py
"""Tribal knowledge input and graph mutation endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from mkg.api.dependencies import get_container
from mkg.api.schemas import (
    AddTribalEdgeRequest,
    AddTribalEntityRequest,
    AnnotateEntityRequest,
    GraphMutateRequest,
    OverrideConfidenceRequest,
)

router = APIRouter()


@router.post("/tribal/entity", status_code=201)
async def add_tribal_entity(body: AddTribalEntityRequest) -> dict[str, Any]:
    """Add an expert-asserted entity to the graph."""
    c = get_container()
    result = await c.tribal_knowledge.add_entity(
        name=body.name,
        entity_type=body.entity_type,
        expert=body.expert,
        notes=body.notes,
        confidence=body.confidence,
    )
    return {"data": result}


@router.post("/tribal/edge", status_code=201)
async def add_tribal_edge(body: AddTribalEdgeRequest) -> dict[str, Any]:
    """Add an expert-asserted relationship edge."""
    c = get_container()
    try:
        result = await c.tribal_knowledge.add_edge(
            source_id=body.source_id,
            target_id=body.target_id,
            relation_type=body.relation_type,
            weight=body.weight,
            expert=body.expert,
            notes=body.notes,
            confidence=body.confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"data": result}


@router.put("/tribal/confidence/{entity_id}")
async def override_confidence(
    entity_id: str, body: OverrideConfidenceRequest
) -> dict[str, Any]:
    """Override an entity's confidence score (expert assertion)."""
    c = get_container()
    try:
        result = await c.tribal_knowledge.override_confidence(
            entity_id=entity_id,
            new_confidence=body.new_confidence,
            expert=body.expert,
            reason=body.reason,
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"data": result}


@router.post("/tribal/annotate/{entity_id}")
async def annotate_entity(
    entity_id: str, body: AnnotateEntityRequest
) -> dict[str, Any]:
    """Add an expert annotation to an entity."""
    c = get_container()
    try:
        result = await c.tribal_knowledge.annotate(
            entity_id=entity_id,
            annotation=body.annotation,
            expert=body.expert,
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"data": result}


@router.get("/tribal/audit")
async def get_audit_trail(
    expert: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Get the tribal knowledge audit trail."""
    c = get_container()
    trail = c.tribal_knowledge.get_audit_trail(expert=expert, limit=limit)
    return {"data": trail, "meta": {"count": len(trail)}}


# --- Graph Mutations (from NER/RE extraction) ---


@router.post("/graph/mutate")
async def apply_mutations(body: GraphMutateRequest) -> dict[str, Any]:
    """Apply extracted entities and relations to the graph."""
    c = get_container()
    extraction = body.extraction or body.model_dump()
    result = await c.graph_mutation.apply(extraction, source=body.source)
    return {"data": result}
