"""
Mistral Vibe CLI integration — skills-based agent.

Vibe uses ``.vibe/skills/speckit-<name>/SKILL.md`` layout (enforced since v2.0.0).
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Callable

from ..base import IntegrationOption, SkillsIntegration
from ..manifest import IntegrationManifest
from ..._toml_string import escape_toml_basic
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

# Keep the native Vibe timeout slightly longer than the dispatcher's inner
# timeout so Vibe does not terminate the dispatcher before it can reap its
# child process.
VIBE_EVENT_TIMEOUT_BUFFER = 5

logger = logging.getLogger(__name__)


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

    @staticmethod
    def _hook_target_os() -> str:
        """Return the shell Vibe uses for hook commands on this host."""
        return "cmd" if os.name == "nt" else "host"

    @staticmethod
    def _toml_quote(value: str) -> str:
        """Render a TOML basic string without exposing Vibe syntax to events."""
        return escape_toml_basic(value)

    @staticmethod
    def _managed_hooks_pattern() -> re.Pattern[str]:
        """Match one Vibe ``[[hooks]]`` block carrying our ownership marker."""
        return re.compile(
            r"\[\[hooks\]\]\n(?:(?!\[\[hooks\]\]).)*?speckit_marker = true\n*",
            re.DOTALL,
        )

    def merge_vibe_event_hooks(
        self,
        project_root: Path,
        events: dict[str, list[dict[str, Any]]],
        *,
        build_dispatcher_command: Callable[[str, str, str, Any], str],
        native_timeout: Callable[[Any], int],
        ensure_safe_destination: Callable[[Path], None],
    ) -> bool:
        """Render and merge managed Vibe hooks without disturbing user content.

        This intentionally lives on Vibe rather than in shared events: Vibe's
        flat TOML schema, supported fields, unique-name rule, native shell
        quoting, and ownership-marker cleanup are all Vibe-specific.
        """
        lines: list[str] = []
        used_names: set[str] = set()
        for event, handlers in events.items():
            native = self.CANONICAL_TO_NATIVE[event]
            for config in handlers:
                command = config.get("command", "")
                dispatcher_command = build_dispatcher_command(
                    command,
                    event,
                    self._hook_target_os(),
                    config.get("timeout", 60),
                )
                command_stem = command.split(".")[-1] if command else "unknown"
                command_stem = re.sub(r"[^A-Za-z0-9_-]+", "-", command_stem) or "unknown"
                base_name = f"speckit-{native}-{command_stem}"
                hook_name = base_name
                suffix = 2
                while hook_name in used_names:
                    hook_name = f"{base_name}-{suffix}"
                    suffix += 1
                used_names.add(hook_name)

                lines.extend(
                    [
                        "[[hooks]]",
                        f"name = {self._toml_quote(hook_name)}",
                        f"type = {self._toml_quote(native)}",
                    ]
                )
                matcher = config.get("matcher", "*")
                if matcher and matcher != "*" and native in ("pre_tool", "post_tool"):
                    lines.append(f"match = {self._toml_quote('re:' + matcher)}")
                lines.extend(
                    [
                        f"command = {self._toml_quote(dispatcher_command)}",
                        f"timeout = {native_timeout(config.get('timeout', 60) + VIBE_EVENT_TIMEOUT_BUFFER)}",
                        "speckit_marker = true",
                        "",
                    ]
                )
        return self._merge_managed_hooks(
            project_root / self.events_config_file,
            "\n".join(lines),
            ensure_safe_destination=ensure_safe_destination,
        )

    def remove_vibe_event_hooks(
        self,
        project_root: Path,
        *,
        ensure_safe_destination: Callable[[Path], None],
    ) -> bool:
        """Remove only Specify-owned Vibe hooks and delete an owned-only file."""
        path = project_root / self.events_config_file
        if not path.exists():
            return False
        ensure_safe_destination(path)
        try:
            existing = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            logger.warning(
                "Could not read %s (it may be unreadable or not UTF-8); "
                "skipping event-config cleanup to preserve user content.",
                path,
            )
            logger.debug("Read error detail: %s", exc)
            return False

        cleaned = self._managed_hooks_pattern().sub("", existing)
        if cleaned == existing:
            return False
        non_comment_content = "\n".join(
            line
            for line in cleaned.splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
        if not non_comment_content:
            path.unlink(missing_ok=True)
            return True
        path.write_text(cleaned, encoding="utf-8")
        return False

    def _merge_managed_hooks(
        self,
        path: Path,
        fragment: str,
        *,
        ensure_safe_destination: Callable[[Path], None],
    ) -> bool:
        """Replace managed entries while retaining every unowned byte sequence."""
        ensure_safe_destination(path)
        existing = ""
        if path.exists():
            try:
                existing = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                logger.warning(
                    "Could not read %s (it may be unreadable or not UTF-8); "
                    "skipping event-config merge to preserve user content.",
                    path,
                )
                logger.debug("Read error detail: %s", exc)
                return False
        cleaned = self._managed_hooks_pattern().sub("", existing)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cleaned.rstrip() + "\n\n" + fragment + "\n", encoding="utf-8")
        return True
