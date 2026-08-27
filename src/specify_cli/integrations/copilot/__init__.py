"""Copilot integration — GitHub Copilot in VS Code.

Copilot supports two layouts:
- Skills are the default and use ``speckit-<name>/SKILL.md`` directories under
  ``.github/skills/``
- ``--commands`` uses ``.agent.md`` files, companion ``.prompt.md`` files, and
  a VS Code settings merge

The two modes are mutually exclusive. The commands layout remains supported,
but is no longer the preferred default.

The commands layout has several unique behaviors compared to standard markdown
agents:
- Commands use ``.agent.md`` extension (not ``.md``)
- Each command gets a companion ``.prompt.md`` file in ``.github/prompts/``
- Installs ``.vscode/settings.json`` with prompt file recommendations
"""

from __future__ import annotations

import json
import os
import shutil
import warnings
from pathlib import Path
from typing import Any

import typer

from ..base import IntegrationBase, IntegrationOption, SkillsIntegration
from ..manifest import IntegrationManifest

_COPILOT_CORE_COMMANDS = {
    "analyze",
    "checklist",
    "clarify",
    "constitution",
    "converge",
    "implement",
    "plan",
    "specify",
    "tasks",
    "taskstoissues",
}


def _copilot_executable() -> str:
    """Return the executable name for Copilot CLI on this platform.

    On Windows, subprocess invocation is reliable with `copilot.cmd`.
    """
    if os.name == "nt":
        return "copilot.cmd"
    return "copilot"


def _allow_all() -> bool:
    """Return True if the Copilot CLI should run with full permissions.

    Checks ``SPECKIT_COPILOT_ALLOW_ALL_TOOLS`` first (new canonical name).
    Falls back to the deprecated ``SPECKIT_ALLOW_ALL_TOOLS`` if set,
    emitting a deprecation warning.  Default when neither is set: enabled.
    """
    new_var = os.environ.get("SPECKIT_COPILOT_ALLOW_ALL_TOOLS")
    if new_var is not None:
        return new_var != "0"

    old_var = os.environ.get("SPECKIT_ALLOW_ALL_TOOLS")
    if old_var is not None:
        warnings.warn(
            "SPECKIT_ALLOW_ALL_TOOLS is deprecated; "
            "use SPECKIT_COPILOT_ALLOW_ALL_TOOLS instead.",
            UserWarning,
            stacklevel=2,
        )
        return old_var != "0"

    return True


def _validate_mode_options(parsed_options: dict[str, Any] | None) -> None:
    """Reject the two explicit Copilot layout selectors used together."""
    opts = parsed_options or {}
    if opts.get("skills") and opts.get("commands"):
        from ..._console import console

        console.print(
            "[red]Error:[/red] --skills and --commands are mutually exclusive; "
            "pass only one."
        )
        raise typer.Exit(1)


class _CopilotSkillsHelper(SkillsIntegration):
    """Internal helper used when Copilot is scaffolded in skills mode.

    Not registered in the integration registry — only used as the default
    skills-layout delegate by ``CopilotIntegration``.
    """

    key = "copilot"
    config = {
        "name": "GitHub Copilot",
        "folder": ".github/",
        "commands_subdir": "skills",
        "install_url": "https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-copilot-cli",
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".github/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }


class CopilotIntegration(IntegrationBase):
    """Integration for GitHub Copilot (VS Code IDE + CLI).

    The default IDE integration (``requires_cli: False``) installs skills under
    ``.github/skills/``. Pass ``--commands`` via ``--integration-options`` to
    install the supported ``.agent.md`` + ``.prompt.md`` layout instead.
    Workflow dispatch additionally requires the ``copilot`` CLI to be installed
    separately.
    """

    key = "copilot"
    config = {
        "name": "GitHub Copilot",
        "folder": ".github/",
        "commands_subdir": "agents",
        "install_url": "https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-copilot-cli",
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".github/agents",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".agent.md",
    }
    invoke_separator = "-"

    CANONICAL_TO_NATIVE = {
        "session_start": "sessionStart",
        "pre_tool_use": "preToolUse",
        "post_tool_use": "postToolUse",
        "session_end": "sessionEnd",
        "user_prompt_submit": "userPromptSubmitted",
        # Copilot CLI supports the canonical per-turn stop lifecycle as native
        # agentStop (U3); mapping it so an extension's stop handler fires.
        "stop": "agentStop",
    }
    events_config_file = ".github/hooks/speckit.json"
    events_format = "copilot-json"
    # Copilot sessionStart and userPromptSubmitted inject a top-level
    # additionalContext field into the model-facing prompt (C13). Non-JSON
    # stdout is discarded harmlessly by Copilot on other events, so no other
    # event needs an envelope.
    events_context_envelope = {
        "session_start": "additionalContext",
        "user_prompt_submit": "additionalContext",
    }

    # Mutable flag set by setup() — indicates the active scaffolding mode.
    _skills_mode: bool = True

    def effective_invoke_separator(
        self,
        parsed_options: dict[str, Any] | None = None,
        project_root: Path | None = None,
    ) -> str:
        """Return the separator for the resolved Copilot layout."""
        return "-" if self.is_skills_mode(parsed_options, project_root) else "."

    def is_skills_mode(
        self,
        parsed_options: dict[str, Any] | None = None,
        project_root: Path | None = None,
    ) -> bool:
        """Copilot defaults to skills; ``--commands`` opts into commands mode.

        Explicit flags override on-disk detection. Without a flag, existing
        projects retain their managed Spec Kit layout while fresh projects use
        skills. This prevents ``use`` and ``upgrade`` from silently migrating
        projects created before skills became the default.
        """
        opts = parsed_options or {}
        _validate_mode_options(opts)
        if opts.get("skills"):
            return True
        if opts.get("commands"):
            return False
        if project_root is not None:
            project_root = Path(project_root)
            manifest_path = (
                project_root
                / ".specify"
                / "integrations"
                / "copilot.manifest.json"
            )
            if manifest_path.is_file():
                try:
                    manifest_files = IntegrationManifest.load(
                        self.key, Path(project_root)
                    ).files
                except (OSError, ValueError):
                    manifest_files = None
                if manifest_files is not None and any(
                    path.startswith(".github/skills/speckit-")
                    and path.endswith("/SKILL.md")
                    for path in manifest_files
                ):
                    return True
                if manifest_files is not None and any(
                    path.startswith(".github/agents/speckit.")
                    and path.endswith(".agent.md")
                    for path in manifest_files
                ):
                    return False

            github_dir = project_root / ".github"
            has_managed_skills = any(
                (
                    github_dir
                    / "skills"
                    / f"speckit-{command}"
                    / "SKILL.md"
                ).is_file()
                for command in _COPILOT_CORE_COMMANDS
            )
            has_managed_commands = any(
                (
                    github_dir
                    / "agents"
                    / f"speckit.{command}.agent.md"
                ).is_file()
                or (
                    github_dir
                    / "prompts"
                    / f"speckit.{command}.prompt.md"
                ).is_file()
                for command in _COPILOT_CORE_COMMANDS
            )
            if has_managed_commands and not has_managed_skills:
                return False
        return True

    def invoke_separator_for_mode(self, skills_enabled: bool) -> str:
        """Skills projects render ``/speckit-<cmd>``; commands use ``.``.

        Copilot is dual-layout, so — like Bob — the command-reference
        separator depends on the persisted ``ai_skills`` state rather than a
        single static value.  This keeps preset/extension command refs in a
        Copilot skills project consistent with ``build_command_invocation``
        (which emits ``/speckit-<stem>``).
        """
        return "-" if skills_enabled else "."

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        # Compose with super() so the base class declares --events for this
        # event-capable integration; otherwise --integration-options
        # "--events false" is rejected as unknown (#9).
        opts = super().options()
        opts.append(
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=False,
                help=(
                    "Force the default skills layout (.github/skills/), "
                    "overriding on-disk auto-detection"
                ),
            ),
        )
        opts.append(
            IntegrationOption(
                "--commands",
                is_flag=True,
                default=False,
                help=(
                    "Scaffold .github/agents/*.agent.md commands with companion "
                    ".github/prompts/*.prompt.md files instead of the default "
                    "skills layout"
                ),
            ),
        )
        return opts

    def _resolve_executable(self) -> str:
        """Return the Copilot CLI executable, respecting the env-var override.

        Checks ``SPECKIT_INTEGRATION_COPILOT_EXECUTABLE`` first.  Falls
        back to the platform-specific default from ``_copilot_executable()``
        (``copilot.cmd`` on Windows, ``copilot`` elsewhere) so that
        existing behaviour is preserved when the env var is unset.
        """
        env_name = "SPECKIT_INTEGRATION_COPILOT_EXECUTABLE"
        override = os.environ.get(env_name, "").strip()
        return override if override else _copilot_executable()

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        # GitHub Copilot CLI uses ``copilot -p "prompt"`` for
        # non-interactive mode.  --yolo enables all permissions
        # (tools, paths, and URLs) so the agent can perform file
        # edits and shell commands without interactive prompts.
        # Controlled by SPECKIT_COPILOT_ALLOW_ALL_TOOLS env var
        # (default: enabled).  The deprecated SPECKIT_ALLOW_ALL_TOOLS
        # is also honoured as a fallback.
        args = [self._resolve_executable(), "-p", prompt]
        self._apply_extra_args_env_var(args)
        if _allow_all():
            args.append("--yolo")
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--output-format", "json"])
        return args

    def build_command_invocation(self, command_name: str, args: str = "") -> str:
        """Build the native invocation for a Copilot command.

        Commands mode: agents are not slash-commands — return args as prompt.
        Skills mode (default): ``/speckit-<stem>`` slash-command dispatch.
        """
        if self._skills_mode:
            stem = command_name
            if stem.startswith("speckit."):
                stem = stem[len("speckit."):]
            invocation = "/speckit-" + stem.replace(".", "-")
            if args:
                invocation = f"{invocation} {args}"
            return invocation
        return args or ""

    def dispatch_command(
        self,
        command_name: str,
        args: str = "",
        *,
        project_root: Path | None = None,
        model: str | None = None,
        timeout: int = 600,
        stream: bool = True,
    ) -> dict[str, Any]:
        """Dispatch via ``--agent speckit.<stem>`` instead of slash-commands.

        Copilot ``.agent.md`` files are agents, not skills.  The CLI
        selects them with ``--agent <name>`` and the prompt is just
        the user's arguments.

        In skills mode, the prompt includes the skill invocation
        (``/speckit-<stem>``).
        """
        import subprocess

        stem = command_name
        if stem.startswith("speckit."):
            stem = stem[len("speckit."):]

        skills_mode = (
            self.is_skills_mode(project_root=project_root)
            if project_root
            else self._skills_mode
        )

        if skills_mode:
            prompt = "/speckit-" + stem.replace(".", "-")
            if args:
                prompt = f"{prompt} {args}"
        else:
            agent_name = f"speckit.{stem}"
            prompt = args or ""

        cli_args = [self._resolve_executable(), "-p", prompt]
        # Honour SPECKIT_INTEGRATION_COPILOT_EXTRA_ARGS for real workflow
        # runs.  `dispatch_command` builds cli_args inline rather than
        # going through `build_exec_args`, so the hook must be invoked
        # here too — otherwise the env var is silently ignored.
        self._apply_extra_args_env_var(cli_args)
        if not skills_mode:
            cli_args.extend(["--agent", agent_name])
        if _allow_all():
            cli_args.append("--yolo")
        if model:
            cli_args.extend(["--model", model])
        if not stream:
            cli_args.extend(["--output-format", "json"])

        cwd = str(project_root) if project_root else None

        if stream:
            try:
                result = subprocess.run(
                    cli_args,
                    text=True,
                    cwd=cwd,
                )
            except KeyboardInterrupt:
                return {
                    "exit_code": 130,
                    "stdout": "",
                    "stderr": "Interrupted by user",
                }
            return {
                "exit_code": result.returncode,
                "stdout": "",
                "stderr": "",
            }

        result = subprocess.run(
            cli_args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def command_filename(self, template_name: str) -> str:
        """Copilot commands use ``.agent.md`` extension."""
        return f"speckit.{template_name}.agent.md"

    def stale_cleanup_exclusions(self) -> set[str]:
        """Protect ``.vscode/settings.json`` from upgrade stale-deletion.

        ``setup()`` records this file in the manifest only when it creates it;
        when it already exists the file is merged and intentionally left
        untracked.  On upgrade the untracked-but-existing file would otherwise
        be flagged stale and deleted, destroying user settings (and the file
        the integration still manages).
        """
        exclusions = super().stale_cleanup_exclusions()
        exclusions.add(".vscode/settings.json")
        return exclusions

    def post_process_skill_content(self, content: str) -> str:
        """Inject shared hook guidance into Copilot skill content.

        Delegates to :class:`_CopilotSkillsHelper` for shared post-processing.
        The ``mode:`` frontmatter field is intentionally omitted: VS Code
        Copilot Agent Skills do not support it (see issue #2799).
        """
        return _CopilotSkillsHelper().post_process_skill_content(content)

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install Copilot skills or the opt-in commands layout.

        Skills are the default. ``parsed_options["commands"]`` selects
        ``.agent.md`` files, companion prompts, and the VS Code settings merge.
        Existing managed command layouts are preserved when no mode is explicit.
        """
        parsed_options = parsed_options or {}
        self._skills_mode = self.is_skills_mode(parsed_options, project_root)
        if self._skills_mode:
            created = self._setup_skills(project_root, manifest, parsed_options, **opts)
        else:
            created = self._setup_commands(project_root, manifest, parsed_options, **opts)

        # Install agent runtime events
        event_files = self.emit_events(
            project_root, manifest, events=opts.get("events"), parsed_options=parsed_options
        )
        created.extend(event_files)
        return created

    def _setup_commands(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Commands mode: .agent.md + .prompt.md + VS Code settings merge."""
        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        templates = self.list_command_templates()
        if not templates:
            return []

        from ...presets import PresetResolver

        preset_resolver = PresetResolver(project_root_resolved)

        dest = self.commands_dest(project_root)
        dest_resolved = dest.resolve()
        try:
            dest_resolved.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Integration destination {dest_resolved} escapes "
                f"project root {project_root_resolved}"
            ) from exc
        dest.mkdir(parents=True, exist_ok=True)
        created: list[Path] = []

        script_type = opts.get("script_type", "sh")
        arg_placeholder = self.registrar_config.get("args", "$ARGUMENTS")

        # 1. Process and write command files as .agent.md
        for src_file in templates:
            resolved_template = preset_resolver.resolve(
                f"speckit.{src_file.stem}", template_type="command"
            )
            source_path = resolved_template or src_file
            raw = source_path.read_text(encoding="utf-8")
            processed = self.process_template(
                raw, self.key, script_type, arg_placeholder,
                project_root=project_root,
            )
            dst_name = self.command_filename(src_file.stem)
            dst_file = self.write_file_and_record(
                processed, dest / dst_name, project_root, manifest
            )
            created.append(dst_file)

        # 2. Generate companion .prompt.md files from the templates we just wrote
        prompts_dir = project_root / ".github" / "prompts"
        for src_file in templates:
            cmd_name = f"speckit.{src_file.stem}"
            prompt_content = f"---\nagent: {cmd_name}\n---\n"
            prompt_file = self.write_file_and_record(
                prompt_content,
                prompts_dir / f"{cmd_name}.prompt.md",
                project_root,
                manifest,
            )
            created.append(prompt_file)

        # Write .vscode/settings.json
        settings_src = self._vscode_settings_path()
        if settings_src and settings_src.is_file():
            dst_settings = project_root / ".vscode" / "settings.json"
            dst_settings.parent.mkdir(parents=True, exist_ok=True)
            if dst_settings.exists():
                # Merge into existing — don't track since we can't safely
                # remove the user's settings file on uninstall.
                self._merge_vscode_settings(settings_src, dst_settings)
            else:
                shutil.copy2(settings_src, dst_settings)
                self.record_file_in_manifest(dst_settings, project_root, manifest)
                created.append(dst_settings)


        return created

    def _setup_skills(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Skills mode: delegate to ``_CopilotSkillsHelper`` then post-process."""
        helper = _CopilotSkillsHelper()
        created = SkillsIntegration.setup(
            helper, project_root, manifest, parsed_options, **opts
        )

        # Post-process generated skill files with Copilot-specific frontmatter
        skills_dir = helper.skills_dest(project_root).resolve()
        for path in created:
            try:
                path.resolve().relative_to(skills_dir)
            except ValueError:
                continue
            if path.name != "SKILL.md":
                continue

            content = path.read_text(encoding="utf-8")
            updated = self.post_process_skill_content(content)
            if updated != content:
                path.write_bytes(updated.encode("utf-8"))
                self.record_file_in_manifest(path, project_root, manifest)

        return created

    def _vscode_settings_path(self) -> Path | None:
        """Return path to the bundled vscode-settings.json template."""
        tpl_dir = self.shared_templates_dir()
        if tpl_dir:
            candidate = tpl_dir / "vscode-settings.json"
            if candidate.is_file():
                return candidate
        return None

    @staticmethod
    def _merge_vscode_settings(src: Path, dst: Path) -> None:
        """Merge settings from *src* into existing *dst* JSON file.

        Top-level keys from *src* are added only if missing in *dst*.
        For dict-valued keys, sub-keys are merged the same way.

        If *dst* cannot be parsed (e.g. JSONC with comments), the merge
        is skipped to avoid overwriting user settings.
        """
        try:
            existing = json.loads(dst.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            # Cannot parse existing file (likely JSONC with comments).
            # Skip merge to preserve the user's settings, but show
            # what they should add manually.
            import logging
            template_content = src.read_text(encoding="utf-8")
            logging.getLogger(__name__).warning(
                "Could not parse %s (may contain JSONC comments). "
                "Skipping settings merge to preserve existing file.\n"
                "Please add the following settings manually:\n%s",
                dst, template_content,
            )
            return

        new_settings = json.loads(src.read_text(encoding="utf-8"))

        if not isinstance(existing, dict) or not isinstance(new_settings, dict):
            import logging
            logging.getLogger(__name__).warning(
                "Skipping settings merge: %s or template is not a JSON object.", dst
            )
            return

        changed = False
        for key, value in new_settings.items():
            if key not in existing:
                existing[key] = value
                changed = True
            elif isinstance(existing[key], dict) and isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in existing[key]:
                        existing[key][sub_key] = sub_value
                        changed = True

        if not changed:
            return

        dst.write_text(
            json.dumps(existing, indent=4) + "\n", encoding="utf-8"
        )
