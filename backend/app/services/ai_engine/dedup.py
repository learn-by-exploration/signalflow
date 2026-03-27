"""Semantic deduplication for news articles.

Identifies duplicate/near-duplicate news articles using text similarity.
Uses TF-IDF + cosine similarity for lightweight, dependency-free dedup.
When articles are duplicates, keeps the one from the highest-credibility source.
"""

import logging
import math
import re
from collections import Counter
from typing import Any

from app.services.ai_engine.news_fetcher import get_source_weight

logger = logging.getLogger(__name__)

# Similarity threshold: articles above this are considered duplicates
SIMILARITY_THRESHOLD = 0.70

# Stop words for TF-IDF (common English + financial noise words)
_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "can",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "and",
        "but",
        "or",
        "not",
        "no",
        "so",
        "if",
        "than",
        "too",
        "very",
        "just",
        "about",
        "up",
        "out",
        "off",
        "over",
        "own",
        "same",
        "only",
        "other",
        "new",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "he",
        "she",
        "they",
        "his",
        "her",
        "their",
        "we",
        "our",
        "you",
        "your",
        "i",
        "me",
        "my",
        "says",
        "said",
        "report",
        "reports",
        "according",
        "also",
        "more",
        "market",
        "markets",
        "stock",
        "stocks",
        "price",
        "prices",
    }
)


def _tokenize(text: str) -> list[str]:
    """Tokenize and normalize text for similarity computation."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = text.split()
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 2]


def _compute_tfidf_vectors(
    documents: list[list[str]],
) -> tuple[list[dict[str, float]], dict[str, float]]:
    """Compute TF-IDF vectors for a corpus of tokenized documents.

    Returns:
        Tuple of (tf-idf vectors per doc, idf weights).
    """
    n_docs = len(documents)
    if n_docs == 0:
        return [], {}

    # Document frequency
    doc_freq: Counter[str] = Counter()
    for tokens in documents:
        unique_tokens = set(tokens)
        for token in unique_tokens:
            doc_freq[token] += 1

    # IDF
    idf: dict[str, float] = {}
    for token, df in doc_freq.items():
        idf[token] = math.log((n_docs + 1) / (df + 1)) + 1  # smoothed IDF

    # TF-IDF per document
    vectors: list[dict[str, float]] = []
    for tokens in documents:
        tf = Counter(tokens)
        total = len(tokens) if tokens else 1
        vec: dict[str, float] = {}
        for token, count in tf.items():
            vec[token] = (count / total) * idf.get(token, 1.0)
        vectors.append(vec)

    return vectors, idf


def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Compute cosine similarity between two sparse vectors."""
    # Dot product
    common_keys = set(vec_a.keys()) & set(vec_b.keys())
    if not common_keys:
        return 0.0

    dot = sum(vec_a[k] * vec_b[k] for k in common_keys)

    # Magnitudes
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)


def deduplicate_articles(
    articles: list[dict[str, str]],
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[dict[str, str]]:
    """Remove semantically duplicate news articles.

    When two articles are similar above threshold, keeps the one from the
    higher-credibility source.

    Args:
        articles: List of article dicts with 'headline' and 'source' fields.
        threshold: Cosine similarity threshold for considering duplicates.

    Returns:
        Deduplicated list of articles.
    """
    if len(articles) <= 1:
        return articles

    # Tokenize all headlines
    tokenized = [_tokenize(a.get("headline", "")) for a in articles]

    # Skip dedup if tokenization produced empty results
    if all(len(t) == 0 for t in tokenized):
        return articles

    # Compute TF-IDF vectors
    vectors, _ = _compute_tfidf_vectors(tokenized)

    # Find duplicate clusters
    is_duplicate = [False] * len(articles)

    for i in range(len(articles)):
        if is_duplicate[i]:
            continue
        for j in range(i + 1, len(articles)):
            if is_duplicate[j]:
                continue

            sim = _cosine_similarity(vectors[i], vectors[j])
            if sim >= threshold:
                # Keep the article from the higher-credibility source
                weight_i = get_source_weight(articles[i].get("source", ""))
                weight_j = get_source_weight(articles[j].get("source", ""))

                if weight_i >= weight_j:
                    is_duplicate[j] = True
                else:
                    is_duplicate[i] = True
                    break  # i is now a duplicate, stop comparing

    result = [a for a, dup in zip(articles, is_duplicate) if not dup]

    removed = len(articles) - len(result)
    if removed > 0:
        logger.info("semantic_dedup_removed", count=removed, original=len(articles))

    return result
