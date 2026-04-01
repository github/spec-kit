"""Generic integration — bring your own agent.

Requires ``--commands-dir`` to specify the output directory for command
files.  No longer special-cased in the core CLI — just another
integration with its own required option.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..base import IntegrationOption, MarkdownIntegration
from ..manifest import IntegrationManifest


class GenericIntegration(MarkdownIntegration):
    """Integration for user-specified (generic) agents."""

    key = "generic"
    config = {
        "name": "Generic (bring your own agent)",
        "folder": None,  # Set dynamically from --commands-dir
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": "",  # Set dynamically from --commands-dir
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = None

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--commands-dir",
                required=True,
                help="Directory for command files (e.g. .myagent/commands/)",
            ),
        ]

    def commands_dest(self, project_root: Path) -> Path:
        """Return the commands output directory from parsed options.

        Overrides the base implementation because ``config["folder"]``
        is ``None`` — the path comes from ``--commands-dir`` instead.

        Falls back to the value stored in ``_commands_dir`` which is set
        by ``setup()`` from the parsed options.
        """
        if hasattr(self, "_commands_dir") and self._commands_dir:
            return project_root / self._commands_dir
        raise ValueError(
            "GenericIntegration requires --commands-dir; call setup() "
            "with parsed_options={'commands_dir': '...'}"
        )

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install commands to the user-provided commands directory."""
        parsed_options = parsed_options or {}
        commands_dir = parsed_options.get("commands_dir")
        if not commands_dir:
            raise ValueError(
                "--commands-dir is required for the generic integration"
            )
        self._commands_dir = commands_dir
        return super().setup(
            project_root, manifest, parsed_options=parsed_options, **opts
        )
