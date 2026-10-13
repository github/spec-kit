"""Tests for TestIntegrationCatalogList."""

from __future__ import annotations

import json  # noqa: F401
import os  # noqa: F401

import pytest  # noqa: F401
import yaml

from tests.specify_cli.integrations._catalog_helpers import (
    IntegrationCatalogCliTestBase,
    IntegrationListCatalogTestBase,
    _normalize_cli_output,
)

class TestIntegrationCatalogList(IntegrationCatalogCliTestBase):
    def test_catalog_list_requires_specify_project(self, tmp_path):
        project = tmp_path / "bare"
        project.mkdir()
        result = self._invoke(["integration", "catalog", "list"], project)
        assert result.exit_code == 1
        assert "Not a Spec Kit project" in result.output

    def test_catalog_list_shows_builtin_defaults(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)
        result = self._invoke(["integration", "catalog", "list"], project)
        assert result.exit_code == 0, result.output
        assert "Integration Catalog Sources" in result.output
        assert "No project-level catalog sources configured" in result.output
        assert "Active catalog sources" in result.output
        assert "non-removable" in result.output
        assert "default" in result.output
        assert "community" in result.output
        # Built-in defaults are active, but not removable project entries.
        assert "[0]" not in result.output
        assert "[1]" not in result.output

    def test_catalog_list_normalizes_blank_project_catalog_names(
        self, tmp_path, monkeypatch
    ):
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)
        cfg_path = project / ".specify" / "integration-catalogs.yml"
        cfg_path.write_text(
            yaml.dump(
                {
                    "catalogs": [
                        {
                            "url": "https://null-name.example.com/catalog.json",
                            "name": None,
                        },
                        {
                            "url": "https://blank-name.example.com/catalog.json",
                            "name": "   ",
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )

        result = self._invoke(["integration", "catalog", "list"], project)
        normalized_output = _normalize_cli_output(result.output)

        assert result.exit_code == 0, result.output
        assert "[0] catalog-1" in normalized_output
        assert "[1] catalog-2" in normalized_output
        assert "None" not in normalized_output

    def test_catalog_list_env_override_supersedes_project_config(
        self, tmp_path, monkeypatch
    ):
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_CATALOG_URL",
            "https://env.example.com/catalog.json",
        )
        cfg_path = project / ".specify" / "integration-catalogs.yml"
        cfg_path.write_text(
            yaml.dump(
                {
                    "catalogs": [
                        {
                            "url": "https://project.example.com/catalog.json",
                            "name": "project",
                            "priority": 1,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        result = self._invoke(["integration", "catalog", "list"], project)
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 0, result.output
        assert "SPECKIT_INTEGRATION_CATALOG_URL is set" in normalized_output
        assert "supersedes configured catalog files" in normalized_output
        assert "non-removable" in normalized_output
        assert "https://env.example.com/catalog.json" in normalized_output
        assert "https://project.example.com/catalog.json" not in normalized_output
        assert "[0]" not in normalized_output


class TestIntegrationCatalogListMarkup(IntegrationListCatalogTestBase):
    def test_catalog_list_escapes_rich_markup(self, tmp_path, monkeypatch):
        """User-editable catalog name/url/description must not be parsed as Rich markup."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.integrations import IntegrationCatalog
        runner = CliRunner()
        project = self._init_project(tmp_path)

        configs = [
            {
                "name": "Bracket [Catalog]",
                "url": "https://example.com/[cat].json",
                "description": "desc [with] brackets",
                "install_allowed": True,
            },
        ]
        monkeypatch.setattr(
            IntegrationCatalog,
            "get_project_catalog_configs",
            lambda self: [dict(c) for c in configs],
        )

        old = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "catalog", "list"])
        finally:
            os.chdir(old)

        assert result.exit_code == 0, result.output
        assert "Bracket [Catalog]" in result.output
        assert "https://example.com/[cat].json" in result.output
        assert "desc [with] brackets" in result.output
