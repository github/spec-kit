"""Tests for the authentication provider registry and config-driven HTTP helpers.

Covers:
- Config loading (auth.json parsing, validation, permission warning)
- Registry mechanics (_register, get_provider, duplicate/empty-key guards)
- GitHubAuth — bearer headers
- AzureDevOpsAuth — basic-pat, bearer, azure-cli, azure-ad headers
- Host matching (find_entries_for_url)
- open_url — config-driven auth with fallthrough and redirect stripping
- build_request — single-shot request construction
- _fetch_latest_release_tag() delegation
"""

from __future__ import annotations

import base64
import json
import os

import pytest

from specify_cli.authentication import AUTH_REGISTRY, _register, get_provider
from specify_cli.authentication.azure_devops import AzureDevOpsAuth
from specify_cli.authentication.base import AuthProvider
from specify_cli.authentication.config import (
    AuthConfigEntry,
    find_entries_for_url,
    load_auth_config,
)
from specify_cli.authentication.github import GitHubAuth


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _github_entry(token_env: str = "GH_TOKEN", token: str | None = None) -> AuthConfigEntry:
    """Build a standard GitHub config entry."""
    return AuthConfigEntry(
        hosts=("github.com", "api.github.com", "raw.githubusercontent.com", "codeload.github.com"),
        provider="github",
        auth="bearer",
        token=token,
        token_env=token_env if token is None else None,
    )


def _ado_basic_entry(token_env: str = "AZURE_DEVOPS_PAT") -> AuthConfigEntry:
    """Build an ADO basic-pat config entry."""
    return AuthConfigEntry(
        hosts=("dev.azure.com",),
        provider="azure-devops",
        auth="basic-pat",
        token_env=token_env,
    )


class _StubProvider(AuthProvider):
    """Minimal concrete provider for registry mechanics tests."""

    key = "stub-provider"
    supported_auth_schemes = ("bearer",)

    def auth_headers(self, token: str, auth_scheme: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


class TestLoadAuthConfig:
    def test_missing_file_returns_empty(self, tmp_path):
        assert load_auth_config(tmp_path / "nonexistent.json") == []

    def test_valid_github_config(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{
                "hosts": ["github.com"],
                "provider": "github",
                "auth": "bearer",
                "token_env": "GH_TOKEN",
            }]
        }))
        entries = load_auth_config(cfg)
        assert len(entries) == 1
        assert entries[0].provider == "github"
        assert entries[0].auth == "bearer"
        assert entries[0].token_env == "GH_TOKEN"

    def test_valid_ado_config(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{
                "hosts": ["dev.azure.com"],
                "provider": "azure-devops",
                "auth": "basic-pat",
                "token_env": "AZURE_DEVOPS_PAT",
            }]
        }))
        entries = load_auth_config(cfg)
        assert len(entries) == 1
        assert entries[0].provider == "azure-devops"
        assert entries[0].auth == "basic-pat"

    def test_inline_token(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{
                "hosts": ["github.com"],
                "provider": "github",
                "auth": "bearer",
                "token": "ghp_inline_token",
            }]
        }))
        entries = load_auth_config(cfg)
        assert entries[0].token == "ghp_inline_token"

    def test_azure_ad_config(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{
                "hosts": ["dev.azure.com"],
                "provider": "azure-devops",
                "auth": "azure-ad",
                "tenant_id": "tid",
                "client_id": "cid",
                "client_secret_env": "SECRET",
            }]
        }))
        entries = load_auth_config(cfg)
        assert entries[0].auth == "azure-ad"
        assert entries[0].tenant_id == "tid"

    def test_azure_cli_config(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{
                "hosts": ["dev.azure.com"],
                "provider": "azure-devops",
                "auth": "azure-cli",
            }]
        }))
        entries = load_auth_config(cfg)
        assert entries[0].auth == "azure-cli"

    def test_multiple_entries(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [
                {"hosts": ["github.com"], "provider": "github", "auth": "bearer", "token_env": "GH_TOKEN"},
                {"hosts": ["dev.azure.com"], "provider": "azure-devops", "auth": "basic-pat", "token_env": "ADO_PAT"},
            ]
        }))
        entries = load_auth_config(cfg)
        assert len(entries) == 2

    # -- Negative: validation errors --

    def test_invalid_json_raises(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text("not json")
        with pytest.raises(json.JSONDecodeError):
            load_auth_config(cfg)

    def test_not_object_raises(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text("[]")
        with pytest.raises(ValueError, match="JSON object"):
            load_auth_config(cfg)

    def test_missing_providers_raises(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({"foo": "bar"}))
        with pytest.raises(ValueError, match="providers"):
            load_auth_config(cfg)

    def test_empty_hosts_raises(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{"hosts": [], "provider": "github", "auth": "bearer", "token_env": "X"}]
        }))
        with pytest.raises(ValueError, match="non-empty"):
            load_auth_config(cfg)

    def test_missing_provider_key_raises(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{"hosts": ["github.com"], "auth": "bearer", "token_env": "X"}]
        }))
        with pytest.raises(ValueError, match="provider"):
            load_auth_config(cfg)

    def test_unsupported_auth_scheme_raises(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{"hosts": ["github.com"], "provider": "github", "auth": "ntlm", "token_env": "X"}]
        }))
        with pytest.raises(ValueError, match="does not support"):
            load_auth_config(cfg)

    def test_bearer_without_token_raises(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{"hosts": ["github.com"], "provider": "github", "auth": "bearer"}]
        }))
        with pytest.raises(ValueError, match="token"):
            load_auth_config(cfg)

    def test_azure_ad_missing_fields_raises(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{
                "hosts": ["dev.azure.com"],
                "provider": "azure-devops",
                "auth": "azure-ad",
                "tenant_id": "tid",
            }]
        }))
        with pytest.raises(ValueError, match="azure-ad"):
            load_auth_config(cfg)

    def test_unknown_provider_raises(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{"hosts": ["example.com"], "provider": "gitlab", "auth": "bearer", "token_env": "X"}]
        }))
        with pytest.raises(ValueError, match="unknown provider"):
            load_auth_config(cfg)

    def test_incompatible_provider_scheme_raises(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{
                "hosts": ["github.com"],
                "provider": "github",
                "auth": "basic-pat",
                "token_env": "X",
            }]
        }))
        with pytest.raises(ValueError, match="does not support"):
            load_auth_config(cfg)

    def test_dangerous_wildcard_host_raises(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{"hosts": ["*github.com"], "provider": "github", "auth": "bearer", "token_env": "X"}]
        }))
        with pytest.raises(ValueError, match="invalid host pattern"):
            load_auth_config(cfg)

    def test_multi_wildcard_host_raises(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{"hosts": ["*.*.example.com"], "provider": "github", "auth": "bearer", "token_env": "X"}]
        }))
        with pytest.raises(ValueError, match="invalid host pattern"):
            load_auth_config(cfg)

    def test_valid_star_dot_host_accepted(self, tmp_path):
        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{"hosts": ["*.visualstudio.com"], "provider": "azure-devops", "auth": "basic-pat", "token_env": "X"}]
        }))
        entries = load_auth_config(cfg)
        assert entries[0].hosts == ("*.visualstudio.com",)

    @pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits not supported on Windows")
    def test_world_readable_warns(self, tmp_path):
        import stat

        cfg = tmp_path / "auth.json"
        cfg.write_text(json.dumps({
            "providers": [{"hosts": ["github.com"], "provider": "github", "auth": "bearer", "token_env": "GH_TOKEN"}]
        }))
        cfg.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        with pytest.warns(UserWarning, match="readable by group"):
            load_auth_config(cfg)


# ---------------------------------------------------------------------------
# Host matching
# ---------------------------------------------------------------------------


class TestFindEntriesForUrl:
    def test_exact_match(self):
        entry = _github_entry()
        result = find_entries_for_url("https://github.com/org/repo", [entry])
        assert result == [entry]

    def test_wildcard_match(self):
        entry = AuthConfigEntry(
            hosts=("*.visualstudio.com",),
            provider="azure-devops",
            auth="basic-pat",
            token_env="ADO_PAT",
        )
        result = find_entries_for_url("https://myorg.visualstudio.com/project", [entry])
        assert result == [entry]

    def test_no_match_returns_empty(self):
        entry = _github_entry()
        result = find_entries_for_url("https://evil.example.com/file", [entry])
        assert result == []

    def test_no_match_for_lookalike_host(self):
        entry = _github_entry()
        result = find_entries_for_url("https://github.com.evil.com/file", [entry])
        assert result == []

    def test_empty_url_returns_empty(self):
        assert find_entries_for_url("", [_github_entry()]) == []

    def test_empty_entries_returns_empty(self):
        assert find_entries_for_url("https://github.com/org/repo", []) == []

    def test_multiple_matches_returned(self):
        e1 = _github_entry(token_env="GH_TOKEN")
        e2 = _github_entry(token_env="GITHUB_TOKEN")
        result = find_entries_for_url("https://github.com/org/repo", [e1, e2])
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Registry mechanics
# ---------------------------------------------------------------------------


class TestAuthRegistry:
    def test_github_registered(self):
        assert "github" in AUTH_REGISTRY

    def test_azure_devops_registered(self):
        assert "azure-devops" in AUTH_REGISTRY

    def test_get_provider_returns_github(self):
        assert isinstance(get_provider("github"), GitHubAuth)

    def test_get_provider_returns_azure_devops(self):
        assert isinstance(get_provider("azure-devops"), AzureDevOpsAuth)

    def test_get_provider_unknown_returns_none(self):
        assert get_provider("does-not-exist") is None

    def test_register_duplicate_raises_key_error(self):
        class _UniqueStub(_StubProvider):
            key = "__test_duplicate__"

        try:
            _register(_UniqueStub())
            with pytest.raises(KeyError, match="already registered"):
                _register(_UniqueStub())
        finally:
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
    def test_bearer_headers(self):
        assert GitHubAuth().auth_headers("my-token", "bearer") == {"Authorization": "Bearer my-token"}

    def test_unsupported_scheme_raises(self):
        with pytest.raises(ValueError, match="basic-pat"):
            GitHubAuth().auth_headers("tok", "basic-pat")

    def test_resolve_token_from_env(self, monkeypatch):
        monkeypatch.setenv("GH_TOKEN", "env-token")
        assert GitHubAuth().resolve_token(_github_entry()) == "env-token"

    def test_resolve_token_inline(self):
        assert GitHubAuth().resolve_token(_github_entry(token="inline-tok")) == "inline-tok"

    def test_resolve_token_strips_whitespace(self, monkeypatch):
        monkeypatch.setenv("GH_TOKEN", "  my-token  ")
        assert GitHubAuth().resolve_token(_github_entry()) == "my-token"

    def test_resolve_token_empty_env_returns_none(self, monkeypatch):
        monkeypatch.setenv("GH_TOKEN", "   ")
        assert GitHubAuth().resolve_token(_github_entry()) is None

    def test_resolve_token_missing_env_returns_none(self, monkeypatch):
        monkeypatch.delenv("GH_TOKEN", raising=False)
        assert GitHubAuth().resolve_token(_github_entry()) is None

    def test_key(self):
        assert GitHubAuth.key == "github"

    def test_supported_schemes(self):
        assert GitHubAuth.supported_auth_schemes == ("bearer",)


# ---------------------------------------------------------------------------
# AzureDevOpsAuth
# ---------------------------------------------------------------------------


class TestAzureDevOpsAuth:
    def test_basic_pat_headers(self):
        headers = AzureDevOpsAuth().auth_headers("my-pat", "basic-pat")
        encoded = base64.b64encode(b":my-pat").decode("ascii")
        assert headers == {"Authorization": f"Basic {encoded}"}

    def test_basic_pat_format(self):
        header = AzureDevOpsAuth().auth_headers("test-pat", "basic-pat")["Authorization"]
        raw = base64.b64decode(header[len("Basic "):]).decode("ascii")
        assert raw == ":test-pat"

    def test_bearer_headers(self):
        assert AzureDevOpsAuth().auth_headers("tok", "bearer") == {"Authorization": "Bearer tok"}

    def test_azure_cli_headers(self):
        assert AzureDevOpsAuth().auth_headers("tok", "azure-cli") == {"Authorization": "Bearer tok"}

    def test_azure_ad_headers(self):
        assert AzureDevOpsAuth().auth_headers("tok", "azure-ad") == {"Authorization": "Bearer tok"}

    def test_unsupported_scheme_raises(self):
        with pytest.raises(ValueError):
            AzureDevOpsAuth().auth_headers("tok", "ntlm")

    def test_resolve_token_basic_pat(self, monkeypatch):
        monkeypatch.setenv("AZURE_DEVOPS_PAT", "my-pat")
        assert AzureDevOpsAuth().resolve_token(_ado_basic_entry()) == "my-pat"

    def test_resolve_token_strips_whitespace(self, monkeypatch):
        monkeypatch.setenv("AZURE_DEVOPS_PAT", "  my-pat  ")
        assert AzureDevOpsAuth().resolve_token(_ado_basic_entry()) == "my-pat"

    def test_resolve_token_missing_returns_none(self, monkeypatch):
        monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
        assert AzureDevOpsAuth().resolve_token(_ado_basic_entry()) is None

    def test_key(self):
        assert AzureDevOpsAuth.key == "azure-devops"

    def test_supported_schemes(self):
        schemes = AzureDevOpsAuth.supported_auth_schemes
        assert "basic-pat" in schemes
        assert "bearer" in schemes
        assert "azure-cli" in schemes
        assert "azure-ad" in schemes

    def test_resolve_token_azure_cli_success(self):
        """azure-cli acquires token via az CLI."""
        from unittest.mock import patch, MagicMock
        entry = AuthConfigEntry(
            hosts=("dev.azure.com",), provider="azure-devops", auth="azure-cli",
        )
        result = MagicMock()
        result.returncode = 0
        result.stdout = '{"accessToken": "cli-acquired-token"}'
        with patch("specify_cli.authentication.azure_devops.subprocess.run", return_value=result):
            assert AzureDevOpsAuth().resolve_token(entry) == "cli-acquired-token"

    def test_resolve_token_azure_cli_failure_returns_none(self):
        """azure-cli returns None when az CLI fails."""
        from unittest.mock import patch, MagicMock
        entry = AuthConfigEntry(
            hosts=("dev.azure.com",), provider="azure-devops", auth="azure-cli",
        )
        result = MagicMock()
        result.returncode = 1
        result.stdout = ""
        with patch("specify_cli.authentication.azure_devops.subprocess.run", return_value=result):
            assert AzureDevOpsAuth().resolve_token(entry) is None

    def test_resolve_token_azure_cli_not_installed_returns_none(self):
        """azure-cli returns None when az is not installed."""
        from unittest.mock import patch
        entry = AuthConfigEntry(
            hosts=("dev.azure.com",), provider="azure-devops", auth="azure-cli",
        )
        with patch("specify_cli.authentication.azure_devops.subprocess.run", side_effect=OSError("not found")):
            assert AzureDevOpsAuth().resolve_token(entry) is None

    def test_resolve_token_azure_ad_success(self, monkeypatch):
        """azure-ad acquires token via OAuth2 client credentials."""
        from unittest.mock import patch, MagicMock
        monkeypatch.setenv("MY_SECRET", "secret-value")
        entry = AuthConfigEntry(
            hosts=("dev.azure.com",), provider="azure-devops", auth="azure-ad",
            tenant_id="tid", client_id="cid", client_secret_env="MY_SECRET",
        )
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"access_token": "ad-acquired-token"}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            assert AzureDevOpsAuth().resolve_token(entry) == "ad-acquired-token"

    def test_resolve_token_azure_ad_missing_secret_returns_none(self, monkeypatch):
        """azure-ad returns None when client secret env var is missing."""
        monkeypatch.delenv("MY_SECRET", raising=False)
        entry = AuthConfigEntry(
            hosts=("dev.azure.com",), provider="azure-devops", auth="azure-ad",
            tenant_id="tid", client_id="cid", client_secret_env="MY_SECRET",
        )
        assert AzureDevOpsAuth().resolve_token(entry) is None

    def test_resolve_token_azure_ad_network_error_returns_none(self, monkeypatch):
        """azure-ad returns None on network errors."""
        import urllib.error
        from unittest.mock import patch
        monkeypatch.setenv("MY_SECRET", "secret-value")
        entry = AuthConfigEntry(
            hosts=("dev.azure.com",), provider="azure-devops", auth="azure-ad",
            tenant_id="tid", client_id="cid", client_secret_env="MY_SECRET",
        )
        with patch("urllib.request.urlopen",
                    side_effect=urllib.error.URLError("connection refused")):
            assert AzureDevOpsAuth().resolve_token(entry) is None


# ---------------------------------------------------------------------------
# open_url / build_request — positive tests
# ---------------------------------------------------------------------------


class TestAuthenticatedHttp:
    def _set_config(self, monkeypatch, entries):
        from specify_cli.authentication import http as _mod
        monkeypatch.setattr(_mod, "_config_override", entries)

    def test_build_request_attaches_auth_for_matching_host(self, monkeypatch):
        from specify_cli.authentication.http import build_request
        monkeypatch.setenv("GH_TOKEN", "my-token")
        self._set_config(monkeypatch, [_github_entry()])
        req = build_request("https://github.com/org/repo")
        assert req.get_header("Authorization") == "Bearer my-token"

    def test_build_request_no_auth_for_non_matching_host(self, monkeypatch):
        from specify_cli.authentication.http import build_request
        monkeypatch.setenv("GH_TOKEN", "my-token")
        self._set_config(monkeypatch, [_github_entry()])
        req = build_request("https://evil.example.com/file")
        assert "Authorization" not in req.headers

    def test_build_request_no_auth_when_no_config(self, monkeypatch):
        from specify_cli.authentication.http import build_request
        self._set_config(monkeypatch, [])
        req = build_request("https://github.com/org/repo")
        assert "Authorization" not in req.headers

    def test_build_request_extra_headers(self, monkeypatch):
        from specify_cli.authentication.http import build_request
        monkeypatch.setenv("GH_TOKEN", "my-token")
        self._set_config(monkeypatch, [_github_entry()])
        req = build_request("https://github.com/api", extra_headers={"Accept": "application/json"})
        assert req.get_header("Accept") == "application/json"
        assert req.get_header("Authorization") == "Bearer my-token"

    def test_open_url_attaches_auth_for_matching_host(self, monkeypatch):
        from unittest.mock import MagicMock, patch
        from specify_cli.authentication.http import open_url
        monkeypatch.setenv("GH_TOKEN", "my-token")
        self._set_config(monkeypatch, [_github_entry()])
        captured = {}
        mock_opener = MagicMock()

        def fake_open(req, timeout=None):
            captured["req"] = req
            resp = MagicMock()
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        mock_opener.open.side_effect = fake_open
        with patch(
            "specify_cli.authentication.http.urllib.request.build_opener",
            return_value=mock_opener,
        ):
            open_url("https://github.com/org/repo/catalog.json")
        assert captured["req"].get_header("Authorization") == "Bearer my-token"

    def test_open_url_no_auth_for_non_matching_host(self, monkeypatch):
        from unittest.mock import MagicMock, patch
        from specify_cli.authentication.http import open_url
        monkeypatch.setenv("GH_TOKEN", "my-token")
        self._set_config(monkeypatch, [_github_entry()])
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["req"] = req
            resp = MagicMock()
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            side_effect=fake_urlopen,
        ):
            open_url("https://example.com/file.json")
        assert captured["req"].get_header("Authorization") is None

    def test_open_url_no_auth_when_no_config(self, monkeypatch):
        from unittest.mock import MagicMock, patch
        from specify_cli.authentication.http import open_url
        self._set_config(monkeypatch, [])
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["req"] = req
            resp = MagicMock()
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            side_effect=fake_urlopen,
        ):
            open_url("https://github.com/org/repo")
        assert captured["req"].get_header("Authorization") is None

    def test_open_url_falls_through_on_401(self, monkeypatch):
        import urllib.error
        from unittest.mock import MagicMock, patch
        from specify_cli.authentication.http import open_url
        monkeypatch.setenv("GH_TOKEN", "bad-token")
        self._set_config(monkeypatch, [_github_entry()])
        call_count = 0

        def fake_side_effect(req, timeout=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise urllib.error.HTTPError("url", 401, "Unauthorized", {}, None)
            resp = MagicMock()
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        mock_opener = MagicMock()
        mock_opener.open.side_effect = fake_side_effect
        with patch(
            "specify_cli.authentication.http.urllib.request.build_opener",
            return_value=mock_opener,
        ), patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            side_effect=fake_side_effect,
        ):
            open_url("https://github.com/org/repo")
        assert call_count == 2


# ---------------------------------------------------------------------------
# open_url — negative tests
# ---------------------------------------------------------------------------


class TestAuthenticatedHttpNegative:
    def _set_config(self, monkeypatch, entries):
        from specify_cli.authentication import http as _mod
        monkeypatch.setattr(_mod, "_config_override", entries)

    def test_500_raises_immediately(self, monkeypatch):
        import urllib.error
        from unittest.mock import MagicMock, patch
        from specify_cli.authentication.http import open_url
        monkeypatch.setenv("GH_TOKEN", "tok")
        self._set_config(monkeypatch, [_github_entry()])
        mock_opener = MagicMock()
        mock_opener.open.side_effect = urllib.error.HTTPError("url", 500, "ISE", {}, None)
        with patch("specify_cli.authentication.http.urllib.request.build_opener", return_value=mock_opener):
            with pytest.raises(urllib.error.HTTPError, match="500"):
                open_url("https://github.com/org/repo")

    def test_404_raises_immediately(self, monkeypatch):
        import urllib.error
        from unittest.mock import MagicMock, patch
        from specify_cli.authentication.http import open_url
        monkeypatch.setenv("GH_TOKEN", "tok")
        self._set_config(monkeypatch, [_github_entry()])
        mock_opener = MagicMock()
        mock_opener.open.side_effect = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
        with patch("specify_cli.authentication.http.urllib.request.build_opener", return_value=mock_opener):
            with pytest.raises(urllib.error.HTTPError, match="404"):
                open_url("https://github.com/org/repo")

    def test_urlerror_propagates(self, monkeypatch):
        import urllib.error
        from unittest.mock import patch
        from specify_cli.authentication.http import open_url
        self._set_config(monkeypatch, [])
        with patch("specify_cli.authentication.http.urllib.request.urlopen",
                    side_effect=urllib.error.URLError("refused")):
            with pytest.raises(urllib.error.URLError):
                open_url("https://example.com/file")

    def test_timeout_propagates(self, monkeypatch):
        import socket
        from unittest.mock import patch
        from specify_cli.authentication.http import open_url
        self._set_config(monkeypatch, [])
        with patch("specify_cli.authentication.http.urllib.request.urlopen",
                    side_effect=socket.timeout("timed out")):
            with pytest.raises(socket.timeout):
                open_url("https://example.com/file")


# ---------------------------------------------------------------------------
# _load_config caching
# ---------------------------------------------------------------------------


class TestLoadConfigCaching:
    def test_config_cached_after_first_load(self, monkeypatch):
        """_load_config() should call load_auth_config only once per process."""
        from unittest.mock import patch
        from specify_cli.authentication import http as _mod
        # Allow the real load path (no override)
        monkeypatch.setattr(_mod, "_config_override", None)
        monkeypatch.setattr(_mod, "_config_cache", None)

        entry = _github_entry()
        call_count = 0

        def fake_load(path=None):
            nonlocal call_count
            call_count += 1
            return [entry]

        with patch.object(_mod, "load_auth_config", side_effect=fake_load):
            _mod._load_config()
            _mod._load_config()
            _mod._load_config()

        assert call_count == 1

    def test_cache_bypassed_by_override(self, monkeypatch):
        """When _config_override is set, the cache is ignored entirely."""
        from specify_cli.authentication import http as _mod
        sentinel = [_github_entry()]
        monkeypatch.setattr(_mod, "_config_override", sentinel)
        monkeypatch.setattr(_mod, "_config_cache", None)

        result = _mod._load_config()
        assert result is sentinel
        # Cache must not have been populated when override is active
        assert _mod._config_cache is None

    def test_failed_load_warns_once_and_caches_empty(self, monkeypatch):
        """A bad auth.json emits exactly one warning and subsequent calls use cache."""
        from unittest.mock import patch
        from specify_cli.authentication import http as _mod
        import warnings as _warnings
        monkeypatch.setattr(_mod, "_config_override", None)
        monkeypatch.setattr(_mod, "_config_cache", None)

        call_count = 0

        def fail_load(path=None):
            nonlocal call_count
            call_count += 1
            raise ValueError("bad config")

        with patch.object(_mod, "load_auth_config", side_effect=fail_load):
            with _warnings.catch_warnings(record=True) as w:
                _warnings.simplefilter("always")
                result1 = _mod._load_config()
                result2 = _mod._load_config()
                result3 = _mod._load_config()

        user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
        assert len(user_warnings) == 1, "Expected exactly one warning"
        # Loader called only once — subsequent calls used cache
        assert call_count == 1
        # All calls returned the cached empty list
        assert result1 == result2 == result3 == []


# ---------------------------------------------------------------------------
# Redirect stripping
# ---------------------------------------------------------------------------


class TestRedirectStripping:
    def test_redirect_within_hosts_preserves_auth(self):
        from specify_cli.authentication.http import _StripAuthOnRedirect
        from urllib.request import Request
        import io
        handler = _StripAuthOnRedirect(("github.com", "codeload.github.com"))
        req = Request("https://github.com/org/repo", headers={"Authorization": "Bearer tok"})
        new_req = handler.redirect_request(req, io.BytesIO(b""), 302, "Found", {},
                                           "https://codeload.github.com/org/repo/zip")
        assert new_req is not None
        auth = new_req.get_header("Authorization") or new_req.unredirected_hdrs.get("Authorization")
        assert auth == "Bearer tok"

    def test_redirect_outside_hosts_strips_auth(self):
        from specify_cli.authentication.http import _StripAuthOnRedirect
        from urllib.request import Request
        import io
        handler = _StripAuthOnRedirect(("github.com",))
        req = Request("https://github.com/org/repo", headers={"Authorization": "Bearer tok"})
        new_req = handler.redirect_request(req, io.BytesIO(b""), 302, "Found", {},
                                           "https://objects.githubusercontent.com/asset")
        assert new_req is not None
        assert new_req.headers.get("Authorization") is None
        assert new_req.unredirected_hdrs.get("Authorization") is None

    def test_multi_hop_redirect_within_hosts_preserves_auth(self):
        """Auth survives a multi-hop redirect chain within allowed hosts."""
        from specify_cli.authentication.http import _StripAuthOnRedirect
        from urllib.request import Request
        import io
        hosts = ("github.com", "codeload.github.com", "objects-origin.githubusercontent.com")
        handler = _StripAuthOnRedirect(hosts)

        # First hop: github.com → codeload.github.com
        req1 = Request("https://github.com/org/repo", headers={"Authorization": "Bearer tok"})
        req2 = handler.redirect_request(req1, io.BytesIO(b""), 302, "Found", {},
                                        "https://codeload.github.com/org/repo/zip")
        assert req2 is not None
        auth2 = req2.get_header("Authorization") or req2.unredirected_hdrs.get("Authorization")
        assert auth2 == "Bearer tok"

        # Second hop: codeload.github.com → objects-origin.githubusercontent.com
        req3 = handler.redirect_request(req2, io.BytesIO(b""), 302, "Found", {},
                                        "https://objects-origin.githubusercontent.com/asset")
        assert req3 is not None
        auth3 = req3.get_header("Authorization") or req3.unredirected_hdrs.get("Authorization")
        assert auth3 == "Bearer tok"


# ---------------------------------------------------------------------------
# _fetch_latest_release_tag delegation
# ---------------------------------------------------------------------------


class TestFetchLatestReleaseTagDelegation:
    def _set_config(self, monkeypatch, entries):
        from specify_cli.authentication import http as _mod
        monkeypatch.setattr(_mod, "_config_override", entries)

    def _capture_request(self):
        import json as _json
        from unittest.mock import MagicMock

        captured: dict = {}

        def side_effect(req, timeout=None):
            captured["request"] = req
            body = _json.dumps({"tag_name": "v9.9.9"}).encode()
            resp = MagicMock()
            resp.read.return_value = body
            cm = MagicMock()
            cm.__enter__.return_value = resp
            cm.__exit__.return_value = False
            return cm

        return captured, side_effect

    def test_gh_token_forwarded_when_configured(self, monkeypatch):
        from unittest.mock import MagicMock, patch
        from specify_cli._version import _fetch_latest_release_tag
        monkeypatch.setenv("GH_TOKEN", "forwarded-sentinel")
        self._set_config(monkeypatch, [_github_entry()])
        captured, side_effect = self._capture_request()
        mock_opener = MagicMock()
        mock_opener.open.side_effect = side_effect
        with patch(
            "specify_cli.authentication.http.urllib.request.build_opener",
            return_value=mock_opener,
        ):
            _fetch_latest_release_tag()
        assert captured["request"].get_header("Authorization") == "Bearer forwarded-sentinel"

    def test_no_config_means_no_auth(self, monkeypatch):
        from unittest.mock import patch
        from specify_cli._version import _fetch_latest_release_tag
        self._set_config(monkeypatch, [])
        captured, side_effect = self._capture_request()
        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=side_effect):
            _fetch_latest_release_tag()
        assert captured["request"].get_header("Authorization") is None

    def test_accept_header_present(self, monkeypatch):
        from unittest.mock import patch
        from specify_cli._version import _fetch_latest_release_tag
        self._set_config(monkeypatch, [])
        captured, side_effect = self._capture_request()
        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=side_effect):
            _fetch_latest_release_tag()
        assert captured["request"].get_header("Accept") == "application/vnd.github+json"
