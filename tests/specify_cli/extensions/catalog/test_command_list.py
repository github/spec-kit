"""Tests for ``specify extension catalog list``.

Mirrors ``specify_cli.extensions.catalog.command_list``.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml
from typer.testing import CliRunner

from specify_cli import app


class TestExtensionCatalogListCLI:
    """CLI tests for ``specify extension catalog list``."""

    def test_catalog_list_escapes_config_path_markup(self, tmp_path):
        """Catalog list's config-path label should render literally under Rich."""

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        specify_dir = project_dir / ".specify"
        specify_dir.mkdir()
        (specify_dir / "extension-catalogs.yml").write_text(
            yaml.safe_dump(
                {
                    "catalogs": [
                        {
                            "name": "community",
                            "url": "https://example.com/catalog.json",
                            "priority": 10,
                            "install_allowed": False,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        display_path = "project[red]/.specify/extension-catalogs.yml"

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.extensions._commands._display_project_path", return_value=display_path):
            result = runner.invoke(
                app,
                ["extension", "catalog", "list"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert f"Config: {display_path}" in result.output

    def test_catalog_list_shows_discovery_only_guidance(self, tmp_path):
        """A discovery-only catalog should trigger the trust-model guidance,
        steering users to --from / their own catalog and away from flipping
        install_allowed."""

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        specify_dir = project_dir / ".specify"
        specify_dir.mkdir()
        (specify_dir / "extension-catalogs.yml").write_text(
            yaml.safe_dump(
                {
                    "catalogs": [
                        {
                            "name": "community",
                            "url": "https://example.com/catalog.json",
                            "priority": 10,
                            "install_allowed": False,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "catalog", "list"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        output = " ".join(result.output.split())
        assert "not installable by design" in output
        assert "--from <url>" in output
        assert "Don't flip a discovery-only catalog to install_allowed" in output

    def test_catalog_list_omits_guidance_when_all_installable(self, tmp_path):
        """When every catalog is an install source, the discovery-only guidance
        should not appear."""

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        specify_dir = project_dir / ".specify"
        specify_dir.mkdir()
        (specify_dir / "extension-catalogs.yml").write_text(
            yaml.safe_dump(
                {
                    "catalogs": [
                        {
                            "name": "my-org",
                            "url": "https://example.com/catalog.json",
                            "priority": 10,
                            "install_allowed": True,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "catalog", "list"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert "not installable by design" not in result.output
