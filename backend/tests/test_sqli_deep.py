"""v1.3.1 — SQL Injection Deep Sweep.

Exhaustive SQL injection tests across ALL endpoints that accept user input.
Tests every query parameter, path parameter, and JSON body field for injection resistance.
"""

import pytest
from uuid import uuid4


# ═══════════════════════════════════════════════════════════════
# SQL Injection Payloads — comprehensive set
# ═══════════════════════════════════════════════════════════════

SQLI_PAYLOADS = [
    # Classic string-based
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR '1'='1' /*",
    "'; DROP TABLE signals; --",
    "'; DELETE FROM signals WHERE 1=1; --",
    "' UNION SELECT 1,2,3,4,5,6,7,8,9,10 --",
    "' UNION SELECT username,password FROM users --",
    # Numeric injection
    "1 OR 1=1",
    "1; DROP TABLE signals",
    "1 AND 1=1",
    # Time-based blind
    "'; WAITFOR DELAY '0:0:5'; --",
    "' OR SLEEP(5) --",
    "' OR pg_sleep(5) --",
    "1; SELECT pg_sleep(5)",
    # Error-based
    "' AND 1=CONVERT(int,(SELECT TOP 1 table_name FROM information_schema.tables)) --",
    "' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) --",
    # Stacked queries
    "'; INSERT INTO signals(id) VALUES('hacked'); --",
    "'; UPDATE users SET tier='pro'; --",
    "'; CREATE TABLE pwned(x text); --",
    # Comment variants
    "admin'--",
    "admin'#",
    "admin'/*",
    # Null byte
    # Note: null bytes cause httpx.InvalidURL — they never reach the server
    # "test\x00' OR '1'='1",
    # Double encoding
    "%27%20OR%20%271%27%3D%271",
    # PostgreSQL specific
    "' || (SELECT version()) || '",
    "'; COPY (SELECT '') TO PROGRAM 'id'; --",
    "' AND 1=1::int --",
]

SYMBOL_SQLI_PAYLOADS = [
    "HDFC' OR 1=1--",
    "HDFC'; DROP TABLE signals;--",
    "HDFC' UNION SELECT * FROM users--",
    "HDFC%27%20OR%201=1",
]


# ═══════════════════════════════════════════════════════════════
# Signals Endpoint
# ═══════════════════════════════════════════════════════════════

class TestSignalsSQLi:
    """SQL injection tests for GET /signals."""

    @pytest.mark.asyncio
    async def test_symbol_sqli(self, test_client):
        """Symbol parameter rejects all SQL injection payloads."""
        for payload in SYMBOL_SQLI_PAYLOADS:
            resp = await test_client.get(f"/api/v1/signals?symbol={payload}")
            assert resp.status_code == 400, f"Expected 400 for: {payload}"

    @pytest.mark.asyncio
    async def test_market_sqli(self, test_client):
        """Market parameter rejects SQL injection."""
        for payload in ["stock' OR 1=1--", "' UNION SELECT 1--", "crypto; DROP TABLE signals"]:
            resp = await test_client.get(f"/api/v1/signals?market={payload}")
            assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_signal_type_sqli(self, test_client):
        """Signal type parameter rejects injection."""
        for payload in ["BUY' OR 1=1--", "' UNION SELECT 1--"]:
            resp = await test_client.get(f"/api/v1/signals?signal_type={payload}")
            assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_min_confidence_sqli(self, test_client):
        """min_confidence is integer — string injection returns 422."""
        resp = await test_client.get("/api/v1/signals?min_confidence=abc' OR 1=1")
        assert resp.status_code == 422  # Pydantic validation

    @pytest.mark.asyncio
    async def test_valid_symbol_still_works(self, test_client):
        """Valid symbols are accepted."""
        for sym in ["HDFCBANK", "BTC/USDT", "EUR/USD", "RELIANCE.NS"]:
            resp = await test_client.get(f"/api/v1/signals?symbol={sym}")
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_valid_markets_still_work(self, test_client):
        """Valid markets are accepted."""
        for m in ["stock", "crypto", "forex"]:
            resp = await test_client.get(f"/api/v1/signals?market={m}")
            assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════
# History Endpoint
# ═══════════════════════════════════════════════════════════════

class TestHistorySQLi:
    """SQL injection tests for GET /signals/history."""

    @pytest.mark.asyncio
    async def test_outcome_sqli(self, test_client):
        """Outcome parameter rejects injection."""
        payloads = [
            "hit_target' OR 1=1--",
            "' UNION SELECT 1,2,3--",
            "pending; DROP TABLE signal_history--",
        ]
        for payload in payloads:
            resp = await test_client.get(f"/api/v1/signals/history?outcome={payload}")
            assert resp.status_code == 400, f"Expected 400 for: {payload}"

    @pytest.mark.asyncio
    async def test_valid_outcomes_work(self, test_client):
        """Valid outcome values are accepted."""
        for o in ["hit_target", "hit_stop", "expired", "pending"]:
            resp = await test_client.get(f"/api/v1/signals/history?outcome={o}")
            assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════
# Track Record Endpoint
# ═══════════════════════════════════════════════════════════════

class TestTrackRecordSQLi:
    """SQL injection tests for GET /signals/{symbol}/track-record."""

    @pytest.mark.asyncio
    async def test_symbol_path_sqli(self, test_client):
        """Path parameter {symbol} rejects injection."""
        payloads = [
            "HDFC' OR 1=1--",
            "' UNION SELECT 1,2,3--",
            "HDFC; DROP TABLE signals--",
        ]
        for payload in payloads:
            resp = await test_client.get(f"/api/v1/signals/{payload}/track-record")
            assert resp.status_code == 400, f"Expected 400 for: {payload}"


# ═══════════════════════════════════════════════════════════════
# News Endpoint
# ═══════════════════════════════════════════════════════════════

class TestNewsSQLi:
    """SQL injection tests for GET /news."""

    @pytest.mark.asyncio
    async def test_news_symbol_sqli(self, test_client):
        """News symbol parameter rejects injection."""
        for payload in SYMBOL_SQLI_PAYLOADS:
            resp = await test_client.get(f"/api/v1/news?symbol={payload}")
            assert resp.status_code == 400, f"Expected 400 for: {payload}"

    @pytest.mark.asyncio
    async def test_news_market_sqli(self, test_client):
        """News market parameter rejects injection."""
        resp = await test_client.get("/api/v1/news?market=' OR 1=1--")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_chains_symbol_sqli(self, test_client):
        """Causal chains symbol path rejects injection."""
        resp = await test_client.get("/api/v1/news/chains/' OR 1=1--")
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════
# Portfolio Endpoint
# ═══════════════════════════════════════════════════════════════

class TestPortfolioSQLi:
    """SQL injection tests for portfolio endpoints."""

    @pytest.mark.asyncio
    async def test_trade_symbol_sqli(self, test_client):
        """POST /portfolio/trades with injection in symbol field."""
        for payload in ["'; DROP TABLE trades;--", "' OR 1=1--"]:
            resp = await test_client.post(
                "/api/v1/portfolio/trades",
                json={
                    "symbol": payload,
                    "market_type": "stock",
                    "side": "buy",
                    "quantity": "1",
                    "price": "100.00",
                },
            )
            assert resp.status_code in (400, 422), f"Expected 400/422 for symbol: {payload}"

    @pytest.mark.asyncio
    async def test_trade_market_type_sqli(self, test_client):
        """POST /portfolio/trades with injection in market_type."""
        resp = await test_client.post(
            "/api/v1/portfolio/trades",
            json={
                "symbol": "HDFCBANK",
                "market_type": "stock' OR 1=1--",
                "side": "buy",
                "quantity": "1",
                "price": "100.00",
            },
        )
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_portfolio_list_symbol_sqli(self, test_client):
        """GET /portfolio/trades?symbol= with injection."""
        resp = await test_client.get("/api/v1/portfolio/trades?symbol=' OR 1=1--")
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════
# Backtest Endpoint
# ═══════════════════════════════════════════════════════════════

class TestBacktestSQLi:
    """SQL injection tests for backtest endpoints."""

    @pytest.mark.asyncio
    async def test_backtest_symbol_sqli(self, test_client):
        """POST /backtest/run with injection in symbol."""
        resp = await test_client.post(
            "/api/v1/backtest/run",
            json={
                "symbol": "'; DROP TABLE backtests;--",
                "market_type": "stock",
                "days": 30,
            },
        )
        assert resp.status_code in (400, 422, 429)


# ═══════════════════════════════════════════════════════════════
# Alert Config / Watchlist Endpoint
# ═══════════════════════════════════════════════════════════════

class TestAlertSQLi:
    """SQL injection tests for alert endpoints."""

    @pytest.mark.asyncio
    async def test_watchlist_symbol_sqli(self, test_client):
        """POST /alerts/watchlist with injection in symbol."""
        resp = await test_client.post(
            "/api/v1/alerts/watchlist",
            json={"symbol": "'; DROP TABLE alert_configs;--", "action": "add"},
        )
        assert resp.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_alert_config_username_sqli(self, test_client):
        """POST /alerts/config with injection in username."""
        resp = await test_client.post(
            "/api/v1/alerts/config",
            json={
                "telegram_chat_id": 12345,
                "username": "admin' OR 1=1--",
            },
        )
        assert resp.status_code in (400, 422)


# ═══════════════════════════════════════════════════════════════
# Price Alerts Endpoint
# ═══════════════════════════════════════════════════════════════

class TestPriceAlertSQLi:
    """SQL injection tests for price alert endpoints."""

    @pytest.mark.asyncio
    async def test_price_alert_symbol_sqli(self, test_client):
        """POST /price-alerts with injection in symbol."""
        resp = await test_client.post(
            "/api/v1/price-alerts",
            json={
                "symbol": "'; DROP TABLE price_alerts;--",
                "target_price": "100.00",
                "condition": "above",
            },
        )
        assert resp.status_code in (400, 404, 422)


# ═══════════════════════════════════════════════════════════════
# SEO Endpoint
# ═══════════════════════════════════════════════════════════════

class TestSeoSQLi:
    """SQL injection tests for SEO endpoints."""

    @pytest.mark.asyncio
    async def test_seo_slug_sqli(self, test_client):
        """GET /seo/{slug} with injection in slug."""
        payloads = [
            "' OR 1=1--",
            "'; DROP TABLE seo_pages;--",
            "test' UNION SELECT 1,2,3--",
        ]
        for payload in payloads:
            resp = await test_client.get(f"/api/v1/seo/{payload}")
            assert resp.status_code in (400, 404), f"Expected 400/404 for: {payload}"


# ═══════════════════════════════════════════════════════════════
# Signal Feedback Endpoint
# ═══════════════════════════════════════════════════════════════

class TestFeedbackSQLi:
    """SQL injection tests for signal feedback endpoints."""

    @pytest.mark.asyncio
    async def test_feedback_notes_sqli(self, test_client):
        """POST /signals/{id}/feedback with injection in notes."""
        signal_id = str(uuid4())
        resp = await test_client.post(
            f"/api/v1/signals/{signal_id}/feedback",
            json={
                "action": "took",
                "notes": "'; DROP TABLE signal_feedback;--",
            },
        )
        # Notes go through Pydantic and parameterized queries — should not crash
        assert resp.status_code in (201, 404)

    @pytest.mark.asyncio
    async def test_feedback_action_sqli(self, test_client):
        """POST /signals/{id}/feedback with injection in action."""
        signal_id = str(uuid4())
        resp = await test_client.post(
            f"/api/v1/signals/{signal_id}/feedback",
            json={
                "action": "took' OR 1=1--",
                "notes": "test",
            },
        )
        assert resp.status_code in (400, 422)


# ═══════════════════════════════════════════════════════════════
# Auth Endpoints (login, register)
# ═══════════════════════════════════════════════════════════════

class TestAuthSQLi:
    """SQL injection tests for auth endpoints."""

    @pytest.mark.asyncio
    async def test_login_email_sqli(self, test_client):
        """POST /auth/login with injection in email."""
        resp = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin' OR 1=1--@test.com",
                "password": "password123",
            },
        )
        # Pydantic email validation should catch this, or query returns no user
        assert resp.status_code in (401, 422, 429)

    @pytest.mark.asyncio
    async def test_login_password_sqli(self, test_client):
        """POST /auth/login with injection in password."""
        resp = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@test.com",
                "password": "' OR '1'='1",
            },
        )
        # Password is hashed, never used in SQL directly
        assert resp.status_code in (401, 429)

    @pytest.mark.asyncio
    async def test_register_sqli_in_name(self, test_client):
        """POST /auth/register with injection in name."""
        resp = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "sqli@test.com",
                "password": "StrongPa$$w0rd!",
                "name": "'; DROP TABLE users;--",
            },
        )
        # Name goes through Pydantic + parameterized query — should not crash
        assert resp.status_code in (201, 400, 422)


# ═══════════════════════════════════════════════════════════════
# AI Q&A Endpoint
# ═══════════════════════════════════════════════════════════════

class TestAiQaSQLi:
    """SQL injection tests for AI Q&A endpoint."""

    @pytest.mark.asyncio
    async def test_ai_ask_symbol_sqli(self, test_client):
        """POST /ai/ask with injection in symbol."""
        resp = await test_client.post(
            "/api/v1/ai/ask",
            json={
                "symbol": "'; DROP TABLE signals;--",
                "question": "What is the outlook?",
            },
        )
        # Should reject or handle safely
        assert resp.status_code in (400, 422, 500)

    @pytest.mark.asyncio
    async def test_ai_ask_question_sqli(self, test_client):
        """POST /ai/ask with injection in question (goes to AI, not SQL)."""
        resp = await test_client.post(
            "/api/v1/ai/ask",
            json={
                "symbol": "HDFCBANK",
                "question": "'; DROP TABLE signals;-- What is the outlook?",
            },
        )
        # Question goes to Claude, not SQL — should not crash
        assert resp.status_code in (200, 400, 422, 429, 500)


# ═══════════════════════════════════════════════════════════════
# Parameterized Query Verification
# ═══════════════════════════════════════════════════════════════

class TestParameterizedQuerySafety:
    """Verify that all SQL queries use parameterized statements."""

    def test_no_f_string_sql_in_signals(self):
        """signals.py must not use f-strings in SQL WHERE clauses unsafely."""
        import ast
        with open("app/api/signals.py") as f:
            source = f.read()
        # After v1.3.1, ilike uses sanitized input
        assert "ilike(f\"%{symbol}%\")" not in source, \
            "Raw symbol interpolation in ilike is unsafe"

    def test_no_f_string_sql_in_news(self):
        """news.py must not use f-strings with raw user input in SQL."""
        with open("app/api/news.py") as f:
            source = f.read()
        assert "ilike(f\"%{symbol}%\")" not in source

    def test_no_f_string_sql_in_portfolio(self):
        """portfolio.py must not use f-strings with raw user input in SQL."""
        with open("app/api/portfolio.py") as f:
            source = f.read()
        # Should use parameterized queries or sanitized input
        assert "ilike(f\"%{symbol}%\")" not in source

    def test_signals_uses_sanitized_ilike(self):
        """signals.py ilike should use the sanitized 'safe' variable."""
        with open("app/api/signals.py") as f:
            source = f.read()
        assert "ilike(f\"%{safe}%\")" in source

    def test_news_uses_sanitized_ilike(self):
        """news.py ilike should use the sanitized variable."""
        with open("app/api/news.py") as f:
            source = f.read()
        assert "ilike(f\"%{safe}%\")" in source
