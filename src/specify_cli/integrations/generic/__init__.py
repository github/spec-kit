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
    context_file = "AGENTS.md"

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--commands-dir",
                required=True,
                help="Directory for command files (e.g. .myagent/commands/)",
            ),
        ]

    @staticmethod
    def _resolve_commands_dir(
        parsed_options: dict[str, Any] | None,
        opts: dict[str, Any],
    ) -> str:
        """Extract ``--commands-dir`` from parsed options or raw_options.

        Returns the directory string or raises ``ValueError``.
        """
        parsed_options = parsed_options or {}

        commands_dir = parsed_options.get("commands_dir")
        if commands_dir:
            return commands_dir

        # Fall back to raw_options (--integration-options="--commands-dir ...")
        raw = opts.get("raw_options")
        if raw:
            import shlex
            tokens = shlex.split(raw)
            for i, token in enumerate(tokens):
                if token == "--commands-dir" and i + 1 < len(tokens):
                    return tokens[i + 1]
                if token.startswith("--commands-dir="):
                    return token.split("=", 1)[1]

        raise ValueError(
            "--commands-dir is required for the generic integration"
        )

    def commands_dest(self, project_root: Path) -> Path:
        """Not supported for GenericIntegration — use setup() directly.

        GenericIntegration is stateless; the output directory comes from
        ``parsed_options`` or ``raw_options`` at call time, not from
        instance state.
        """
        raise ValueError(
            "GenericIntegration.commands_dest() cannot be called directly; "
            "the output directory is resolved from parsed_options in setup()"
        )

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install commands to the user-provided commands directory."""
        commands_dir = self._resolve_commands_dir(parsed_options, opts)

        templates = self.list_command_templates()
        if not templates:
            return []

        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        dest = (project_root / commands_dir).resolve()
        try:
            dest.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Integration destination {dest} escapes "
                f"project root {project_root_resolved}"
            ) from exc
        dest.mkdir(parents=True, exist_ok=True)

        script_type = opts.get("script_type", "sh")
        arg_placeholder = "$ARGUMENTS"
        created: list[Path] = []

        for src_file in templates:
            raw = src_file.read_text(encoding="utf-8")
            processed = self.process_template(
                raw, self.key, script_type, arg_placeholder,
                context_file=self.context_file or "",
            )
            dst_name = self.command_filename(src_file.stem)
            dst_file = self.write_file_and_record(
                processed, dest / dst_name, project_root, manifest
            )
            created.append(dst_file)

        # Upsert managed context section into the agent context file
        self.upsert_context_section(project_root)

        return created
