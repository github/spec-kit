"""
Mistral Vibe CLI integration — skills-based agent.

Vibe uses ``.vibe/skills/speckit-<name>/SKILL.md`` layout (enforced since v2.0.0).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..base import IntegrationOption, SkillsIntegration
from ..manifest import IntegrationManifest


class VibeIntegration(SkillsIntegration):
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
    context_file = "AGENTS.md"

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills",
            ),
        ]

    @staticmethod
    def _inject_frontmatter_flag(content: str, key: str, value: str = "true") -> str:
        """
        Insert ``key: value`` before the closing ``---`` if not already present.
        Value: true by default
        """
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
        """
        Inject Vibe-specific frontmatter flags:
        - user-invocable: allows the skill to be invoked by the user (not just other agents)
        """
        updated = self._inject_frontmatter_flag(content, "user-invocable")
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

        created = super().setup(project_root, manifest, parsed_options=parsed_options, **opts)

        # Post-process generated skill files
        skills_dir = self.skills_dest(project_root).resolve()

        for path in created:
            # Only touch SKILL.md files under the skills directory
            try:
                path.resolve().relative_to(skills_dir)
            except ValueError:
                continue
            if path.name != "SKILL.md":
                continue

            content_bytes = path.read_bytes()
            content = content_bytes.decode("utf-8")

            updated = self.post_process_skill_content(content)

            if updated != content:
                path.write_bytes(updated.encode("utf-8"))
                self.record_file_in_manifest(path, project_root, manifest)

        return created
