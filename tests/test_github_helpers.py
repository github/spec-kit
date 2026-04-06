"""Tests for GitHub-related helper functions."""

import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import httpx
import pytest

from infrakit_cli import (
    _github_auth_headers,
    _github_token,
    _format_rate_limit_error,
    _parse_rate_limit_headers,
)


class TestGithubToken:
    """Test suite for _github_token function."""

    def test_github_token_with_cli_token(self):
        """Test that CLI token takes precedence."""
        result = _github_token("cli-token")
        assert result == "cli-token"

    def test_github_token_with_whitespace(self):
        """Test that whitespace is stripped from token."""
        result = _github_token("  token-with-spaces  ")
        assert result == "token-with-spaces"

    def test_github_token_empty_string_returns_none(self):
        """Test that empty string returns None."""
        result = _github_token("")
        assert result is None

    def test_github_token_whitespace_only_returns_none(self):
        """Test that whitespace-only string returns None."""
        result = _github_token("   ")
        assert result is None

    @patch.dict(os.environ, {"GH_TOKEN": "env-gh-token"}, clear=True)
    def test_github_token_from_gh_env(self):
        """Test token from GH_TOKEN environment variable."""
        result = _github_token()
        assert result == "env-gh-token"

    @patch.dict(os.environ, {"GITHUB_TOKEN": "env-github-token"}, clear=True)
    def test_github_token_from_github_env(self):
        """Test token from GITHUB_TOKEN environment variable."""
        result = _github_token()
        assert result == "env-github-token"

    @patch.dict(
        os.environ, {"GH_TOKEN": "gh-token", "GITHUB_TOKEN": "github-token"}, clear=True
    )
    def test_github_token_gh_takes_precedence_over_github(self):
        """Test that GH_TOKEN takes precedence over GITHUB_TOKEN."""
        result = _github_token()
        assert result == "gh-token"

    @patch.dict(os.environ, {"GH_TOKEN": ""}, clear=True)
    def test_github_token_empty_env_returns_none(self):
        """Test that empty env variable returns None."""
        result = _github_token()
        assert result is None

    @patch.dict(os.environ, {}, clear=True)
    def test_github_token_no_env_returns_none(self):
        """Test that missing env variables return None."""
        result = _github_token()
        assert result is None

    @patch.dict(os.environ, {"GH_TOKEN": "env-token"}, clear=True)
    def test_github_token_cli_overrides_env(self):
        """Test that CLI token overrides env variable."""
        result = _github_token("cli-token")
        assert result == "cli-token"


class TestGithubAuthHeaders:
    """Test suite for _github_auth_headers function."""

    def test_github_auth_headers_with_token(self):
        """Test headers with valid token."""
        result = _github_auth_headers("my-token")
        assert result == {"Authorization": "Bearer my-token"}

    def test_github_auth_headers_with_none(self):
        """Test headers with None token."""
        result = _github_auth_headers(None)
        assert result == {}

    def test_github_auth_headers_with_empty_string(self):
        """Test headers with empty string token."""
        result = _github_auth_headers("")
        assert result == {}

    def test_github_auth_headers_with_whitespace(self):
        """Test headers with whitespace-only token."""
        result = _github_auth_headers("   ")
        assert result == {}


class TestParseRateLimitHeaders:
    """Test suite for _parse_rate_limit_headers function."""

    def test_parse_all_headers_present(self):
        """Test parsing with all rate limit headers present."""
        headers = httpx.Headers(
            {
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Reset": "1234567890",
                "Retry-After": "60",
            }
        )
        result = _parse_rate_limit_headers(headers)

        assert result["limit"] == "5000"
        assert result["remaining"] == "4999"
        assert result["reset_epoch"] == 1234567890
        assert result["reset_time"] == datetime.fromtimestamp(
            1234567890, tz=timezone.utc
        )
        assert result["retry_after_seconds"] == 60

    def test_parse_partial_headers(self):
        """Test parsing with only some headers present."""
        headers = httpx.Headers(
            {
                "X-RateLimit-Limit": "5000",
            }
        )
        result = _parse_rate_limit_headers(headers)

        assert result["limit"] == "5000"
        assert "remaining" not in result
        assert "reset_epoch" not in result

    def test_parse_no_headers(self):
        """Test parsing with no rate limit headers."""
        headers = httpx.Headers({})
        result = _parse_rate_limit_headers(headers)

        assert result == {}

    def test_parse_retry_after_non_numeric(self):
        """Test parsing with non-numeric Retry-After header."""
        headers = httpx.Headers(
            {
                "Retry-After": "Wed, 21 Oct 2025 07:28:00 GMT",
            }
        )
        result = _parse_rate_limit_headers(headers)

        assert result["retry_after"] == "Wed, 21 Oct 2025 07:28:00 GMT"
        assert "retry_after_seconds" not in result

    def test_parse_reset_time_conversion(self):
        """Test that reset time is properly converted to local timezone."""
        headers = httpx.Headers(
            {
                "X-RateLimit-Reset": "1234567890",
            }
        )
        result = _parse_rate_limit_headers(headers)

        assert "reset_local" in result
        # Verify it's a datetime with timezone info
        assert isinstance(result["reset_local"], datetime)
        assert result["reset_local"].tzinfo is not None


class TestFormatRateLimitError:
    """Test suite for _format_rate_limit_error function."""

    def test_format_basic_error(self):
        """Test basic error formatting."""
        headers = httpx.Headers({})
        result = _format_rate_limit_error(403, headers, "https://api.github.com/test")

        assert "403" in result
        assert "https://api.github.com/test" in result
        assert "Troubleshooting Tips" in result

    def test_format_with_rate_limit_info(self):
        """Test error formatting with rate limit info."""
        headers = httpx.Headers(
            {
                "X-RateLimit-Limit": "60",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "1234567890",
            }
        )
        result = _format_rate_limit_error(403, headers, "https://api.github.com/test")

        assert "Rate Limit Information" in result
        assert "60" in result
        assert "0" in result

    def test_format_includes_troubleshooting(self):
        """Test that error includes troubleshooting tips."""
        headers = httpx.Headers({})
        result = _format_rate_limit_error(500, headers, "https://api.github.com/test")

        assert "Troubleshooting Tips" in result
        assert "shared CI" in result or "corporate environment" in result
        assert "GitHub token" in result or "GH_TOKEN" in result
