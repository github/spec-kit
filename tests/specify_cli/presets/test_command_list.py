from __future__ import annotations

from pathlib import Path

import yaml

from specify_cli.presets import (
    PresetManager,
)
from tests.conftest import strip_ansi


class TestPresetListOrdering:
    """``preset list`` must print presets in actual resolution/precedence order.

    Regression coverage for #4086: the printed order was registry/insertion
    order, so a preset with a *higher* priority number (lower precedence) could
    appear before one with a lower number, misleading users about which preset
    wins. Output must be sorted by (priority, id) to match
    ``PresetRegistry.list_by_priority()``.
    """

    def _install(self, temp_dir, project_dir, pack_id, priority):

        src = temp_dir / f"src-{pack_id}"
        (src / "templates").mkdir(parents=True)
        (src / "templates" / "spec-template.md").write_text("# tmpl\n")
        (src / "preset.yml").write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "preset": {
                        "id": pack_id,
                        "name": pack_id,
                        "version": "1.0.0",
                        "description": "plain description",
                    },
                    "requires": {"speckit_version": ">=0.0.1"},
                    "provides": {
                        "templates": [
                            {
                                "type": "template",
                                "name": "spec-template",
                                "file": "templates/spec-template.md",
                            }
                        ]
                    },
                }
            )
        )
        PresetManager(project_dir).install_from_directory(src, "9.9.9", priority)

    def _invoke(self, project_dir, args):
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        with patch.object(Path, "cwd", return_value=project_dir):
            return CliRunner().invoke(app, args)

    def test_list_sorted_by_priority(self, temp_dir, project_dir):
        """Lower priority number is listed first regardless of install order."""
        # Install in an order that does NOT match precedence.
        self._install(temp_dir, project_dir, "copilot-sub-agents", priority=100)
        self._install(temp_dir, project_dir, "lean", priority=10)

        result = self._invoke(project_dir, ["preset", "list"])
        assert result.exit_code == 0, result.output
        output = strip_ansi(result.output)
        # `lean` (priority 10) must appear before `copilot-sub-agents` (100).
        assert output.index("(lean)") < output.index("(copilot-sub-agents)"), output
        assert "resolution order" in output, output
        assert "Ties are broken by preset id" in output, output

    def test_list_ties_broken_by_id(self, temp_dir, project_dir):
        """Equal priority ties are broken alphabetically by preset id."""
        self._install(temp_dir, project_dir, "zebra", priority=10)
        self._install(temp_dir, project_dir, "alpha", priority=10)

        result = self._invoke(project_dir, ["preset", "list"])
        assert result.exit_code == 0, result.output
        output = strip_ansi(result.output)
        assert output.index("(alpha)") < output.index("(zebra)"), output
