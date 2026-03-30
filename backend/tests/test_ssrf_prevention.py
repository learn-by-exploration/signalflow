"""v1.3.5 — SSRF Prevention Tests.

Verify that no user-controlled input can cause the server
to make requests to arbitrary URLs (Server-Side Request Forgery).
"""

import ast
import os
import re

import pytest


class TestNoUserControlledURLs:
    """Verify all HTTP requests go to hardcoded, trusted URLs only."""

    def _get_python_files(self, base: str) -> list[str]:
        result = []
        for root, _, files in os.walk(base):
            for f in files:
                if f.endswith(".py") and "__pycache__" not in root:
                    result.append(os.path.join(root, f))
        return result

    def test_no_requests_get_with_user_input_in_url(self):
        """Scan codebase: no httpx/requests calls use f-string URLs."""
        app_dir = os.path.join(os.path.dirname(__file__), "..", "app")
        dangerous_patterns = [
            # f-string URL construction
            re.compile(r'client\.(get|post|put|delete|patch)\(\s*f["\']'),
            # .format() URL construction
            re.compile(r'client\.(get|post|put|delete|patch)\(\s*["\'].*\.format\('),
            # string concatenation with variable in URL
            re.compile(r'client\.(get|post|put|delete|patch)\(\s*["\'].*\+\s*\w+'),
        ]
        violations = []
        for filepath in self._get_python_files(app_dir):
            with open(filepath, "r") as fh:
                for i, line in enumerate(fh, 1):
                    for pat in dangerous_patterns:
                        if pat.search(line):
                            violations.append(f"{filepath}:{i}: {line.strip()}")
        assert violations == [], (
            f"Potential SSRF: f-string/format/concat URLs found:\n"
            + "\n".join(violations)
        )

    def test_all_http_urls_are_hardcoded(self):
        """All httpx.AsyncClient/Client calls use hardcoded base URLs."""
        app_dir = os.path.join(os.path.dirname(__file__), "..", "app")
        # Collect all URL strings passed to HTTP clients
        http_call_pattern = re.compile(
            r'client\.(get|post|put|delete|patch)\(\s*"(https?://[^"]+)"'
        )
        urls = set()
        for filepath in self._get_python_files(app_dir):
            with open(filepath, "r") as fh:
                content = fh.read()
                for match in http_call_pattern.finditer(content):
                    urls.add(match.group(2))

        # All URLs should be from trusted domains
        trusted_domains = {
            "news.google.com",
            "www.bing.com",
            "economictimes.indiatimes.com",
            "www.moneycontrol.com",
            "www.livemint.com",
            "cointelegraph.com",
            "www.coindesk.com",
            "www.forexlive.com",
            "www.fxstreet.com",
            "www.rbi.org.in",
            "www.federalreserve.gov",
            "api.binance.com",
            "fapi.binance.com",
            "www.alphavantage.co",
            "api.anthropic.com",
            "api.telegram.org",
            "api.coingecko.com",
            "api.razorpay.com",
        }
        for url in urls:
            from urllib.parse import urlparse
            domain = urlparse(url).hostname
            assert domain in trusted_domains, (
                f"Untrusted domain in HTTP call: {url} (domain: {domain})"
            )

    def test_news_fetcher_uses_params_not_url_interpolation(self):
        """Google/Bing news queries use params= not f-string URLs."""
        fetcher_path = os.path.join(
            os.path.dirname(__file__),
            "..", "app", "services", "ai_engine", "news_fetcher.py",
        )
        with open(fetcher_path, "r") as fh:
            content = fh.read()

        # Should use params= for query parameters
        assert "params=" in content, "news_fetcher should use params= for safe URL encoding"

        # Should NOT construct URLs with f-strings containing user input
        # (Google/Bing URLs should be string literals, not f-strings with query)
        google_call = re.search(r'client\.get\(\s*f["\']https://news\.google\.com', content)
        assert google_call is None, "Google News URL should not use f-string interpolation"

        bing_call = re.search(r'client\.get\(\s*f["\']https://www\.bing\.com', content)
        assert bing_call is None, "Bing News URL should not use f-string interpolation"

    def test_response_size_limits(self):
        """All HTTP responses have size limits to prevent DoS."""
        fetcher_path = os.path.join(
            os.path.dirname(__file__),
            "..", "app", "services", "ai_engine", "news_fetcher.py",
        )
        with open(fetcher_path, "r") as fh:
            content = fh.read()

        assert "MAX_RESPONSE_SIZE" in content, "Response size limit should be defined"
        assert "len(resp.content)" in content, "Response size should be checked"

    def test_http_timeouts_configured(self):
        """All HTTP clients must have timeouts to prevent hanging."""
        app_dir = os.path.join(os.path.dirname(__file__), "..", "app")
        timeout_pattern = re.compile(r"httpx\.AsyncClient\(")
        no_timeout = []
        for filepath in self._get_python_files(app_dir):
            with open(filepath, "r") as fh:
                content = fh.read()
                for match in timeout_pattern.finditer(content):
                    # Check that the AsyncClient call has timeout= parameter
                    # Get the line containing this match
                    start = match.start()
                    end = content.find(")", start)
                    call_text = content[start:end + 1]
                    if "timeout" not in call_text:
                        lineno = content[:start].count("\n") + 1
                        no_timeout.append(f"{filepath}:{lineno}")

        assert no_timeout == [], (
            f"httpx.AsyncClient without timeout=:\n" + "\n".join(no_timeout)
        )

    def test_no_urllib_urlopen(self):
        """urllib.urlopen is banned — use httpx with timeout instead."""
        app_dir = os.path.join(os.path.dirname(__file__), "..", "app")
        violations = []
        for filepath in self._get_python_files(app_dir):
            with open(filepath, "r") as fh:
                for i, line in enumerate(fh, 1):
                    if "urlopen" in line and not line.strip().startswith("#"):
                        violations.append(f"{filepath}:{i}: {line.strip()}")
        assert violations == [], (
            f"urlopen found (SSRF risk — use httpx instead):\n" + "\n".join(violations)
        )

    def test_no_requests_library_in_async_code(self):
        """Sync requests library should not be used in async FastAPI code."""
        app_dir = os.path.join(os.path.dirname(__file__), "..", "app")
        # Exclude tasks/ which may use sync code
        violations = []
        for filepath in self._get_python_files(app_dir):
            if "/tasks/" in filepath:
                continue
            with open(filepath, "r") as fh:
                for i, line in enumerate(fh, 1):
                    if line.strip().startswith("import requests") or line.strip().startswith("from requests"):
                        violations.append(f"{filepath}:{i}: {line.strip()}")
        assert violations == [], (
            f"sync requests library in async code (use httpx):\n" + "\n".join(violations)
        )

    def test_webhook_does_not_make_outbound_requests(self):
        """Razorpay webhook handler must not make outbound HTTP calls."""
        payments_path = os.path.join(
            os.path.dirname(__file__),
            "..", "app", "api", "payments.py",
        )
        with open(payments_path, "r") as fh:
            content = fh.read()

        # Find the webhook function
        webhook_start = content.find("async def razorpay_webhook")
        assert webhook_start != -1, "Webhook handler should exist"

        # Get the webhook function body (until next def or end of file)
        next_def = content.find("\nasync def ", webhook_start + 1)
        next_def2 = content.find("\ndef ", webhook_start + 1)
        end = min(
            next_def if next_def != -1 else len(content),
            next_def2 if next_def2 != -1 else len(content),
        )
        webhook_body = content[webhook_start:end]

        # Webhook should not contain HTTP client calls
        assert "httpx" not in webhook_body, "Webhook should not make outbound HTTP requests"
        assert "client.get" not in webhook_body, "Webhook should not make GET requests"
        assert "client.post" not in webhook_body, "Webhook should not make POST requests"

    def test_ai_api_calls_use_hardcoded_anthropic_url(self):
        """AI engine only calls Anthropic API at the official endpoint."""
        ai_dir = os.path.join(
            os.path.dirname(__file__),
            "..", "app", "services", "ai_engine",
        )
        for filepath in self._get_python_files(ai_dir):
            with open(filepath, "r") as fh:
                content = fh.read()
                if "httpx" not in content and "client" not in content:
                    continue
                # If it makes HTTP calls, verify they go to anthropic
                url_pattern = re.compile(r'["\'](https?://[^"\']+)["\']')
                for match in url_pattern.finditer(content):
                    url = match.group(1)
                    if url.startswith("http://") or url.startswith("https://"):
                        from urllib.parse import urlparse
                        domain = urlparse(url).hostname
                        if domain and domain not in {
                            "api.anthropic.com",
                            "news.google.com",
                            "www.bing.com",
                            # RSS feeds
                            "economictimes.indiatimes.com",
                            "www.moneycontrol.com",
                            "www.livemint.com",
                            "cointelegraph.com",
                            "www.coindesk.com",
                            "www.forexlive.com",
                            "www.fxstreet.com",
                            "www.rbi.org.in",
                            "www.federalreserve.gov",
                        }:
                            pytest.fail(
                                f"Unexpected domain in AI engine: {url} in {filepath}"
                            )
