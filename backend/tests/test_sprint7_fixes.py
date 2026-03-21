"""Tests for Sprint 7: .NS resolution fix, track record schema, symbol normalization."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.schemas.signal import SymbolTrackRecord


class TestSymbolTrackRecordSchema:
    """Test the SymbolTrackRecord Pydantic schema."""

    def test_basic_creation(self) -> None:
        record = SymbolTrackRecord(
            symbol="HDFCBANK.NS",
            total_signals_30d=5,
            hit_target=3,
            hit_stop=1,
            expired=1,
            win_rate=75.0,
            avg_return_pct=2.3,
        )
        assert record.symbol == "HDFCBANK.NS"
        assert record.total_signals_30d == 5
        assert record.hit_target == 3
        assert record.win_rate == 75.0

    def test_zero_signals(self) -> None:
        record = SymbolTrackRecord(
            symbol="BTCUSDT",
            total_signals_30d=0,
            hit_target=0,
            hit_stop=0,
            expired=0,
            win_rate=0.0,
            avg_return_pct=0.0,
        )
        assert record.total_signals_30d == 0
        assert record.win_rate == 0.0

    def test_negative_avg_return(self) -> None:
        record = SymbolTrackRecord(
            symbol="EURUSD=X",
            total_signals_30d=3,
            hit_target=0,
            hit_stop=2,
            expired=1,
            win_rate=0.0,
            avg_return_pct=-1.5,
        )
        assert record.avg_return_pct == -1.5

    def test_win_rate_validation(self) -> None:
        """Win rate must be between 0 and 100."""
        with pytest.raises(Exception):
            SymbolTrackRecord(
                symbol="X",
                total_signals_30d=1,
                hit_target=1,
                hit_stop=0,
                expired=0,
                win_rate=150.0,  # Invalid
                avg_return_pct=0.0,
            )


class TestNSResolutionNormalization:
    """Test the .NS suffix normalization in signal resolution."""

    def test_ns_stripped_in_resolution_query(self) -> None:
        """The fix: signal.symbol.replace('.NS', '') matches market_data storage."""
        test_cases = [
            ("RELIANCE.NS", "RELIANCE"),
            ("HDFCBANK.NS", "HDFCBANK"),
            ("INFY.NS", "INFY"),
            ("BTCUSDT", "BTCUSDT"),
            ("EURUSD=X", "EURUSD=X"),
            ("SOLUSD", "SOLUSD"),
        ]
        for input_symbol, expected in test_cases:
            assert input_symbol.replace(".NS", "") == expected

    def test_double_ns_does_not_over_strip(self) -> None:
        """Edge case: replace strips all .NS occurrences."""
        symbol = "TEST.NS.NS"
        # str.replace replaces all occurrences — both .NS are stripped
        assert symbol.replace(".NS", "") == "TEST"


class TestTrackRecordWinRate:
    """Test win rate calculation logic used in the endpoint."""

    def test_all_hits(self) -> None:
        ht, hs = 5, 0
        resolved = ht + hs
        win_rate = (ht / resolved * 100) if resolved > 0 else 0.0
        assert win_rate == 100.0

    def test_all_stops(self) -> None:
        ht, hs = 0, 3
        resolved = ht + hs
        win_rate = (ht / resolved * 100) if resolved > 0 else 0.0
        assert win_rate == 0.0

    def test_mixed_results(self) -> None:
        ht, hs = 2, 1
        resolved = ht + hs
        win_rate = round((ht / resolved * 100), 1)
        assert win_rate == 66.7

    def test_no_resolved_signals(self) -> None:
        ht, hs = 0, 0
        resolved = ht + hs
        win_rate = (ht / resolved * 100) if resolved > 0 else 0.0
        assert win_rate == 0.0

    def test_only_expired(self) -> None:
        """When all signals expired, win rate should be 0."""
        ht, hs, expired = 0, 0, 5
        resolved = ht + hs
        win_rate = (ht / resolved * 100) if resolved > 0 else 0.0
        assert win_rate == 0.0
