from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pytest
import yaml

from specify_cli.presets import PresetCatalog
from tests.conftest import strip_ansi
from tests.specify_cli.presets._helpers import (
    default_catalog_entries,
    seed_catalog,
)


class TestPresetSearchCatalogFailures:
    @pytest.mark.parametrize("layer", ["project", "user", "environment"])
    @pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "[::1]"])
    def test_invalid_http_catalog_reports_error(
        self, project_dir, tmp_path, monkeypatch, layer, host
    ):
        from unittest.mock import Mock

        from typer.testing import CliRunner

        from specify_cli import app

        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setattr(Path, "cwd", lambda: project_dir)
        monkeypatch.setattr(Path, "home", lambda: home)
        monkeypatch.delenv("SPECKIT_PRESET_CATALOG_URL", raising=False)
        url = f"http://{host}:8080/catalog.json"
        if layer == "environment":
            monkeypatch.setenv("SPECKIT_PRESET_CATALOG_URL", url)
        else:
            root = project_dir if layer == "project" else home
            config_dir = root / ".specify"
            config_dir.mkdir(exist_ok=True)
            (config_dir / "preset-catalogs.yml").write_text(
                yaml.safe_dump({"catalogs": [{"name": "local", "url": url}]}),
                encoding="utf-8",
            )
        open_url = Mock(side_effect=AssertionError("Unexpected network request"))
        monkeypatch.setattr("specify_cli.authentication.http.open_url", open_url)

        result = CliRunner().invoke(app, ["preset", "search"])

        assert result.exit_code == 1, result.output
        output = " ".join(strip_ansi(result.output).split())
        assert "must use HTTPS" in output
        assert "No presets found" not in output
        open_url.assert_not_called()

    def test_recoverable_fetch_failure_reports_no_results(
        self, project_dir, monkeypatch
    ):
        from unittest.mock import Mock

        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.presets import PresetError

        monkeypatch.setattr(Path, "cwd", lambda: project_dir)
        monkeypatch.delenv("SPECKIT_PRESET_CATALOG_URL", raising=False)
        (project_dir / ".specify" / "preset-catalogs.yml").write_text(
            yaml.safe_dump({
                "catalogs": [{
                    "name": "unavailable",
                    "url": "https://example.com/catalog.json",
                }],
            }),
            encoding="utf-8",
        )
        fetch = Mock(side_effect=PresetError("catalog unavailable"))
        monkeypatch.setattr(PresetCatalog, "_fetch_single_catalog", fetch)

        result = CliRunner().invoke(app, ["preset", "search"])

        assert result.exit_code == 0, result.output
        output = strip_ansi(result.output)
        assert "No presets found" in output
        assert "Error:" not in output
        fetch.assert_called_once()


class TestPresetTagsNonString:
    """Non-string catalog tags must not crash preset display commands.

    Catalog payloads are user-editable YAML/JSON, so a `tags:` list can contain
    numbers or other non-strings. The display path joins them; a raw
    ``", ".join(...)`` blows up with ``TypeError: sequence item 0: expected str``.
    Sibling command surfaces (extensions/integrations/workflows) already guard
    this with ``str(t) for t in ...`` — presets must match.
    """

    def test_search_renders_non_string_tags(self, project_dir):
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        catalog = seed_catalog(project_dir, [1, 2])
        default_only = default_catalog_entries(catalog)

        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch.object(
                PresetCatalog, "get_active_catalogs", return_value=default_only
            ),
        ):
            result = CliRunner().invoke(app, ["preset", "search", "Numeric"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "Tags: 1, 2" in plain

    def test_search_by_author_tolerates_non_string_author(self, project_dir):
        """``--author`` must not crash on a numeric catalog ``author``.

        ``PresetCatalog.search`` called ``.lower()`` straight on the raw value,
        raising ``AttributeError: 'int' object has no attribute 'lower'``. The
        sibling extension/integration catalogs coerce with ``str(...)`` first.
        """
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        catalog = seed_catalog(project_dir, ["ci"], extra={"author": 789})

        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch.object(
                PresetCatalog,
                "get_active_catalogs",
                return_value=default_catalog_entries(catalog),
            ),
        ):
            result = CliRunner().invoke(app, ["preset", "search", "--author", "789"])

        assert result.exit_code == 0, result.output
        assert "Numeric Tags" in strip_ansi(result.output)

    def test_search_query_tolerates_non_string_name_and_description(self, project_dir):
        """A query search must not crash on numeric ``name``/``description``.

        The searchable-text join passed the raw values through, raising
        ``TypeError: sequence item 0: expected str instance, int found``.
        """
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        catalog = seed_catalog(
            project_dir, ["ci"], extra={"name": 123, "description": 456}
        )

        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch.object(
                PresetCatalog,
                "get_active_catalogs",
                return_value=default_catalog_entries(catalog),
            ),
        ):
            result = CliRunner().invoke(app, ["preset", "search", "123"])

        assert result.exit_code == 0, result.output
        assert "numeric-tags" in strip_ansi(result.output)

    def test_search_tolerates_non_list_tags(self, project_dir):
        """A scalar ``tags:`` value must not crash the tag filter or display.

        ``tags: 5`` is truthy but not iterable, so both the ``--tag`` filter and
        the result-display join raised ``TypeError: 'int' object is not
        iterable``. Siblings guard with ``isinstance(raw_tags, list)``.
        """
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        catalog = seed_catalog(project_dir, 5)

        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch.object(
                PresetCatalog,
                "get_active_catalogs",
                return_value=default_catalog_entries(catalog),
            ),
        ):
            filtered = CliRunner().invoke(app, ["preset", "search", "--tag", "ci"])
            displayed = CliRunner().invoke(app, ["preset", "search", "Numeric"])

        assert filtered.exit_code == 0, filtered.output
        assert "No presets found" in strip_ansi(filtered.output)

        assert displayed.exit_code == 0, displayed.output
        plain = strip_ansi(displayed.output)
        assert "Numeric Tags" in plain
        assert "Tags:" not in plain

    def test_search_escapes_rich_markup_in_tags(self, project_dir):
        """Bracketed tag text must survive Rich markup parsing.

        ``preset search`` printed tags unescaped, so a tag like ``[bold]`` was
        swallowed as a style tag. ``preset list`` already escaped this.
        """
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        catalog = seed_catalog(project_dir, ["[bold]ci"])

        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch.object(
                PresetCatalog,
                "get_active_catalogs",
                return_value=default_catalog_entries(catalog),
            ),
        ):
            result = CliRunner().invoke(app, ["preset", "search", "Numeric"])

        assert result.exit_code == 0, result.output
        assert "[bold]ci" in strip_ansi(result.output)


class TestPresetSearchRichMarkup:
    """Catalog metadata must render as literal text in Rich output."""

    MARKUP_PRESET: ClassVar[dict[str, object]] = {
        "id": "[red]markup-id[/red]",
        "name": "[green]Markup Name[/green]",
        "version": "[blue]1.0.0[/blue]",
        "description": "[yellow]Markup Description[/yellow]",
        "author": "[magenta]Markup Author[/magenta]",
        "tags": ["[italic]markup-tag[/italic]"],
        "repository": "[bold]Markup Repository[/bold]",
        "license": "[cyan]Markup License[/cyan]",
    }

    def test_search_escapes_catalog_markup(self, project_dir):
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch.object(
                PresetCatalog,
                "search",
                return_value=[self.MARKUP_PRESET],
            ),
        ):
            result = CliRunner().invoke(app, ["preset", "search"])

        assert result.exit_code == 0, result.output
        output = " ".join(strip_ansi(result.output).split())
        for value in (
            self.MARKUP_PRESET["id"],
            self.MARKUP_PRESET["name"],
            self.MARKUP_PRESET["version"],
            self.MARKUP_PRESET["description"],
        ):
            assert value in output
