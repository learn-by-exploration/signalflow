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
