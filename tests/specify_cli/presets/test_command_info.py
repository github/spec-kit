from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import yaml

from specify_cli.presets import (
    PresetCatalog,
    PresetManager,
)
from tests.conftest import strip_ansi
from tests.specify_cli.presets._helpers import (
    default_catalog_entries,
    seed_catalog,
)


class TestPresetInfoTags:
    """Non-string catalog tags must not crash preset display commands.

    Catalog payloads are user-editable YAML/JSON, so a `tags:` list can contain
    numbers or other non-strings. The display path joins them; a raw
    ``", ".join(...)`` blows up with ``TypeError: sequence item 0: expected str``.
    Sibling command surfaces (extensions/integrations/workflows) already guard
    this with ``str(t) for t in ...`` — presets must match.
    """

    def test_info_renders_non_string_tags(self, project_dir):
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
            result = CliRunner().invoke(app, ["preset", "info", "numeric-tags"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "Tags:        1, 2" in plain

    def test_info_tolerates_non_list_tags(self, project_dir):
        """``preset info`` must not crash rendering a scalar ``tags:`` value."""
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
            result = CliRunner().invoke(app, ["preset", "info", "numeric-tags"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "numeric-tags" in plain
        assert "Tags:" not in plain


class TestPresetInfoCatalogMarkup:
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

    def test_info_escapes_catalog_markup(self, project_dir):
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch.object(
                PresetCatalog,
                "get_pack_info",
                return_value=self.MARKUP_PRESET,
            ),
        ):
            result = CliRunner().invoke(
                app,
                ["preset", "info", self.MARKUP_PRESET["id"]],
            )

        assert result.exit_code == 0, result.output
        output = " ".join(strip_ansi(result.output).split())
        for field in (
            "id",
            "name",
            "version",
            "description",
            "author",
            "repository",
            "license",
        ):
            value = self.MARKUP_PRESET[field]
            assert value in output
        # Tags are joined into a single line, so assert on the rendered join.
        assert ", ".join(self.MARKUP_PRESET["tags"]) in output


class TestPresetInfoInstalledMarkup:
    """Locally installed preset metadata must render as literal text.

    ``preset.yml`` is user-editable, so its fields can contain ``[...]``.
    ``TestPresetCatalogRichMarkup`` covers the catalog branch of these
    commands; the installed-preset branch of ``preset list``/``preset info``
    and all of ``preset resolve`` were left unescaped, so a field like
    ``Does [stuff] nicely`` silently rendered as ``Does  nicely`` and an
    unbalanced tag such as ``[/red]`` raised ``rich.errors.MarkupError``,
    aborting the command with a traceback.
    """

    MARKUP_FIELDS: ClassVar[dict[str, str]] = {
        "name": "[green]Markup Name[/green]",
        "version": "1.0.0",
        "description": "[yellow]Markup Description[/yellow]",
        "author": "[magenta]Markup Author[/magenta]",
        "repository": "[bold]Markup Repository[/bold]",
        "license": "[cyan]Markup License[/cyan]",
    }

    def _install(
        self,
        temp_dir,
        project_dir,
        preset_overrides=None,
        strategy=None,
        pack_id="markup-pack",
        priority=10,
        tmpl_description=None,
    ):
        """Install a preset from a directory built with the given manifest fields."""

        src = temp_dir / f"src-{pack_id}"
        (src / "templates").mkdir(parents=True)
        (src / "templates" / "spec-template.md").write_text("# tmpl\n")

        preset_section = {
            "id": pack_id,
            "name": pack_id,
            "version": "1.0.0",
            "description": "plain description",
        }
        preset_section.update(preset_overrides or {})
        tmpl = {
            "type": "template",
            "name": "spec-template",
            "file": "templates/spec-template.md",
        }
        if tmpl_description is not None:
            tmpl["description"] = tmpl_description
        if strategy:
            tmpl["strategy"] = strategy
        (src / "preset.yml").write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "preset": preset_section,
                    "requires": {"speckit_version": ">=0.0.1"},
                    "provides": {"templates": [tmpl]},
                    "tags": ["[italic]markup-tag[/italic]"],
                }
            )
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(src, "9.9.9", priority)
        return manager

    def _invoke(self, project_dir, args):
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        with patch.object(Path, "cwd", return_value=project_dir):
            return CliRunner().invoke(app, args)

    def test_list_and_info_escape_installed_markup(self, temp_dir, project_dir):
        """Every ``preset.yml`` field must survive verbatim in list/info output."""
        self._install(temp_dir, project_dir, preset_overrides=self.MARKUP_FIELDS)

        for args in (["preset", "list"], ["preset", "info", "markup-pack"]):
            result = self._invoke(project_dir, args)
            assert result.exit_code == 0, result.output
            output = " ".join(strip_ansi(result.output).split())
            # `preset list` does not render repository/license.
            fields = (
                ("name", "description") if args[1] == "list" else self.MARKUP_FIELDS
            )
            for field in fields:
                assert self.MARKUP_FIELDS[field] in output, (field, args, output)
            assert "[italic]markup-tag[/italic]" in output, (args, output)

    def test_info_does_not_swallow_template_description(self, temp_dir, project_dir):
        """The per-template line in ``preset info`` must escape the template description.

        ``name``/``type`` are format-restricted by manifest validation, but
        ``description`` is free-form, so it is the field that can carry markup.
        """
        self._install(
            temp_dir,
            project_dir,
            tmpl_description="Template [desc] here",
        )
        result = self._invoke(project_dir, ["preset", "info", "markup-pack"])
        assert result.exit_code == 0, result.output
        output = " ".join(strip_ansi(result.output).split())
        assert "spec-template (template): Template [desc] here" in output, output

    def test_unbalanced_markup_does_not_crash_list_or_info(self, temp_dir, project_dir):
        """An unbalanced tag must not raise MarkupError and abort the command."""
        self._install(
            temp_dir,
            project_dir,
            preset_overrides={"description": "Broken [/red] tag"},
        )

        for args in (["preset", "list"], ["preset", "info", "markup-pack"]):
            result = self._invoke(project_dir, args)
            assert result.exit_code == 0, (args, result.output, result.exception)
            assert "Broken [/red] tag" in strip_ansi(result.output)
