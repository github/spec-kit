"""Claude Code integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .skill_postprocess import (
    ARGUMENT_HINTS,
    apply_claude_skill_postprocess,
    inject_argument_hint,
    inject_frontmatter_flag,
    inject_hook_command_note,
    set_frontmatter_key,
)
from ..base import SkillsIntegration
from ..manifest import IntegrationManifest


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
        """Delegate to shared Claude skill transform implementation."""
        return inject_argument_hint(content, hint)

    @staticmethod
    def _inject_frontmatter_flag(content: str, key: str, value: str = "true") -> str:
        """Delegate to shared Claude skill transform implementation."""
        return inject_frontmatter_flag(content, key, value)

    @staticmethod
    def _inject_hook_command_note(content: str) -> str:
        """Delegate to shared Claude skill transform implementation."""
        return inject_hook_command_note(content)

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

    def post_process_skill_content(self, content: str) -> str:
        """Inject Claude-specific frontmatter flags and hook notes (no argument-hint).

        Used by preset/extension skill generators; matches flags applied during
        ``setup()`` except for fenced question rendering and argument-hint lines.
        """
        updated = inject_frontmatter_flag(content, "user-invocable")
        updated = set_frontmatter_key(updated, "disable-model-invocation", "false")
        updated = inject_hook_command_note(updated)
        return updated

    @classmethod
    def render_skill_postprocess(cls, content: str, skill_path: Path) -> str:
        """Run Claude-specific skill post-processing pipeline."""
        return apply_claude_skill_postprocess(content, skill_path)

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install Claude skills, then run the skill post-process extension chain."""
        created = super().setup(project_root, manifest, parsed_options, **opts)

        skills_dir = self.skills_dest(project_root).resolve()

        for path in created:
            try:
                path.resolve().relative_to(skills_dir)
            except ValueError:
                continue
            if path.name != "SKILL.md":
                continue

            content_bytes = path.read_bytes()
            content = content_bytes.decode("utf-8")

            updated = self.render_skill_postprocess(content, path)

            if updated != content:
                path.write_bytes(updated.encode("utf-8"))
                self.record_file_in_manifest(path, project_root, manifest)

        return created
