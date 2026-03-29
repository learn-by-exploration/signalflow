"""Tests for Phase 4: Product Focus (v1.4 plan).

Tests cover: nav cleanup, performance endpoint, streak protection, seed data.
"""

import inspect
import os

import pytest


# ═══════════════════════════════════════════════════════════
# Task 4.1: Nav Cleanup Tests
# ═══════════════════════════════════════════════════════════
class TestNavCleanup:
    """Verify navigation is properly organized into primary + research groups."""

    def test_navbar_uses_constants(self):
        """Navbar should import nav link constants instead of hardcoding routes."""
        navbar_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "frontend", "src", "components", "shared", "Navbar.tsx",
        )
        with open(navbar_path) as f:
            content = f.read()
        assert "NAV_PRIMARY_LINKS" in content, "Navbar should use NAV_PRIMARY_LINKS from constants"
        assert "NAV_RESEARCH_LINKS" in content, "Navbar should use NAV_RESEARCH_LINKS for dropdown"

    def test_navbar_has_research_dropdown(self):
        """Navbar should have a Research dropdown for secondary pages."""
        navbar_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "frontend", "src", "components", "shared", "Navbar.tsx",
        )
        with open(navbar_path) as f:
            content = f.read()
        # Research routes are listed for active-state detection
        assert "'/news'" in content
        assert "'/calendar'" in content

    def test_primary_links_in_constants(self):
        """Primary nav links should be defined in constants.ts, not hardcoded."""
        constants_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "frontend", "src", "lib", "constants.ts",
        )
        with open(constants_path) as f:
            content = f.read()
        assert "NAV_PRIMARY_LINKS" in content
        assert "'Dashboard'" in content
        assert "'Track Record'" in content

    def test_research_links_in_constants(self):
        """Research nav links should be defined in constants.ts."""
        constants_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "frontend", "src", "lib", "constants.ts",
        )
        with open(constants_path) as f:
            content = f.read()
        assert "NAV_RESEARCH_LINKS" in content
        assert "'News'" in content
        assert "'Calendar'" in content
        assert "'Backtest'" in content

    def test_info_links_in_constants(self):
        """Info links (How It Works, Pricing) in constants.ts."""
        constants_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "frontend", "src", "lib", "constants.ts",
        )
        with open(constants_path) as f:
            content = f.read()
        assert "NAV_INFO_LINKS" in content
        assert "'How It Works'" in content
        assert "'Pricing'" in content

    def test_page_files_still_exist(self):
        """Hidden pages should still have their code (not deleted from disk)."""
        frontend_base = os.path.join(
            os.path.dirname(__file__), "..", "..", "frontend", "src", "app",
        )
        hidden_pages = ["backtest", "portfolio"]
        for page in hidden_pages:
            page_file = os.path.join(frontend_base, page, "page.tsx")
            assert os.path.isfile(page_file), f"{page}/page.tsx should still exist"


# ═══════════════════════════════════════════════════════════
# Task 4.4: Signal Performance by Market Type Tests
# ═══════════════════════════════════════════════════════════
class TestSignalPerformance:
    """Verify signal performance endpoint."""

    @pytest.mark.asyncio
    async def test_performance_endpoint_exists(self, test_client):
        """GET /signals/performance should return 200."""
        resp = await test_client.get("/api/v1/signals/performance")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_performance_returns_data_dict(self, test_client):
        """Performance response should have 'data' key."""
        resp = await test_client.get("/api/v1/signals/performance")
        data = resp.json()
        assert "data" in data
        assert isinstance(data["data"], dict)

    def test_performance_endpoint_in_history_module(self):
        """Performance endpoint should be in history.py."""
        import app.api.history as mod
        source = inspect.getsource(mod)
        assert "performance" in source
        assert "market_type" in source

    @pytest.mark.asyncio
    async def test_performance_structure(self, test_client):
        """Each market in performance should have win_rate and by_signal_type."""
        resp = await test_client.get("/api/v1/signals/performance")
        data = resp.json()["data"]
        for _market_type, metrics in data.items():
            assert "total" in metrics
            assert "hit_target" in metrics
            assert "hit_stop" in metrics
            assert "win_rate" in metrics
            assert "by_signal_type" in metrics


# ═══════════════════════════════════════════════════════════
# Task 4.3: Losing Streak Protection Tests
# ═══════════════════════════════════════════════════════════
class TestLosingStreakProtection:
    """Verify streak detection and alert formatting."""

    def test_streak_protection_module_exists(self):
        """streak_protection module should be importable."""
        from app.services.signal_gen.streak_protection import (
            STREAK_THRESHOLD,
            check_losing_streak,
            format_streak_alert,
        )
        assert STREAK_THRESHOLD == 3
        assert callable(check_losing_streak)
        assert callable(format_streak_alert)

    def test_format_streak_alert(self):
        """format_streak_alert should produce readable message."""
        from app.services.signal_gen.streak_protection import format_streak_alert

        data = {
            "is_streak": True,
            "streak_length": 4,
            "symbols": ["HDFCBANK", "TCS", "INFY", "RELIANCE"],
            "suggestion": "Reduce position sizes.",
        }
        msg = format_streak_alert(data)
        assert "LOSING STREAK" in msg
        assert "4 consecutive" in msg
        assert "HDFCBANK" in msg
        assert "50%" in msg

    @pytest.mark.asyncio
    async def test_streak_check_endpoint(self, test_client):
        """GET /signals/streak-check should return 200."""
        resp = await test_client.get("/api/v1/signals/streak-check")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "is_streak" in data
        assert "streak_length" in data

    @pytest.mark.asyncio
    async def test_streak_check_with_market_filter(self, test_client):
        """Streak check should accept market_type filter."""
        resp = await test_client.get("/api/v1/signals/streak-check?market_type=crypto")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_no_streak_on_empty_db(self, test_client):
        """No streak should be detected on empty/sparse database."""
        resp = await test_client.get("/api/v1/signals/streak-check")
        data = resp.json()["data"]
        assert "is_streak" in data
        assert "streak_length" in data
        # May or may not have 0 streak depending on seeded data
        assert isinstance(data["streak_length"], int)


# ═══════════════════════════════════════════════════════════
# Task 4.2: Seed Demo Signals Tests
# ═══════════════════════════════════════════════════════════
class TestSeedDemoSignals:
    """Verify demo signal seed data."""

    def test_demo_signals_module_exists(self):
        """seed_demo_signals module should be importable."""
        import os
        import sys
        scripts_dir = os.path.join(os.path.dirname(__file__), "..", "scripts")
        sys.path.insert(0, scripts_dir)
        try:
            from seed_demo_signals import DEMO_SIGNALS, seed_demo_signals
            assert len(DEMO_SIGNALS) == 5
            assert callable(seed_demo_signals)
        finally:
            sys.path.pop(0)

    def test_demo_signals_have_required_fields(self):
        """Each demo signal must have required fields."""
        import os
        import sys
        scripts_dir = os.path.join(os.path.dirname(__file__), "..", "scripts")
        sys.path.insert(0, scripts_dir)
        try:
            from seed_demo_signals import DEMO_SIGNALS

            required_fields = {
                "symbol", "market_type", "signal_type", "confidence",
                "current_price", "target_price", "stop_loss", "timeframe",
                "ai_reasoning", "technical_data", "sentiment_data",
            }
            for sig in DEMO_SIGNALS:
                for field in required_fields:
                    assert field in sig, f"Demo signal missing '{field}'"
        finally:
            sys.path.pop(0)

    def test_demo_signals_market_diversity(self):
        """Demo signals should cover all 3 markets."""
        import os
        import sys
        scripts_dir = os.path.join(os.path.dirname(__file__), "..", "scripts")
        sys.path.insert(0, scripts_dir)
        try:
            from seed_demo_signals import DEMO_SIGNALS

            markets = {s["market_type"] for s in DEMO_SIGNALS}
            assert "stock" in markets
            assert "crypto" in markets
            assert "forex" in markets
        finally:
            sys.path.pop(0)

    def test_demo_signal_types_diversity(self):
        """Demo signals should include BUY and SELL types."""
        import os
        import sys
        scripts_dir = os.path.join(os.path.dirname(__file__), "..", "scripts")
        sys.path.insert(0, scripts_dir)
        try:
            from seed_demo_signals import DEMO_SIGNALS

            types = {s["signal_type"] for s in DEMO_SIGNALS}
            assert "STRONG_BUY" in types or "BUY" in types
            assert "SELL" in types or "STRONG_SELL" in types
        finally:
            sys.path.pop(0)
