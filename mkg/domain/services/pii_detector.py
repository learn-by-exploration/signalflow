# mkg/domain/services/pii_detector.py
"""PIIDetector — detects and redacts PII in extracted text.

Protects privacy by scanning for:
- Email addresses
- Phone numbers (Indian and international)
- Aadhaar numbers (Indian national ID)
- PAN (Permanent Account Number)

Financial news articles should not contain PII, but scraped content
may accidentally include it. This service flags and optionally redacts
PII before storing content in the knowledge graph.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# PII detection patterns
_PATTERNS: dict[str, re.Pattern] = {
    "email": re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    ),
    "phone": re.compile(
        r"(?:\+?\d{1,3}[\s\-]?)?\(?\d{3,5}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}",
    ),
    "aadhaar": re.compile(
        r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    ),
    "pan": re.compile(
        r"\b[A-Z]{5}\d{4}[A-Z]\b",
    ),
}

# Redaction marker
_REDACTED = "[REDACTED]"


class PIIDetector:
    """Detects and redacts Personally Identifiable Information.

    Usage:
        detector = PIIDetector()
        result = detector.scan(text)
        if result["has_pii"]:
            clean_text = detector.redact(text)
    """

    def scan(self, text: str) -> dict[str, Any]:
        """Scan text for PII.

        Args:
            text: The text to scan.

        Returns:
            Dict with:
            - has_pii: bool — whether PII was found
            - pii_types: list[str] — types of PII found
            - pii_count: int — total number of PII instances
        """
        pii_types: list[str] = []
        pii_count = 0

        for pii_type, pattern in _PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                pii_types.append(pii_type)
                pii_count += len(matches)

        return {
            "has_pii": len(pii_types) > 0,
            "pii_types": pii_types,
            "pii_count": pii_count,
        }

    def redact(self, text: str) -> str:
        """Redact all PII from text.

        Replaces PII matches with [REDACTED] marker.

        Args:
            text: The text to redact.

        Returns:
            Text with PII replaced by [REDACTED].
        """
        result = text
        for pattern in _PATTERNS.values():
            result = pattern.sub(_REDACTED, result)
        return result
