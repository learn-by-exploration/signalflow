# mkg/tests/test_claude_real_api.py
"""Tests for ClaudeExtractor real API call implementation via httpx.

Iteration 1-2: Real API integration with mocked httpx responses.
All tests mock httpx — no real API calls are made.
"""

import json

import pytest

from mkg.infrastructure.llm.claude_extractor import ClaudeExtractor


class _MockResponse:
    """Simulates an httpx.Response."""

    def __init__(self, status_code: int, json_data: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._json = json_data
        self.text = text or (json.dumps(json_data) if json_data else "")

    def json(self) -> dict:
        if self._json is not None:
            return self._json
        return json.loads(self.text)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def _claude_response(content_text: str, input_tokens: int = 100, output_tokens: int = 50) -> dict:
    """Build a Claude Messages API response dict."""
    return {
        "id": "msg_test_123",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": content_text}],
        "model": "claude-sonnet-4-20250514",
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    }


class TestClaudeRealApiCall:
    """Tests for _real_api_call via httpx."""

    @pytest.fixture
    def extractor(self):
        return ClaudeExtractor(api_key="test-key-abc123")

    @pytest.mark.asyncio
    async def test_real_api_call_makes_post_request(self, extractor):
        """_real_api_call should POST to Anthropic Messages API."""
        captured = {}

        async def mock_post(url, **kwargs):
            captured["url"] = url
            captured["headers"] = kwargs.get("headers", {})
            captured["json"] = kwargs.get("json", {})
            return _MockResponse(
                200,
                _claude_response('{"entities": []}'),
            )

        extractor._http_post = mock_post
        result = await extractor._real_api_call("Extract entities from: test")
        assert captured["url"] == "https://api.anthropic.com/v1/messages"
        assert captured["headers"]["x-api-key"] == "test-key-abc123"
        assert captured["headers"]["anthropic-version"] == "2023-06-01"
        assert captured["json"]["model"] == "claude-sonnet-4-20250514"

    @pytest.mark.asyncio
    async def test_real_api_call_sends_prompt_as_user_message(self, extractor):
        """Prompt should be sent as user message content."""
        captured = {}

        async def mock_post(url, **kwargs):
            captured["json"] = kwargs.get("json", {})
            return _MockResponse(200, _claude_response('{"entities": []}'))

        extractor._http_post = mock_post
        await extractor._real_api_call("Extract entities from: TSMC fab fire")
        messages = captured["json"]["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert "TSMC fab fire" in messages[0]["content"]

    @pytest.mark.asyncio
    async def test_real_api_call_returns_text_content(self, extractor):
        """Should return the text content from Claude's response."""
        response_text = '{"entities": [{"name": "TSMC", "entity_type": "Company"}]}'

        async def mock_post(url, **kwargs):
            return _MockResponse(200, _claude_response(response_text))

        extractor._http_post = mock_post
        result = await extractor._real_api_call("Extract entities")
        assert result == response_text

    @pytest.mark.asyncio
    async def test_real_api_call_tracks_token_usage(self, extractor):
        """Should track input/output tokens after each call."""
        async def mock_post(url, **kwargs):
            return _MockResponse(
                200,
                _claude_response('{"entities": []}', input_tokens=150, output_tokens=75),
            )

        extractor._http_post = mock_post
        await extractor._real_api_call("Extract entities")
        assert extractor.last_usage["input_tokens"] == 150
        assert extractor.last_usage["output_tokens"] == 75

    @pytest.mark.asyncio
    async def test_real_api_call_handles_http_error(self, extractor):
        """Should raise on HTTP errors (4xx/5xx)."""
        async def mock_post(url, **kwargs):
            return _MockResponse(429, text='{"error": {"type": "rate_limit", "message": "Too many"}}')

        extractor._http_post = mock_post
        with pytest.raises(Exception, match="rate_limit|429"):
            await extractor._real_api_call("Extract entities")

    @pytest.mark.asyncio
    async def test_real_api_call_handles_overloaded(self, extractor):
        """Should raise on 529 (overloaded)."""
        async def mock_post(url, **kwargs):
            return _MockResponse(529, text='{"error": {"type": "overloaded", "message": "Overloaded"}}')

        extractor._http_post = mock_post
        with pytest.raises(Exception, match="overloaded|529"):
            await extractor._real_api_call("Extract entities")

    @pytest.mark.asyncio
    async def test_real_api_call_sets_max_tokens(self, extractor):
        """Should set max_tokens in request."""
        captured = {}

        async def mock_post(url, **kwargs):
            captured["json"] = kwargs.get("json", {})
            return _MockResponse(200, _claude_response('{}'))

        extractor._http_post = mock_post
        await extractor._real_api_call("Extract entities")
        assert captured["json"]["max_tokens"] > 0

    @pytest.mark.asyncio
    async def test_real_api_call_sets_timeout(self, extractor):
        """Should set a reasonable timeout."""
        captured = {}

        async def mock_post(url, **kwargs):
            captured["timeout"] = kwargs.get("timeout")
            return _MockResponse(200, _claude_response('{}'))

        extractor._http_post = mock_post
        await extractor._real_api_call("Extract entities")
        assert captured.get("timeout") is not None
        assert captured["timeout"] >= 30  # At least 30 seconds


class TestClaudeEndToEndWithMock:
    """End-to-end tests: extract_entities/relations/all via mocked API."""

    @pytest.fixture
    def extractor(self):
        ext = ClaudeExtractor(api_key="test-key")

        async def mock_post(url, **kwargs):
            body = kwargs.get("json", {})
            prompt = body.get("messages", [{}])[0].get("content", "")

            if "entities and relationships" in prompt.lower() or "ner+re" in prompt.lower():
                text = json.dumps({
                    "entities": [
                        {"name": "TSMC", "entity_type": "Company", "confidence": 0.95},
                        {"name": "NVIDIA", "entity_type": "Company", "confidence": 0.92},
                    ],
                    "relations": [
                        {"source": "TSMC", "target": "NVIDIA", "relation_type": "SUPPLIES_TO",
                         "weight": 0.85, "confidence": 0.9},
                    ],
                })
            elif "relationship" in prompt.lower() or "relation" in prompt.lower():
                text = json.dumps({
                    "relations": [
                        {"source": "TSMC", "target": "NVIDIA", "relation_type": "SUPPLIES_TO",
                         "weight": 0.85, "confidence": 0.9},
                    ]
                })
            else:
                text = json.dumps({
                    "entities": [
                        {"name": "TSMC", "entity_type": "Company", "confidence": 0.95},
                        {"name": "NVIDIA", "entity_type": "Company", "confidence": 0.92},
                    ]
                })
            return _MockResponse(200, _claude_response(text))

        ext._http_post = mock_post
        return ext

    @pytest.mark.asyncio
    async def test_extract_entities_e2e(self, extractor):
        entities = await extractor.extract_entities("TSMC supplies chips to NVIDIA")
        assert len(entities) >= 1
        names = {e["name"] for e in entities}
        assert "TSMC" in names

    @pytest.mark.asyncio
    async def test_extract_relations_e2e(self, extractor):
        entities = [{"name": "TSMC"}, {"name": "NVIDIA"}]
        relations = await extractor.extract_relations("TSMC supplies chips to NVIDIA", entities)
        assert len(relations) >= 1
        assert relations[0]["relation_type"] == "SUPPLIES_TO"

    @pytest.mark.asyncio
    async def test_extract_all_e2e(self, extractor):
        result = await extractor.extract_all("TSMC supplies chips to NVIDIA for AI GPUs")
        assert "entities" in result
        assert "relations" in result
        assert len(result["entities"]) >= 1
        assert len(result["relations"]) >= 1

    @pytest.mark.asyncio
    async def test_cost_estimate_scales_with_length(self, extractor):
        short = extractor.get_cost_estimate(100)
        long = extractor.get_cost_estimate(10000)
        assert long > short

    @pytest.mark.asyncio
    async def test_extract_entities_bad_json_returns_empty(self, extractor):
        """Should handle malformed JSON gracefully."""
        async def bad_response(url, **kwargs):
            return _MockResponse(200, _claude_response("not json at all"))

        extractor._http_post = bad_response
        result = await extractor.extract_entities("test text")
        assert result == []


class TestClaudeRetryLogic:
    """Tests for retry with exponential backoff."""

    @pytest.fixture
    def extractor(self):
        return ClaudeExtractor(api_key="test-key")

    @pytest.mark.asyncio
    async def test_retries_on_rate_limit(self, extractor):
        """Should retry on 429 and succeed on subsequent attempt."""
        call_count = 0

        async def mock_post(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                return _MockResponse(429, text='{"error": {"type": "rate_limit"}}')
            return _MockResponse(200, _claude_response('{"entities": []}'))

        extractor._http_post = mock_post
        result = await extractor._real_api_call("test", max_retries=2)
        assert call_count == 2
        assert result == '{"entities": []}'

    @pytest.mark.asyncio
    async def test_retries_on_server_error(self, extractor):
        """Should retry on 500."""
        call_count = 0

        async def mock_post(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                return _MockResponse(500, text='{"error": {"type": "internal"}}')
            return _MockResponse(200, _claude_response('{"entities": []}'))

        extractor._http_post = mock_post
        result = await extractor._real_api_call("test", max_retries=2)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_does_not_retry_on_400(self, extractor):
        """Should NOT retry on 400 (client error)."""
        call_count = 0

        async def mock_post(url, **kwargs):
            nonlocal call_count
            call_count += 1
            return _MockResponse(400, text='{"error": {"type": "invalid_request"}}')

        extractor._http_post = mock_post
        with pytest.raises(Exception):
            await extractor._real_api_call("test", max_retries=3)
        assert call_count == 1  # No retries

    @pytest.mark.asyncio
    async def test_exhausts_retries_and_raises(self, extractor):
        """Should raise after max_retries exhausted."""
        async def mock_post(url, **kwargs):
            return _MockResponse(429, text='{"error": {"type": "rate_limit"}}')

        extractor._http_post = mock_post
        with pytest.raises(Exception, match="rate_limit|429|exhausted"):
            await extractor._real_api_call("test", max_retries=2)
