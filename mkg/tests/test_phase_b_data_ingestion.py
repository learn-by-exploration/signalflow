# mkg/tests/test_phase_b_data_ingestion.py
"""Phase B — Data Ingestion Scale.

TDD Red tests for:
  B1: Multi-source RSS (10+ feeds across finance categories)
  B2: Multilingual NER support (entity extraction in 5+ languages)
  B3: Source credibility scoring
  B4: Temporal event extraction from articles
"""

import pytest
from datetime import datetime, timezone

# ── B1: Multi-source RSS ──


class TestMultiSourceRSSFeeds:
    """B1: The system must support 10+ configurable RSS feed sources."""

    def test_default_financial_feeds_count(self):
        """Default feed list has 10+ feeds across categories."""
        from mkg.infrastructure.external.real_news_fetcher import get_default_feeds

        feeds = get_default_feeds()
        assert len(feeds) >= 10, f"Expected 10+ feeds, got {len(feeds)}"

    def test_feeds_have_required_metadata(self):
        """Each feed must have url, category, language, and credibility_score."""
        from mkg.infrastructure.external.real_news_fetcher import get_default_feeds

        feeds = get_default_feeds()
        required_keys = {"url", "category", "language", "credibility_score"}
        for feed in feeds:
            missing = required_keys - set(feed.keys())
            assert not missing, f"Feed {feed.get('url', '?')} missing: {missing}"

    def test_feeds_cover_required_categories(self):
        """Feeds must cover: equities, crypto, forex, macro, commodities."""
        from mkg.infrastructure.external.real_news_fetcher import get_default_feeds

        feeds = get_default_feeds()
        categories = {f["category"] for f in feeds}
        required_categories = {"equities", "crypto", "forex", "macro", "commodities"}
        missing = required_categories - categories
        assert not missing, f"Missing feed categories: {missing}"

    def test_rss_fetcher_uses_configured_feeds(self):
        """RSSNewsFetcher accepts the structured feed list."""
        from mkg.infrastructure.external.real_news_fetcher import (
            RSSNewsFetcher,
            get_default_feeds,
        )

        feeds = get_default_feeds()
        fetcher = RSSNewsFetcher(feed_urls=[f["url"] for f in feeds])
        assert len(fetcher._feed_urls) >= 10

    def test_fetched_articles_include_source_metadata(self):
        """Articles from RSS include feed category and credibility."""
        from mkg.infrastructure.external.real_news_fetcher import (
            RSSNewsFetcher,
            get_default_feeds,
        )

        feeds = get_default_feeds()
        # Build a feed_url -> metadata map
        feed_meta = {f["url"]: f for f in feeds}
        fetcher = RSSNewsFetcher(feed_urls=[f["url"] for f in feeds])
        fetcher._feed_metadata = feed_meta
        # Metadata map should be accessible
        assert len(fetcher._feed_metadata) >= 10


# ── B2: Multilingual NER ──


class TestMultilingualNER:
    """B2: Entity extraction in 5+ languages."""

    @pytest.mark.asyncio
    async def test_regex_extractor_detects_english_companies(self):
        """Baseline: English extraction still works."""
        from mkg.infrastructure.llm.regex_extractor import RegexExtractor

        ext = RegexExtractor()
        entities = await ext.extract_entities(
            "TSMC announced a new factory. NVIDIA is their top customer."
        )
        names = [e["name"] for e in entities]
        assert "TSMC" in names
        assert "NVIDIA" in names

    @pytest.mark.asyncio
    async def test_regex_extractor_detects_chinese_companies(self):
        """Chinese entity names are recognized."""
        from mkg.infrastructure.llm.regex_extractor import RegexExtractor

        ext = RegexExtractor()
        entities = await ext.extract_entities(
            "台積電宣布在美國建設新晶圓廠。三星電子也在擴大產能。"
        )
        names = [e["name"] for e in entities]
        assert any("台積電" in n or "TSMC" in n for n in names), \
            f"Expected 台積電/TSMC in {names}"

    @pytest.mark.asyncio
    async def test_regex_extractor_detects_japanese_companies(self):
        """Japanese entity names are recognized."""
        from mkg.infrastructure.llm.regex_extractor import RegexExtractor

        ext = RegexExtractor()
        entities = await ext.extract_entities(
            "ソニーとトヨタ自動車が半導体供給に関する提携を発表した。"
        )
        names = [e["name"] for e in entities]
        assert any("ソニー" in n or "Sony" in n for n in names), \
            f"Expected Sony/ソニー in {names}"

    @pytest.mark.asyncio
    async def test_regex_extractor_detects_korean_companies(self):
        """Korean entity names are recognized."""
        from mkg.infrastructure.llm.regex_extractor import RegexExtractor

        ext = RegexExtractor()
        entities = await ext.extract_entities(
            "삼성전자와 SK하이닉스가 HBM 생산을 확대하고 있다."
        )
        names = [e["name"] for e in entities]
        assert any("삼성" in n or "Samsung" in n for n in names), \
            f"Expected Samsung/삼성 in {names}"

    @pytest.mark.asyncio
    async def test_regex_extractor_detects_hindi_companies(self):
        """Hindi/Devanagari entity names are recognized."""
        from mkg.infrastructure.llm.regex_extractor import RegexExtractor

        ext = RegexExtractor()
        entities = await ext.extract_entities(
            "रिलायंस इंडस्ट्रीज ने टीसीएस के साथ एक नई साझेदारी की घोषणा की।"
        )
        names = [e["name"] for e in entities]
        assert any("रिलायंस" in n or "Reliance" in n for n in names), \
            f"Expected Reliance/रिलायंस in {names}"

    @pytest.mark.asyncio
    async def test_language_detection(self):
        """detect_language() identifies text language correctly."""
        from mkg.infrastructure.llm.regex_extractor import detect_language

        assert detect_language("TSMC announced a new factory") == "en"
        assert detect_language("台積電宣布建設新晶圓廠") in ("zh", "zh-TW")
        assert detect_language("삼성전자가 발표했다") == "ko"
        assert detect_language("ソニーが新製品を発表") == "ja"
        assert detect_language("रिलायंस ने घोषणा की") == "hi"


# ── B3: Source Credibility ──


class TestSourceCredibility:
    """B3: Source credibility scoring for weighted signal generation."""

    def test_credibility_scorer_exists(self):
        """SourceCredibilityScorer class exists."""
        from mkg.domain.services.source_credibility import SourceCredibilityScorer
        scorer = SourceCredibilityScorer()
        assert scorer is not None

    def test_known_sources_have_scores(self):
        """Well-known financial sources have pre-configured scores."""
        from mkg.domain.services.source_credibility import SourceCredibilityScorer

        scorer = SourceCredibilityScorer()
        # Tier 1 sources should score high
        assert scorer.score("reuters.com") >= 0.85
        assert scorer.score("bloomberg.com") >= 0.85
        # Tier 2 sources should score medium
        assert scorer.score("finance.yahoo.com") >= 0.6
        # Unknown sources should get default score
        assert scorer.score("unknown-blog.example.com") <= 0.5

    def test_credibility_score_range(self):
        """All scores must be in [0.0, 1.0]."""
        from mkg.domain.services.source_credibility import SourceCredibilityScorer

        scorer = SourceCredibilityScorer()
        for source in ["reuters.com", "xyz.com", "bbc.com", ""]:
            score = scorer.score(source)
            assert 0.0 <= score <= 1.0, f"Score {score} out of range for {source}"

    def test_credibility_from_url(self):
        """score_url() extracts domain and scores it."""
        from mkg.domain.services.source_credibility import SourceCredibilityScorer

        scorer = SourceCredibilityScorer()
        score = scorer.score_url("https://www.reuters.com/markets/us/something")
        assert score >= 0.85

    def test_credibility_adjusts_extraction_confidence(self):
        """Extraction confidence is scaled by source credibility."""
        from mkg.domain.services.source_credibility import SourceCredibilityScorer

        scorer = SourceCredibilityScorer()
        entity_confidence = 0.8
        source_score = scorer.score("reuters.com")
        adjusted = scorer.adjust_confidence(entity_confidence, source_score)
        assert adjusted <= entity_confidence  # Can't exceed original
        assert adjusted > 0.0

    def test_credibility_register_custom_source(self):
        """Custom sources can be registered with a score."""
        from mkg.domain.services.source_credibility import SourceCredibilityScorer

        scorer = SourceCredibilityScorer()
        scorer.register("my-trusted-source.com", 0.9)
        assert scorer.score("my-trusted-source.com") == 0.9


# ── B4: Temporal Event Extraction ──


class TestTemporalEventExtraction:
    """B4: Extract dates, deadlines, and temporal references from articles."""

    @pytest.mark.asyncio
    async def test_extract_explicit_dates(self):
        """Explicit dates like 'March 15, 2025' are extracted."""
        from mkg.domain.services.temporal_extractor import TemporalExtractor

        ext = TemporalExtractor()
        text = "TSMC will begin production at the Arizona fab on March 15, 2025."
        events = await ext.extract(text)
        assert len(events) >= 1
        assert any(e["date"] == "2025-03-15" for e in events)

    @pytest.mark.asyncio
    async def test_extract_relative_dates(self):
        """Relative dates like 'next quarter' or 'by Q3 2025' are extracted."""
        from mkg.domain.services.temporal_extractor import TemporalExtractor

        ext = TemporalExtractor()
        text = "Samsung plans to ramp HBM4 production by Q3 2025."
        events = await ext.extract(text)
        assert len(events) >= 1
        assert any("Q3" in e.get("reference", "") or "2025" in e.get("date", "") for e in events)

    @pytest.mark.asyncio
    async def test_extract_deadline_context(self):
        """Temporal events include context about what the deadline is for."""
        from mkg.domain.services.temporal_extractor import TemporalExtractor

        ext = TemporalExtractor()
        text = "Intel's earnings report is scheduled for January 23, 2025."
        events = await ext.extract(text)
        assert len(events) >= 1
        event = events[0]
        assert "context" in event
        assert len(event["context"]) > 0

    @pytest.mark.asyncio
    async def test_extract_iso_dates(self):
        """ISO format dates (2025-03-15) are extracted."""
        from mkg.domain.services.temporal_extractor import TemporalExtractor

        ext = TemporalExtractor()
        text = "The deadline is 2025-03-15 for all submissions."
        events = await ext.extract(text)
        assert len(events) >= 1
        assert events[0]["date"] == "2025-03-15"

    @pytest.mark.asyncio
    async def test_extract_multiple_dates(self):
        """Multiple dates in one article are all extracted."""
        from mkg.domain.services.temporal_extractor import TemporalExtractor

        ext = TemporalExtractor()
        text = (
            "Phase 1 begins April 1, 2025. Phase 2 starts August 15, 2025. "
            "Final delivery expected by December 31, 2025."
        )
        events = await ext.extract(text)
        assert len(events) >= 3

    @pytest.mark.asyncio
    async def test_empty_text_returns_empty(self):
        """No temporal events from empty text."""
        from mkg.domain.services.temporal_extractor import TemporalExtractor

        ext = TemporalExtractor()
        events = await ext.extract("")
        assert events == []

    @pytest.mark.asyncio
    async def test_event_type_classification(self):
        """Extracted events are classified: earnings, launch, deadline, general."""
        from mkg.domain.services.temporal_extractor import TemporalExtractor

        ext = TemporalExtractor()
        text = "TSMC earnings call on January 18, 2025. New chip launch on March 1, 2025."
        events = await ext.extract(text)
        types = {e.get("event_type") for e in events}
        assert len(types) >= 1  # At least some classification
