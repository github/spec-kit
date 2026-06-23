"""Tests for GitHub-authenticated HTTP request helpers."""

import io
import json
import os
from contextlib import contextmanager
from unittest.mock import MagicMock, patch
from urllib.request import Request

import pytest

from specify_cli._github_http import (
    GITHUB_HOSTS,
    build_github_request,
    resolve_github_release_asset_api_url,
)
from specify_cli.authentication.http import _StripAuthOnRedirect


class TestBuildGitHubRequest:
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


class TestResolveGitHubReleaseAssetApiUrl:
    """Tests for resolve_github_release_asset_api_url()."""

    def _make_open_url_fn(self, release_json):
        """Create a fake open_url_fn that returns release JSON."""
        @contextmanager
        def fake_open(url, timeout=None, extra_headers=None):
            resp = MagicMock()
            resp.read.side_effect = io.BytesIO(json.dumps(release_json).encode()).read
            yield resp
        return fake_open

    def test_returns_none_for_non_github_url(self):
        """Non-GitHub URLs should return None."""
        result = resolve_github_release_asset_api_url(
            "https://example.com/file.zip", lambda *a, **kw: None
        )
        assert result is None

    def test_returns_none_for_non_release_github_url(self):
        """GitHub URLs that aren't release downloads return None."""
        result = resolve_github_release_asset_api_url(
            "https://github.com/org/repo/archive/refs/tags/v1.zip",
            lambda *a, **kw: None,
        )
        assert result is None

    def test_passthrough_for_existing_api_asset_url(self):
        """Already-resolved REST API asset URLs are returned as-is."""
        url = "https://api.github.com/repos/org/repo/releases/assets/12345"
        result = resolve_github_release_asset_api_url(url, lambda *a, **kw: None)
        assert result == url

    def test_resolves_browser_url_to_api_url(self):
        """Browser release URL resolves to REST API asset URL."""
        release_json = {
            "assets": [
                {"name": "pack.zip", "url": "https://api.github.com/repos/org/repo/releases/assets/99"}
            ]
        }
        result = resolve_github_release_asset_api_url(
            "https://github.com/org/repo/releases/download/v1.0/pack.zip",
            self._make_open_url_fn(release_json),
        )
        assert result == "https://api.github.com/repos/org/repo/releases/assets/99"

    def test_returns_none_when_asset_not_found(self):
        """Returns None when the release exists but asset name doesn't match."""
        release_json = {"assets": [{"name": "other.zip", "url": "https://api.github.com/repos/org/repo/releases/assets/1"}]}
        result = resolve_github_release_asset_api_url(
            "https://github.com/org/repo/releases/download/v1/missing.zip",
            self._make_open_url_fn(release_json),
        )
        assert result is None

    def test_returns_none_on_network_error(self):
        """Returns None when the API request fails."""
        import urllib.error

        @contextmanager
        def failing_open(url, timeout=None, extra_headers=None):
            raise urllib.error.URLError("network error")
            yield  # pragma: no cover

        result = resolve_github_release_asset_api_url(
            "https://github.com/org/repo/releases/download/v1/pack.zip",
            failing_open,
        )
        assert result is None

    def test_metadata_lookup_is_bounded_and_redirect_validated(self):
        """Release metadata reads stay bounded and use the caller's policy."""
        captured = {}

        class OversizedResponse:
            def read(self, amount=None):
                captured["read_amount"] = amount
                return b"x" * amount

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def redirect_validator(old_url, new_url):
            return None

        def fake_open(
            url,
            timeout=None,
            extra_headers=None,
            redirect_validator=None,
        ):
            captured["redirect_validator"] = redirect_validator
            return OversizedResponse()

        result = resolve_github_release_asset_api_url(
            "https://github.com/org/repo/releases/download/v1/pack.zip",
            fake_open,
            redirect_validator=redirect_validator,
            max_metadata_bytes=8,
        )

        assert result is None
        assert captured["read_amount"] == 9
        assert captured["redirect_validator"] is redirect_validator

    def test_tag_with_special_characters_is_url_encoded(self):
        """Tags with reserved characters (e.g. '/') are encoded in the API URL."""
        captured_urls = []

        @contextmanager
        def capturing_open(url, timeout=None, extra_headers=None):
            captured_urls.append(url)
            resp = MagicMock()
            resp.read.side_effect = io.BytesIO(json.dumps({"assets": []}).encode()).read
            yield resp

        resolve_github_release_asset_api_url(
            "https://github.com/org/repo/releases/download/feature%2Fv1/pack.zip",
            capturing_open,
        )
        # The tag "feature/v1" (decoded from %2F) must be re-encoded as "feature%2Fv1"
        assert len(captured_urls) == 1
        assert "releases/tags/feature%2Fv1" in captured_urls[0]

    def test_tag_with_hash_is_url_encoded(self):
        """Tags with '#' character are properly encoded."""
        captured_urls = []

        @contextmanager
        def capturing_open(url, timeout=None, extra_headers=None):
            captured_urls.append(url)
            resp = MagicMock()
            resp.read.side_effect = io.BytesIO(json.dumps({"assets": []}).encode()).read
            yield resp

        resolve_github_release_asset_api_url(
            "https://github.com/org/repo/releases/download/v1%23beta/pack.zip",
            capturing_open,
        )
        assert len(captured_urls) == 1
        assert "releases/tags/v1%23beta" in captured_urls[0]

    # --- GHES (GitHub Enterprise Server) ---

    def test_resolves_ghes_browser_url_to_api_url(self):
        """A GHES browser release URL resolves to the /api/v3 asset URL."""
        release_json = {
            "assets": [
                {"name": "ext.zip",
                 "url": "https://ghes.example/api/v3/repos/o/r/releases/assets/7"}
            ]
        }
        result = resolve_github_release_asset_api_url(
            "https://ghes.example/o/r/releases/download/v1/ext.zip",
            self._make_open_url_fn(release_json),
            github_hosts=("ghes.example",),
        )
        assert result == "https://ghes.example/api/v3/repos/o/r/releases/assets/7"

    def test_passthrough_for_existing_ghes_api_asset_url(self):
        """An already-resolved GHES /api/v3 asset URL is returned as-is."""
        url = "https://ghes.example/api/v3/repos/o/r/releases/assets/7"
        result = resolve_github_release_asset_api_url(
            url, lambda *a, **kw: None, github_hosts=("ghes.example",)
        )
        assert result == url

    def test_returns_none_for_ghes_host_not_in_allowlist(self):
        """Unlisted hosts get no GHES treatment and trigger no API call (anti-SSRF)."""
        called = []

        @contextmanager
        def recording_open(url, timeout=None, extra_headers=None):
            called.append(url)
            resp = MagicMock()
            resp.read.side_effect = io.BytesIO(b"{}").read
            yield resp

        result = resolve_github_release_asset_api_url(
            "https://ghes.example/o/r/releases/download/v1/ext.zip",
            recording_open,
            github_hosts=("other.example",),
        )
        assert result is None
        assert called == []

    def test_returns_none_on_malformed_ghes_port(self):
        """A malformed port on an allowlisted GHES host returns None, not a
        ValueError (contract: resolve or return None, never raise)."""
        called = []

        def open_never(url, timeout=None, extra_headers=None):
            called.append(url)
            raise AssertionError("open_url_fn must not be called")

        result = resolve_github_release_asset_api_url(
            "https://ghes.example:notaport/o/r/releases/download/v1/ext.zip",
            open_never,
            github_hosts=("ghes.example",),
        )
        assert result is None
        assert called == []

    def test_passthrough_for_unlisted_ghes_api_asset_url(self):
        """A direct GHES /api/v3 asset URL passes through even when the host is
        not allowlisted: passthrough issues no API request, and the download
        helper gates the token independently, so octet-stream resolution must
        not be withheld."""
        called = []

        @contextmanager
        def recording_open(url, timeout=None, extra_headers=None):
            called.append(url)
            resp = MagicMock()
            resp.read.side_effect = io.BytesIO(b"{}").read
            yield resp

        url = "https://ghes.example/api/v3/repos/o/r/releases/assets/7"
        result = resolve_github_release_asset_api_url(
            url, recording_open, github_hosts=("other.example",)
        )
        assert result == url
        assert called == []

    def test_ghes_api_base_preserves_scheme_and_port(self):
        """The GHES API base mirrors the URL scheme and keeps a non-standard port."""
        captured = []

        @contextmanager
        def capturing_open(url, timeout=None, extra_headers=None):
            captured.append(url)
            resp = MagicMock()
            resp.read.side_effect = io.BytesIO(json.dumps({"assets": []}).encode()).read
            yield resp

        resolve_github_release_asset_api_url(
            "http://localhost:8000/o/r/releases/download/v1/ext.zip",
            capturing_open,
            github_hosts=("localhost",),
        )
        assert captured == ["http://localhost:8000/api/v3/repos/o/r/releases/tags/v1"]

    def test_ghes_wildcard_does_not_match_bare_host(self):
        """A '*.suffix' pattern does not match the bare host (must list it explicitly)."""
        result = resolve_github_release_asset_api_url(
            "https://ghes.example/o/r/releases/download/v1/ext.zip",
            lambda *a, **kw: None,
            github_hosts=("*.ghes.example",),
        )
        assert result is None

    def test_public_github_url_unaffected_by_github_hosts(self):
        """Public github.com still resolves via api.github.com even with github_hosts set."""
        captured = []

        @contextmanager
        def capturing_open(url, timeout=None, extra_headers=None):
            captured.append(url)
            resp = MagicMock()
            resp.read.side_effect = io.BytesIO(json.dumps({
                "assets": [{"name": "pack.zip",
                            "url": "https://api.github.com/repos/org/repo/releases/assets/99"}]
            }).encode()).read
            yield resp

        result = resolve_github_release_asset_api_url(
            "https://github.com/org/repo/releases/download/v1.0/pack.zip",
            capturing_open,
            github_hosts=("ghes.example",),
        )
        assert result == "https://api.github.com/repos/org/repo/releases/assets/99"
        assert captured == ["https://api.github.com/repos/org/repo/releases/tags/v1.0"]


class TestGitHubRedirectAuth:
    """Tests for GitHub-owned redirect auth handling."""

    def test_multi_hop_github_redirect_preserves_unredirected_auth(self):
        """Auth survives a multi-hop redirect chain within GitHub hosts."""
        handler = _StripAuthOnRedirect(tuple(GITHUB_HOSTS))
        req1 = Request(
            "https://github.com/org/repo",
            headers={"Authorization": "Bearer tok"},
        )

        req2 = handler.redirect_request(
            req1,
            io.BytesIO(b""),
            302,
            "Found",
            {},
            "https://codeload.github.com/org/repo/zip",
        )
        assert req2 is not None
        auth2 = req2.get_header("Authorization") or req2.unredirected_hdrs.get(
            "Authorization"
        )
        assert auth2 == "Bearer tok"

        req3 = handler.redirect_request(
            req2,
            io.BytesIO(b""),
            302,
            "Found",
            {},
            "https://raw.githubusercontent.com/org/repo/main/file",
        )
        assert req3 is not None
        auth3 = req3.get_header("Authorization") or req3.unredirected_hdrs.get(
            "Authorization"
        )
        assert auth3 == "Bearer tok"
