"""Tests for TestIntegrationInfo."""

from __future__ import annotations

import json  # noqa: F401
import os  # noqa: F401

import pytest  # noqa: F401

from tests.specify_cli.integrations._catalog_helpers import (
    IntegrationCatalogCliTestBase,
    _normalize_cli_output,
)

class TestIntegrationInfo(IntegrationCatalogCliTestBase):
    def test_info_found(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch)
        result = self._invoke(
            ["integration", "info", "stellar-agent"], project
        )
        assert result.exit_code == 0, result.output
        assert "Stellar Agent" in result.output
        assert "stellar-agent" in result.output
        assert "v1.3.0" in result.output

    def test_info_not_found(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch)
        result = self._invoke(
            ["integration", "info", "does-not-exist"], project
        )
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_info_not_found_escapes_query_markup(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch)
        integration_id = "[red]does-not-exist[/red]"

        result = self._invoke(
            ["integration", "info", integration_id],
            project,
        )

        assert result.exit_code == 1
        assert integration_id in _normalize_cli_output(result.output)

    def test_info_builtin_not_in_catalog(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        # Empty catalog, but copilot is a registered built-in.
        self._patch_catalog(monkeypatch, integrations=[])
        result = self._invoke(["integration", "info", "copilot"], project)
        assert result.exit_code == 0, result.output
        assert "Built-in integration" in result.output

    def test_info_escapes_catalog_markup(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch, integrations=[self.MARKUP_INTEGRATION])

        result = self._invoke(
            ["integration", "info", self.MARKUP_INTEGRATION["id"]],
            project,
        )

        assert result.exit_code == 0, result.output
        output = _normalize_cli_output(result.output)
        for value in (
            self.MARKUP_INTEGRATION["id"],
            self.MARKUP_INTEGRATION["name"],
            self.MARKUP_INTEGRATION["version"],
            self.MARKUP_INTEGRATION["description"],
            self.MARKUP_INTEGRATION["author"],
            self.MARKUP_INTEGRATION["license"],
            self.MARKUP_INTEGRATION["repository"],
            self.MARKUP_INTEGRATION["tags"][0],
            self.MARKUP_INTEGRATION["_catalog_name"],
        ):
            assert value in output

    def test_info_unknown_with_local_config_error_shows_local_config_tip(
        self, tmp_path, monkeypatch
    ):
        """`integration info <unknown>` falls back to the catalog-error branch
        and must show local-config guidance, not 'Try again when online'."""
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)
        cfg = project / ".specify" / "integration-catalogs.yml"
        invalid_yaml = "catalogs:\n  - [bad\n"
        cfg.write_text(invalid_yaml, encoding="utf-8")

        result = self._invoke(
            ["integration", "info", "definitely-not-real"], project
        )
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 1, result.output
        assert "configuration file path shown above" in normalized_output
        assert ".specify/integration-catalogs.yml" in normalized_output
        assert "~/.specify/integration-catalogs.yml" in normalized_output
        assert "Try again when online" not in normalized_output

    def test_info_unknown_with_invalid_env_catalog_url_shows_env_tip(
        self, tmp_path, monkeypatch
    ):
        project = self._make_project(tmp_path)
        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_CATALOG_URL",
            "http://insecure.example.com/catalog.json",
        )

        result = self._invoke(
            ["integration", "info", "definitely-not-real"], project
        )
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 1, result.output
        assert "SPECKIT_INTEGRATION_CATALOG_URL" in normalized_output
        assert "unset it to use the configured catalog files" in normalized_output
        assert "Try again when online" not in normalized_output
