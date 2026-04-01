# mkg/tests/test_concurrent_safety.py
"""Concurrent write safety tests for persistent storage.

Verifies that concurrent writes to SQLite-backed audit and provenance
don't cause data loss or corruption (WAL mode + serialized writes).
"""

import os
import threading
import time

import pytest

from mkg.domain.services.audit_logger import AuditAction


class TestConcurrentAuditWrites:
    """Test concurrent write safety for PersistentAuditLogger."""

    def test_concurrent_audit_log_writes(self, tmp_path):
        """Multiple threads writing audit entries should not lose data."""
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger

        db_path = str(tmp_path / "audit_concurrent.db")
        # Pre-create the DB
        PersistentAuditLogger(db_path=db_path)

        entries_per_thread = 50
        num_threads = 4
        total_expected = entries_per_thread * num_threads

        errors: list[str] = []

        def writer(thread_id: int):
            try:
                logger = PersistentAuditLogger(db_path=db_path)
                for i in range(entries_per_thread):
                    logger.log(
                        AuditAction.ENTITY_CREATED,
                        f"thread-{thread_id}",
                        f"art-{thread_id}-{i}",
                        "article",
                        {"thread": thread_id, "index": i},
                    )
                    time.sleep(0.001)  # Small delay to reduce lock contention
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")

        threads = [
            threading.Thread(target=writer, args=(t,))
            for t in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread errors: {errors}"

        # Verify all entries were written
        verifier = PersistentAuditLogger(db_path=db_path)
        entries = verifier.get_entries(limit=10000)
        assert len(entries) >= total_expected

    def test_concurrent_read_write(self, tmp_path):
        """Reads while writes are happening should not fail."""
        from mkg.infrastructure.persistent.audit_logger import PersistentAuditLogger

        db_path = str(tmp_path / "audit_rw.db")
        # Pre-create the DB so both threads share the same schema
        PersistentAuditLogger(db_path=db_path)

        read_results: list[int] = []
        errors: list[str] = []

        def writer():
            try:
                logger = PersistentAuditLogger(db_path=db_path)
                for i in range(50):
                    logger.log(
                        AuditAction.ENTITY_CREATED,
                        "writer",
                        f"art-{i}",
                        "article",
                        {},
                    )
                    time.sleep(0.002)
            except Exception as e:
                errors.append(f"Writer: {e}")

        def reader():
            try:
                time.sleep(0.01)  # Let writer get started
                logger = PersistentAuditLogger(db_path=db_path)
                for _ in range(10):
                    entries = logger.get_entries(limit=100)
                    read_results.append(len(entries))
                    time.sleep(0.01)
            except Exception as e:
                errors.append(f"Reader: {e}")

        w = threading.Thread(target=writer)
        r = threading.Thread(target=reader)
        w.start()
        r.start()
        w.join()
        r.join()

        assert len(errors) == 0, f"Errors: {errors}"
        # Reader should see some entries
        assert len(read_results) > 0


class TestConcurrentProvenanceWrites:
    """Test concurrent write safety for PersistentProvenanceTracker."""

    def test_concurrent_provenance_writes(self, tmp_path):
        """Multiple threads writing provenance steps should not lose data."""
        from mkg.infrastructure.persistent.provenance_tracker import PersistentProvenanceTracker

        db_path = str(tmp_path / "prov_concurrent.db")
        # Pre-create the DB
        PersistentProvenanceTracker(db_path=db_path)

        steps_per_thread = 50
        num_threads = 4
        total_expected = steps_per_thread * num_threads

        errors: list[str] = []

        def writer(thread_id: int):
            try:
                tracker = PersistentProvenanceTracker(db_path=db_path)
                for i in range(steps_per_thread):
                    tracker.record_step(
                        f"art-{thread_id}-{i}",
                        "extraction",
                        {"thread": thread_id},
                        {"entities": i},
                    )
                    time.sleep(0.001)  # Small delay to reduce lock contention
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")

        threads = [
            threading.Thread(target=writer, args=(t,))
            for t in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread errors: {errors}"

        # Verify all steps were written
        verifier = PersistentProvenanceTracker(db_path=db_path)
        summary = verifier.get_summary()
        assert summary["total_steps_recorded"] >= total_expected

    def test_concurrent_entity_origin_writes(self, tmp_path):
        """Multiple threads recording entity origins concurrently."""
        from mkg.infrastructure.persistent.provenance_tracker import PersistentProvenanceTracker

        db_path = str(tmp_path / "prov_entities.db")
        # Pre-create the DB
        PersistentProvenanceTracker(db_path=db_path)

        errors: list[str] = []

        def writer(thread_id: int):
            try:
                tracker = PersistentProvenanceTracker(db_path=db_path)
                for i in range(30):
                    tracker.record_entity_origin(
                        f"ent-{thread_id}-{i}",
                        f"Entity_{thread_id}_{i}",
                        f"art-{thread_id}",
                        "regex",
                        0.85,
                    )
                    time.sleep(0.001)  # Small delay to reduce lock contention
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")

        threads = [
            threading.Thread(target=writer, args=(t,))
            for t in range(3)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread errors: {errors}"

        verifier = PersistentProvenanceTracker(db_path=db_path)
        summary = verifier.get_summary()
        assert summary["total_entities_tracked"] >= 90  # 3 threads * 30 entities
