"""Claude Code integration."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, TYPE_CHECKING

from ..base import MarkdownIntegration

if TYPE_CHECKING:
    from ..manifest import IntegrationManifest

# Mapping of command template stem → argument-hint text shown inline
# when a user invokes the slash command in Claude Code.
ARGUMENT_HINTS: dict[str, str] = {
    "specify": "Describe the feature you want to specify",
    "plan": "Optional guidance for the planning phase",
    "tasks": "Optional task generation constraints",
    "implement": "Optional implementation guidance or task filter",
    "analyze": "Optional focus areas for analysis",
    "clarify": "Optional areas to clarify in the spec",
    "constitution": "Principles or values for the project constitution",
    "checklist": "Domain or focus area for the checklist",
    "taskstoissues": "Optional filter or label for GitHub issues",
}


class ClaudeIntegration(MarkdownIntegration):
    key = "claude"
    config = {
        "name": "Claude Code",
        "folder": ".claude/",
        "commands_subdir": "commands",
        "install_url": "https://docs.anthropic.com/en/docs/claude-code/setup",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".claude/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = "CLAUDE.md"

    @staticmethod
    def inject_argument_hint(content: str, hint: str) -> str:
        """Insert ``argument-hint`` after the first ``description:`` in YAML frontmatter."""
        lines = content.splitlines(keepends=True)
        out: list[str] = []
        in_fm = False
        dash_count = 0
        injected = False
        for line in lines:
            stripped = line.rstrip("\n\r")
            if stripped == "---":
                dash_count += 1
                in_fm = dash_count == 1
                out.append(line)
                continue
            if in_fm and not injected and stripped.startswith("description:"):
                out.append(line)
                # Preserve the line-ending style of the file
                eol = "\n" if line.endswith("\n") else ""
                out.append(f"argument-hint: {hint}{eol}")
                injected = True
                continue
            out.append(line)
        return "".join(out)

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        templates = self.list_command_templates()
        if not templates:
            return []

        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        dest = self.commands_dest(project_root).resolve()
        try:
            dest.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Integration destination {dest} escapes "
                f"project root {project_root_resolved}"
            ) from exc
        dest.mkdir(parents=True, exist_ok=True)

        script_type = opts.get("script_type", "sh")
        arg_placeholder = self.registrar_config.get("args", "$ARGUMENTS") if self.registrar_config else "$ARGUMENTS"
        created: list[Path] = []

        for src_file in templates:
            raw = src_file.read_text(encoding="utf-8")
            processed = self.process_template(raw, self.key, script_type, arg_placeholder)

            # Inject argument-hint for Claude Code commands
            hint = ARGUMENT_HINTS.get(src_file.stem, "")
            if hint:
                processed = self.inject_argument_hint(processed, hint)

            dst_name = self.command_filename(src_file.stem)
            dst_file = self.write_file_and_record(
                processed, dest / dst_name, project_root, manifest
            )
            created.append(dst_file)

        created.extend(self.install_scripts(project_root, manifest))
        return created
