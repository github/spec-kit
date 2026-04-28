"""Tests for the authentication provider registry.

Covers:
- Registry mechanics (_register, get_provider, configured_providers, duplicate/empty-key guards)
- GitHubAuth — token resolution, auth headers, is_configured
- AzureDevOpsAuth — token resolution, auth headers, is_configured
- open_url / build_request — authenticated HTTP helpers with provider fallthrough
- _fetch_latest_release_tag() delegation via the registry
"""

from __future__ import annotations

import base64

import pytest

from specify_cli.authentication import AUTH_REGISTRY, _register, get_provider, configured_providers
from specify_cli.authentication.azure_devops import AzureDevOpsAuth
from specify_cli.authentication.base import AuthProvider
from specify_cli.authentication.github import GitHubAuth


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _StubProvider(AuthProvider):
    """Minimal concrete provider for registry mechanics tests."""

    key = "stub-provider"

    def get_token(self) -> str | None:
        return None

    def auth_headers(self) -> dict[str, str]:
        return {}


# ---------------------------------------------------------------------------
# Registry mechanics
# ---------------------------------------------------------------------------


class TestAuthRegistry:
    def test_github_registered(self):
        assert "github" in AUTH_REGISTRY

    def test_azure_devops_registered(self):
        assert "azure-devops" in AUTH_REGISTRY

    def test_get_provider_returns_github(self):
        provider = get_provider("github")
        assert isinstance(provider, GitHubAuth)

    def test_get_provider_returns_azure_devops(self):
        provider = get_provider("azure-devops")
        assert isinstance(provider, AzureDevOpsAuth)

    def test_get_provider_unknown_returns_none(self):
        assert get_provider("does-not-exist") is None

    def test_register_duplicate_raises_key_error(self):
        # Register once (may already exist from a previous run; use a fresh key)
        class _UniqueStub(_StubProvider):
            key = "__test_duplicate__"

        first = _UniqueStub()
        second = _UniqueStub()
        _register(first)
        with pytest.raises(KeyError, match="already registered"):
            _register(second)
        # Cleanup: remove the sentinel so it doesn't pollute other tests
        AUTH_REGISTRY.pop("__test_duplicate__", None)

    def test_register_empty_key_raises_value_error(self):
        class _EmptyKey(_StubProvider):
            key = ""

        with pytest.raises(ValueError, match="empty key"):
            _register(_EmptyKey())


# ---------------------------------------------------------------------------
# GitHubAuth
# ---------------------------------------------------------------------------


class TestGitHubAuth:
    def test_get_token_prefers_gh_token(self, monkeypatch):
        monkeypatch.setenv("GH_TOKEN", "gh-sentinel")
        monkeypatch.setenv("GITHUB_TOKEN", "github-sentinel")
        auth = GitHubAuth()
        assert auth.get_token() == "gh-sentinel"

    def test_get_token_falls_back_to_github_token(self, monkeypatch):
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.setenv("GITHUB_TOKEN", "github-sentinel")
        auth = GitHubAuth()
        assert auth.get_token() == "github-sentinel"

    def test_get_token_whitespace_only_gh_token_treated_as_absent(self, monkeypatch):
        monkeypatch.setenv("GH_TOKEN", "   ")
        monkeypatch.setenv("GITHUB_TOKEN", "github-sentinel")
        auth = GitHubAuth()
        assert auth.get_token() == "github-sentinel"

    def test_get_token_empty_gh_token_falls_back(self, monkeypatch):
        monkeypatch.setenv("GH_TOKEN", "")
        monkeypatch.setenv("GITHUB_TOKEN", "github-sentinel")
        auth = GitHubAuth()
        assert auth.get_token() == "github-sentinel"

    def test_get_token_both_absent_returns_none(self, monkeypatch):
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        auth = GitHubAuth()
        assert auth.get_token() is None

    def test_get_token_strips_leading_trailing_whitespace(self, monkeypatch):
        monkeypatch.setenv("GH_TOKEN", "  my-token  ")
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        auth = GitHubAuth()
        assert auth.get_token() == "my-token"

    def test_auth_headers_returns_bearer_when_configured(self, monkeypatch):
        monkeypatch.setenv("GH_TOKEN", "my-token")
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        auth = GitHubAuth()
        assert auth.auth_headers() == {"Authorization": "Bearer my-token"}

    def test_auth_headers_returns_empty_dict_when_not_configured(self, monkeypatch):
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        auth = GitHubAuth()
        assert auth.auth_headers() == {}

    def test_is_configured_true_when_token_present(self, monkeypatch):
        monkeypatch.setenv("GH_TOKEN", "my-token")
        assert GitHubAuth().is_configured() is True

    def test_is_configured_false_when_no_token(self, monkeypatch):
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        assert GitHubAuth().is_configured() is False

    def test_key(self):
        assert GitHubAuth.key == "github"


# ---------------------------------------------------------------------------
# AzureDevOpsAuth
# ---------------------------------------------------------------------------


class TestAzureDevOpsAuth:
    def test_get_token_prefers_azure_devops_pat(self, monkeypatch):
        monkeypatch.setenv("AZURE_DEVOPS_PAT", "ado-sentinel")
        monkeypatch.setenv("ADO_TOKEN", "ado-token-sentinel")
        auth = AzureDevOpsAuth()
        assert auth.get_token() == "ado-sentinel"

    def test_get_token_falls_back_to_ado_token(self, monkeypatch):
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.setenv("ADO_TOKEN", "ado-token-sentinel")
        auth = AzureDevOpsAuth()
        assert auth.get_token() == "ado-token-sentinel"

    def test_get_token_whitespace_only_pat_treated_as_absent(self, monkeypatch):
        monkeypatch.setenv("AZURE_DEVOPS_PAT", "   ")
        monkeypatch.setenv("ADO_TOKEN", "ado-token-sentinel")
        auth = AzureDevOpsAuth()
        assert auth.get_token() == "ado-token-sentinel"

    def test_get_token_empty_pat_falls_back(self, monkeypatch):
        monkeypatch.setenv("AZURE_DEVOPS_PAT", "")
        monkeypatch.setenv("ADO_TOKEN", "ado-token-sentinel")
        auth = AzureDevOpsAuth()
        assert auth.get_token() == "ado-token-sentinel"

    def test_get_token_both_absent_returns_none(self, monkeypatch):
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        auth = AzureDevOpsAuth()
        assert auth.get_token() is None

    def test_get_token_strips_whitespace(self, monkeypatch):
        monkeypatch.setenv("AZURE_DEVOPS_PAT", "  my-pat  ")
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        auth = AzureDevOpsAuth()
        assert auth.get_token() == "my-pat"

    def test_auth_headers_returns_basic_auth_when_configured(self, monkeypatch):
        pat = "my-pat"
        monkeypatch.setenv("AZURE_DEVOPS_PAT", pat)
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        auth = AzureDevOpsAuth()
        expected_encoded = base64.b64encode(f":{pat}".encode("ascii")).decode("ascii")
        assert auth.auth_headers() == {"Authorization": f"Basic {expected_encoded}"}

    def test_auth_headers_basic_auth_format(self, monkeypatch):
        """Verify the Base64 encoding uses :<PAT> with empty username."""
        pat = "test-token-123"
        monkeypatch.setenv("AZURE_DEVOPS_PAT", pat)
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        auth = AzureDevOpsAuth()
        header_value = auth.auth_headers()["Authorization"]
        assert header_value.startswith("Basic ")
        raw = base64.b64decode(header_value[len("Basic "):]).decode("ascii")
        assert raw == f":{pat}"

    def test_auth_headers_returns_empty_dict_when_not_configured(self, monkeypatch):
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        auth = AzureDevOpsAuth()
        assert auth.auth_headers() == {}

    def test_is_configured_true_when_pat_present(self, monkeypatch):
        monkeypatch.setenv("AZURE_DEVOPS_PAT", "my-pat")
        assert AzureDevOpsAuth().is_configured() is True

    def test_is_configured_false_when_no_credentials(self, monkeypatch):
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        assert AzureDevOpsAuth().is_configured() is False

    def test_key(self):
        assert AzureDevOpsAuth.key == "azure-devops"


# ---------------------------------------------------------------------------
# configured_providers
# ---------------------------------------------------------------------------


class TestConfiguredProviders:
    def test_returns_only_github_when_only_gh_token_set(self, monkeypatch):
        monkeypatch.setenv("GH_TOKEN", "tok")
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        providers = configured_providers()
        assert any(isinstance(p, GitHubAuth) for p in providers)
        assert not any(isinstance(p, AzureDevOpsAuth) for p in providers)

    def test_returns_only_ado_when_only_ado_pat_set(self, monkeypatch):
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setenv("AZURE_DEVOPS_PAT", "pat")
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        providers = configured_providers()
        assert not any(isinstance(p, GitHubAuth) for p in providers)
        assert any(isinstance(p, AzureDevOpsAuth) for p in providers)

    def test_returns_empty_when_none_configured(self, monkeypatch):
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        assert configured_providers() == []

    def test_returns_both_when_both_configured(self, monkeypatch):
        monkeypatch.setenv("GH_TOKEN", "tok")
        monkeypatch.setenv("AZURE_DEVOPS_PAT", "pat")
        providers = configured_providers()
        types = {type(p) for p in providers}
        assert GitHubAuth in types
        assert AzureDevOpsAuth in types


# ---------------------------------------------------------------------------
# open_url / build_request — positive tests
# ---------------------------------------------------------------------------


class TestAuthenticatedHttp:
    def test_build_request_attaches_first_configured_auth(self, monkeypatch):
        from specify_cli.authentication.http import build_request

        monkeypatch.setenv("GH_TOKEN", "my-token")
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        req = build_request("https://example.com/catalog.json")
        assert req.get_header("Authorization") == "Bearer my-token"

    def test_build_request_extra_headers_merged(self, monkeypatch):
        from specify_cli.authentication.http import build_request

        monkeypatch.setenv("GH_TOKEN", "my-token")
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        req = build_request("https://example.com/api", extra_headers={"Accept": "application/json"})
        assert req.get_header("Authorization") == "Bearer my-token"
        assert req.get_header("Accept") == "application/json"

    def test_build_request_no_auth_when_unconfigured(self, monkeypatch):
        from specify_cli.authentication.http import build_request

        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        req = build_request("https://example.com/catalog.json")
        assert "Authorization" not in req.headers

    def test_open_url_uses_first_configured_provider(self, monkeypatch):
        from unittest.mock import MagicMock, patch
        from specify_cli.authentication.http import open_url

        monkeypatch.setenv("GH_TOKEN", "my-token")
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["req"] = req
            resp = MagicMock()
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=fake_urlopen):
            open_url("https://example.com/file.json")

        assert captured["req"].get_header("Authorization") == "Bearer my-token"

    def test_open_url_unauthenticated_when_no_providers(self, monkeypatch):
        from unittest.mock import MagicMock, patch
        from specify_cli.authentication.http import open_url

        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)

        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["req"] = req
            resp = MagicMock()
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=fake_urlopen):
            open_url("https://example.com/file.json")

        assert captured["req"].get_header("Authorization") is None

    def test_open_url_falls_through_on_401_to_unauthenticated(self, monkeypatch):
        """Single configured provider gets 401 → falls through to unauthenticated."""
        import urllib.error
        from unittest.mock import MagicMock, patch
        from specify_cli.authentication.http import open_url

        monkeypatch.setenv("GH_TOKEN", "bad-token")
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)

        call_count = 0

        def fake_urlopen(req, timeout=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise urllib.error.HTTPError(
                    req.full_url, 401, "Unauthorized", {}, None
                )
            resp = MagicMock()
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=fake_urlopen):
            open_url("https://example.com/file.json")

        assert call_count == 2

    def test_open_url_falls_through_on_403_to_unauthenticated(self, monkeypatch):
        """Single configured provider gets 403 → falls through to unauthenticated."""
        import urllib.error
        from unittest.mock import MagicMock, patch
        from specify_cli.authentication.http import open_url

        monkeypatch.setenv("GH_TOKEN", "bad-token")
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)

        call_count = 0

        def fake_urlopen(req, timeout=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise urllib.error.HTTPError(
                    req.full_url, 403, "Forbidden", {}, None
                )
            resp = MagicMock()
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=fake_urlopen):
            open_url("https://example.com/file.json")

        assert call_count == 2

    def test_open_url_tries_second_provider_after_first_fails(self, monkeypatch):
        """Two configured providers: first gets 401, second succeeds."""
        import urllib.error
        from unittest.mock import MagicMock, patch
        from specify_cli.authentication.http import open_url

        monkeypatch.setenv("AZURE_DEVOPS_PAT", "bad-pat")
        monkeypatch.setenv("GH_TOKEN", "good-token")
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        calls = []

        def fake_urlopen(req, timeout=None):
            auth = req.get_header("Authorization") or "none"
            calls.append(auth)
            if auth.startswith("Basic"):
                raise urllib.error.HTTPError(
                    req.full_url, 401, "Unauthorized", {}, None
                )
            resp = MagicMock()
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=fake_urlopen):
            open_url("https://example.com/file.json")

        # ADO tried first (alphabetical), then GitHub succeeded
        assert len(calls) == 2
        assert calls[0].startswith("Basic")
        assert calls[1].startswith("Bearer")


# ---------------------------------------------------------------------------
# open_url — negative tests
# ---------------------------------------------------------------------------


class TestAuthenticatedHttpNegative:
    def test_non_auth_error_raises_immediately(self, monkeypatch):
        """A 500 error is not retried — it raises immediately."""
        import urllib.error
        from unittest.mock import patch
        from specify_cli.authentication.http import open_url

        monkeypatch.setenv("GH_TOKEN", "my-token")
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)

        def fake_urlopen(req, timeout=None):
            raise urllib.error.HTTPError(
                req.full_url, 500, "Internal Server Error", {}, None
            )

        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=fake_urlopen):
            with pytest.raises(urllib.error.HTTPError, match="500"):
                open_url("https://example.com/file.json")

    def test_404_raises_immediately(self, monkeypatch):
        """A 404 is not an auth error — it raises immediately."""
        import urllib.error
        from unittest.mock import patch
        from specify_cli.authentication.http import open_url

        monkeypatch.setenv("GH_TOKEN", "my-token")
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)

        def fake_urlopen(req, timeout=None):
            raise urllib.error.HTTPError(
                req.full_url, 404, "Not Found", {}, None
            )

        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=fake_urlopen):
            with pytest.raises(urllib.error.HTTPError, match="404"):
                open_url("https://example.com/file.json")

    def test_urlerror_raises_immediately(self, monkeypatch):
        """Network errors are not retried."""
        import urllib.error
        from unittest.mock import patch
        from specify_cli.authentication.http import open_url

        monkeypatch.setenv("GH_TOKEN", "my-token")
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)

        def fake_urlopen(req, timeout=None):
            raise urllib.error.URLError("connection refused")

        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=fake_urlopen):
            with pytest.raises(urllib.error.URLError):
                open_url("https://example.com/file.json")

    def test_all_providers_fail_auth_then_unauthenticated_also_fails(self, monkeypatch):
        """All providers get 401, unauthenticated also gets 401 — raises HTTPError."""
        import urllib.error
        from unittest.mock import patch
        from specify_cli.authentication.http import open_url

        monkeypatch.setenv("GH_TOKEN", "bad")
        monkeypatch.setenv("AZURE_DEVOPS_PAT", "bad")
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)

        def fake_urlopen(req, timeout=None):
            raise urllib.error.HTTPError(
                req.full_url, 401, "Unauthorized", {}, None
            )

        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=fake_urlopen):
            with pytest.raises(urllib.error.HTTPError, match="401"):
                open_url("https://example.com/file.json")

    def test_timeout_propagates(self, monkeypatch):
        """Socket timeout is not retried."""
        import socket
        from unittest.mock import patch
        from specify_cli.authentication.http import open_url

        monkeypatch.setenv("GH_TOKEN", "my-token")
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)

        def fake_urlopen(req, timeout=None):
            raise socket.timeout("timed out")

        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=fake_urlopen):
            with pytest.raises(socket.timeout):
                open_url("https://example.com/file.json")


# ---------------------------------------------------------------------------
# _fetch_latest_release_tag delegation
# ---------------------------------------------------------------------------


class TestFetchLatestReleaseTagDelegation:
    """Verify that _fetch_latest_release_tag() delegates to open_url."""

    def _capture_request(self):
        """Return (captured_dict, side_effect) for urlopen patching."""
        import json
        from unittest.mock import MagicMock

        captured: dict = {}

        def side_effect(req, timeout=None):
            captured["request"] = req
            body = json.dumps({"tag_name": "v9.9.9"}).encode()
            resp = MagicMock()
            resp.read.return_value = body
            cm = MagicMock()
            cm.__enter__.return_value = resp
            cm.__exit__.return_value = False
            return cm

        return captured, side_effect

    def test_gh_token_forwarded_as_bearer(self, monkeypatch):
        from unittest.mock import patch
        from specify_cli import _fetch_latest_release_tag

        monkeypatch.setenv("GH_TOKEN", "forwarded-sentinel")
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        captured, side_effect = self._capture_request()
        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=side_effect):
            _fetch_latest_release_tag()
        assert captured["request"].get_header("Authorization") == "Bearer forwarded-sentinel"

    def test_no_token_means_no_authorization_header(self, monkeypatch):
        from unittest.mock import patch
        from specify_cli import _fetch_latest_release_tag

        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        monkeypatch.delenv("ADO_TOKEN", raising=False)
        captured, side_effect = self._capture_request()
        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=side_effect):
            _fetch_latest_release_tag()
        assert captured["request"].get_header("Authorization") is None
