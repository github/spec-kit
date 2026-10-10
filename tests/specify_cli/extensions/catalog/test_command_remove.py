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

    def test_extension_catalog_remove_final_entry_restores_defaults(
        self, tmp_path, monkeypatch
    ):
        """The loader rejects an empty ``catalogs`` list, so removing the last
        entry must not leave one behind for follow-up commands to trip on."""
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_CATALOG_URL", raising=False)

        add = self._invoke(
            [
                "extension",
                "catalog",
                "add",
                "https://only.example.com/catalog.json",
                "--name",
                "only",
            ],
            project,
        )
        assert add.exit_code == 0, add.output

        remove = self._invoke(["extension", "catalog", "remove", "only"], project)
        assert remove.exit_code == 0, remove.output
        assert "Built-in defaults will be used" in _normalize_cli_output(remove.output)

        listing = self._invoke(["extension", "catalog", "list"], project)
        assert listing.exit_code == 0, listing.output
        output = _normalize_cli_output(listing.output)
        assert "default (priority 1)" in output
        assert "community (priority 2)" in output
        assert "Using built-in default catalog stack" in output
        assert not (project / ".specify" / "extension-catalogs.yml").exists()

    def test_extension_catalog_remove_keeps_config_with_remaining_entries(
        self, tmp_path
    ):
        project = self._make_project(tmp_path)
        keep = {
            "name": "keep",
            "url": "https://keep.example.com/catalog.json",
            "priority": 20,
            "install_allowed": False,
            "description": "",
        }
        cfg_path = project / ".specify" / "extension-catalogs.yml"
        cfg_path.write_text(
            yaml.safe_dump(
                {
                    "catalogs": [
                        {
                            "name": "drop",
                            "url": "https://drop.example.com/catalog.json",
                            "priority": 10,
                            "install_allowed": False,
                            "description": "",
                        },
                        keep,
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        result = self._invoke(["extension", "catalog", "remove", "drop"], project)

        assert result.exit_code == 0, result.output
        assert "No catalogs remain" not in _normalize_cli_output(result.output)
        assert yaml.safe_load(cfg_path.read_text(encoding="utf-8")) == {
            "catalogs": [keep]
        }
