"""Claude Code integration."""

from __future__ import annotations

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
        """Insert ``argument-hint`` after the first ``description:`` in YAML frontmatter.

        Skips injection if ``argument-hint:`` already exists in the
        frontmatter to avoid duplicate keys.
        """
        lines = content.splitlines(keepends=True)

        # Pre-scan: bail out if argument-hint already present in frontmatter
        dash_count = 0
        for line in lines:
            stripped = line.rstrip("\n\r")
            if stripped == "---":
                dash_count += 1
                if dash_count == 2:
                    break
                continue
            if dash_count == 1 and stripped.startswith("argument-hint:"):
                return content  # already present

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
                # Preserve the exact line-ending style (\r\n vs \n)
                if line.endswith("\r\n"):
                    eol = "\r\n"
                elif line.endswith("\n"):
                    eol = "\n"
                else:
                    eol = ""
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
        """Run standard MarkdownIntegration setup, then inject argument-hint."""
        created = super().setup(project_root, manifest, parsed_options, **opts)

        # Post-process generated command files to add argument-hint
        commands_dest = self.commands_dest(project_root).resolve()
        ext = self.registrar_config.get("extension", ".md") if self.registrar_config else ".md"

        for path in created:
            # Only touch command files, not scripts
            try:
                path.resolve().relative_to(commands_dest)
            except ValueError:
                continue
            if path.suffix != ext:
                continue

            # Extract template stem: speckit.plan.md -> plan
            stem = path.stem  # speckit.plan
            if stem.startswith("speckit."):
                stem = stem[len("speckit."):]

            hint = ARGUMENT_HINTS.get(stem, "")
            if not hint:
                continue

            content = path.read_text(encoding="utf-8")
            updated = self.inject_argument_hint(content, hint)
            if updated != content:
                path.write_text(updated, encoding="utf-8")

        return created
