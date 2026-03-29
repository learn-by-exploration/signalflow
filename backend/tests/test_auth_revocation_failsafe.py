"""Tests for token revocation failsafe behavior (B4).

Ensures is_token_revoked fails closed (returns True = revoked) on
unexpected errors in production, and fails open only in dev/test.
"""

from unittest.mock import MagicMock, patch


def test_revocation_fails_closed_on_unexpected_error_in_production():
    """In production, an unexpected error should treat the token as revoked."""
    from app.auth import is_token_revoked

    mock_redis = MagicMock()
    mock_redis.exists.side_effect = ValueError("Unexpected serialization error")

    mock_settings = MagicMock()
    mock_settings.redis_url = "redis://localhost:6379/0"
    mock_settings.environment = "production"

    with (
        patch("app.auth._get_revocation_redis", return_value=mock_redis),
        patch("app.auth.get_settings", return_value=mock_settings),
    ):
        result = is_token_revoked("jti-123", "user-456", 1000.0)
        assert result is True, "Should fail closed (revoked) in production on unexpected error"


def test_revocation_fails_open_on_unexpected_error_in_development():
    """In development, an unexpected error should treat the token as valid."""
    from app.auth import is_token_revoked

    mock_redis = MagicMock()
    mock_redis.exists.side_effect = ValueError("Unexpected error")

    mock_settings = MagicMock()
    mock_settings.redis_url = "redis://localhost:6379/0"
    mock_settings.environment = "development"

    with (
        patch("app.auth._get_revocation_redis", return_value=mock_redis),
        patch("app.auth.get_settings", return_value=mock_settings),
    ):
        result = is_token_revoked("jti-123", "user-456", 1000.0)
        assert result is False, "Should fail open (valid) in development"


def test_revocation_fails_open_on_unexpected_error_in_test():
    """In test environment, an unexpected error should treat the token as valid."""
    from app.auth import is_token_revoked

    mock_redis = MagicMock()
    mock_redis.exists.side_effect = TypeError("Mock object not subscriptable")

    mock_settings = MagicMock()
    mock_settings.redis_url = "redis://localhost:6379/0"
    mock_settings.environment = "test"

    with (
        patch("app.auth._get_revocation_redis", return_value=mock_redis),
        patch("app.auth.get_settings", return_value=mock_settings),
    ):
        result = is_token_revoked("jti-123", "user-456", 1000.0)
        assert result is False, "Should fail open (valid) in test"


def test_revoke_token_uses_config_ttl():
    """revoke_token() should derive TTL from config when not explicitly provided."""
    from app.auth import revoke_token

    mock_redis = MagicMock()
    mock_settings = MagicMock()
    mock_settings.jwt_access_token_expire_minutes = 30  # = 1800 seconds

    with (
        patch("app.auth._get_revocation_redis", return_value=mock_redis),
        patch("app.auth.get_settings", return_value=mock_settings),
    ):
        revoke_token("jti-abc")
        mock_redis.set.assert_called_once_with("token_bl:jti-abc", "1", ex=1800)


def test_revoke_token_accepts_explicit_ttl():
    """revoke_token() should use explicit TTL when provided."""
    from app.auth import revoke_token

    mock_redis = MagicMock()

    with patch("app.auth._get_revocation_redis", return_value=mock_redis):
        revoke_token("jti-xyz", ttl_seconds=3600)
        mock_redis.set.assert_called_once_with("token_bl:jti-xyz", "1", ex=3600)
