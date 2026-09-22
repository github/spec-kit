"""Tests for ``specify extension catalog add``.

Mirrors ``specify_cli.extensions.catalog.command_add``.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import (
    ExtensionCatalog,
    ValidationError,
)
from tests.integrations.test_cli import _normalize_cli_output


class TestExtensionCatalogAddCLI:
    """CLI tests for ``specify extension catalog add``."""

    def test_catalog_add_escapes_url_markup(self, tmp_path):
        """Catalog add should render user-supplied URLs literally."""
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        url = "https://example.com/[red]catalog[/red].json"

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                [
                    "extension",
                    "catalog",
                    "add",
                    url,
                    "--name",
                    "community",
                ],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert f"URL: {url}" in result.output

    def test_catalog_add_escapes_config_saved_path_markup(self, tmp_path):
        """Catalog add's saved-path label should render literally under Rich."""
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        display_path = "project[red]/.specify/extension-catalogs.yml"

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.extensions._commands._display_project_path", return_value=display_path):
            result = runner.invoke(
                app,
                [
                    "extension",
                    "catalog",
                    "add",
                    "https://example.com/catalog.json",
                    "--name",
                    "community",
                ],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert f"Config saved to {display_path}" in result.output

    def test_catalog_add_escapes_config_read_exception_markup(self, tmp_path):
        """Catalog config parse errors can include user-controlled file content."""
        from typer.testing import CliRunner
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        specify_dir = project_dir / ".specify"
        specify_dir.mkdir()
        (specify_dir / "extension-catalogs.yml").write_text("[red]bad[/red]", encoding="utf-8")

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch(
                 "specify_cli.extensions._commands.yaml.safe_load",
                 side_effect=yaml.YAMLError("bad [red]catalog[/red] yaml"),
             ):
            result = runner.invoke(
                app,
                [
                    "extension",
                    "catalog",
                    "add",
                    "https://example.com/catalog.json",
                    "--name",
                    "community",
                ],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert "bad [red]catalog[/red]" in result.output
        assert "yaml" in result.output

    def test_catalog_add_escapes_url_validation_exception_markup(self, tmp_path):
        """URL validation errors may include user-controlled URL text."""
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(
                 ExtensionCatalog,
                 "_validate_catalog_url",
                 side_effect=ValidationError("bad [red]url[/red]"),
             ):
            result = runner.invoke(
                app,
                [
                    "extension",
                    "catalog",
                    "add",
                    "https://example.com/[red]catalog[/red].json",
                    "--name",
                    "community",
                ],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert "bad [red]url[/red]" in result.output

class TestExtensionCatalogAddIntegrationCLI:
    """Integration coverage for the extension catalog command."""

    def _make_project(self, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        return project

    def _invoke(self, argv, cwd):

        runner = CliRunner()
        old = os.getcwd()
        try:
            os.chdir(cwd)
            return runner.invoke(app, argv, catch_exceptions=False)
        finally:
            os.chdir(old)

    def test_extension_catalog_add_rejects_non_mapping_config_root(self, tmp_path):
        project = self._make_project(tmp_path)
        cfg_path = project / ".specify" / "extension-catalogs.yml"
        cfg_path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

        result = self._invoke([
            "extension", "catalog", "add",
            "https://example.com/extension-catalog.yml",
            "--name", "demo-extensions",
        ], project)

        assert result.exit_code == 1, result.output
        output = _normalize_cli_output(result.output)
        assert "Invalid catalog config .specify/extension-catalogs.yml" in output
        assert "expected a YAML mapping at the root" in output
        assert "AttributeError" not in output

    def test_extension_catalog_add_escapes_catalog_name_markup(self, tmp_path):
        project = self._make_project(tmp_path)
        catalog_name = "[red]demo[/red]"

        result = self._invoke([
            "extension", "catalog", "add",
            "https://example.com/extension-catalog.yml",
            "--name", catalog_name,
        ], project)

        assert result.exit_code == 0, result.output
        output = _normalize_cli_output(result.output)
        assert f"Added catalog '{catalog_name}'" in output
