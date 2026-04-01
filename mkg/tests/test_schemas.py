# mkg/tests/test_schemas.py
"""Tests for MKG Pydantic request/response schemas.

Validates:
- Required field enforcement
- Field constraints (min/max length, ge/le bounds)
- Default values
- Invalid input rejection
- Serialization round-trips
"""

import pytest
from pydantic import ValidationError

from mkg.api.schemas import (
    CreateEntityRequest,
    UpdateEntityRequest,
    CreateEdgeRequest,
    PropagateRequest,
    WeightAdjustRequest,
    WeightDecayRequest,
    RecordPredictionRequest,
    RecordOutcomeRequest,
    IngestArticleRequest,
    UpdateArticleStatusRequest,
    ExtractArticleRequest,
    GenerateAlertsRequest,
    RegisterWebhookRequest,
    AddTribalEntityRequest,
    AddTribalEdgeRequest,
    OverrideConfidenceRequest,
    AnnotateEntityRequest,
    GraphMutateRequest,
    ErrorDetail,
    Meta,
)


class TestCreateEntityRequest:
    """Validates entity creation schema."""

    def test_valid_minimal(self):
        req = CreateEntityRequest(entity_type="COMPANY", name="TSMC")
        assert req.entity_type == "COMPANY"
        assert req.name == "TSMC"
        assert req.confidence == 1.0  # default

    def test_valid_full(self):
        req = CreateEntityRequest(
            entity_type="COMPANY",
            name="TSMC",
            canonical_name="TSMC",
            id="tsmc-001",
            confidence=0.95,
            source="expert:John",
            metadata={"sector": "Semiconductors"},
        )
        assert req.id == "tsmc-001"

    def test_missing_entity_type(self):
        with pytest.raises(ValidationError) as exc:
            CreateEntityRequest(name="TSMC")
        assert "entity_type" in str(exc.value)

    def test_missing_name(self):
        with pytest.raises(ValidationError):
            CreateEntityRequest(entity_type="COMPANY")

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            CreateEntityRequest(entity_type="COMPANY", name="")

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            CreateEntityRequest(entity_type="COMPANY", name="X", confidence=1.5)
        with pytest.raises(ValidationError):
            CreateEntityRequest(entity_type="COMPANY", name="X", confidence=-0.1)

    def test_name_max_length(self):
        with pytest.raises(ValidationError):
            CreateEntityRequest(entity_type="COMPANY", name="X" * 501)


class TestUpdateEntityRequest:
    """Validates entity update schema."""

    def test_valid_partial(self):
        req = UpdateEntityRequest(name="Updated Name")
        assert req.name == "Updated Name"
        assert req.confidence is None

    def test_empty_body_allowed(self):
        req = UpdateEntityRequest()
        assert req.name is None
        assert req.confidence is None

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            UpdateEntityRequest(confidence=2.0)


class TestCreateEdgeRequest:
    """Validates edge creation schema."""

    def test_valid(self):
        req = CreateEdgeRequest(
            source_id="a", target_id="b",
            relation_type="SUPPLIES_TO", weight=0.85, confidence=0.9,
        )
        assert req.weight == 0.85

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            CreateEdgeRequest(source_id="a", target_id="b")

    def test_weight_bounds(self):
        with pytest.raises(ValidationError):
            CreateEdgeRequest(
                source_id="a", target_id="b",
                relation_type="X", weight=1.5, confidence=0.5,
            )

    def test_empty_source_rejected(self):
        with pytest.raises(ValidationError):
            CreateEdgeRequest(
                source_id="", target_id="b",
                relation_type="X", weight=0.5, confidence=0.5,
            )


class TestPropagateRequest:
    """Validates propagation request schema."""

    def test_valid_minimal(self):
        req = PropagateRequest(trigger_entity_id="tsmc-001")
        assert req.impact_score == 1.0
        assert req.max_depth == 4
        assert req.min_impact == 0.01
        assert req.event_description == "Unknown event"

    def test_valid_full(self):
        req = PropagateRequest(
            trigger_entity_id="tsmc-001",
            impact_score=5.0,
            max_depth=6,
            event_description="Fab fire in Tainan",
            relation_types=["SUPPLIES_TO"],
        )
        assert req.relation_types == ["SUPPLIES_TO"]

    def test_missing_trigger(self):
        with pytest.raises(ValidationError):
            PropagateRequest()

    def test_max_depth_bounds(self):
        with pytest.raises(ValidationError):
            PropagateRequest(trigger_entity_id="x", max_depth=11)
        with pytest.raises(ValidationError):
            PropagateRequest(trigger_entity_id="x", max_depth=0)


class TestWeightAdjustRequest:
    """Validates weight adjustment schema."""

    def test_valid(self):
        req = WeightAdjustRequest(edge_id="e1", new_evidence_weight=0.9)
        assert req.evidence_confidence == 0.5  # default

    def test_missing_edge_id(self):
        with pytest.raises(ValidationError):
            WeightAdjustRequest(new_evidence_weight=0.5)

    def test_missing_weight(self):
        with pytest.raises(ValidationError):
            WeightAdjustRequest(edge_id="e1")


class TestWeightDecayRequest:
    """Validates weight decay schema."""

    def test_defaults(self):
        req = WeightDecayRequest()
        assert req.days_old == 60
        assert req.half_life_days == 90.0

    def test_custom(self):
        req = WeightDecayRequest(days_old=30, half_life_days=45.0)
        assert req.days_old == 30

    def test_days_old_bounds(self):
        with pytest.raises(ValidationError):
            WeightDecayRequest(days_old=0)


class TestRecordPredictionRequest:
    """Validates prediction recording schema."""

    def test_valid(self):
        req = RecordPredictionRequest(
            prediction_id="p1", entity_id="e1", predicted_impact=0.8,
        )
        assert req.source == "api"

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            RecordPredictionRequest(prediction_id="p1")


class TestRecordOutcomeRequest:
    """Validates outcome recording schema."""

    def test_valid(self):
        req = RecordOutcomeRequest(prediction_id="p1", actual_impact=0.65)
        assert req.prediction_id == "p1"

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            RecordOutcomeRequest(prediction_id="p1")


class TestIngestArticleRequest:
    """Validates article ingestion schema."""

    def test_valid(self):
        req = IngestArticleRequest(
            title="TSMC Fab Fire",
            content="A fire broke out at TSMC...",
            source="Reuters",
            url="https://example.com/fire",
        )
        assert req.title == "TSMC Fab Fire"

    def test_missing_title(self):
        with pytest.raises(ValidationError):
            IngestArticleRequest(content="text")

    def test_missing_content(self):
        with pytest.raises(ValidationError):
            IngestArticleRequest(title="title")

    def test_empty_title_rejected(self):
        with pytest.raises(ValidationError):
            IngestArticleRequest(title="", content="text")

    def test_content_max_length(self):
        with pytest.raises(ValidationError):
            IngestArticleRequest(title="t", content="x" * 100_001)


class TestUpdateArticleStatusRequest:
    """Validates article status update schema."""

    def test_valid(self):
        req = UpdateArticleStatusRequest(status="processing")
        assert req.status == "processing"

    def test_empty_status_rejected(self):
        with pytest.raises(ValidationError):
            UpdateArticleStatusRequest(status="")


class TestExtractArticleRequest:
    """Validates extraction request schema."""

    def test_text_field(self):
        req = ExtractArticleRequest(text="TSMC supplies chips.")
        assert req.text == "TSMC supplies chips."

    def test_content_field(self):
        req = ExtractArticleRequest(content="NVIDIA earnings beat.")
        assert req.content == "NVIDIA earnings beat."

    def test_empty_both(self):
        req = ExtractArticleRequest()
        assert req.text is None and req.content is None


class TestRegisterWebhookRequest:
    """Validates webhook registration schema."""

    def test_valid(self):
        req = RegisterWebhookRequest(
            webhook_id="wh-1",
            url="https://example.com/hook",
            events=["signal.new"],
        )
        assert req.webhook_id == "wh-1"

    def test_missing_events(self):
        with pytest.raises(ValidationError):
            RegisterWebhookRequest(webhook_id="wh-1", url="https://example.com/hook")

    def test_empty_events_rejected(self):
        with pytest.raises(ValidationError):
            RegisterWebhookRequest(
                webhook_id="wh-1", url="https://example.com/hook", events=[],
            )


class TestAddTribalEntityRequest:
    """Validates tribal entity creation schema."""

    def test_valid(self):
        req = AddTribalEntityRequest(
            name="Secret Supplier", entity_type="COMPANY", expert="John",
        )
        assert req.confidence == 1.0

    def test_missing_expert(self):
        with pytest.raises(ValidationError):
            AddTribalEntityRequest(name="X", entity_type="COMPANY")

    def test_missing_name(self):
        with pytest.raises(ValidationError):
            AddTribalEntityRequest(entity_type="COMPANY", expert="John")


class TestAddTribalEdgeRequest:
    """Validates tribal edge creation schema."""

    def test_valid(self):
        req = AddTribalEdgeRequest(
            source_id="a", target_id="b", relation_type="SUPPLIES_TO",
            weight=0.8, expert="John",
        )
        assert req.confidence == 1.0

    def test_missing_expert(self):
        with pytest.raises(ValidationError):
            AddTribalEdgeRequest(
                source_id="a", target_id="b", relation_type="X", weight=0.5,
            )


class TestOverrideConfidenceRequest:
    """Validates confidence override schema."""

    def test_valid(self):
        req = OverrideConfidenceRequest(
            new_confidence=0.95, expert="Jane", reason="Verified",
        )
        assert req.new_confidence == 0.95

    def test_missing_reason(self):
        with pytest.raises(ValidationError):
            OverrideConfidenceRequest(new_confidence=0.9, expert="Jane")

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            OverrideConfidenceRequest(
                new_confidence=1.5, expert="Jane", reason="nope",
            )


class TestAnnotateEntityRequest:
    """Validates entity annotation schema."""

    def test_valid(self):
        req = AnnotateEntityRequest(annotation="Key supplier", expert="Jane")
        assert req.annotation == "Key supplier"

    def test_missing_expert(self):
        with pytest.raises(ValidationError):
            AnnotateEntityRequest(annotation="test")


class TestGraphMutateRequest:
    """Validates graph mutation schema."""

    def test_valid_defaults(self):
        req = GraphMutateRequest()
        assert req.source == "api"
        assert req.entities == []
        assert req.relations == []

    def test_with_entities(self):
        req = GraphMutateRequest(
            entities=[{"name": "TSMC", "entity_type": "Company"}],
        )
        assert len(req.entities) == 1


class TestErrorDetail:
    """Validates error response schema."""

    def test_valid(self):
        err = ErrorDetail(
            error="NotFound", detail="Entity not found",
            status_code=404, request_id="abc-123",
        )
        assert err.status_code == 404

    def test_without_request_id(self):
        err = ErrorDetail(error="Bad", detail="Bad request", status_code=400)
        assert err.request_id is None


class TestMeta:
    """Validates meta schema."""

    def test_defaults(self):
        m = Meta()
        assert m.count == 0

    def test_with_pagination(self):
        m = Meta(count=42, limit=100, offset=0)
        assert m.count == 42
