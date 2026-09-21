from __future__ import annotations

from pathlib import Path

import yaml


class TestPresetCatalogRemove:
    """Test multi-catalog support in PresetCatalog."""

    def test_catalog_remove_escapes_rich_markup(self, project_dir):
        """`preset catalog remove` must not parse the name as Rich markup."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        name = "[/red]my-catalog"
        (project_dir / ".specify" / "preset-catalogs.yml").write_text(
            yaml.dump(
                {
                    "catalogs": [
                        {
                            "name": name,
                            "url": "https://example.com/c.json",
                            "priority": 1,
                            "install_allowed": False,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "catalog", "remove", name])
        assert result.exit_code == 0, result.output
        assert name in result.output

    def test_catalog_remove_escapes_markup_in_not_found_error(self, project_dir):
        """The not-found error path renders the name too."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        (project_dir / ".specify" / "preset-catalogs.yml").write_text(
            yaml.dump({"catalogs": []}), encoding="utf-8"
        )
        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "catalog", "remove", "[/red]absent"])
        assert result.exit_code == 1
        assert "[/red]absent" in result.output
