"""Alquimia AI integration."""

from __future__ import annotations

from typing import Any

from ..._utils import dump_frontmatter
from ..base import SkillsIntegration

# Mapping of command template stem → argument-hint text shown inline
# when a user invokes the slash command in Alquimia AI.
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


class AlquimiaAIIntegration(SkillsIntegration):
    """Integration for Alquimia AI skills."""

    key = "alquimia"
    config = {
        "name": "Alquimia AI",
        "folder": ".alquimia/",
        "commands_subdir": "skills",
        "install_url": "https://docs.alquimia.ai",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".alquimia/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    multi_install_safe = True

    def _render_skill(
        self, template_name: str, frontmatter: dict[str, Any], body: str
    ) -> str:
        """Render a processed command template as an Alquimia skill."""
        skill_name = f"speckit-{template_name.replace('.', '-')}"
        description = frontmatter.get(
            "description",
            f"Spec-kit workflow command: {template_name}",
        )
        skill_frontmatter = self._build_skill_fm(
            skill_name, description, f"templates/commands/{template_name}.md"
        )
        frontmatter_text = dump_frontmatter(skill_frontmatter)
        return f"---\n{frontmatter_text}\n---\n\n{body.strip()}\n"

    def _build_skill_fm(self, name: str, description: str, source: str) -> dict:
        from specify_cli.agents import CommandRegistrar

        return CommandRegistrar.build_skill_frontmatter(
            self.key, name, description, source
        )

    @staticmethod
    def inject_argument_hint(content: str, hint: str) -> str:
        """Insert ``argument-hint`` after the ``description:`` scalar in YAML frontmatter.

        A long ``description`` gets folded by the YAML dumper across
        indented continuation lines (plain or quoted), and an embedded
        paragraph break can add unindented blank lines inside a quoted
        scalar. Inserting the new line right after the *first* line of
        that scalar — instead of after the whole scalar — either produces
        invalid YAML or gets silently absorbed into the description
        string (#4044), so every continuation line (indented, or blank)
        is skipped first.

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
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]
            stripped = line.rstrip("\n\r")
            if stripped == "---":
                dash_count += 1
                in_fm = dash_count == 1
                out.append(line)
                i += 1
                continue
            if in_fm and not injected and stripped.startswith("description:"):
                out.append(line)
                i += 1
                # Skip folded/quoted continuation lines before inserting
                # so the new key lands after the description scalar ends.
                # Blank lines count too: PyYAML emits unindented blank
                # lines for embedded "\n\n" inside a quoted scalar.
                while i < n and (
                    lines[i][:1] in (" ", "\t") or lines[i].rstrip("\r\n") == ""
                ):
                    out.append(lines[i])
                    i += 1
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
            i += 1
        return "".join(out)

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

    def post_process_skill_content(self, content: str) -> str:
        """Inject Alquimia-specific frontmatter flags, hints and hook notes."""
        updated = super().post_process_skill_content(content)
        updated = self._inject_frontmatter_flag(updated, "user-invocable")
        updated = self._inject_frontmatter_flag(
            updated, "disable-model-invocation", "false"
        )
        for line in updated.splitlines():
            if line.startswith("name:"):
                name = line.removeprefix("name:").strip().strip("\"'")
                hint = ARGUMENT_HINTS.get(name.removeprefix("speckit-"))
                if hint:
                    updated = self.inject_argument_hint(updated, hint)
                break
        return updated
