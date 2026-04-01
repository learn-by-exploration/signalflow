# mkg/tests/test_pipeline_error_recovery.py
"""Tests for pipeline error recovery and graceful degradation.

Verifies:
1. Extraction failure doesn't crash the pipeline
2. Graph mutation failure is handled and logged
3. PII detection failure doesn't block processing
4. Provenance records error events
5. Audit logger records errors
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mkg.domain.services.pipeline_orchestrator import PipelineOrchestrator


@pytest.fixture
def mock_services():
    """Create mock service dependencies for the pipeline."""
    graph_storage = AsyncMock()
    extraction = AsyncMock()
    verifier = MagicMock()
    mutation = AsyncMock()
    propagation = AsyncMock()
    chain_builder = AsyncMock()
    alert_system = MagicMock()
    impact_table = AsyncMock()
    dedup = AsyncMock()
    provenance = MagicMock()
    audit = MagicMock()
    pii = MagicMock()

    return {
        "graph_storage": graph_storage,
        "extraction_orchestrator": extraction,
        "hallucination_verifier": verifier,
        "graph_mutation": mutation,
        "propagation_engine": propagation,
        "causal_chain_builder": chain_builder,
        "alert_system": alert_system,
        "impact_table_builder": impact_table,
        "article_dedup": dedup,
        "provenance_tracker": provenance,
        "audit_logger": audit,
        "pii_detector": pii,
    }


class TestExtractionErrorRecovery:
    """Pipeline handles extraction failures gracefully."""

    async def test_extraction_error_returns_error_status(self, mock_services):
        """When extraction raises, pipeline returns error status, not crash."""
        mock_services["extraction_orchestrator"].extract.side_effect = RuntimeError("Claude API timeout")
        mock_services["article_dedup"].compute_fingerprint.return_value = "fp123"

        pipeline = PipelineOrchestrator(**mock_services)

        result = await pipeline.process_article(
            title="Test",
            content="NVIDIA launches new GPU product.",
            source="test",
        )

        assert result["status"] == "error"
        assert "Extraction failed" in result.get("error", "")

    async def test_extraction_error_records_provenance(self, mock_services):
        """Error is recorded in provenance for traceability."""
        mock_services["extraction_orchestrator"].extract.side_effect = RuntimeError("API error")

        pipeline = PipelineOrchestrator(**mock_services)
        await pipeline.process_article(
            title="Test",
            content="Article content here.",
            source="test",
        )

        # Provenance should have been called with error details
        mock_services["provenance_tracker"].record_step.assert_called()

    async def test_extraction_error_records_audit(self, mock_services):
        """Error is logged to audit trail."""
        mock_services["extraction_orchestrator"].extract.side_effect = RuntimeError("Budget exceeded")

        pipeline = PipelineOrchestrator(**mock_services)
        await pipeline.process_article(
            title="Test",
            content="Article content here.",
            source="test",
        )

        mock_services["audit_logger"].log.assert_called()


class TestMutationErrorRecovery:
    """Pipeline handles graph mutation failures gracefully."""

    async def test_mutation_error_returns_error_status(self, mock_services):
        """When mutation raises, pipeline returns error, not crash."""
        mock_services["extraction_orchestrator"].extract.return_value = {
            "entities": [{"name": "TSMC", "type": "Company", "confidence": 0.9}],
            "relations": [],
            "tier_used": "regex",
        }
        mock_services["hallucination_verifier"].verify_result.return_value = {
            "verified_entities": [{"name": "TSMC", "type": "Company", "confidence": 0.9}],
            "verified_relations": [],
        }
        mock_services["graph_mutation"].apply_entities.side_effect = RuntimeError("DB locked")

        pipeline = PipelineOrchestrator(**mock_services)
        result = await pipeline.process_article(
            title="Test",
            content="TSMC fab disruption reported.",
            source="test",
        )

        assert result["status"] == "error"
        assert "Graph mutation failed" in result.get("error", "")


class TestPIIIntegration:
    """PII detection integrated into pipeline."""

    async def test_pii_redacted_before_extraction(self, mock_services):
        """PII in article content is redacted before entity extraction."""
        mock_services["pii_detector"].scan.return_value = {
            "has_pii": True,
            "pii_types": ["email"],
            "pii_count": 1,
        }
        mock_services["pii_detector"].redact.return_value = "CEO [REDACTED] announced merger."
        mock_services["extraction_orchestrator"].extract.return_value = {
            "entities": [],
            "relations": [],
            "tier_used": "regex",
        }

        pipeline = PipelineOrchestrator(**mock_services)
        await pipeline.process_article(
            title="Test",
            content="CEO john@company.com announced merger.",
            source="test",
        )

        # Extraction should receive redacted content
        call_args = mock_services["extraction_orchestrator"].extract.call_args
        assert "[REDACTED]" in call_args.args[0]

    async def test_pii_redaction_recorded_in_audit(self, mock_services):
        """PII redaction is logged in audit trail."""
        mock_services["pii_detector"].scan.return_value = {
            "has_pii": True,
            "pii_types": ["email", "phone"],
            "pii_count": 2,
        }
        mock_services["pii_detector"].redact.return_value = "Redacted content."
        mock_services["extraction_orchestrator"].extract.return_value = {
            "entities": [],
            "relations": [],
            "tier_used": "regex",
        }

        pipeline = PipelineOrchestrator(**mock_services)
        await pipeline.process_article(
            title="Test",
            content="Contact: john@corp.com, +91-9876543210",
            source="test",
        )

        # Audit should log PII redaction
        assert mock_services["audit_logger"].log.called

    async def test_no_pii_no_redaction(self, mock_services):
        """When no PII found, content passes through unchanged."""
        mock_services["pii_detector"].scan.return_value = {
            "has_pii": False,
            "pii_types": [],
            "pii_count": 0,
        }
        original_content = "NVIDIA revenue beats estimates by 20%."
        mock_services["extraction_orchestrator"].extract.return_value = {
            "entities": [],
            "relations": [],
            "tier_used": "regex",
        }

        pipeline = PipelineOrchestrator(**mock_services)
        await pipeline.process_article(
            title="Test",
            content=original_content,
            source="test",
        )

        # Extraction should receive original content
        call_args = mock_services["extraction_orchestrator"].extract.call_args
        assert call_args.args[0] == original_content

    async def test_pipeline_works_without_pii_detector(self, mock_services):
        """Pipeline still works when pii_detector is None."""
        mock_services.pop("pii_detector")
        mock_services["extraction_orchestrator"].extract.return_value = {
            "entities": [],
            "relations": [],
            "tier_used": "regex",
        }

        pipeline = PipelineOrchestrator(**mock_services)
        result = await pipeline.process_article(
            title="Test",
            content="No PII detector active.",
            source="test",
        )

        assert result["status"] == "completed"
