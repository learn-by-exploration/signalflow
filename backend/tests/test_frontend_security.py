"""v1.3.19 — Cookie & Frontend State Security Tests.

Verify token storage approach and frontend security patterns.
"""

import os
import re

import pytest


class TestTokenStorageStrategy:
    """Verify token storage uses sessionStorage (not localStorage for JWTs)."""

    def test_user_store_uses_session_storage(self):
        """User store should use sessionStorage, not localStorage for tokens."""
        store_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "frontend", "src", "store", "userStore.ts"
        )
        if os.path.exists(store_path):
            with open(store_path) as f:
                content = f.read()
            # Tokens should be in sessionStorage (session-scoped) not localStorage
            if "localStorage" in content:
                # Check if it's for tokens specifically
                token_in_local = bool(re.search(r'localStorage.*token', content, re.IGNORECASE))
                assert not token_in_local, (
                    "JWT tokens should use sessionStorage, not localStorage"
                )
        else:
            pytest.skip("Frontend store not found")

    def test_no_tokens_in_url(self):
        """Frontend should not pass tokens in URL parameters (except WebSocket which requires it)."""
        frontend_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "frontend", "src"
        )
        if not os.path.exists(frontend_dir):
            pytest.skip("Frontend not found")

        violations = []
        for root, _, files in os.walk(frontend_dir):
            if "node_modules" in root or "__tests__" in root:
                continue
            for f in files:
                if f.endswith((".ts", ".tsx")):
                    filepath = os.path.join(root, f)
                    with open(filepath) as fh:
                        for i, line in enumerate(fh, 1):
                            if re.search(r'token=.*\$\{|token=.*\+', line):
                                # WebSocket auth via query param is standard (no header support)
                                if "websocket" not in filepath.lower():
                                    violations.append(f"{filepath}:{i}")
        assert violations == [], f"Token in URL risk:\n" + "\n".join(violations)


class TestFrontendXSSProtection:
    """Frontend should use React's built-in XSS protection."""

    def test_no_dangerouslysetinnerhtml(self):
        """No dangerouslySetInnerHTML in components."""
        frontend_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "frontend", "src", "components"
        )
        if not os.path.exists(frontend_dir):
            pytest.skip("Frontend components not found")

        violations = []
        for root, _, files in os.walk(frontend_dir):
            for f in files:
                if f.endswith((".tsx", ".jsx")):
                    filepath = os.path.join(root, f)
                    with open(filepath) as fh:
                        for i, line in enumerate(fh, 1):
                            if "dangerouslySetInnerHTML" in line:
                                violations.append(f"{filepath}:{i}: {line.strip()}")
        assert violations == [], (
            f"dangerouslySetInnerHTML found (XSS risk):\n" + "\n".join(violations)
        )

    def test_no_eval_in_frontend(self):
        """No eval() usage in frontend code."""
        frontend_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "frontend", "src"
        )
        if not os.path.exists(frontend_dir):
            pytest.skip("Frontend not found")

        violations = []
        for root, _, files in os.walk(frontend_dir):
            if "node_modules" in root or "__tests__" in root:
                continue
            for f in files:
                if f.endswith((".ts", ".tsx")):
                    filepath = os.path.join(root, f)
                    with open(filepath) as fh:
                        for i, line in enumerate(fh, 1):
                            if re.search(r'\beval\s*\(', line) and not line.strip().startswith("//"):
                                violations.append(f"{filepath}:{i}: {line.strip()}")
        assert violations == [], f"eval() found in frontend (XSS risk):\n" + "\n".join(violations)
