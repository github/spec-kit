"""Tests for ``specify extension catalog remove``.

Mirrors ``specify_cli.extensions.catalog.command_remove``.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import typer
import yaml

from tests.integrations.test_cli import _normalize_cli_output


class TestExtensionCatalogRemoveValidation:
    """Reject malformed entries before changing the user's catalog config."""

    @pytest.mark.parametrize("invalid_entry", ["unfinished-entry", 0, False, None, []])
    @pytest.mark.parametrize("invalid_index", [0, 1])
    @pytest.mark.parametrize("target", ["keep", "does-not-exist"])
    def test_malformed_entries_preserve_config(
        self, tmp_path, monkeypatch, capsys, invalid_entry, invalid_index, target
    ):
        from specify_cli.extensions import _commands
        from specify_cli.extensions.catalog.command_remove import catalog_remove

        (tmp_path / ".specify").mkdir()
        config_path = tmp_path / ".specify" / "extension-catalogs.yml"
        entries = [{"name": "keep", "url": "https://example.com/team.json"}]
        entries.insert(invalid_index, invalid_entry)
        original = (
            "# Local settings: café\n"
            + yaml.safe_dump({"catalogs": entries, "metadata": "keep me"})
        ).replace("\n", "\r\n").encode("utf-8")
        config_path.write_bytes(original)
        monkeypatch.setattr(_commands, "_require_specify_project", lambda: tmp_path)

        with pytest.raises(typer.Exit) as exc_info:
            catalog_remove(target)

        assert exc_info.value.exit_code == 1
        assert config_path.read_bytes() == original
        output = _normalize_cli_output(capsys.readouterr().out)
        assert f"Invalid catalog entry at index {invalid_index}" in output
        assert f"expected a mapping, got {type(invalid_entry).__name__}" in output
        assert "Removed catalog" not in output


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

    @pytest.mark.parametrize("target", ["keep", "does-not-exist"])
    def test_remove_malformed_config_in_initialized_project(
        self, tmp_path, target
    ):
        """A real initialized project keeps all config bytes on rejection."""
        project = tmp_path / "initialized"
        project.mkdir()
        initialized = self._invoke(
            [
                "init", "--here", "--integration", "codex",
                "--ignore-agent-tools", "--non-interactive", "--script", "py",
            ],
            project,
        )
        assert initialized.exit_code == 0, initialized.output
        config_path = project / ".specify" / "extension-catalogs.yml"
        original = (
            "# Local settings: café\r\n"
            "catalogs:\r\n"
            "  - name: keep\r\n"
            "    url: https://example.com/team.json\r\n"
            "  - https://example.com/private.json\r\n"
            "metadata: keep me\r\n"
        ).encode("utf-8")
        config_path.write_bytes(original)

        result = self._invoke(["extension", "catalog", "remove", target], project)

        assert result.exit_code == 1, result.output
        assert config_path.read_bytes() == original
        output = _normalize_cli_output(result.output)
        assert "Invalid catalog entry at index 1: expected a mapping, got str" in output
        assert "Removed catalog" not in output

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
        assert (
            "Project catalog override removed; user configuration or built-in "
            "defaults will be used." in _normalize_cli_output(remove.output)
        )

        listing = self._invoke(["extension", "catalog", "list"], project)
        assert listing.exit_code == 0, listing.output
        output = _normalize_cli_output(listing.output)
        assert "default (priority 1)" in output
        assert "community (priority 2)" in output
        assert "Using built-in default catalog stack" in output
        assert not (project / ".specify" / "extension-catalogs.yml").exists()

    def test_extension_catalog_remove_final_entry_falls_back_to_user_config(
        self, tmp_path, monkeypatch
    ):
        project = self._make_project(tmp_path)
        home = tmp_path / "home"
        (home / ".specify").mkdir(parents=True)
        (home / ".specify" / "extension-catalogs.yml").write_text(
            yaml.safe_dump(
                {
                    "catalogs": [
                        {
                            "name": "user-catalog",
                            "url": "https://user.example.com/catalog.json",
                            "priority": 5,
                            "install_allowed": True,
                            "description": "",
                        }
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("USERPROFILE", str(home))
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

        listing = self._invoke(["extension", "catalog", "list"], project)
        assert listing.exit_code == 0, listing.output
        output = _normalize_cli_output(listing.output)
        assert "user-catalog (priority 5)" in output
        assert "Config: ~/.specify/extension-catalogs.yml" in output
        assert "only (priority" not in output
        assert "default (priority 1)" not in output

    def test_extension_catalog_remove_final_entry_notes_env_catalog_precedence(
        self, tmp_path, monkeypatch
    ):
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.setenv("SPECKIT_CATALOG_URL", "https://env.example.com/catalog.json")

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
        output = _normalize_cli_output(remove.output)
        assert (
            "Project catalog override removed; the SPECKIT_CATALOG_URL environment "
            "variable still takes precedence." in output
        )
        assert "built-in defaults will be used" not in output

        listing = self._invoke(["extension", "catalog", "list"], project)
        assert listing.exit_code == 0, listing.output
        output = _normalize_cli_output(listing.output)
        assert "https://env.example.com/catalog.json" in output
        assert "Catalog configured via SPECKIT_CATALOG_URL environment variable." in output

    def test_extension_catalog_remove_final_entry_reports_unlink_failure(
        self, tmp_path, monkeypatch
    ):
        project = self._make_project(tmp_path)
        cfg_path = project / ".specify" / "extension-catalogs.yml"
        cfg_path.write_text(
            yaml.safe_dump(
                {
                    "catalogs": [
                        {
                            "name": "only",
                            "url": "https://only.example.com/catalog.json",
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
        before = cfg_path.read_text(encoding="utf-8")

        def fail_unlink(self, *args, **kwargs):
            raise OSError("simulated unlink failure")

        monkeypatch.setattr(Path, "unlink", fail_unlink)
        result = self._invoke(["extension", "catalog", "remove", "only"], project)

        assert result.exit_code == 1, result.output
        output = _normalize_cli_output(result.output)
        assert (
            "Failed to delete .specify/extension-catalogs.yml: simulated unlink failure"
            in output
        )
        assert "Removed catalog" not in output
        assert cfg_path.read_text(encoding="utf-8") == before

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
        assert "Project catalog override removed" not in _normalize_cli_output(
            result.output
        )
        assert yaml.safe_load(cfg_path.read_text(encoding="utf-8")) == {
            "catalogs": [keep]
        }
