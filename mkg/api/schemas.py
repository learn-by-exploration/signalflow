# mkg/api/schemas.py
"""Pydantic v2 request/response schemas for all MKG API endpoints.

Every endpoint uses typed models for:
- Input validation (reject malformed requests before business logic)
- Output serialization (consistent, documented response shapes)
- Auto-generated OpenAPI docs
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl


# ─── Generic Envelope ────────────────────────────────────────────────

class Meta(BaseModel):
    """Pagination and summary metadata."""
    count: int = 0
    limit: int | None = None
    offset: int | None = None


class ErrorDetail(BaseModel):
    """Structured error response body."""
    error: str
    detail: str
    status_code: int
    request_id: str | None = None


# ─── Entity Schemas ──────────────────────────────────────────────────

class CreateEntityRequest(BaseModel):
    """Create a new entity node."""
    entity_type: str = Field(..., description="Entity type: Company, Product, Facility, Person, Country, Regulation, Sector, Event")
    name: str = Field(..., min_length=1, max_length=500)
    canonical_name: str | None = Field(None, max_length=500)
    id: str | None = Field(None, max_length=200, description="Custom entity ID; auto-generated if omitted")
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    source: str | None = Field(None, max_length=200)
    metadata: dict[str, Any] | None = None


class UpdateEntityRequest(BaseModel):
    """Update an entity's properties."""
    name: str | None = Field(None, min_length=1, max_length=500)
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    metadata: dict[str, Any] | None = None


class EntityResponse(BaseModel):
    """Single entity response."""
    data: dict[str, Any]


class EntityListResponse(BaseModel):
    """Paginated entity list."""
    data: list[dict[str, Any]]
    meta: Meta


class DeleteResponse(BaseModel):
    """Deletion confirmation."""
    data: dict[str, Any]


# ─── Edge Schemas ────────────────────────────────────────────────────

class CreateEdgeRequest(BaseModel):
    """Create a relationship edge between two entities."""
    source_id: str = Field(..., min_length=1, max_length=200)
    target_id: str = Field(..., min_length=1, max_length=200)
    relation_type: str = Field(..., description="e.g. SUPPLIES_TO, COMPETES_WITH")
    weight: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    id: str | None = Field(None, max_length=200)
    source: str | None = Field(None, max_length=200)
    metadata: dict[str, Any] | None = None


class EdgeResponse(BaseModel):
    """Single edge response."""
    data: dict[str, Any]


class EdgeListResponse(BaseModel):
    """Paginated edge list."""
    data: list[dict[str, Any]]
    meta: Meta


# ─── Propagation Schemas ─────────────────────────────────────────────

class PropagateRequest(BaseModel):
    """Trigger event propagation from an entity."""
    trigger_entity_id: str = Field(..., min_length=1)
    impact_score: float = Field(1.0, ge=0.0, le=10.0)
    max_depth: int = Field(4, ge=1, le=10)
    min_impact: float = Field(0.01, ge=0.0, le=1.0)
    event_description: str = Field("Unknown event", max_length=2000)
    relation_types: list[str] | None = None


class PropagateResponse(BaseModel):
    """Propagation result with causal chains and impact table."""
    data: dict[str, Any]
    meta: dict[str, Any]


class WeightAdjustRequest(BaseModel):
    """Adjust an edge weight with new evidence."""
    edge_id: str = Field(..., min_length=1)
    new_evidence_weight: float = Field(..., ge=0.0, le=1.0)
    evidence_confidence: float = Field(0.5, ge=0.0, le=1.0)


class WeightDecayRequest(BaseModel):
    """Apply time-based weight decay."""
    days_old: int = Field(60, ge=1, le=3650)
    half_life_days: float = Field(90.0, gt=0.0, le=3650.0)


class RecordPredictionRequest(BaseModel):
    """Record a prediction for accuracy tracking."""
    prediction_id: str = Field(..., min_length=1, max_length=200)
    entity_id: str = Field(..., min_length=1, max_length=200)
    predicted_impact: float = Field(..., ge=-10.0, le=10.0)
    source: str = Field("api", max_length=100)


class RecordOutcomeRequest(BaseModel):
    """Record the actual outcome of a prediction."""
    prediction_id: str = Field(..., min_length=1, max_length=200)
    actual_impact: float = Field(..., ge=-10.0, le=10.0)


# ─── Article Schemas ─────────────────────────────────────────────────

class IngestArticleRequest(BaseModel):
    """Ingest a new article into the pipeline."""
    title: str = Field(..., min_length=1, max_length=1000)
    content: str = Field(..., min_length=1, max_length=100_000)
    source: str | None = Field(None, max_length=200)
    url: str | None = Field(None, max_length=2000)


class UpdateArticleStatusRequest(BaseModel):
    """Update an article's processing status."""
    status: str = Field(..., min_length=1, max_length=50, description="pending, processing, completed, failed, duplicate")


class ExtractArticleRequest(BaseModel):
    """Run NER/RE extraction on article text."""
    text: str | None = Field(None, min_length=1, max_length=100_000)
    content: str | None = Field(None, min_length=1, max_length=100_000)
    context: dict[str, Any] | None = None


# ─── Alert Schemas ───────────────────────────────────────────────────

class GenerateAlertsRequest(BaseModel):
    """Generate alerts from causal chains."""
    chains: list[dict[str, Any]] = Field(default_factory=list)
    min_severity: str | None = Field(None, description="Filter: critical, high, medium, low")


class RegisterWebhookRequest(BaseModel):
    """Register a webhook for event notifications."""
    webhook_id: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., min_length=1, max_length=2000)
    events: list[str] = Field(..., min_length=1, description="Event types to subscribe to")


# ─── Tribal Knowledge Schemas ────────────────────────────────────────

class AddTribalEntityRequest(BaseModel):
    """Add an expert-asserted entity to the graph."""
    name: str = Field(..., min_length=1, max_length=500)
    entity_type: str = Field(..., description="Company, Product, Facility, etc.")
    expert: str = Field(..., min_length=1, max_length=200)
    notes: str | None = Field(None, max_length=5000)
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class AddTribalEdgeRequest(BaseModel):
    """Add an expert-asserted relationship edge."""
    source_id: str = Field(..., min_length=1, max_length=200)
    target_id: str = Field(..., min_length=1, max_length=200)
    relation_type: str = Field(...)
    weight: float = Field(..., ge=0.0, le=1.0)
    expert: str = Field(..., min_length=1, max_length=200)
    notes: str | None = Field(None, max_length=5000)
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class OverrideConfidenceRequest(BaseModel):
    """Override an entity's confidence score."""
    new_confidence: float = Field(..., ge=0.0, le=1.0)
    expert: str = Field(..., min_length=1, max_length=200)
    reason: str = Field(..., min_length=1, max_length=2000)


class AnnotateEntityRequest(BaseModel):
    """Add an expert annotation to an entity."""
    annotation: str = Field(..., min_length=1, max_length=5000)
    expert: str = Field(..., min_length=1, max_length=200)


class GraphMutateRequest(BaseModel):
    """Apply extracted entities and relations to the graph."""
    entities: list[dict[str, Any]] = Field(default_factory=list)
    relations: list[dict[str, Any]] = Field(default_factory=list)
    source: str = Field("api", max_length=200)
    extraction: dict[str, Any] | None = None


# ─── Graph Schemas ───────────────────────────────────────────────────

class SeedGraphRequest(BaseModel):
    """Optional custom seed data for the graph."""
    entities: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)


# ─── Generic Response ────────────────────────────────────────────────

class DataResponse(BaseModel):
    """Generic data wrapper."""
    data: Any


class DataMetaResponse(BaseModel):
    """Generic data + meta wrapper."""
    data: Any
    meta: dict[str, Any] = Field(default_factory=dict)
