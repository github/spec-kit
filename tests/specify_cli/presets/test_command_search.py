from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

from specify_cli.presets import (
    PresetCatalog,
    PresetCatalogEntry,
)
from tests.conftest import strip_ansi


class TestPresetTagsNonString:
    """Non-string catalog tags must not crash preset display commands.

    Catalog payloads are user-editable YAML/JSON, so a `tags:` list can contain
    numbers or other non-strings. The display path joins them; a raw
    ``", ".join(...)`` blows up with ``TypeError: sequence item 0: expected str``.
    Sibling command surfaces (extensions/integrations/workflows) already guard
    this with ``str(t) for t in ...`` — presets must match.
    """

    def _seed_catalog(self, project_dir, tags, extra=None):
        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        pack = {
            "name": "Numeric Tags",
            "description": "Preset with non-string tags",
            "version": "1.0.0",
            "tags": tags,
        }
        if extra:
            pack.update(extra)
        catalog_data = {
            "schema_version": "1.0",
            "presets": {
                "numeric-tags": pack,
            },
        }
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(UTC).isoformat(),
                }
            )
        )
        return catalog

    def test_search_renders_non_string_tags(self, project_dir):
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        catalog = self._seed_catalog(project_dir, [1, 2])
        default_only = [
            PresetCatalogEntry(
                url=catalog.DEFAULT_CATALOG_URL,
                name="default",
                priority=1,
                install_allowed=True,
            )
        ]

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

    def _default_only(self, catalog):
        return [
            PresetCatalogEntry(
                url=catalog.DEFAULT_CATALOG_URL,
                name="default",
                priority=1,
                install_allowed=True,
            )
        ]

    def test_search_by_author_tolerates_non_string_author(self, project_dir):
        """``--author`` must not crash on a numeric catalog ``author``.

        ``PresetCatalog.search`` called ``.lower()`` straight on the raw value,
        raising ``AttributeError: 'int' object has no attribute 'lower'``. The
        sibling extension/integration catalogs coerce with ``str(...)`` first.
        """
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        catalog = self._seed_catalog(project_dir, ["ci"], extra={"author": 789})

        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch.object(
                PresetCatalog,
                "get_active_catalogs",
                return_value=self._default_only(catalog),
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

        catalog = self._seed_catalog(
            project_dir, ["ci"], extra={"name": 123, "description": 456}
        )

        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch.object(
                PresetCatalog,
                "get_active_catalogs",
                return_value=self._default_only(catalog),
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

        catalog = self._seed_catalog(project_dir, 5)

        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch.object(
                PresetCatalog,
                "get_active_catalogs",
                return_value=self._default_only(catalog),
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

        catalog = self._seed_catalog(project_dir, ["[bold]ci"])

        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch.object(
                PresetCatalog,
                "get_active_catalogs",
                return_value=self._default_only(catalog),
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
