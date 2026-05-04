"""Tests for GitHub-authenticated HTTP request helpers."""

import os
from unittest.mock import patch
import pytest

from specify_cli._github_http import (
    build_github_request,
)


class TestBuildGithubRequest:
    """Tests for build_github_request() URL validation and auth handling."""

    # --- URL Validation Tests ---

    def test_empty_url_raises_value_error(self):
        """build_github_request() must reject an empty string URL."""
        with pytest.raises(ValueError, match="url must not be empty"):
            build_github_request("")

    def test_whitespace_url_raises_value_error(self):
        """build_github_request() must reject a whitespace-only URL."""
        with pytest.raises(ValueError, match="url must not be empty"):
            build_github_request("   ")

    def test_non_http_url_raises_value_error(self):
        """build_github_request() must reject URLs without http/https scheme."""
        with pytest.raises(ValueError, match="url must start with http"):
            build_github_request("not-a-url")

    def test_ftp_url_raises_value_error(self):
        """build_github_request() must reject ftp:// URLs."""
        with pytest.raises(ValueError, match="url must start with http"):
            build_github_request("ftp://github.com/file.zip")

    # --- Valid URL Tests ---

    def test_valid_https_url_returns_request(self):
        """build_github_request() must return a Request for a valid https URL."""
        req = build_github_request("https://github.com/github/spec-kit")
        assert req.full_url == "https://github.com/github/spec-kit"

    def test_valid_http_url_returns_request(self):
        """build_github_request() must accept http:// URLs."""
        req = build_github_request("http://example.com/file")
        assert req.full_url == "http://example.com/file"

    # --- Auth Header Tests ---

    def test_github_token_added_for_github_host(self):
        """Authorization header is set when GITHUB_TOKEN is present."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test-token", "GH_TOKEN": ""}):
            req = build_github_request("https://github.com/github/spec-kit")
        assert req.get_header("Authorization") == "Bearer test-token"

    def test_gh_token_used_as_fallback(self):
        """GH_TOKEN is used when GITHUB_TOKEN is absent."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "", "GH_TOKEN": "fallback-token"}):
            req = build_github_request("https://github.com/github/spec-kit")
        assert req.get_header("Authorization") == "Bearer fallback-token"

    def test_no_auth_header_for_non_github_host(self):
        """Authorization header must NOT be set for non-GitHub URLs."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test-token"}):
            req = build_github_request("https://example.com/file")
        assert req.get_header("Authorization") is None

    def test_no_auth_header_when_no_token(self):
        """No Authorization header when no token is set in environment."""
        with patch.dict(os.environ, {}, clear=True):
            req = build_github_request("https://github.com/github/spec-kit")
        assert req.get_header("Authorization") is None
        
    def test_missing_hostname_raises_value_error(self):
        """build_github_request() must reject URLs with valid scheme but no hostname."""
        with pytest.raises(ValueError, match="url must include a hostname"):
            build_github_request("http://")