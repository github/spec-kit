"""Tests for ``specify extension info``.

Mirrors ``specify_cli.extensions.command_info``.
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import (
    ExtensionManager,
)


class TestExtensionInfoRendering:
    """Rendering tests for ``specify extension info``."""

    @pytest.mark.parametrize(
        "downloads",
        [
            "1500",          # plain string: crashed the ``:,`` format
            "[/red]foo",      # unbalanced closing tag: raises MarkupError unescaped
            "[bold]x[/bold]",  # balanced tags: would silently restyle the output
        ],
    )
    def test_info_renders_non_numeric_downloads(self, downloads):
        """A non-numeric ``downloads`` from an untrusted catalog must not crash the
        info renderer — neither with 'Cannot specify ',' with 's'' (the ``:,``
        format) nor with a Rich MarkupError (the joined stats are markup)."""
        from specify_cli.extensions._commands import _print_extension_info

        manager = MagicMock()
        manager.registry.is_installed.return_value = False
        ext_info = {
            "name": "Jira", "id": "jira", "version": "1.0.0",
            "description": "desc", "downloads": downloads,  # from catalog JSON
        }
        # Must not raise ValueError or rich.errors.MarkupError.
        _print_extension_info(ext_info, manager)

    def test_info_renders_markup_bearing_stars(self):
        """``stars`` sits in the same joined stats string as ``downloads`` and is
        equally catalog-controlled, so it must be escaped too."""
        from specify_cli.extensions._commands import _print_extension_info

        manager = MagicMock()
        manager.registry.is_installed.return_value = False
        ext_info = {
            "name": "Jira", "id": "jira", "version": "1.0.0",
            "description": "desc", "stars": "[/red]x",
        }
        _print_extension_info(ext_info, manager)  # must not raise MarkupError


class TestExtensionInfoCLI:
    """CLI tests for ``specify extension info``."""

    def test_info_discovery_only_shows_candidate_archive_url(self, tmp_path):
        """For a discovery-only entry that carries a ``download_url``, ``info``
        surfaces the candidate archive URL (flagged for vetting) and the vetted
        ``--from`` install guidance, so users have a CLI path to the URL."""
        from unittest.mock import MagicMock

        runner = CliRunner()

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".specify" / "extensions").mkdir(parents=True)

        archive_url = "https://example.com/acme-thing-1.0.0.zip"
        mock_catalog = MagicMock()
        mock_catalog.get_extension_info.return_value = {
            "id": "acme-thing",
            "name": "Acme Thing",
            "version": "1.0.0",
            "description": "A thing",
            "download_url": archive_url,
            "_install_allowed": False,
            "_catalog_name": "community",
        }
        mock_catalog.search.return_value = []

        with patch("specify_cli.extensions.ExtensionCatalog", return_value=mock_catalog), \
             patch("specify_cli.extensions.ExtensionManager") as mock_mgr, \
             patch.object(Path, "cwd", return_value=project_dir):
            mock_mgr.return_value.registry.is_installed.return_value = False
            result = runner.invoke(
                app,
                ["extension", "info", "acme-thing"],
                catch_exceptions=True,
            )

        output = " ".join(result.output.split())
        assert "discovery-only" in output
        assert f"Candidate archive (vet before installing): {archive_url}" in output
        assert "specify extension add acme-thing --from <archive-url>" in output

    def test_info_discovery_only_without_url_falls_back(self, tmp_path):
        """A discovery-only entry lacking ``download_url`` still gets vetted
        ``--from`` guidance, without claiming a candidate archive it doesn't
        have."""
        from unittest.mock import MagicMock

        runner = CliRunner()

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".specify" / "extensions").mkdir(parents=True)

        mock_catalog = MagicMock()
        mock_catalog.get_extension_info.return_value = {
            "id": "acme-thing",
            "name": "Acme Thing",
            "version": "1.0.0",
            "description": "A thing",
            "_install_allowed": False,
            "_catalog_name": "community",
        }
        mock_catalog.search.return_value = []

        with patch("specify_cli.extensions.ExtensionCatalog", return_value=mock_catalog), \
             patch("specify_cli.extensions.ExtensionManager") as mock_mgr, \
             patch.object(Path, "cwd", return_value=project_dir):
            mock_mgr.return_value.registry.is_installed.return_value = False
            result = runner.invoke(
                app,
                ["extension", "info", "acme-thing"],
                catch_exceptions=True,
            )

        output = " ".join(result.output.split())
        assert "Candidate archive" not in output
        assert "vetted its release archive" in output
        assert "specify extension add acme-thing --from <archive-url>" in output

    def test_info_by_name_tolerates_non_string_catalog_name(self, tmp_path):
        """Display-name resolution must not crash on a non-string catalog name.

        Catalog JSON is user-editable, so ``catalog.search()`` may return an
        entry whose ``name`` is a non-string (e.g. ``name: 123``). The
        display-name filter calls ``.lower()`` on it; without coercion this
        raises ``AttributeError`` and takes down ``extension info``/``add``.
        The entry with the bad name must simply not match, yielding a clean
        "not found" rather than a traceback.
        """
        from unittest.mock import MagicMock

        runner = CliRunner()

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".specify" / "extensions").mkdir(parents=True)

        # Catalog search returns an entry with a non-string name.
        mock_catalog = MagicMock()
        mock_catalog.get_extension_info.return_value = None  # ID lookup fails
        mock_catalog.search.return_value = [
            {
                "id": "acme-thing",
                "name": 123,
                "version": "1.0.0",
                "description": "A thing",
                "_install_allowed": True,
            }
        ]

        with patch("specify_cli.extensions.ExtensionCatalog", return_value=mock_catalog), \
             patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "info", "Some Name"],
                catch_exceptions=True,
            )

        # Must not crash with AttributeError; the bad-named entry just doesn't
        # match, so resolution ends as a clean not-found error exit.
        assert not isinstance(result.exception, AttributeError), (
            f"non-string catalog name crashed resolution: {result.exception!r}"
        )
        assert result.exit_code != 0


def test_forge_extension_info_hyphenates_command_names(
    extension_dir, project_dir, monkeypatch
):
    """`extension info` for an installed extension must show hyphenated
    /speckit-<name> command names on a Forge project, matching the names Forge
    actually registers — the same parity `extension add`'s listing already has.
    """

    from rich.console import Console

    from specify_cli.extensions import _commands

    init_options = project_dir / ".specify" / "init-options.json"
    init_options.write_text(json.dumps({"ai": "forge", "script": "sh"}))

    manager = ExtensionManager(project_dir)
    manager.install_from_directory(
        extension_dir, "1.0.0", register_commands=False
    )

    # Force the "installed locally, not in catalog" branch (the one that prints
    # the local manifest's Commands section) and avoid any network catalog
    # lookup.
    monkeypatch.setattr(
        _commands, "_resolve_catalog_extension", lambda *a, **k: (None, None)
    )

    # Call the handler directly against a plain captured Console. (Driving it
    # through CliRunner reformats output via Rich's live console, which
    # recurses under pytest's captured stdout — unrelated to this code path.)
    buf = io.StringIO()
    original_console = _commands.console
    _commands.console = Console(file=buf, force_terminal=False, width=200)
    old_cwd = os.getcwd()
    try:
        os.chdir(project_dir)
        _commands.extension_info("test-ext")
    except SystemExit:
        pass
    finally:
        os.chdir(old_cwd)
        _commands.console = original_console

    output = buf.getvalue()
    # The Commands section must render the hyphenated form Forge registers,
    # not the manifest's dotted name.
    assert "speckit-test-ext-hello" in output, output
    assert "speckit.test-ext.hello" not in output, output
