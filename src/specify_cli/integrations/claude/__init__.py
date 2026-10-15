"""Claude Code integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..base import IntegrationOption, SkillsIntegration
from ..manifest import IntegrationManifest
from ..._utils import dump_frontmatter

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

# Per-command frontmatter overrides for skills that should run in a forked
# subagent context. See https://code.claude.com/docs/en/skills#run-skills-in-a-subagent
#
# This is intentionally empty. ``analyze`` was previously forked (added in
# #2511) on the assumption that its heavy reads collapse to a short summary,
# but in practice ``/speckit-analyze`` returns a 300-500 line report that is
# injected back into the main conversation. In long sessions each subsequent
# fork inherits that growing context, compounding overhead until the chat
# freezes (#3185). Until a command genuinely returns a compact result, no
# command opts into ``context: fork``. The injection mechanism below stays in
# place so a future command can be added here when that holds true.
FORK_CONTEXT_COMMANDS: dict[str, dict[str, str]] = {}


class ClaudeIntegration(SkillsIntegration):
    """Integration for Claude Code skills."""

    key = "claude"
    skills_invocation_only = True
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
    multi_install_safe = True

    CANONICAL_TO_NATIVE = {
        "session_start": "SessionStart",
        "pre_tool_use": "PreToolUse",
        "post_tool_use": "PostToolUse",
        "session_end": "SessionEnd",
        "user_prompt_submit": "UserPromptSubmit",
        "stop": "Stop",
    }
    events_config_file = ".claude/settings.json"
    events_format = "json-nested"

    # Set by ``setup()`` from ``--no-model-invocation``; applies to core
    # command skills only, since mandatory extension hooks rely on the model
    # invoking the hook skill. Integrations are process-wide singletons, so
    # preset overrides re-registered later in the same run (init, upgrade,
    # or a switch that installs Claude) see the same value. Commands that
    # rewrite skills without calling setup() (e.g. ``preset add``,
    # ``integration use``) get the default.
    _disable_model_invocation: bool = False

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        opts = super().options()
        opts.append(
            IntegrationOption(
                "--no-model-invocation",
                is_flag=True,
                default=False,
                help=(
                    "Install core command skills as user-invocable only "
                    "(disable-model-invocation: true)"
                ),
            )
        )
        return opts

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        self._disable_model_invocation = (
            (parsed_options or {}).get("no_model_invocation") is True
        )
        try:
            return super().setup(
                project_root, manifest, parsed_options=parsed_options, **opts
            )
        except BaseException:
            self._disable_model_invocation = False
            raise

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
                # Skip past folded/quoted continuation lines of the scalar
                # before inserting, so the new key lands after it ends.
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
        frontmatter_text = dump_frontmatter(skill_frontmatter)
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

        # Inject before the closing --- of frontmatter. Preserve the
        # existing EOL style, but default to "\n" (rather than "") when the
        # closing delimiter is the last line of the file with no trailing
        # newline -- otherwise the injected text glues onto the "---"
        # (e.g. "user-invocable: true---"), destroying the delimiter so a
        # later call's pre-scan/injection never finds a second "---" and
        # silently drops that key entirely.
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
                        eol = "\n"
                    out.append(f"{key}: {value}{eol}")
                    injected = True
            out.append(line)
        return "".join(out)

    @staticmethod
    def _skill_name_from_content(content: str) -> str | None:
        """Return the ``name:`` field of a skill's first frontmatter block."""
        dash_count = 0
        for line in content.splitlines():
            stripped = line.rstrip("\r\n")
            if stripped == "---":
                dash_count += 1
                if dash_count == 2:
                    break
                continue
            if dash_count == 1 and stripped.startswith("name:"):
                name = stripped[len("name:"):].strip().strip('"').strip("'")
                return name or None
        return None

    @staticmethod
    def _is_core_command_skill(name: str | None) -> bool:
        from specify_cli.extensions import CORE_COMMAND_NAMES  # lazy: avoids circular import

        return bool(name) and name.startswith("speckit-") and (
            name.removeprefix("speckit-") in CORE_COMMAND_NAMES
        )

    def post_process_skill_content(self, content: str) -> str:
        """Inject Claude-specific frontmatter flags, hook notes, and any
        per-command frontmatter.

        Applied by every skill-generation path (setup, presets, extensions),
        so command-specific frontmatter (argument-hint, fork context) stays
        consistent however the SKILL.md was produced.

        ``disable-model-invocation`` is ``true`` for core command skills when
        the last ``setup()`` in this process was given
        ``--no-model-invocation``, else ``false``.
        """
        updated = super().post_process_skill_content(content)
        updated = self._inject_frontmatter_flag(updated, "user-invocable")
        name = self._skill_name_from_content(updated)
        disable = self._disable_model_invocation and self._is_core_command_skill(name)
        updated = self._inject_frontmatter_flag(
            updated, "disable-model-invocation", "true" if disable else "false"
        )

        stem = name.removeprefix("speckit-") if name else None
        if stem:
            hint = ARGUMENT_HINTS.get(stem, "")
            if hint:
                updated = self.inject_argument_hint(updated, hint)
            fork_config = FORK_CONTEXT_COMMANDS.get(stem)
            if fork_config:
                for key, value in fork_config.items():
                    updated = self._inject_frontmatter_flag(updated, key, value)
        return updated
