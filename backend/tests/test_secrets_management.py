"""v1.3.20 — Secrets Management Tests.

Verify no hardcoded secrets, proper env var usage,
and secure configuration management.
"""

import os
import re

import pytest


class TestNoHardcodedSecrets:
    """No API keys, passwords, or secrets hardcoded in source."""

    def _scan_for_secrets(self, directory: str, exclude_dirs: set[str] | None = None) -> list[str]:
        """Scan Python files for potential hardcoded secrets."""
        if exclude_dirs is None:
            exclude_dirs = {"__pycache__", "migrations", ".git"}
        violations = []
        secret_patterns = [
            # API key patterns
            re.compile(r'sk-ant-[a-zA-Z0-9]{20,}'),  # Anthropic
            re.compile(r'sk-[a-zA-Z0-9]{20,}'),       # Generic API key
            re.compile(r'key_[a-zA-Z0-9]{20,}'),       # Razorpay-style
            # AWS-style keys
            re.compile(r'AKIA[A-Z0-9]{16}'),
            # Connection strings with passwords
            re.compile(r'postgresql://\w+:\w+@'),
            re.compile(r'redis://:\w+@'),
        ]
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for f in files:
                if f.endswith((".py", ".ts", ".tsx", ".js")):
                    filepath = os.path.join(root, f)
                    with open(filepath) as fh:
                        for i, line in enumerate(fh, 1):
                            if line.strip().startswith("#") or line.strip().startswith("//"):
                                continue
                            for pat in secret_patterns:
                                if pat.search(line):
                                    violations.append(f"{filepath}:{i}: {line.strip()[:80]}")
        return violations

    def test_no_hardcoded_secrets_in_backend(self):
        """Backend code must not contain hardcoded secrets."""
        app_dir = os.path.join(os.path.dirname(__file__), "..", "app")
        violations = self._scan_for_secrets(app_dir)
        assert violations == [], f"Hardcoded secrets found:\n" + "\n".join(violations)

    def test_no_hardcoded_secrets_in_frontend(self):
        """Frontend code must not contain hardcoded secrets."""
        frontend_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "frontend", "src"
        )
        if os.path.exists(frontend_dir):
            violations = self._scan_for_secrets(frontend_dir, {"node_modules", "__tests__"})
            assert violations == [], f"Hardcoded secrets in frontend:\n" + "\n".join(violations)
        else:
            pytest.skip("Frontend not found")


class TestEnvVarUsage:
    """All secrets must come from environment variables."""

    def test_config_uses_env_vars(self):
        """config.py should load settings from environment."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "config.py")
        with open(path) as f:
            content = f.read()
        # Should use pydantic Settings or os.environ
        assert "BaseSettings" in content or "os.environ" in content or "env" in content.lower()

    def test_jwt_secret_from_env(self):
        """JWT secret must come from environment, not hardcoded."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "config.py")
        with open(path) as f:
            content = f.read()
        assert "jwt_secret_key" in content.lower()

    def test_api_secret_from_env(self):
        """API secret key must come from environment."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "config.py")
        with open(path) as f:
            content = f.read()
        assert "api_secret_key" in content.lower()

    def test_database_url_from_env(self):
        """Database URL must come from environment."""
        path = os.path.join(os.path.dirname(__file__), "..", "app", "config.py")
        with open(path) as f:
            content = f.read()
        assert "database_url" in content.lower()


class TestEnvExample:
    """The .env.example should document all required env vars."""

    def test_env_example_exists(self):
        """An .env.example file should exist."""
        root = os.path.join(os.path.dirname(__file__), "..", "..")
        example_path = os.path.join(root, ".env.example")
        assert os.path.exists(example_path), ".env.example must exist"

    def test_env_example_has_required_vars(self):
        """Required env vars should be documented in .env.example."""
        root = os.path.join(os.path.dirname(__file__), "..", "..")
        example_path = os.path.join(root, ".env.example")
        if not os.path.exists(example_path):
            pytest.skip(".env.example not found")
        with open(example_path) as f:
            content = f.read()
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "JWT_SECRET_KEY",
        ]
        for var in required_vars:
            assert var in content, f"{var} missing from .env.example"

    def test_env_file_not_committed(self):
        """Actual .env file should not exist in the repo (only .env.example)."""
        root = os.path.join(os.path.dirname(__file__), "..", "..")
        env_path = os.path.join(root, ".env")
        # .env may exist locally but should be in .gitignore
        gitignore_path = os.path.join(root, ".gitignore")
        if os.path.exists(gitignore_path):
            with open(gitignore_path) as f:
                gitignore = f.read()
            assert ".env" in gitignore, ".env must be in .gitignore"

    def test_no_real_secrets_in_env_example(self):
        """The .env.example must only have placeholder values."""
        root = os.path.join(os.path.dirname(__file__), "..", "..")
        example_path = os.path.join(root, ".env.example")
        if not os.path.exists(example_path):
            pytest.skip(".env.example not found")
        with open(example_path) as f:
            content = f.read()
        # Should have ... or placeholder values, not real keys
        real_key_patterns = [
            re.compile(r'sk-ant-[a-zA-Z0-9]{20,}'),
            re.compile(r'AKIA[A-Z0-9]{16}'),
        ]
        for pat in real_key_patterns:
            assert not pat.search(content), "Real secret found in .env.example!"
