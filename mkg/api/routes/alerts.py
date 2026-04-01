# mkg/api/routes/alerts.py
"""Alert system and webhook delivery endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from mkg.api.dependencies import get_container
from mkg.api.schemas import GenerateAlertsRequest, RegisterWebhookRequest

router = APIRouter()


@router.get("/alerts")
async def list_alerts(
    limit: int = Query(10, ge=1, le=100),
) -> dict[str, Any]:
    """Get recent alerts."""
    c = get_container()
    alerts = c.alert_system.get_recent_alerts(limit=limit)
    return {"data": alerts, "meta": {"count": len(alerts)}}


@router.post("/alerts/generate")
async def generate_alerts(body: GenerateAlertsRequest) -> dict[str, Any]:
    """Generate alerts from causal chains."""
    c = get_container()
    alerts = c.alert_system.generate_alerts(body.chains, min_severity=body.min_severity)
    return {"data": alerts, "meta": {"count": len(alerts)}}


# --- Webhooks ---


@router.post("/webhooks", status_code=201)
async def register_webhook(body: RegisterWebhookRequest) -> dict[str, Any]:
    """Register a webhook for event notifications."""
    c = get_container()
    result = c.webhook_delivery.register(
        body.webhook_id, body.url, body.events
    )
    return {"data": result}


@router.delete("/webhooks/{webhook_id}")
async def unregister_webhook(webhook_id: str) -> dict[str, Any]:
    """Unregister a webhook."""
    c = get_container()
    removed = c.webhook_delivery.unregister(webhook_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"data": {"deleted": True, "id": webhook_id}}


@router.get("/webhooks/{webhook_id}/log")
async def get_webhook_log(
    webhook_id: str,
    limit: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    """Get delivery log for a webhook."""
    c = get_container()
    log = c.webhook_delivery.get_delivery_log(webhook_id, limit=limit)
    stats = c.webhook_delivery.get_stats(webhook_id)
    return {"data": log, "meta": stats}


# --- Observability ---


@router.get("/pipeline/metrics")
async def pipeline_metrics() -> dict[str, Any]:
    """Get pipeline observability metrics."""
    c = get_container()
    return {"data": c.observability.get_metrics()}


@router.get("/pipeline/health")
async def pipeline_health() -> dict[str, Any]:
    """Get pipeline health status."""
    c = get_container()
    return {"data": c.observability.health_check()}


# --- Cost Governance ---


@router.get("/cost")
async def cost_stats() -> dict[str, Any]:
    """Get AI cost governance stats."""
    c = get_container()
    return {
        "data": {
            "stats": c.cost_governance.get_stats(),
            "budget_remaining": c.cost_governance.budget_remaining,
            "within_budget": c.cost_governance.is_within_budget(),
        }
    }


# --- Backpressure ---


@router.get("/backpressure")
async def backpressure_stats() -> dict[str, Any]:
    """Get backpressure manager status."""
    c = get_container()
    return {"data": c.backpressure.get_stats()}
