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
    """Integration for GitHub Copilot in VS Code."""

    key = "copilot"
    config = {
        "name": "GitHub Copilot",
        "folder": ".github/",
        "commands_subdir": "agents",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".github/agents",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".agent.md",
    }
    context_file = ".github/copilot-instructions.md"

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
        scripts_src = Path(__file__).resolve().parent / "scripts"
        if scripts_src.is_dir():
            scripts_dest = project_root / ".specify" / "integrations" / "copilot" / "scripts"
            scripts_dest.mkdir(parents=True, exist_ok=True)
            for src_script in sorted(scripts_src.iterdir()):
                if src_script.is_file():
                    dst_script = scripts_dest / src_script.name
                    shutil.copy2(src_script, dst_script)
                    # Make shell scripts executable
                    if dst_script.suffix == ".sh":
                        dst_script.chmod(dst_script.stat().st_mode | 0o111)
                    self.record_file_in_manifest(dst_script, project_root, manifest)
                    created.append(dst_script)

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

        for key, value in new_settings.items():
            if key not in existing:
                existing[key] = value
            elif isinstance(existing[key], dict) and isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in existing[key]:
                        existing[key][sub_key] = sub_value

        dst.write_text(
            json.dumps(existing, indent=4) + "\n", encoding="utf-8"
        )
