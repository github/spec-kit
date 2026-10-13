"""Tests for ``specify extension search``.

Mirrors ``specify_cli.extensions.command_search``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import (
    ExtensionCatalog,
)


class TestExtensionSearchCLI:
    """CLI tests for ``specify extension search``."""

    @pytest.mark.parametrize("downloads", ["1500", "[/red]foo"])
    def test_search_survives_non_numeric_downloads(self, temp_dir, downloads):
        """`specify extension search` must not abort when a catalog entry's
        ``downloads`` is a non-numeric string — not with a raw ValueError from the
        ``:,`` format, nor with a Rich MarkupError from unescaped markup."""
        import yaml as yaml_module

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump(
                {"catalogs": [{
                    "name": "test-catalog",
                    "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                    "priority": 1, "install_allowed": True,
                }]}, f,
            )

        catalog = ExtensionCatalog(project_dir)
        catalog_data = {
            "schema_version": "1.0",
            "extensions": {"jira": {
                "name": "Jira", "id": "jira", "version": "1.0.0",
                "description": "Jira integration", "author": "x",
                "tags": ["jira"], "verified": True,
                "downloads": downloads,  # non-numeric, straight from catalog JSON
            }},
        }
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(json.dumps({
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "catalog_url": "http://test.com",
        }))

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "search"], catch_exceptions=True)
        assert result.exit_code == 0, result.output
        # Rendered literally (escaped), not interpreted as markup or dropped.
        assert f"Downloads: {downloads}" in result.output

    def test_search_and_info_tolerate_non_list_tags(self, temp_dir):
        """A scalar ``tags:`` value must not crash the search/info display.

        ``ExtensionCatalog.search`` guards its tag *filter* with
        ``isinstance(raw_tags, list)``, but the ``extension search`` and
        ``extension info`` display paths only tested truthiness before
        iterating. ``tags: 5`` is truthy and not iterable, so both raised
        ``TypeError: 'int' object is not iterable``.
        """

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        merged = [{
            "id": "jira",
            "name": "Jira",
            "version": "1.0.0",
            "description": "Jira",
            "tags": 5,
        }]

        with patch.object(ExtensionCatalog, "_get_merged_extensions", return_value=merged), \
                patch("specify_cli.extensions._commands._require_specify_project",
                      return_value=project_dir):
            searched = CliRunner().invoke(app, ["extension", "search", "Jira"])
            info = CliRunner().invoke(app, ["extension", "info", "jira"])

        assert searched.exit_code == 0, searched.output
        assert "Jira" in searched.output
        assert "Tags:" not in searched.output

        assert info.exit_code == 0, info.output
        assert "Tags:" not in info.output
