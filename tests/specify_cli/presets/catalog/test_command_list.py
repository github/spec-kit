from __future__ import annotations

from pathlib import Path

from specify_cli.presets import (
    PresetCatalog,
    PresetCatalogEntry,
)


class TestPresetCatalogList:
    """Test multi-catalog support in PresetCatalog."""

    def test_catalog_list_escapes_rich_markup(self, project_dir):
        """User-editable catalog name/url/description must not be parsed as Rich markup."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        entry = PresetCatalogEntry(
            url="https://example.com/[cat].json",
            name="Bracket [Catalog]",
            priority=1,
            install_allowed=True,
            description="desc [with] brackets",
        )
        runner = CliRunner()
        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch.object(PresetCatalog, "get_active_catalogs", return_value=[entry]),
        ):
            result = runner.invoke(app, ["preset", "catalog", "list"])
        assert result.exit_code == 0, result.output
        assert "Bracket [Catalog]" in result.output
        assert "https://example.com/[cat].json" in result.output
        assert "desc [with] brackets" in result.output
