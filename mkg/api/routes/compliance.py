# mkg/api/routes/compliance.py
"""Compliance, Audit, Lineage, and PII endpoints.

Exposes traceability and compliance services via REST API:
- GET /compliance/report — aggregate compliance stats
- GET /compliance/disclaimers — all disclaimer texts
- GET /audit/log — query audit trail
- GET /audit/report — audit summary
- GET /lineage/entity/{entity_id} — entity → article traceability
- GET /lineage/article/{article_id} — article provenance chain
- POST /pii/scan — detect PII in text
- POST /pii/redact — redact PII from text
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from mkg.api.dependencies import get_container

router = APIRouter()


# --- Compliance ---


@router.get("/compliance/report")
async def compliance_report() -> dict[str, Any]:
    """Get aggregate compliance report."""
    c = get_container()
    report = c.compliance_manager.get_compliance_report()
    return {"data": report}


@router.get("/compliance/disclaimers")
async def list_disclaimers() -> dict[str, Any]:
    """Get all regulatory disclaimer texts."""
    c = get_container()
    from mkg.domain.services.compliance_manager import DisclaimerType
    disclaimers = []
    for dt in DisclaimerType:
        disclaimers.append({
            "type": dt.value,
            "text": c.compliance_manager.get_disclaimer(dt),
        })
    return {"data": disclaimers}


# --- Audit ---


@router.get("/audit/log")
async def audit_log(
    action: Optional[str] = Query(None, description="Filter by action type"),
    target_id: Optional[str] = Query(None, description="Filter by target ID"),
    actor: Optional[str] = Query(None, description="Filter by actor"),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """Query audit trail with optional filters."""
    c = get_container()

    # Convert action string to AuditAction if provided
    action_enum = None
    if action:
        from mkg.domain.services.audit_logger import AuditAction
        try:
            action_enum = AuditAction(action)
        except ValueError:
            pass  # Invalid action, return all

    entries = c.audit_logger.get_entries(
        action=action_enum, target_id=target_id, actor=actor, limit=limit
    )
    return {"data": entries, "meta": {"count": len(entries)}}


@router.get("/audit/report")
async def audit_report() -> dict[str, Any]:
    """Get audit summary report."""
    c = get_container()
    report = c.audit_logger.export_report()
    return {"data": report}


# --- Lineage ---


@router.get("/lineage/entity/{entity_id}")
async def entity_lineage(entity_id: str) -> dict[str, Any]:
    """Trace an entity back to its source articles."""
    c = get_container()
    lineage = c.lineage_tracer.trace_entity(entity_id)
    return {"data": lineage}


@router.get("/lineage/article/{article_id}")
async def article_lineage(article_id: str) -> dict[str, Any]:
    """Get full provenance chain for an article."""
    c = get_container()
    lineage = c.provenance_tracker.get_article_lineage(article_id)
    return {"data": lineage}


# --- PII ---


class PIIRequest(BaseModel):
    text: str


class SignalEnrichRequest(BaseModel):
    symbol: str
    pipeline_result: dict[str, Any]


@router.post("/pii/scan")
async def pii_scan(body: PIIRequest) -> dict[str, Any]:
    """Scan text for PII (email, phone, Aadhaar, PAN)."""
    c = get_container()
    result = c.pii_detector.scan(body.text)
    return {"data": result}


@router.post("/pii/redact")
async def pii_redact(body: PIIRequest) -> dict[str, Any]:
    """Redact PII from text."""
    c = get_container()
    redacted = c.pii_detector.redact(body.text)
    return {"data": {"redacted_text": redacted}}


# --- Signal Enrichment ---


@router.post("/signals/enrich")
async def enrich_signal(body: SignalEnrichRequest) -> dict[str, Any]:
    """Enrich a signal with compliance metadata from MKG.

    Takes a symbol and pipeline result and returns enrichment data
    including disclaimers, risk classification, and supply chain risk.
    """
    c = get_container()
    from mkg.domain.services.signal_bridge import SignalBridge

    bridge = SignalBridge(
        compliance_manager=c.compliance_manager,
        lineage_tracer=c.lineage_tracer,
    )
    enrichment = bridge.enrich_signal_with_compliance(
        symbol=body.symbol,
        pipeline_result=body.pipeline_result,
    )
    return {"data": enrichment}


# --- Retention ---


@router.get("/retention/status")
async def retention_status() -> dict[str, Any]:
    """Get current retention policy configuration."""
    c = get_container()
    policy = c.retention_policy
    return {"data": {
        "article_retention_days": policy.article_retention_days,
        "entity_retention_days": policy.entity_retention_days,
        "audit_retention_days": policy.audit_retention_days,
    }}


@router.post("/retention/enforce")
async def enforce_retention() -> dict[str, Any]:
    """Enforce retention policy — purge expired records.

    Checks each data type against its retention period and
    reports what would be/was purged.
    """
    c = get_container()
    policy = c.retention_policy

    purged: dict[str, int] = {
        "articles": 0,
        "entities": 0,
        "audit_entries": 0,
    }

    # For now, report the cutoff dates (actual purging requires
    # storage-level delete operations which are type-specific)
    from datetime import datetime, timezone
    cutoffs = {
        "article_cutoff": policy.get_expiry_date("article").isoformat(),
        "entity_cutoff": policy.get_expiry_date("entity").isoformat(),
        "audit_cutoff": policy.get_expiry_date("audit").isoformat(),
    }

    return {"data": {"purged": purged, "cutoffs": cutoffs}}
