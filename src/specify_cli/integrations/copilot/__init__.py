"""Copilot integration — GitHub Copilot in VS Code.

Copilot has several unique behaviors compared to standard markdown agents:
- Commands use ``.agent.md`` extension (not ``.md``)
- Each command gets a companion ``.prompt.md`` file in ``.github/prompts/``
- Installs ``.vscode/settings.json`` with prompt file recommendations
- Context file lives at ``.github/copilot-instructions.md``
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from ..base import IntegrationBase
from ..manifest import IntegrationManifest


class CopilotIntegration(IntegrationBase):
    """Integration for GitHub Copilot (VS Code IDE + CLI).

    The IDE integration (``requires_cli: False``) installs ``.agent.md``
    command files.  Workflow dispatch additionally requires the
    ``copilot`` CLI to be installed separately.
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
    context_file = ".github/copilot-instructions.md"

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        # GitHub Copilot CLI uses ``copilot -p "prompt"`` for
        # non-interactive mode.  --allow-all-tools is required for the
        # agent to perform file edits and shell commands.  Controlled
        # by SPECKIT_ALLOW_ALL_TOOLS env var (default: enabled).
        import os
        args = ["copilot", "-p", prompt]
        if os.environ.get("SPECKIT_ALLOW_ALL_TOOLS", "1") != "0":
            args.append("--allow-all-tools")
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--output-format", "json"])
        return args

    def build_command_invocation(self, command_name: str, args: str = "") -> str:
        """Copilot agents are not slash-commands — just return the args as prompt."""
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
        """
        import subprocess

        stem = command_name
        if "." in stem:
            stem = stem.rsplit(".", 1)[-1]
        agent_name = f"speckit.{stem}"

        prompt = args or ""
        import os
        cli_args = [
            "copilot", "-p", prompt,
            "--agent", agent_name,
        ]
        if os.environ.get("SPECKIT_ALLOW_ALL_TOOLS", "1") != "0":
            cli_args.append("--allow-all-tools")
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

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install copilot commands, companion prompts, and VS Code settings.

        Uses base class primitives to: read templates, process them
        (replace placeholders, strip script blocks, rewrite paths),
        write as ``.agent.md``, then add companion prompts and VS Code settings.
        """
        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        templates = self.list_command_templates()
        if not templates:
            return []

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
            raw = src_file.read_text(encoding="utf-8")
            processed = self.process_template(raw, self.key, script_type, arg_placeholder)
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

        # 4. Install integration-specific update-context scripts
        created.extend(self.install_scripts(project_root, manifest))

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
        except (json.JSONDecodeError, OSError):
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
