"""v1.3.47 — News & Calendar Injection Tests.

Verify news endpoints and calendar events handle injection
attempts safely. Input is sanitized before storage/display.
"""

import pytest


class TestNewsEndpointSafety:
    """News endpoints handle malicious input safely."""

    @pytest.mark.asyncio
    async def test_news_list_returns_json(self, test_client):
        """GET /news returns valid JSON."""
        r = await test_client.get("/api/v1/news")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_news_sql_injection_in_query(self, test_client):
        """SQL injection in news query parameter is safe."""
        r = await test_client.get("/api/v1/news?symbol=' OR 1=1--")
        assert r.status_code in (200, 400, 422)
        if r.status_code == 200:
            data = r.json()
            assert "data" in data

    @pytest.mark.asyncio
    async def test_news_xss_in_query(self, test_client):
        """XSS in news query parameter is handled."""
        r = await test_client.get("/api/v1/news?symbol=<script>alert(1)</script>")
        assert r.status_code in (200, 400, 422)
        if r.status_code == 200:
            body = r.text
            assert "<script>" not in body


class TestCalendarEndpointSafety:
    """Calendar endpoints reject malicious input."""

    @pytest.mark.asyncio
    async def test_calendar_get_returns_json(self, test_client):
        """GET /news/calendar returns valid JSON."""
        r = await test_client.get("/api/v1/news/calendar")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_calendar_create_requires_fields(self, test_client):
        """POST /news/calendar requires proper fields."""
        r = await test_client.post("/api/v1/news/calendar", json={})
        assert r.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_calendar_xss_in_title(self, test_client):
        """XSS in calendar event title is sanitized."""
        r = await test_client.post(
            "/api/v1/news/calendar",
            json={
                "title": "<img src=x onerror=alert(1)>",
                "event_type": "earnings",
                "symbol": "TEST.NS",
                "event_date": "2026-04-01T10:00:00Z",
            },
        )
        if r.status_code in (200, 201):
            body = r.text
            assert "onerror" not in body


class TestChainsEndpointSafety:
    """Causal chain endpoints handle injection safely."""

    @pytest.mark.asyncio
    async def test_chains_sql_injection(self, test_client):
        """SQL injection in chains symbol is handled."""
        r = await test_client.get("/api/v1/news/chains/'; DROP TABLE signals;--")
        assert r.status_code in (200, 400, 404, 422)
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_chains_path_traversal(self, test_client):
        """Path traversal in chains endpoint is safe."""
        r = await test_client.get("/api/v1/news/chains/../../etc/passwd")
        assert r.status_code in (200, 400, 404, 422)

    @pytest.mark.asyncio
    async def test_events_detail_invalid_id(self, test_client):
        """Invalid event ID is handled gracefully."""
        r = await test_client.get("/api/v1/news/events/not-a-uuid")
        assert r.status_code in (400, 404, 422)

    @pytest.mark.asyncio
    async def test_signal_news_invalid_id(self, test_client):
        """Invalid signal ID in news endpoint is handled."""
        r = await test_client.get("/api/v1/news/signal/not-a-uuid")
        assert r.status_code in (400, 404, 422)
