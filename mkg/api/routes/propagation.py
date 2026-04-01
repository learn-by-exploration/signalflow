# mkg/api/routes/propagation.py
"""Propagation engine, causal chains, impact table, and weight adjustment endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from mkg.api.dependencies import get_container
from mkg.api.schemas import (
    PropagateRequest,
    RecordOutcomeRequest,
    RecordPredictionRequest,
    WeightAdjustRequest,
    WeightDecayRequest,
)

router = APIRouter()


@router.post("/propagate")
async def propagate(body: PropagateRequest) -> dict[str, Any]:
    """Trigger event propagation from an entity.

    Returns ranked impact list with causal chains.
    """
    c = get_container()
    entity = await c.graph_storage.get_entity(body.trigger_entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Trigger entity not found")

    results = await c.propagation_engine.propagate(
        trigger_entity_id=body.trigger_entity_id,
        impact_score=body.impact_score,
        max_depth=body.max_depth,
        min_impact=body.min_impact,
        relation_types=body.relation_types,
    )

    chains = await c.causal_chain.build_chains(
        body.trigger_entity_id, body.event_description, results
    )

    trigger_name = entity.get("name", body.trigger_entity_id)
    impact_table = await c.impact_table.build(results, trigger_name=trigger_name)

    return {
        "data": {
            "propagation": results,
            "causal_chains": chains,
            "impact_table": impact_table,
        },
        "meta": {"affected_entities": len(results), "trigger": body.trigger_entity_id},
    }


@router.post("/weight/adjust")
async def adjust_weight(body: WeightAdjustRequest) -> dict[str, Any]:
    """Adjust an edge weight with new evidence."""
    c = get_container()
    result = await c.weight_adjustment.update_edge_weight(
        body.edge_id, body.new_evidence_weight, body.evidence_confidence
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Edge not found")
    return {"data": result}


@router.post("/weight/decay")
async def batch_decay(body: WeightDecayRequest) -> dict[str, Any]:
    """Apply time-based weight decay to all edges."""
    c = get_container()
    result = await c.weight_adjustment.batch_decay(body.days_old, body.half_life_days)
    return {"data": result}


@router.get("/accuracy")
async def get_accuracy() -> dict[str, Any]:
    """Get prediction accuracy statistics."""
    c = get_container()
    return {
        "data": {
            "overall": c.accuracy_tracker.get_accuracy(),
            "by_entity": c.accuracy_tracker.get_accuracy_by_entity(),
            "stats": c.accuracy_tracker.get_stats(),
        }
    }


@router.post("/accuracy/prediction")
async def record_prediction(body: RecordPredictionRequest) -> dict[str, Any]:
    """Record a new prediction for accuracy tracking."""
    c = get_container()
    c.accuracy_tracker.record_prediction(
        body.prediction_id,
        body.entity_id,
        body.predicted_impact,
        body.source,
    )
    return {"data": {"recorded": True}}


@router.post("/accuracy/outcome")
async def record_outcome(body: RecordOutcomeRequest) -> dict[str, Any]:
    """Record an actual outcome for a previous prediction."""
    c = get_container()
    c.accuracy_tracker.record_outcome(body.prediction_id, body.actual_impact)
    return {"data": {"recorded": True}}
