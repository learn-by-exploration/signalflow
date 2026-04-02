# mkg/domain/services/source_credibility.py
"""SourceCredibilityScorer — rates news sources by trustworthiness.

B3: Source credibility scoring for weighted signal generation.
Higher scores for established financial news outlets.
"""

from urllib.parse import urlparse
from typing import Optional

# Tier 1: Primary financial data sources (0.85-1.0)
_TIER_1_SOURCES: dict[str, float] = {
    "reuters.com": 0.95,
    "bloomberg.com": 0.95,
    "ft.com": 0.93,
    "wsj.com": 0.93,
    "sec.gov": 0.98,
    "federalreserve.gov": 0.98,
    "rbi.org.in": 0.97,
    "sebi.gov.in": 0.97,
    "bseindia.com": 0.95,
    "nseindia.com": 0.95,
}

# Tier 2: Reputable financial media (0.65-0.84)
_TIER_2_SOURCES: dict[str, float] = {
    "finance.yahoo.com": 0.75,
    "cnbc.com": 0.78,
    "economictimes.indiatimes.com": 0.72,
    "moneycontrol.com": 0.70,
    "livemint.com": 0.70,
    "marketwatch.com": 0.75,
    "investopedia.com": 0.65,
    "bbc.com": 0.80,
    "nikkei.com": 0.82,
    "scmp.com": 0.75,
    "coindesk.com": 0.70,
    "theblock.co": 0.68,
    "cointelegraph.com": 0.65,
    "forexfactory.com": 0.68,
}

# Tier 3: General news / aggregators (0.40-0.64)
_TIER_3_SOURCES: dict[str, float] = {
    "news.google.com": 0.55,
    "reddit.com": 0.40,
    "twitter.com": 0.40,
    "x.com": 0.40,
    "seeking alpha.com": 0.55,
    "medium.com": 0.45,
    "substack.com": 0.50,
}

_DEFAULT_SCORE = 0.3


class SourceCredibilityScorer:
    """Scores news sources by credibility for extraction confidence weighting."""

    def __init__(self) -> None:
        self._scores: dict[str, float] = {}
        self._scores.update(_TIER_1_SOURCES)
        self._scores.update(_TIER_2_SOURCES)
        self._scores.update(_TIER_3_SOURCES)

    def score(self, domain: str) -> float:
        """Score a domain by credibility [0.0, 1.0].

        Args:
            domain: Domain name (e.g., 'reuters.com') or subdomain.

        Returns:
            Credibility score. Unknown sources get default (0.3).
        """
        if not domain:
            return _DEFAULT_SCORE
        domain = domain.lower().strip()
        # Direct match
        if domain in self._scores:
            return self._scores[domain]
        # Try stripping www.
        if domain.startswith("www."):
            domain = domain[4:]
            if domain in self._scores:
                return self._scores[domain]
        # Try parent domain (e.g., finance.yahoo.com -> yahoo.com)
        parts = domain.split(".")
        if len(parts) > 2:
            parent = ".".join(parts[-2:])
            if parent in self._scores:
                return self._scores[parent]
            # Check subdomain match
            full_domain = domain
            if full_domain in self._scores:
                return self._scores[full_domain]
        return _DEFAULT_SCORE

    def score_url(self, url: str) -> float:
        """Extract domain from URL and score it."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            domain = domain.lower().strip()
            if domain.startswith("www."):
                domain = domain[4:]
            return self.score(domain)
        except Exception:
            return _DEFAULT_SCORE

    def register(self, domain: str, score: float) -> None:
        """Register a custom source with a credibility score."""
        if not 0.0 <= score <= 1.0:
            raise ValueError(f"Score must be in [0.0, 1.0], got {score}")
        self._scores[domain.lower().strip()] = score

    def adjust_confidence(
        self, entity_confidence: float, source_score: float
    ) -> float:
        """Adjust extraction confidence by source credibility.

        Uses geometric mean: sqrt(entity_confidence * source_score).
        This penalizes low-credibility sources without zeroing out confidence.
        """
        if entity_confidence <= 0 or source_score <= 0:
            return 0.0
        return min(entity_confidence, (entity_confidence * source_score) ** 0.5)
