from __future__ import annotations

from pathlib import Path

import yaml

from specify_cli.presets import (
    PresetManager,
)
from tests.conftest import strip_ansi


class TestPresetResolve:
    """Locally installed preset metadata must render as literal text.

    ``preset.yml`` is user-editable, so its fields can contain ``[...]``.
    ``TestPresetCatalogRichMarkup`` covers the catalog branch of these
    commands; the installed-preset branch of ``preset list``/``preset info``
    and all of ``preset resolve`` were left unescaped, so a field like
    ``Does [stuff] nicely`` silently rendered as ``Does  nicely`` and an
    unbalanced tag such as ``[/red]`` raised ``rich.errors.MarkupError``,
    aborting the command with a traceback.
    """

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

    def test_resolve_rejects_invalid_template_name(self, project_dir):
        """``preset resolve`` rejects names before joining them into paths."""
        result = self._invoke(project_dir, ["preset", "resolve", "no[/red]such"])
        assert result.exit_code == 1, (result.output, result.exception)
        assert "invalid template name" in strip_ansi(result.output)

    def test_resolve_rejects_path_traversal(self, project_dir):
        """The resolver rejects traversal before joining names into paths."""
        result = self._invoke(
            project_dir,
            ["preset", "resolve", "../../../README"],
        )

        assert result.exit_code == 1
        assert "invalid template name" in strip_ansi(result.output)

    def test_resolve_accepts_dotted_command_name(self, project_dir):
        """Documented dotted command identifiers use command resolution."""
        result = self._invoke(
            project_dir,
            ["preset", "resolve", "speckit.constitution"],
        )

        assert result.exit_code == 0, (result.output, result.exception)
        assert "constitution.md" in "".join(strip_ansi(result.output).split())

    def test_resolve_rejects_empty_command_segments(self, project_dir):
        """Dotted command identifiers cannot contain empty path-like segments."""
        result = self._invoke(
            project_dir,
            ["preset", "resolve", "speckit..constitution"],
        )

        assert result.exit_code == 1
        assert "invalid template name" in strip_ansi(result.output)

    def test_resolve_escapes_layer_path_and_source(self, project_dir):
        """The top-layer path/source lines must render markup literally.

        A preset can be installed from any directory, so the resolved path can
        contain ``[...]``; the layer source carries the pack id and version.
        """
        from unittest.mock import patch

        from specify_cli.presets import PresetResolver

        # A closing tag cannot live inside a path segment: `Path` treats its
        # `/` as a separator on POSIX and rewrites it to `\` on Windows. The
        # opening tag covers the swallowing case for the path; the unbalanced
        # closing tag rides on `source`, which is a plain string.
        layer = {
            "path": Path("/tmp/[red]dir/spec-template.md"),
            "source": "pack [/red] v1.0.0",
            "strategy": "replace",
        }
        with patch.object(PresetResolver, "collect_all_layers", return_value=[layer]):
            result = self._invoke(project_dir, ["preset", "resolve", "spec-template"])

        assert result.exit_code == 0, (result.output, result.exception)
        output = " ".join(strip_ansi(result.output).split())
        assert "[red]dir" in output, output
        assert "pack [/red] v1.0.0" in output, output

    def test_resolve_escapes_fallback_path_and_source(self, project_dir):
        """The no-layer fallback branch must escape ``resolve_with_source`` output."""
        from unittest.mock import patch

        from specify_cli.presets import PresetResolver

        with (
            patch.object(PresetResolver, "collect_all_layers", return_value=[]),
            patch.object(
                PresetResolver,
                "resolve_with_source",
                return_value={
                    "path": "/tmp/[blue]fallback[/blue]/spec-template.md",
                    "source": "fallback [/red] source",
                },
            ),
        ):
            result = self._invoke(project_dir, ["preset", "resolve", "spec-template"])

        assert result.exit_code == 0, (result.output, result.exception)
        output = " ".join(strip_ansi(result.output).split())
        assert "[blue]fallback[/blue]" in output, output
        assert "fallback [/red] source" in output, output

    def test_resolve_escapes_composition_error(self, project_dir):
        """A composition exception message must not be parsed as markup."""
        from unittest.mock import patch

        from specify_cli.presets import PresetResolver

        layers = [
            {
                "path": Path("/tmp/top/spec-template.md"),
                "source": "top-pack v1.0.0",
                "strategy": "append",
            },
            {
                "path": Path("/tmp/base/spec-template.md"),
                "source": "base-pack v1.0.0",
                "strategy": "append",
            },
        ]
        with (
            patch.object(PresetResolver, "collect_all_layers", return_value=layers),
            patch.object(
                PresetResolver,
                "resolve_content",
                side_effect=RuntimeError("compose failed: [/red] bad layer"),
            ),
        ):
            result = self._invoke(project_dir, ["preset", "resolve", "spec-template"])

        assert result.exit_code == 0, (result.output, result.exception)
        output = " ".join(strip_ansi(result.output).split())
        assert "compose failed: [/red] bad layer" in output, output

    def test_resolve_renders_composition_strategy_labels(self, temp_dir, project_dir):
        """The composition chain's ``[<strategy>]`` label must not be eaten as a tag."""
        self._install(
            temp_dir, project_dir, strategy="replace", pack_id="base-pack", priority=20
        )
        self._install(
            temp_dir, project_dir, strategy="append", pack_id="app-pack", priority=5
        )

        result = self._invoke(project_dir, ["preset", "resolve", "spec-template"])
        assert result.exit_code == 0, (result.output, result.exception)
        output = strip_ansi(result.output)
        assert "Composition chain" in output, output
        assert "[base]" in output, output
        assert "[append]" in output, output
