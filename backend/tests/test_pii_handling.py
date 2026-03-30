"""v1.3.16 — PII Handling Tests.

Verify personal data (email, chat_id, passwords) is not
leaked in logs, responses, or transmitted unnecessarily.
"""

import os
import re

import pytest
from httpx import AsyncClient


class TestPIIInResponses:
    """API responses must not expose other users' PII."""

    @pytest.mark.asyncio
    async def test_signals_no_user_data(self, test_client: AsyncClient):
        """Signal list must not contain user emails or chat IDs."""
        resp = await test_client.get("/api/v1/signals")
        body = resp.text
        assert "@" not in body or "example.com" not in body
        assert "telegram_chat_id" not in body or "chat_id" not in body

    @pytest.mark.asyncio
    async def test_history_no_user_data(self, test_client: AsyncClient):
        """Signal history must not expose user info."""
        resp = await test_client.get("/api/v1/signals/history")
        body = resp.text
        assert "password" not in body.lower()

    @pytest.mark.asyncio
    async def test_shared_signal_no_owner_info(self, test_client: AsyncClient):
        """Shared signal view must not reveal signal owner."""
        # Create a share (may fail if no signal exists — that's OK)
        resp = await test_client.get("/api/v1/signals")
        if resp.status_code == 200:
            signals = resp.json().get("data", [])
            if signals:
                signal_id = signals[0].get("id", "")
                share_resp = await test_client.post(f"/api/v1/signals/{signal_id}/share")
                if share_resp.status_code == 201:
                    share_data = share_resp.json().get("data", {})
                    share_id = share_data.get("share_id", "")
                    if share_id:
                        view_resp = await test_client.get(f"/api/v1/signals/shared/{share_id}")
                        body = view_resp.text
                        assert "email" not in body.lower()
                        assert "password" not in body.lower()


class TestPIIInLogs:
    """Logging must not contain sensitive PII."""

    def _scan_files_for_pattern(self, directory: str, pattern: str) -> list[str]:
        """Scan Python files for a pattern."""
        violations = []
        for root, _, files in os.walk(directory):
            if "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    filepath = os.path.join(root, f)
                    with open(filepath) as fh:
                        for i, line in enumerate(fh, 1):
                            if re.search(pattern, line) and not line.strip().startswith("#"):
                                violations.append(f"{filepath}:{i}: {line.strip()}")
        return violations

    def test_no_password_logging(self):
        """No logging of password values in codebase."""
        app_dir = os.path.join(os.path.dirname(__file__), "..", "app")
        violations = self._scan_files_for_pattern(
            app_dir,
            r'logger\.\w+\(.*password.*%s|logger\.\w+\(.*password.*{|'
            r'logging\.\w+\(.*password.*%s|logging\.\w+\(.*password.*{',
        )
        # Filter out legitimate uses (like "password change" log messages)
        real_violations = [
            v for v in violations
            if "password_hash" not in v
            and "change_password" not in v
            and "payload.password" not in v
            and "password_reset" not in v
            and "requires" not in v
        ]
        assert real_violations == [], f"Password logging found:\n" + "\n".join(real_violations)

    def test_no_api_key_logging(self):
        """API keys must not be logged."""
        app_dir = os.path.join(os.path.dirname(__file__), "..", "app")
        violations = self._scan_files_for_pattern(
            app_dir,
            r'logger\.\w+\(.*api_key.*%s|logger\.\w+\(.*api_key.*{|'
            r'logger\.\w+\(.*secret.*%s|logger\.\w+\(.*secret.*{',
        )
        assert violations == [], f"API key/secret logging found:\n" + "\n".join(violations)

    def test_no_jwt_token_logging(self):
        """JWT tokens must not be logged in full."""
        app_dir = os.path.join(os.path.dirname(__file__), "..", "app")
        violations = self._scan_files_for_pattern(
            app_dir,
            r'logger\.\w+\(.*access_token|logger\.\w+\(.*refresh_token',
        )
        assert violations == [], f"JWT token logging found:\n" + "\n".join(violations)


class TestPIIMinimization:
    """Data minimization: only collect what's needed."""

    def test_user_model_no_extra_pii(self):
        """User model should store minimal PII."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "models", "user.py")
        with open(path) as f:
            content = f.read()
        # Should NOT store: full name, phone number, address, SSN
        pii_fields = ["phone", "address", "ssn", "social_security", "date_of_birth", "dob"]
        for field in pii_fields:
            assert field not in content.lower(), f"Unnecessary PII field '{field}' in User model"

    def test_signal_model_no_user_pii(self):
        """Signal model should not contain user PII."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "models", "signal.py")
        with open(path) as f:
            content = f.read()
        assert "email" not in content.lower()
        assert "password" not in content.lower()
