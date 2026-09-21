"""Tests for ``specify extension catalog remove``.

Mirrors ``specify_cli.extensions.catalog.command_remove``.
"""

from __future__ import annotations

import os

import yaml

from tests.integrations.test_cli import _normalize_cli_output


class TestExtensionCatalogRemoveCLI:
    """Integration coverage for the extension catalog command."""

    def _make_project(self, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        return project

    def _invoke(self, argv, cwd):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        old = os.getcwd()
        try:
            os.chdir(cwd)
            return runner.invoke(app, argv, catch_exceptions=False)
        finally:
            os.chdir(old)

    def test_extension_catalog_remove_rejects_non_mapping_config_root(self, tmp_path):
        project = self._make_project(tmp_path)
        cfg_path = project / ".specify" / "extension-catalogs.yml"
        cfg_path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

        result = self._invoke(["extension", "catalog", "remove", "demo"], project)

        assert result.exit_code == 1, result.output
        output = _normalize_cli_output(result.output)
        assert "Invalid catalog config .specify/extension-catalogs.yml" in output
        assert "expected a YAML mapping at the root" in output
        assert "AttributeError" not in output

    def test_extension_catalog_remove_escapes_catalog_name_markup(self, tmp_path):
        project = self._make_project(tmp_path)
        catalog_name = "[red]demo[/red]"
        cfg_path = project / ".specify" / "extension-catalogs.yml"
        cfg_path.write_text(
            yaml.safe_dump(
                {
                    "catalogs": [
                        {
                            "name": catalog_name,
                            "url": "https://example.com/extension-catalog.yml",
                            "priority": 10,
                            "install_allowed": False,
                            "description": "",
                        }
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        result = self._invoke(["extension", "catalog", "remove", catalog_name], project)

        assert result.exit_code == 0, result.output
        output = _normalize_cli_output(result.output)
        assert f"Removed catalog '{catalog_name}'" in output
