"""Tests for TestIntegrationSearch."""

from __future__ import annotations

import json  # noqa: F401
import os  # noqa: F401

import pytest  # noqa: F401

from tests.specify_cli.integrations._catalog_helpers import (
    IntegrationCatalogCliTestBase,
    _normalize_cli_output,
)

class TestIntegrationSearch(IntegrationCatalogCliTestBase):
    def test_search_requires_specify_project(self, tmp_path):
        project = tmp_path / "bare"
        project.mkdir()
        result = self._invoke(["integration", "search"], project)
        assert result.exit_code == 1
        assert "Not a Spec Kit project" in result.output

    def test_search_lists_all(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch)
        result = self._invoke(["integration", "search"], project)
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 0, result.output
        assert "Found 2 integration(s)" in result.output
        assert "acme-coder" in result.output
        assert "stellar-agent" in result.output
        assert "specify integration install stellar-agent" not in normalized_output
        assert "Only built-in integration IDs can be installed" in normalized_output

    def test_search_validates_integration_json_before_catalog_lookup(
        self, tmp_path, monkeypatch
    ):
        project = self._make_project(tmp_path)
        (project / ".specify" / "integration.json").write_text(
            "{bad json\n", encoding="utf-8"
        )

        from specify_cli.integrations import IntegrationCatalog

        def fail_search(self, **kwargs):
            raise AssertionError("catalog search should not be called")

        monkeypatch.setattr(IntegrationCatalog, "search", fail_search)

        result = self._invoke(["integration", "search"], project)
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 1
        assert "contains invalid JSON" in normalized_output
        assert "integration.json" in normalized_output

    def test_search_rejects_non_utf8_integration_json_before_catalog_lookup(
        self, tmp_path, monkeypatch
    ):
        """A non-UTF8 ``integration.json`` must surface a clear error and
        avoid falling through to the catalog lookup, mirroring the malformed-JSON
        case but for the ``UnicodeDecodeError`` branch in ``_read_integration_json``."""
        project = self._make_project(tmp_path)
        # 0xFF is invalid as the leading byte of any UTF-8 sequence, so
        # ``Path.read_text(encoding="utf-8")`` raises ``UnicodeDecodeError``.
        (project / ".specify" / "integration.json").write_bytes(b"\xff\xfe\x00\x00")

        from specify_cli.integrations import IntegrationCatalog

        def fail_search(self, **kwargs):
            raise AssertionError("catalog search should not be called")

        monkeypatch.setattr(IntegrationCatalog, "search", fail_search)

        result = self._invoke(["integration", "search"], project)
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 1
        assert "not valid UTF-8" in normalized_output
        assert "integration.json" in normalized_output

    def test_search_filters_by_tag(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch)
        result = self._invoke(["integration", "search", "--tag", "acme"], project)
        assert result.exit_code == 0, result.output
        assert "Found 1 integration(s)" in result.output
        assert "acme-coder" in result.output
        assert "stellar-agent" not in result.output

    def test_search_filters_by_author(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch)
        result = self._invoke(
            ["integration", "search", "--author", "stellar-labs"], project
        )
        assert result.exit_code == 0, result.output
        assert "Found 1 integration(s)" in result.output
        assert "stellar-agent" in result.output

    def test_search_no_match_hint(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch)
        result = self._invoke(
            ["integration", "search", "--tag", "nope"], project
        )
        assert result.exit_code == 0, result.output
        assert "No integrations found" in result.output
        assert "specify integration search" in result.output

    def test_search_marks_discovery_only_entry(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch)
        result = self._invoke(["integration", "search", "acme"], project)
        assert result.exit_code == 0, result.output
        # acme-coder is flagged _install_allowed=False, so we should warn
        assert "Not directly installable" in result.output

    def test_search_escapes_catalog_markup(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch, integrations=[self.MARKUP_INTEGRATION])

        result = self._invoke(["integration", "search"], project)

        assert result.exit_code == 0, result.output
        output = _normalize_cli_output(result.output)
        for value in (
            self.MARKUP_INTEGRATION["id"],
            self.MARKUP_INTEGRATION["name"],
            self.MARKUP_INTEGRATION["version"],
            self.MARKUP_INTEGRATION["description"],
            self.MARKUP_INTEGRATION["author"],
            self.MARKUP_INTEGRATION["tags"][0],
            self.MARKUP_INTEGRATION["_catalog_name"],
        ):
            assert value in output

    def test_search_local_config_error_shows_local_config_tip(
        self, tmp_path, monkeypatch
    ):
        """`integration search` must point at .specify/integration-catalogs.yml
        for local-config errors (not the generic 'temporarily unavailable')."""
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)
        # Corrupt YAML to drive _load_catalog_config -> IntegrationValidationError.
        cfg = project / ".specify" / "integration-catalogs.yml"
        invalid_yaml = "catalogs:\n  - [bad\n"
        cfg.write_text(invalid_yaml, encoding="utf-8")

        result = self._invoke(["integration", "search"], project)
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 1, result.output
        assert "configuration file path shown above" in normalized_output
        assert ".specify/integration-catalogs.yml" in normalized_output
        assert "~/.specify/integration-catalogs.yml" in normalized_output
        assert "temporarily unavailable" not in normalized_output

    def test_search_invalid_env_catalog_url_shows_env_tip(
        self, tmp_path, monkeypatch
    ):
        project = self._make_project(tmp_path)
        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_CATALOG_URL",
            "http://insecure.example.com/catalog.json",
        )

        result = self._invoke(["integration", "search"], project)
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 1, result.output
        assert "SPECKIT_INTEGRATION_CATALOG_URL environment variable" in normalized_output
        assert "unset it to use the configured catalog files" in normalized_output
        assert ".specify/integration-catalogs.yml" in normalized_output
        assert "~/.specify/integration-catalogs.yml" in normalized_output
        assert "temporarily unavailable" not in normalized_output

    def test_search_whitespace_env_catalog_url_uses_generic_catalog_tip(
        self, tmp_path, monkeypatch
    ):
        project = self._make_project(tmp_path)
        monkeypatch.setenv("SPECKIT_INTEGRATION_CATALOG_URL", "   ")

        from specify_cli.integrations import (
            IntegrationCatalog,
            IntegrationCatalogError,
        )

        def fail_search(self, **kwargs):
            raise IntegrationCatalogError("catalog offline")

        monkeypatch.setattr(IntegrationCatalog, "search", fail_search)

        result = self._invoke(["integration", "search"], project)
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 1, result.output
        assert "temporarily unavailable" in normalized_output
        assert (
            "SPECKIT_INTEGRATION_CATALOG_URL environment variable"
            not in normalized_output
        )
