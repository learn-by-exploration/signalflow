# mkg/tests/test_audit_logger.py
"""Tests for AuditLogger — structured audit trail for all graph mutations.

Iterations 11-15: Every entity creation, edge creation, weight update,
deletion, and pipeline decision must be recorded in an immutable audit log
for regulatory and internal review.
"""

import pytest


class TestAuditLogRecording:
    """Basic audit log recording and querying."""

    def test_log_entity_creation(self):
        from mkg.domain.services.audit_logger import AuditLogger, AuditAction

        al = AuditLogger()
        al.log(
            action=AuditAction.ENTITY_CREATED,
            actor="pipeline:extraction",
            target_id="nvidia-001",
            target_type="entity",
            details={"name": "NVIDIA", "entity_type": "Company", "source_article": "art-001"},
        )
        entries = al.get_entries()
        assert len(entries) == 1
        assert entries[0]["action"] == "entity_created"
        assert entries[0]["target_id"] == "nvidia-001"

    def test_log_edge_creation(self):
        from mkg.domain.services.audit_logger import AuditLogger, AuditAction

        al = AuditLogger()
        al.log(
            action=AuditAction.EDGE_CREATED,
            actor="pipeline:mutation",
            target_id="edge-001",
            target_type="edge",
            details={"source": "TSMC", "target": "NVIDIA", "relation": "SUPPLIES_TO"},
        )
        entries = al.get_entries()
        assert entries[0]["action"] == "edge_created"

    def test_log_weight_update(self):
        from mkg.domain.services.audit_logger import AuditLogger, AuditAction

        al = AuditLogger()
        al.log(
            action=AuditAction.WEIGHT_UPDATED,
            actor="weight_decay_job",
            target_id="edge-001",
            target_type="edge",
            details={"old_weight": 0.85, "new_weight": 0.72, "reason": "time_decay"},
        )
        entries = al.get_entries()
        assert entries[0]["details"]["old_weight"] == 0.85

    def test_log_entity_deletion(self):
        from mkg.domain.services.audit_logger import AuditLogger, AuditAction

        al = AuditLogger()
        al.log(AuditAction.ENTITY_DELETED, "admin", "e-001", "entity", {"reason": "stale"})
        entries = al.get_entries()
        assert entries[0]["action"] == "entity_deleted"

    def test_log_pipeline_decision(self):
        from mkg.domain.services.audit_logger import AuditLogger, AuditAction

        al = AuditLogger()
        al.log(
            action=AuditAction.PIPELINE_DECISION,
            actor="pipeline:dedup",
            target_id="art-001",
            target_type="article",
            details={"decision": "duplicate_rejected", "reason": "content_hash_match"},
        )
        entries = al.get_entries()
        assert entries[0]["action"] == "pipeline_decision"


class TestAuditQuerying:
    """Querying and filtering audit log entries."""

    def _seed_logger(self):
        from mkg.domain.services.audit_logger import AuditLogger, AuditAction

        al = AuditLogger()
        al.log(AuditAction.ENTITY_CREATED, "pipeline", "e-001", "entity", {"name": "TSMC"})
        al.log(AuditAction.ENTITY_CREATED, "pipeline", "e-002", "entity", {"name": "NVIDIA"})
        al.log(AuditAction.EDGE_CREATED, "pipeline", "ed-001", "edge", {"rel": "SUPPLIES_TO"})
        al.log(AuditAction.WEIGHT_UPDATED, "decay_job", "ed-001", "edge", {"new_weight": 0.7})
        al.log(AuditAction.PIPELINE_DECISION, "pipeline", "art-001", "article", {"decision": "processed"})
        return al

    def test_filter_by_action(self):
        al = self._seed_logger()
        entries = al.get_entries(action="entity_created")
        assert len(entries) == 2

    def test_filter_by_target_id(self):
        al = self._seed_logger()
        entries = al.get_entries(target_id="ed-001")
        assert len(entries) == 2  # edge_created + weight_updated

    def test_filter_by_actor(self):
        al = self._seed_logger()
        entries = al.get_entries(actor="decay_job")
        assert len(entries) == 1

    def test_all_entries_have_timestamps(self):
        al = self._seed_logger()
        for entry in al.get_entries():
            assert "timestamp" in entry

    def test_entries_ordered_chronologically(self):
        al = self._seed_logger()
        entries = al.get_entries()
        timestamps = [e["timestamp"] for e in entries]
        assert timestamps == sorted(timestamps)

    def test_limit_entries(self):
        al = self._seed_logger()
        entries = al.get_entries(limit=2)
        assert len(entries) == 2


class TestAuditExport:
    """Export audit log for regulatory review."""

    def test_export_report(self):
        from mkg.domain.services.audit_logger import AuditLogger, AuditAction

        al = AuditLogger()
        al.log(AuditAction.ENTITY_CREATED, "pipeline", "e-001", "entity", {"name": "TSMC"})
        al.log(AuditAction.EDGE_CREATED, "pipeline", "ed-001", "edge", {})
        al.log(AuditAction.PIPELINE_DECISION, "pipeline", "art-001", "article", {})

        report = al.export_report()
        assert report["total_entries"] == 3
        assert "actions_breakdown" in report
        assert report["actions_breakdown"]["entity_created"] == 1
        assert "generated_at" in report

    def test_export_entries_as_list(self):
        from mkg.domain.services.audit_logger import AuditLogger, AuditAction

        al = AuditLogger()
        al.log(AuditAction.ENTITY_CREATED, "p", "e1", "entity", {})
        exported = al.export_entries()
        assert isinstance(exported, list)
        assert len(exported) == 1

    def test_export_empty_log(self):
        from mkg.domain.services.audit_logger import AuditLogger

        al = AuditLogger()
        report = al.export_report()
        assert report["total_entries"] == 0
