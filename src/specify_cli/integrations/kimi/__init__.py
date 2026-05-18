"""Kimi Code integration — skills-based agent (Moonshot AI).

Kimi uses the ``.kimi/skills/speckit-<name>/SKILL.md`` layout with
``/skill:speckit-<name>`` invocation syntax.

Includes legacy migration logic for projects initialised before Kimi
moved from dotted skill directories (``speckit.xxx``) to hyphenated
(``speckit-xxx``).
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from ..base import IntegrationOption, SkillsIntegration
from ..manifest import IntegrationManifest


class KimiIntegration(SkillsIntegration):
    """Integration for Kimi Code CLI (Moonshot AI)."""

    key = "kimi"
    config = {
        "name": "Kimi Code",
        "folder": ".kimi/",
        "commands_subdir": "skills",
        "install_url": "https://code.kimi.com/",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".kimi/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    context_file = "KIMI.md"
    multi_install_safe = True

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for Kimi)",
            ),
            IntegrationOption(
                "--migrate-legacy",
                is_flag=True,
                default=False,
                help="Migrate legacy dotted skill dirs (speckit.xxx → speckit-xxx)",
            ),
        ]

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install skills with optional legacy dotted-name migration."""
        parsed_options = parsed_options or {}

        # Run base setup first so hyphenated targets (speckit-*) exist,
        # then migrate/clean legacy dotted dirs without risking user content loss.
        created = super().setup(
            project_root, manifest, parsed_options=parsed_options, **opts
        )

        if parsed_options.get("migrate_legacy", False):
            skills_dir = self.skills_dest(project_root)
            if skills_dir.is_dir():
                _migrate_legacy_kimi_dotted_skills(skills_dir)

        return created


def _migrate_legacy_kimi_dotted_skills(skills_dir: Path) -> tuple[int, int]:
    """Migrate legacy Kimi dotted skill dirs (speckit.xxx) to hyphenated format.

    Returns ``(migrated_count, removed_count)``.
    """
    if not skills_dir.is_dir():
        return (0, 0)

    migrated_count = 0
    removed_count = 0

    for legacy_dir in sorted(skills_dir.glob("speckit.*")):
        if not legacy_dir.is_dir():
            continue
        if not (legacy_dir / "SKILL.md").exists():
            continue

        suffix = legacy_dir.name[len("speckit."):]
        if not suffix:
            continue

        target_dir = skills_dir / f"speckit-{suffix.replace('.', '-')}"

        if not target_dir.exists():
            shutil.move(str(legacy_dir), str(target_dir))
            migrated_count += 1
            continue

        # Target exists — only remove legacy if SKILL.md is identical
        target_skill = target_dir / "SKILL.md"
        legacy_skill = legacy_dir / "SKILL.md"
        if target_skill.is_file():
            try:
                if target_skill.read_bytes() == legacy_skill.read_bytes():
                    has_extra = any(
                        child.name != "SKILL.md" for child in legacy_dir.iterdir()
                    )
                    if not has_extra:
                        shutil.rmtree(legacy_dir)
                        removed_count += 1
            except OSError:
                pass

    return (migrated_count, removed_count)
