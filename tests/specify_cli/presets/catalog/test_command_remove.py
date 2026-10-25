from __future__ import annotations

from pathlib import Path

import pytest
import yaml


class TestPresetCatalogRemove:
    """Test multi-catalog support in PresetCatalog."""

    @pytest.mark.parametrize(
        "invalid_entry",
        [
            pytest.param("broken-entry", id="string"),
            pytest.param(0, id="number"),
            pytest.param(False, id="boolean"),
            pytest.param(None, id="null"),
            pytest.param([], id="list"),
        ],
    )
    @pytest.mark.parametrize("invalid_index", [0, 1], ids=["first", "last"])
    @pytest.mark.parametrize("name", ["keep", "does-not-exist"])
    def test_catalog_remove_rejects_malformed_entries_without_writing(
        self, project_dir, invalid_entry, invalid_index, name
    ):
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        entries = [{"name": "keep", "url": "https://example.com/c.json"}]
        entries.insert(invalid_index, invalid_entry)
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(
            "# Preserve the original document on validation failure.\n"
            + yaml.safe_dump({"catalogs": entries, "metadata": "keep me"}),
            encoding="utf-8",
        )
        original = config_path.read_bytes()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = CliRunner().invoke(app, ["preset", "catalog", "remove", name])

        assert config_path.read_bytes() == original
        assert result.exit_code == 1, result.output
        assert f"Invalid catalog entry at index {invalid_index}" in result.output
        assert "expected a mapping" in result.output
        assert type(invalid_entry).__name__ in result.output
        assert "Removed catalog" not in result.output

    @pytest.mark.parametrize(
        "names,target,expected_names,exit_code",
        [
            pytest.param(["keep", "target"], "target", ["keep"], 0, id="remove-one"),
            pytest.param(["keep"], "missing", ["keep"], 1, id="missing-name"),
            pytest.param([], "missing", [], 1, id="empty-catalogs"),
            pytest.param(["target"], "target", [], 0, id="remove-last"),
        ],
    )
    def test_catalog_remove_preserves_valid_config_behavior(
        self, project_dir, names, target, expected_names, exit_code
    ):
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        entries = [
            {"name": name, "url": f"https://example.com/{name}.json"}
            for name in names
        ]
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(
            yaml.safe_dump({"catalogs": entries, "metadata": "keep me"}),
            encoding="utf-8",
        )
        original = config_path.read_bytes()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = CliRunner().invoke(app, ["preset", "catalog", "remove", target])

        assert result.exit_code == exit_code, result.output
        if exit_code:
            assert config_path.read_bytes() == original
            assert "Removed catalog" not in result.output
        else:
            config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            assert config["catalogs"] == [
                entry for entry in entries if entry["name"] in expected_names
            ]
            assert config["metadata"] == "keep me"

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
