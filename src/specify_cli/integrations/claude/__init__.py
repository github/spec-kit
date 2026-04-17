"""Claude Code integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import re

import yaml

from ..base import SkillsIntegration
from ..manifest import IntegrationManifest

# Note injected into hook sections so Claude maps dot-notation command
# names (from extensions.yml) to the hyphenated skill names it uses.
_HOOK_COMMAND_NOTE = (
    "- When constructing slash commands from hook command names, "
    "replace dots (`.`) with hyphens (`-`). "
    "For example, `speckit.git.commit` → `/speckit-git-commit`.\n"
)

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


class ClaudeIntegration(SkillsIntegration):
    """Integration for Claude Code skills."""

    key = "claude"
    config = {
        "name": "Claude Code",
        "folder": ".claude/",
        "commands_subdir": "skills",
        "install_url": "https://docs.anthropic.com/en/docs/claude-code/setup",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".claude/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
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
                escaped = hint.replace("\\", "\\\\").replace('"', '\\"')
                out.append(f'argument-hint: "{escaped}"{eol}')
                injected = True
                continue
            out.append(line)
        return "".join(out)

    def _render_skill(self, template_name: str, frontmatter: dict[str, Any], body: str) -> str:
        """Render a processed command template as a Claude skill."""
        skill_name = f"speckit-{template_name.replace('.', '-')}"
        description = frontmatter.get(
            "description",
            f"Spec-kit workflow command: {template_name}",
        )
        skill_frontmatter = self._build_skill_fm(
            skill_name, description, f"templates/commands/{template_name}.md"
        )
        frontmatter_text = yaml.safe_dump(skill_frontmatter, sort_keys=False).strip()
        return f"---\n{frontmatter_text}\n---\n\n{body.strip()}\n"

    def _build_skill_fm(self, name: str, description: str, source: str) -> dict:
        from specify_cli.agents import CommandRegistrar
        return CommandRegistrar.build_skill_frontmatter(
            self.key, name, description, source
        )

    @staticmethod
    def _inject_frontmatter_flag(content: str, key: str, value: str = "true") -> str:
        """Insert ``key: value`` before the closing ``---`` if not already present."""
        lines = content.splitlines(keepends=True)

        # Pre-scan: bail out if already present in frontmatter
        dash_count = 0
        for line in lines:
            stripped = line.rstrip("\n\r")
            if stripped == "---":
                dash_count += 1
                if dash_count == 2:
                    break
                continue
            if dash_count == 1 and stripped.startswith(f"{key}:"):
                return content

        # Inject before the closing --- of frontmatter
        out: list[str] = []
        dash_count = 0
        injected = False
        for line in lines:
            stripped = line.rstrip("\n\r")
            if stripped == "---":
                dash_count += 1
                if dash_count == 2 and not injected:
                    if line.endswith("\r\n"):
                        eol = "\r\n"
                    elif line.endswith("\n"):
                        eol = "\n"
                    else:
                        eol = ""
                    out.append(f"{key}: {value}{eol}")
                    injected = True
            out.append(line)
        return "".join(out)

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
            eol = m.group(3)
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
        """Inject Claude-specific frontmatter flags and hook notes."""
        updated = self._inject_frontmatter_flag(content, "user-invocable")
        updated = self._inject_frontmatter_flag(updated, "disable-model-invocation", "false")
        updated = self._inject_hook_command_note(updated)
        return updated

    def ensure_context_file(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
    ) -> Path | None:
        """Create a minimal root ``CLAUDE.md`` if missing.

        Typically called from ``init()`` after
        ``ensure_constitution_from_template``. This file acts as a bridge
        to the constitution at ``CONSTITUTION_REL_PATH`` and is only
        created if that constitution file exists. Returns the created
        path or ``None`` (existing file, or prerequisites not met).
        """
        from specify_cli import CONSTITUTION_REL_PATH

        if self.context_file is None:
            return None

        constitution = project_root / CONSTITUTION_REL_PATH
        context_file = project_root / self.context_file
        if context_file.exists() or not constitution.exists():
            return None

        constitution_rel = CONSTITUTION_REL_PATH.as_posix()
        inv = self.build_command_invocation
        command_lines = [
            (inv("constitution"), "establish or amend project principles"),
            (inv("specify"), "generate spec"),
            (inv("clarify"), f"ask structured de-risking questions (before `{inv('plan')}`)"),
            (inv("plan"), "generate plan"),
            (inv("tasks"), "generate task list"),
            (inv("analyze"), f"cross-artifact consistency report (after `{inv('tasks')}`)"),
            (inv("checklist"), "generate quality checklists"),
            (inv("implement"), "execute plan"),
        ]
        commands_section = "".join(
            f"- `{command}` — {description}\n" for command, description in command_lines
        )
        content = (
            "## Claude's Role\n"
            f"Read `{constitution_rel}` first. It is the authoritative source of truth for this project. "
            "Everything in it is non-negotiable.\n\n"
            "## SpecKit Commands\n"
            f"{commands_section}\n"
            "## On Ambiguity\n"
            "If a spec is missing, incomplete, or conflicts with the constitution — stop and ask. "
            "Do not infer. Do not proceed.\n\n"
        )
        return self.write_file_and_record(content, context_file, project_root, manifest)

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install Claude skills, then inject Claude-specific flags and argument-hints."""
        created = super().setup(project_root, manifest, parsed_options, **opts)

        # Post-process generated skill files
        skills_dir = self.skills_dest(project_root).resolve()

        for path in created:
            # Only touch SKILL.md files under the skills directory
            try:
                path.resolve().relative_to(skills_dir)
            except ValueError:
                continue
            if path.name != "SKILL.md":
                continue

            content_bytes = path.read_bytes()
            content = content_bytes.decode("utf-8")

            updated = self.post_process_skill_content(content)

            # Inject argument-hint if available for this skill
            skill_dir_name = path.parent.name  # e.g. "speckit-plan"
            stem = skill_dir_name
            if stem.startswith("speckit-"):
                stem = stem[len("speckit-"):]
            hint = ARGUMENT_HINTS.get(stem, "")
            if hint:
                updated = self.inject_argument_hint(updated, hint)

            if updated != content:
                path.write_bytes(updated.encode("utf-8"))
                self.record_file_in_manifest(path, project_root, manifest)

        return created
