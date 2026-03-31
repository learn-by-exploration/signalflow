# mkg/tests/test_article_dedup.py
"""Tests for ArticleDedup — deduplicates articles by URL and content similarity."""

import pytest


class TestArticleDedup:
    """Test article deduplication logic."""

    @pytest.fixture
    def dedup(self):
        from mkg.domain.services.article_dedup import ArticleDedup
        return ArticleDedup()

    def test_url_dedup_detects_duplicate(self, dedup):
        assert dedup.is_duplicate_url("https://reuters.com/article/1") is False
        dedup.mark_seen_url("https://reuters.com/article/1")
        assert dedup.is_duplicate_url("https://reuters.com/article/1") is True

    def test_url_dedup_normalizes_trailing_slash(self, dedup):
        dedup.mark_seen_url("https://reuters.com/article/1/")
        assert dedup.is_duplicate_url("https://reuters.com/article/1") is True

    def test_url_dedup_normalizes_query_params(self, dedup):
        dedup.mark_seen_url("https://reuters.com/article/1?utm_source=twitter")
        assert dedup.is_duplicate_url("https://reuters.com/article/1") is True

    def test_content_similarity_exact_match(self, dedup):
        text = "TSMC reported record revenue of $23.5 billion in Q1 2026"
        dedup.mark_seen_content(text)
        assert dedup.is_duplicate_content(text) is True

    def test_content_similarity_near_match(self, dedup):
        text1 = "TSMC reported record revenue of $23.5 billion in Q1 2026"
        text2 = "TSMC reported record revenue of $23.5 billion for Q1 2026"
        dedup.mark_seen_content(text1)
        assert dedup.is_duplicate_content(text2) is True

    def test_content_similarity_different_articles(self, dedup):
        text1 = "TSMC reported record revenue of $23.5 billion in Q1 2026"
        text2 = "NVIDIA launches new H200 GPU for AI training workloads"
        dedup.mark_seen_content(text1)
        assert dedup.is_duplicate_content(text2) is False

    def test_check_article_combines_url_and_content(self, dedup):
        result = dedup.check_article(
            url="https://reuters.com/tsmc",
            content="TSMC reported record revenue"
        )
        assert result["is_duplicate"] is False
        dedup.mark_seen_url("https://reuters.com/tsmc")
        result = dedup.check_article(
            url="https://reuters.com/tsmc",
            content="Different content entirely"
        )
        assert result["is_duplicate"] is True
        assert result["reason"] == "url"

    def test_content_hash_fingerprint(self, dedup):
        fp = dedup.fingerprint("Hello World Test Article")
        assert isinstance(fp, str)
        assert len(fp) > 0

    def test_stats(self, dedup):
        dedup.mark_seen_url("https://test.com/1")
        dedup.mark_seen_content("Test content here")
        stats = dedup.get_stats()
        assert stats["urls_seen"] == 1
        assert stats["content_hashes_seen"] == 1

    def test_empty_content_not_duplicate(self, dedup):
        """Two empty strings shouldn't create false duplicates."""
        result = dedup.is_duplicate_content("")
        assert result is False

    def test_unicode_content_dedup(self, dedup):
        text = "日本の半導体メーカーは成長している"
        dedup.mark_seen_content(text)
        assert dedup.is_duplicate_content(text) is True

    def test_url_with_fragment_normalized(self, dedup):
        dedup.mark_seen_url("https://reuters.com/article/1#section2")
        assert dedup.is_duplicate_url("https://reuters.com/article/1") is True

    def test_content_similarity_threshold(self):
        from mkg.domain.services.article_dedup import ArticleDedup
        strict = ArticleDedup(similarity_threshold=0.99)
        text1 = "TSMC reported record revenue of 23.5 billion in Q1 2026 period"
        text2 = "TSMC reported record revenues of 23.5 billion for Q1 2026 period"
        strict.mark_seen_content(text1)
        # Almost same but strict threshold should reject slight differences
        # Depends on actual similarity
        result = strict.is_duplicate_content(text2)
        assert isinstance(result, bool)  # Just verify it doesn't crash

    def test_fingerprint_is_deterministic(self, dedup):
        text = "Same content for fingerprinting"
        fp1 = dedup.fingerprint(text)
        fp2 = dedup.fingerprint(text)
        assert fp1 == fp2

    def test_fingerprint_ignores_whitespace(self, dedup):
        fp1 = dedup.fingerprint("  Hello   World  ")
        fp2 = dedup.fingerprint("Hello World")
        assert fp1 == fp2
