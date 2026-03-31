# mkg/domain/services/article_dedup.py
"""ArticleDedup — deduplicates articles by URL and content similarity.

R-IA3: Prevent duplicate article processing.
Uses URL normalization and content fingerprinting (simhash-like).
"""

import hashlib
import re
from typing import Any
from urllib.parse import urlparse, urlunparse


def _normalize_url(url: str) -> str:
    """Strip query params, fragments, and trailing slashes."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def _tokenize(text: str) -> set[str]:
    """Extract word tokens from text, lowercased."""
    return set(re.findall(r"\w+", text.lower()))


class ArticleDedup:
    """Deduplicates articles by URL and content similarity."""

    def __init__(self, similarity_threshold: float = 0.8) -> None:
        self._seen_urls: set[str] = set()
        self._content_hashes: set[str] = set()
        self._content_tokens: list[set[str]] = []
        self._similarity_threshold = similarity_threshold

    def fingerprint(self, content: str) -> str:
        """Generate a stable hash fingerprint from content."""
        normalized = " ".join(content.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def mark_seen_url(self, url: str) -> None:
        """Mark a URL as seen."""
        self._seen_urls.add(_normalize_url(url))

    def is_duplicate_url(self, url: str) -> bool:
        """Check if a URL has been seen before."""
        return _normalize_url(url) in self._seen_urls

    def mark_seen_content(self, content: str) -> None:
        """Mark content as seen (stores hash + tokens)."""
        self._content_hashes.add(self.fingerprint(content))
        self._content_tokens.append(_tokenize(content))

    def is_duplicate_content(self, content: str) -> bool:
        """Check if content is a duplicate or near-duplicate."""
        fp = self.fingerprint(content)
        if fp in self._content_hashes:
            return True
        # Jaccard similarity check against stored token sets
        tokens = _tokenize(content)
        for stored_tokens in self._content_tokens:
            if not tokens or not stored_tokens:
                continue
            intersection = len(tokens & stored_tokens)
            union = len(tokens | stored_tokens)
            if union > 0 and intersection / union >= self._similarity_threshold:
                return True
        return False

    def check_article(self, url: str, content: str) -> dict[str, Any]:
        """Check if an article (URL + content) is a duplicate."""
        if self.is_duplicate_url(url):
            return {"is_duplicate": True, "reason": "url"}
        if self.is_duplicate_content(content):
            return {"is_duplicate": True, "reason": "content"}
        return {"is_duplicate": False, "reason": None}

    def get_stats(self) -> dict[str, int]:
        """Get dedup statistics."""
        return {
            "urls_seen": len(self._seen_urls),
            "content_hashes_seen": len(self._content_hashes),
        }
