# mkg/domain/services/temporal_extractor.py
"""TemporalExtractor — extract dates, deadlines, and temporal events from text.

B4: Extract structured temporal references from financial articles.
Supports explicit dates, ISO dates, and quarter/fiscal references.
"""

import re
from datetime import datetime
from typing import Any

# Month name lookup
_MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9,
    "oct": 10, "nov": 11, "dec": 12,
}

# ISO date: 2025-03-15
_ISO_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")

# Long date: March 15, 2025 or 15 March 2025
_LONG_DATE = re.compile(
    r"(?:(\d{1,2})\s+)?"
    r"(January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
    r"\.?\s+(\d{1,2}),?\s*(\d{4})",
    re.IGNORECASE,
)

# Reversed long date: 15 March 2025
_REVERSED_DATE = re.compile(
    r"(\d{1,2})\s+"
    r"(January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
    r"\.?,?\s*(\d{4})",
    re.IGNORECASE,
)

# Quarter reference: Q3 2025, Q1 FY2025
_QUARTER_REF = re.compile(r"Q([1-4])\s*(?:FY)?(\d{4})", re.IGNORECASE)

# Event type keywords
_EVENT_KEYWORDS = {
    "earnings": ["earnings", "quarterly results", "financial results", "profit", "revenue report"],
    "launch": ["launch", "release", "unveil", "introduce", "announce", "debut"],
    "deadline": ["deadline", "due date", "expires", "expiry", "by"],
    "regulatory": ["filing", "compliance", "regulatory", "approval"],
    "production": ["production", "manufacturing", "fab", "factory", "ramp"],
}


class TemporalExtractor:
    """Extract temporal events (dates, deadlines) from financial text."""

    async def extract(self, text: str) -> list[dict[str, Any]]:
        """Extract all temporal references from text.

        Returns list of dicts with: date, reference, context, event_type.
        """
        if not text:
            return []

        events: list[dict[str, Any]] = []
        seen_dates: set[str] = set()

        # ISO dates
        for match in _ISO_DATE.finditer(text):
            date_str = match.group(0)
            if date_str not in seen_dates:
                seen_dates.add(date_str)
                context = self._extract_context(text, match.start(), match.end())
                events.append({
                    "date": date_str,
                    "reference": date_str,
                    "context": context,
                    "event_type": self._classify_event(context),
                })

        # Long dates: March 15, 2025
        for match in _LONG_DATE.finditer(text):
            month_name = match.group(2).lower()
            day = int(match.group(3))
            year = int(match.group(4))
            month = _MONTH_NAMES.get(month_name)
            if month:
                try:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    if date_str not in seen_dates:
                        seen_dates.add(date_str)
                        context = self._extract_context(text, match.start(), match.end())
                        events.append({
                            "date": date_str,
                            "reference": match.group(0),
                            "context": context,
                            "event_type": self._classify_event(context),
                        })
                except ValueError:
                    pass

        # Reversed dates: 15 March 2025
        for match in _REVERSED_DATE.finditer(text):
            day = int(match.group(1))
            month_name = match.group(2).lower()
            year = int(match.group(3))
            month = _MONTH_NAMES.get(month_name)
            if month:
                try:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    if date_str not in seen_dates:
                        seen_dates.add(date_str)
                        context = self._extract_context(text, match.start(), match.end())
                        events.append({
                            "date": date_str,
                            "reference": match.group(0),
                            "context": context,
                            "event_type": self._classify_event(context),
                        })
                except ValueError:
                    pass

        # Quarter references: Q3 2025
        for match in _QUARTER_REF.finditer(text):
            quarter = int(match.group(1))
            year = int(match.group(2))
            # Map quarter to approximate month
            quarter_month = {1: 3, 2: 6, 3: 9, 4: 12}[quarter]
            date_str = f"{year}-{quarter_month:02d}-01"
            ref = match.group(0)
            if date_str not in seen_dates:
                seen_dates.add(date_str)
                context = self._extract_context(text, match.start(), match.end())
                events.append({
                    "date": date_str,
                    "reference": ref,
                    "context": context,
                    "event_type": self._classify_event(context),
                })

        return events

    def _extract_context(self, text: str, start: int, end: int, window: int = 80) -> str:
        """Extract surrounding context around a match."""
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)
        context = text[ctx_start:ctx_end].strip()
        # Clean up partial words at boundaries
        if ctx_start > 0:
            space_idx = context.find(" ")
            if space_idx > 0:
                context = context[space_idx + 1:]
        if ctx_end < len(text):
            space_idx = context.rfind(" ")
            if space_idx > 0:
                context = context[:space_idx]
        return context

    def _classify_event(self, context: str) -> str:
        """Classify a temporal event based on context keywords."""
        context_lower = context.lower()
        for event_type, keywords in _EVENT_KEYWORDS.items():
            if any(kw in context_lower for kw in keywords):
                return event_type
        return "general"
