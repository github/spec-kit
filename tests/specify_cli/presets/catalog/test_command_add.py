from __future__ import annotations

from pathlib import Path

import pytest
import yaml


class TestPresetCatalogAdd:
    """Test multi-catalog support in PresetCatalog."""

    def test_catalog_add_escapes_rich_markup(self, project_dir):
        """`preset catalog add` must not parse the name/url as Rich markup.

        An unbalanced closing tag raised MarkupError *after* the entry was
        already written to preset-catalogs.yml, so the user saw a traceback
        and no confirmation for a catalog that had in fact been added.
        """
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        name = "[/red]my-catalog"
        url = "https://example.com/[bold]c.json"
        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app, ["preset", "catalog", "add", url, "--name", name]
            )
        assert result.exit_code == 0, result.output
        # Rendered verbatim, not swallowed as markup.
        assert name in result.output
        assert url in result.output
        # Only rendering is escaped: the raw values still round-trip to disk.
        config = yaml.safe_load(
            (project_dir / ".specify" / "preset-catalogs.yml").read_text(
                encoding="utf-8"
            )
        )
        assert config["catalogs"][0]["name"] == name
        assert config["catalogs"][0]["url"] == url

    @pytest.mark.parametrize(
        "args",
        [
            [
                "preset",
                "catalog",
                "add",
                "https://example.com/catalog.json",
                "--name",
                "example",
            ],
            ["preset", "catalog", "remove", "example"],
        ],
    )
    def test_catalog_mutation_rejects_non_mapping_config_root(self, project_dir, args):
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        original = "[]\n"
        config_path.write_text(original, encoding="utf-8")

        with patch.object(Path, "cwd", return_value=project_dir):
            result = CliRunner().invoke(app, args)

        assert result.exit_code == 1
        assert "expected a mapping" in result.output
        assert config_path.read_text(encoding="utf-8") == original
