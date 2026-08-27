"""Antigravity (agy) integration — skills-based agent.

Antigravity uses ``.agents/skills/speckit-<name>/SKILL.md`` layout (enforced since v1.20.5).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..base import SkillsIntegration

if TYPE_CHECKING:
    from ..manifest import IntegrationManifest

# Note injected into hook sections so agy maps dot-notation command
# names (from extensions.yml) to the hyphenated skill names it uses.
# Without this, agy emits ``/speckit.git.commit`` (which does not
# resolve) instead of ``/speckit-git-commit``.
_HOOK_COMMAND_NOTE = (
    "- When constructing slash commands from hook command names, "
    "replace dots (`.`) with hyphens (`-`). "
    "For example, `speckit.git.commit` → `/speckit-git-commit`.\n"
)


class AgyIntegration(SkillsIntegration):
    """Integration for Antigravity IDE."""

    key = "agy"
    config = {
        "name": "Antigravity",
        "folder": ".agents/",
        "commands_subdir": "skills",
        "install_url": "https://antigravity.google/",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".agents/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }

    @staticmethod
    def _inject_hook_command_note(content: str) -> str:
        """Insert a dot-to-hyphen note before each hook output instruction.

        Targets the line ``- For each executable hook, output the following``
        and inserts the note on the line before it, matching its indentation.
        Skips if the note is already present.
        """
        if "replace dots" in content:
            return content

        def repl(m: re.Match[str]) -> str:
            indent = m.group(1)
            instruction = m.group(2)
            # ``eol`` is empty when the regex matched via ``$`` because the
            # instruction was the final line of a file with no trailing
            # newline. Default to ``\n`` so the note never collapses onto
            # the same line as the instruction.
            eol = m.group(3) or "\n"
            return (
                indent
                + _HOOK_COMMAND_NOTE.rstrip("\n")
                + eol
                + indent
                + instruction
                + eol
            )

        return re.sub(
            r"(?m)^(\s*)(- For each executable hook, output the following[^\r\n]*)(\r\n|\n|$)",
            repl,
            content,
        )

    def post_process_skill_content(self, content: str) -> str:
        """Inject the dot-to-hyphen hook command note."""
        return self._inject_hook_command_note(content)

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        # agy does not support --model or JSON output; both params are ignored
        args = [self._resolve_executable(), "--print", prompt]
        # Honor SPECKIT_INTEGRATION_AGY_EXTRA_ARGS (operator-supplied flags),
        # appended after the positional prompt like the devin integration.
        self._apply_extra_args_env_var(args)
        return args

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        import click

        click.secho(
            "Warning: The .agents/ layout requires Antigravity v1.20.5 or newer. "
            "Please ensure your agy installation is up to date.",
            fg="yellow",
            err=True,
        )
        created = super().setup(project_root, manifest, parsed_options=parsed_options, **opts)

        skills_dir = self.skills_dest(project_root).resolve()
        for path in created:
            try:
                path.resolve().relative_to(skills_dir)
            except ValueError:
                continue
            if path.name != "SKILL.md":
                continue

            content = path.read_bytes().decode("utf-8")
            updated = self.post_process_skill_content(content)
            if updated != content:
                path.write_bytes(updated.encode("utf-8"))
                self.record_file_in_manifest(path, project_root, manifest)

        return created
