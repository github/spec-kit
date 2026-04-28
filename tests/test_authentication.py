"""Tests for the authentication provider registry.

Covers:
- Registry mechanics (_register, get_provider, duplicate/empty-key guards)
- GitHubAuth — token resolution, auth headers, api_base_url, is_configured
- AzureDevOpsAuth — token resolution, auth headers, api_base_url, is_configured
- _fetch_latest_release_tag() delegation to GitHubAuth via the registry
"""

from __future__ import annotations

import base64

import pytest

from specify_cli.authentication import AUTH_REGISTRY, _register, get_provider
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

    def api_base_url(self) -> str:
        return "https://example.com"


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
        stub = _StubProvider()
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

    def test_api_base_url(self):
        assert GitHubAuth().api_base_url() == "https://api.github.com"

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

    def test_api_base_url(self):
        assert AzureDevOpsAuth().api_base_url() == "https://dev.azure.com"

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
# _fetch_latest_release_tag delegation
# ---------------------------------------------------------------------------


class TestFetchLatestReleaseTagDelegation:
    """Verify that _fetch_latest_release_tag() uses GitHubAuth for the token."""

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
        captured, side_effect = self._capture_request()
        with patch("specify_cli.urllib.request.urlopen", side_effect=side_effect):
            _fetch_latest_release_tag()
        assert captured["request"].get_header("Authorization") == "Bearer forwarded-sentinel"

    def test_no_token_means_no_authorization_header(self, monkeypatch):
        from unittest.mock import patch
        from specify_cli import _fetch_latest_release_tag

        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        captured, side_effect = self._capture_request()
        with patch("specify_cli.urllib.request.urlopen", side_effect=side_effect):
            _fetch_latest_release_tag()
        assert captured["request"].get_header("Authorization") is None

    def test_accept_header_always_present(self, monkeypatch):
        from unittest.mock import patch
        from specify_cli import _fetch_latest_release_tag

        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        captured, side_effect = self._capture_request()
        with patch("specify_cli.urllib.request.urlopen", side_effect=side_effect):
            _fetch_latest_release_tag()
        assert captured["request"].get_header("Accept") == "application/vnd.github+json"
