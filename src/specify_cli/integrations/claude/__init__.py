"""Claude Code integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ...agents import CommandRegistrar
from ..base import IntegrationBase
from ..manifest import IntegrationManifest


class ClaudeIntegration(IntegrationBase):
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

    def command_filename(self, template_name: str) -> str:
        """Claude skills live at .claude/skills/<name>/SKILL.md."""
        skill_name = f"speckit-{template_name.replace('.', '-')}"
        return f"{skill_name}/SKILL.md"

    def _render_skill(self, template_name: str, frontmatter: dict[str, Any], body: str) -> str:
        """Render a processed command template as a Claude skill."""
        skill_name = f"speckit-{template_name.replace('.', '-')}"
        description = frontmatter.get(
            "description",
            f"Spec-kit workflow command: {template_name}",
        )
        skill_frontmatter = CommandRegistrar.build_skill_frontmatter(
            self.key,
            skill_name,
            description,
            f"templates/commands/{template_name}.md",
        )
        frontmatter_text = yaml.safe_dump(skill_frontmatter, sort_keys=False).strip()
        return f"---\n{frontmatter_text}\n---\n\n{body.strip()}\n"

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install Claude skills into .claude/skills."""
        templates = self.list_command_templates()
        if not templates:
            return []

        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        dest = self.commands_dest(project_root).resolve()
        try:
            dest.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Integration destination {dest} escapes "
                f"project root {project_root_resolved}"
            ) from exc
        dest.mkdir(parents=True, exist_ok=True)

        script_type = opts.get("script_type", "sh")
        arg_placeholder = self.registrar_config.get("args", "$ARGUMENTS")
        registrar = CommandRegistrar()
        created: list[Path] = []

        for src_file in templates:
            raw = src_file.read_text(encoding="utf-8")
            processed = self.process_template(raw, self.key, script_type, arg_placeholder)
            frontmatter, body = registrar.parse_frontmatter(processed)
            if not isinstance(frontmatter, dict):
                frontmatter = {}

            rendered = self._render_skill(src_file.stem, frontmatter, body)
            dst_file = self.write_file_and_record(
                rendered,
                dest / self.command_filename(src_file.stem),
                project_root,
                manifest,
            )
            created.append(dst_file)

        created.extend(self.install_scripts(project_root, manifest))
        return created
