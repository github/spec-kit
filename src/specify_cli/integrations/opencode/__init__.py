"""opencode integration."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from ..base import IntegrationOption, MarkdownIntegration, SkillsIntegration
from ..manifest import IntegrationManifest


class _OpencodeSkillsHelper(SkillsIntegration):
    """Internal delegate used by OpencodeIntegration when --skills is active."""

    key = "opencode"
    config = {
        "name": "opencode",
        "folder": ".opencode/",
        "commands_subdir": "skills",
        "install_url": "https://opencode.ai",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".opencode/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    context_file = "AGENTS.md"


class OpencodeIntegration(MarkdownIntegration):
    key = "opencode"
    config = {
        "name": "opencode",
        "folder": ".opencode/",
        "commands_subdir": "commands",
        "install_url": "https://opencode.ai",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".opencode/commands",
        "legacy_dir": ".opencode/command",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = "AGENTS.md"
    # Mutable flag set by setup() — indicates the active scaffolding mode.
    _skills_mode: bool = False

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=False,
                help="Scaffold commands as agent skills (speckit-<name>/SKILL.md) instead of .md files",
            ),
        ]

    def effective_invoke_separator(
        self, parsed_options: dict[str, Any] | None = None
    ) -> str:
        if parsed_options and parsed_options.get("skills"):
            return "-"
        if self._skills_mode:
            return "-"
        return self.invoke_separator  # default: "."

    def build_command_invocation(self, command_name: str, args: str = "") -> str:
        if not self._skills_mode:
            return super().build_command_invocation(command_name, args)
        stem = command_name
        if stem.startswith("speckit."):
            stem = stem[len("speckit."):]
        invocation = "/speckit-" + stem.replace(".", "-")
        if args:
            invocation = f"{invocation} {args}"
        return invocation

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
        # Derive skills mode from project layout when project_root is provided;
        # fall back to _skills_mode only when no root is given. This prevents
        # stale _skills_mode=True from a prior setup() affecting subsequent
        # dispatches against non-skills projects.
        if project_root:
            skills_dir = project_root / ".opencode" / "skills"
            skills_mode = skills_dir.is_dir() and any(
                d.is_dir() and (d / "SKILL.md").is_file()
                for d in skills_dir.glob("speckit-*")
            )
        else:
            skills_mode = self._skills_mode

        stem = command_name
        if stem.startswith("speckit."):
            stem = stem[len("speckit."):]
        if skills_mode:
            invocation = "/speckit-" + stem.replace(".", "-")
        else:
            invocation = "/speckit." + stem
        if args:
            invocation = f"{invocation} {args}"

        exec_args = self.build_exec_args(invocation, model=model, output_json=not stream)
        cwd = str(project_root) if project_root else None

        if stream:
            try:
                result = subprocess.run(exec_args, text=True, cwd=cwd)
            except KeyboardInterrupt:
                return {"exit_code": 130, "stdout": "", "stderr": "Interrupted by user"}
            return {"exit_code": result.returncode, "stdout": "", "stderr": ""}

        result = subprocess.run(
            exec_args, capture_output=True, text=True, cwd=cwd, timeout=timeout,
        )
        return {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        parsed_options = parsed_options or {}
        self._skills_mode = bool(parsed_options.get("skills"))
        if self._skills_mode:
            return _OpencodeSkillsHelper().setup(project_root, manifest, parsed_options, **opts)
        return super().setup(project_root, manifest, parsed_options, **opts)

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        args = [self._resolve_executable(), "run"]
        # Apply operator-injected extra args before the prompt-derived
        # --command and the canonical --format/-m flags so Spec Kit's
        # later appends remain authoritative under repeated-flag CLI
        # semantics.
        self._apply_extra_args_env_var(args)

        message = prompt
        if prompt.startswith("/"):
            command, _, remainder = prompt[1:].partition(" ")
            if command:
                args.extend(["--command", command])
                message = remainder

        if model:
            args.extend(["-m", model])
        if output_json:
            args.extend(["--format", "json"])
        if message:
            args.append(message)
        return args
