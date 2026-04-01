# mkg/tests/test_persistent_services.py
"""Tests for persistent (SQLite-backed) audit and provenance services.

These test the adapter classes that wrap in-memory services with SQLite
persistence. They maintain the same sync API as the domain services but
persist data across process restarts.
"""

import os
import tempfile

import pytest

from mkg.domain.services.audit_logger import AuditAction


class TestPersistentAuditLogger:
    """Tests for PersistentAuditLogger — sync API with SQLite backing."""

    def _make_logger(self, db_path: str):
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger
        return PersistentAuditLogger(db_path=db_path)

    def test_log_and_retrieve(self, tmp_path):
        db = str(tmp_path / "audit.db")
        logger = self._make_logger(db)
        logger.log(
            action=AuditAction.ENTITY_CREATED,
            actor="pipeline",
            target_id="art-1",
            target_type="article",
            details={"entities_created": 3},
        )
        entries = logger.get_entries()
        assert len(entries) == 1
        assert entries[0]["action"] == "entity_created"
        assert entries[0]["actor"] == "pipeline"
        assert entries[0]["details"]["entities_created"] == 3

    def test_filter_by_action(self, tmp_path):
        db = str(tmp_path / "audit.db")
        logger = self._make_logger(db)
        logger.log(AuditAction.ENTITY_CREATED, "p", "a1", "article", {})
        logger.log(AuditAction.EDGE_CREATED, "p", "a1", "article", {})
        logger.log(AuditAction.ENTITY_CREATED, "p", "a2", "article", {})

        entries = logger.get_entries(action=AuditAction.ENTITY_CREATED)
        assert len(entries) == 2

    def test_filter_by_target_id(self, tmp_path):
        db = str(tmp_path / "audit.db")
        logger = self._make_logger(db)
        logger.log(AuditAction.ENTITY_CREATED, "p", "a1", "article", {})
        logger.log(AuditAction.ENTITY_CREATED, "p", "a2", "article", {})

        entries = logger.get_entries(target_id="a1")
        assert len(entries) == 1
        assert entries[0]["target_id"] == "a1"

    def test_filter_by_actor(self, tmp_path):
        db = str(tmp_path / "audit.db")
        logger = self._make_logger(db)
        logger.log(AuditAction.ENTITY_CREATED, "pipeline", "a1", "article", {})
        logger.log(AuditAction.ENTITY_CREATED, "admin", "a2", "article", {})

        entries = logger.get_entries(actor="admin")
        assert len(entries) == 1
        assert entries[0]["actor"] == "admin"

    def test_limit(self, tmp_path):
        db = str(tmp_path / "audit.db")
        logger = self._make_logger(db)
        for i in range(10):
            logger.log(AuditAction.ENTITY_CREATED, "p", f"a{i}", "article", {})

        entries = logger.get_entries(limit=5)
        assert len(entries) == 5

    def test_export_report(self, tmp_path):
        db = str(tmp_path / "audit.db")
        logger = self._make_logger(db)
        logger.log(AuditAction.ENTITY_CREATED, "p", "a1", "article", {})
        logger.log(AuditAction.EDGE_CREATED, "p", "a1", "article", {})
        logger.log(AuditAction.ENTITY_CREATED, "p", "a2", "article", {})

        report = logger.export_report()
        assert report["total_entries"] == 3
        assert report["actions_breakdown"]["entity_created"] == 2
        assert report["actions_breakdown"]["edge_created"] == 1

    def test_persists_across_instances(self, tmp_path):
        db = str(tmp_path / "audit.db")

        # Write with first instance
        logger1 = self._make_logger(db)
        logger1.log(AuditAction.ENTITY_CREATED, "p", "a1", "article", {"k": "v"})

        # Read with second instance — same data
        logger2 = self._make_logger(db)
        entries = logger2.get_entries()
        assert len(entries) == 1
        assert entries[0]["details"]["k"] == "v"

    def test_in_memory_also_populated(self, tmp_path):
        """In-memory cache stays in sync with SQLite."""
        db = str(tmp_path / "audit.db")
        logger = self._make_logger(db)
        logger.log(AuditAction.ENTITY_CREATED, "p", "a1", "article", {})

        # Check in-memory entries from parent class
        assert len(logger._entries) == 1


class TestPersistentProvenanceTracker:
    """Tests for PersistentProvenanceTracker — sync API with SQLite backing."""

    def _make_tracker(self, db_path: str):
        from mkg.infrastructure.persistent.provenance_tracker import PersistentProvenanceTracker
        return PersistentProvenanceTracker(db_path=db_path)

    def test_record_and_retrieve_step(self, tmp_path):
        db = str(tmp_path / "prov.db")
        tracker = self._make_tracker(db)
        tracker.record_step("art-1", "extraction", {"src": "rss"}, {"entities": 3})

        records = tracker.get_records("art-1")
        assert len(records) == 1
        assert records[0]["step"] == "extraction"
        assert records[0]["outputs"]["entities"] == 3

    def test_record_entity_origin(self, tmp_path):
        db = str(tmp_path / "prov.db")
        tracker = self._make_tracker(db)
        tracker.record_entity_origin("ent-1", "Apple Inc", "art-1", "regex", 0.85)

        articles = tracker.get_entity_articles("ent-1")
        assert len(articles) == 1
        assert articles[0]["entity_name"] == "Apple Inc"
        assert articles[0]["confidence"] == 0.85

    def test_article_lineage(self, tmp_path):
        db = str(tmp_path / "prov.db")
        tracker = self._make_tracker(db)
        tracker.record_step("art-1", "extraction", {}, {"entities": 2})
        tracker.record_step("art-1", "verification", {}, {"verified": 2})
        tracker.record_entity_origin("ent-1", "Apple", "art-1", "regex", 0.9)

        lineage = tracker.get_article_lineage("art-1")
        assert len(lineage["steps"]) == 2
        assert len(lineage["entities_created"]) == 1

    def test_persists_across_instances(self, tmp_path):
        db = str(tmp_path / "prov.db")

        # Write with first instance
        tracker1 = self._make_tracker(db)
        tracker1.record_step("art-1", "dedup", {}, {"dup": False})

        # Read with second instance
        tracker2 = self._make_tracker(db)
        records = tracker2.get_records("art-1")
        assert len(records) == 1
        assert records[0]["step"] == "dedup"

    def test_summary(self, tmp_path):
        db = str(tmp_path / "prov.db")
        tracker = self._make_tracker(db)
        tracker.record_step("art-1", "extraction", {}, {})
        tracker.record_step("art-2", "extraction", {}, {})
        tracker.record_entity_origin("e1", "X", "art-1", "regex", 0.9)

        summary = tracker.get_summary()
        assert summary["total_articles_processed"] == 2
        assert summary["total_steps_recorded"] == 2
        assert summary["total_entities_tracked"] == 1

    def test_in_memory_also_populated(self, tmp_path):
        """In-memory cache stays in sync with SQLite."""
        db = str(tmp_path / "prov.db")
        tracker = self._make_tracker(db)
        tracker.record_step("art-1", "extraction", {}, {})

        # Check in-memory records from parent class
        assert "art-1" in tracker._steps
        assert len(tracker._steps["art-1"]) == 1

    def test_get_all_data_sources(self, tmp_path):
        """Verify get_all_data_sources works (used by SignalBridge)."""
        db = str(tmp_path / "prov.db")
        tracker = self._make_tracker(db)
        tracker.record_step("art-1", "extraction", {"source": "reuters"}, {})
        tracker.record_step("art-2", "extraction", {"source": "rss"}, {})

        sources = tracker.get_all_data_sources()
        assert isinstance(sources, list)
