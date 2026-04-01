# mkg/tests/test_data_retention.py
"""Tests for Data Retention & Privacy — Iterations 31-35.

Verifies:
1. RetentionPolicy — configurable article/entity/audit retention periods
2. PII detection in extracted content
3. Purging of expired data
"""

import pytest
from datetime import datetime, timezone, timedelta


class TestRetentionPolicy:
    """Configurable data retention periods."""

    def test_default_retention_periods(self):
        from mkg.domain.services.retention_policy import RetentionPolicy
        rp = RetentionPolicy()
        assert rp.article_retention_days == 90
        assert rp.entity_retention_days == 365
        assert rp.audit_retention_days == 730  # 2 years for SEBI compliance

    def test_custom_retention_periods(self):
        from mkg.domain.services.retention_policy import RetentionPolicy
        rp = RetentionPolicy(
            article_retention_days=30,
            entity_retention_days=180,
            audit_retention_days=365,
        )
        assert rp.article_retention_days == 30
        assert rp.entity_retention_days == 180
        assert rp.audit_retention_days == 365

    def test_is_expired_article(self):
        from mkg.domain.services.retention_policy import RetentionPolicy
        rp = RetentionPolicy(article_retention_days=30)
        old_date = datetime.now(timezone.utc) - timedelta(days=31)
        assert rp.is_expired("article", old_date) is True

    def test_is_not_expired_article(self):
        from mkg.domain.services.retention_policy import RetentionPolicy
        rp = RetentionPolicy(article_retention_days=30)
        recent_date = datetime.now(timezone.utc) - timedelta(days=5)
        assert rp.is_expired("article", recent_date) is False

    def test_is_expired_entity(self):
        from mkg.domain.services.retention_policy import RetentionPolicy
        rp = RetentionPolicy(entity_retention_days=365)
        old_date = datetime.now(timezone.utc) - timedelta(days=400)
        assert rp.is_expired("entity", old_date) is True

    def test_is_expired_audit(self):
        from mkg.domain.services.retention_policy import RetentionPolicy
        rp = RetentionPolicy(audit_retention_days=730)
        old_date = datetime.now(timezone.utc) - timedelta(days=800)
        assert rp.is_expired("audit", old_date) is True

    def test_unknown_type_never_expires(self):
        from mkg.domain.services.retention_policy import RetentionPolicy
        rp = RetentionPolicy()
        old_date = datetime.now(timezone.utc) - timedelta(days=9999)
        assert rp.is_expired("unknown_type", old_date) is False

    def test_get_expiry_date(self):
        from mkg.domain.services.retention_policy import RetentionPolicy
        rp = RetentionPolicy(article_retention_days=30)
        expiry = rp.get_expiry_date("article")
        assert expiry < datetime.now(timezone.utc)
        expected = datetime.now(timezone.utc) - timedelta(days=30)
        assert abs((expiry - expected).total_seconds()) < 2


class TestPIIDetector:
    """Detect PII in extracted text to protect privacy."""

    def test_detects_email(self):
        from mkg.domain.services.pii_detector import PIIDetector
        detector = PIIDetector()
        result = detector.scan("Contact us at john@example.com for details")
        assert result["has_pii"] is True
        assert "email" in result["pii_types"]

    def test_detects_phone_number(self):
        from mkg.domain.services.pii_detector import PIIDetector
        detector = PIIDetector()
        result = detector.scan("Call +91-9876543210 for details")
        assert result["has_pii"] is True
        assert "phone" in result["pii_types"]

    def test_detects_aadhaar(self):
        from mkg.domain.services.pii_detector import PIIDetector
        detector = PIIDetector()
        result = detector.scan("Aadhaar number 1234 5678 9012")
        assert result["has_pii"] is True
        assert "aadhaar" in result["pii_types"]

    def test_detects_pan(self):
        from mkg.domain.services.pii_detector import PIIDetector
        detector = PIIDetector()
        result = detector.scan("PAN: ABCDE1234F issued to individual")
        assert result["has_pii"] is True
        assert "pan" in result["pii_types"]

    def test_clean_text_no_pii(self):
        from mkg.domain.services.pii_detector import PIIDetector
        detector = PIIDetector()
        result = detector.scan("TSMC reported strong revenue growth driven by AI chip demand")
        assert result["has_pii"] is False
        assert len(result["pii_types"]) == 0

    def test_redact_pii(self):
        from mkg.domain.services.pii_detector import PIIDetector
        detector = PIIDetector()
        redacted = detector.redact("Contact john@example.com for details")
        assert "john@example.com" not in redacted
        assert "[REDACTED]" in redacted

    def test_scan_returns_count(self):
        from mkg.domain.services.pii_detector import PIIDetector
        detector = PIIDetector()
        result = detector.scan(
            "Email john@example.com or jane@test.org"
        )
        assert result["pii_count"] >= 2
