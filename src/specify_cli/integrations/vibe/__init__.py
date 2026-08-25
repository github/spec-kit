"""
Mistral Vibe CLI integration — skills-based agent.

Vibe uses ``.vibe/skills/speckit-<name>/SKILL.md`` layout (enforced since v2.0.0).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..base import IntegrationOption, SkillsIntegration
from ..manifest import IntegrationManifest
from ..._utils import dump_frontmatter

# Per-command frontmatter overrides for skills that should run in a forked
# subagent context.
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


class VibeIntegration(SkillsIntegration):
    """Integration for Mistral Vibe skills."""

    key = "vibe"
    config = {
        "name": "Mistral Vibe",
        "folder": ".vibe/",
        "commands_subdir": "skills",
        "install_url": "https://github.com/mistralai/mistral-vibe",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".vibe/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    multi_install_safe = True

    # Vibe's hooks schema supports exactly three hook types (HookConfig
    # rejects anything else): pre_tool, post_tool, post_agent. Unsupported
    # canonical events (session_start/session_end/user_prompt_submit) are
    # intentionally absent so install_integration_events skips them with a
    # warning instead of writing entries Vibe would refuse to load.
    CANONICAL_TO_NATIVE = {
        "pre_tool_use": "pre_tool",
        "post_tool_use": "post_tool",
        "stop": "post_agent",
    }
    events_config_file = ".vibe/hooks.toml"
    events_format = "toml-vibe"
    # Vibe parses any non-empty hook stdout as a JSON HookStructuredResponse;
    # plain text is reported as a hook failure and its output dropped. The
    # dispatcher therefore wraps handler stdout as {"decision": "allow",
    # "hook_specific_output": {"additional_context": ...}} for every event:
    # post_tool injects additional_context, pre_tool/post_agent ignore it but
    # still parse cleanly.
    events_context_envelope = {"*": "hook_specific_output"}

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        opts = super().options()
        opts.append(
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills",
            ),
        )
        return opts

    def _render_skill(self, template_name: str, frontmatter: dict[str, Any], body: str) -> str:
        """Render a processed command template as a Vibe skill."""
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
    def _skill_stem_from_content(content: str) -> str | None:
        """Derive the command stem (e.g. ``analyze``) from a skill's frontmatter.

        Reads the ``name:`` field of the first frontmatter block and strips
        the ``speckit-`` prefix. Returns ``None`` when no name is present.
        """
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
                if name.startswith("speckit-"):
                    return name[len("speckit-"):]
                return name or None
        return None

    def post_process_skill_content(self, content: str) -> str:
        """Inject Vibe-specific frontmatter flags.

        Applied by every skill-generation path (setup, presets, extensions),
        so Vibe-specific frontmatter stays consistent however the SKILL.md
        was produced.
        """
        updated = super().post_process_skill_content(content)
        updated = self._inject_frontmatter_flag(updated, "user-invocable")
        updated = self._inject_frontmatter_flag(updated, "disable-model-invocation", "false")

        stem = self._skill_stem_from_content(updated)
        if stem:
            fork_config = FORK_CONTEXT_COMMANDS.get(stem)
            if fork_config:
                for key, value in fork_config.items():
                    updated = self._inject_frontmatter_flag(updated, key, value)
        return updated

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install Vibe skills then inject Vibe-specific flags"""
        import click

        click.secho(
            "Warning: The .vibe/skills layout requires Mistral Vibe v2.0.0 or newer. "
            "Please ensure your installation is up to date.",
            fg="yellow",
            err=True,
        )

        return super().setup(project_root, manifest, parsed_options=parsed_options, **opts)
