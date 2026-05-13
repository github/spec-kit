"""RovoDev integration — Atlassian Rovo Dev via ``acli rovodev``.

Extends ``SkillsIntegration`` to generate skill files under
``.rovodev/skills/`` and additionally generates prompt wrappers
under ``.rovodev/prompts/`` and a ``prompts.yml`` manifest.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..base import SkillsIntegration
from ..manifest import IntegrationManifest


class RovodevIntegration(SkillsIntegration):
    """Integration for Atlassian Rovo Dev.

    Uses the skills layout (``speckit-<name>/SKILL.md``) and adds
    prompt wrappers plus a ``prompts.yml`` manifest on top.
    Runtime execution dispatches through ``acli rovodev``.
    """

    key = "rovodev"
    config = {
        "name": "RovoDev ACLI",
        "folder": ".rovodev/",
        "commands_subdir": "skills",
        "install_url": "https://www.atlassian.com/software/rovo",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".rovodev/prompts",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".prompt.md",
    }
    context_file = "AGENTS.md"


    # -- CLI dispatch ------------------------------------------------------

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        args = ["acli", "rovodev", "-p", prompt]
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--output-format", "json"])
        return args


    # -- Prompt wrapper + manifest generation ------------------------------

    @staticmethod
    def _render_prompt_wrapper(command_name: str) -> str:
        return f"use skill {command_name} $ARGUMENTS\n"

    @staticmethod
    def _skill_name_to_dot_name(skill_name: str) -> str:
        """Convert skill names like ``speckit-git-commit`` to ``speckit.git.commit``."""
        if skill_name.startswith("speckit-"):
            stem = skill_name[len("speckit-"):]
            return "speckit." + stem.replace("-", ".")
        return skill_name

    def _generate_prompt_files(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        skill_paths: list[Path],
    ) -> tuple[list[Path], list[dict[str, str]]]:
        """Create thin prompt wrappers for each SKILL.md.

        Returns (created_files, prompt_entries) where prompt_entries are
        dicts suitable for inclusion in ``prompts.yml``.
        """
        prompts_dir = project_root / ".rovodev" / "prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)

        created: list[Path] = []
        prompt_entries: list[dict[str, str]] = []

        for skill_path in skill_paths:
            if skill_path.name != "SKILL.md":
                continue

            content = skill_path.read_text(encoding="utf-8")
            if not content.startswith("---"):
                continue
            parts = content.split("---", 2)
            if len(parts) < 3:
                continue
            try:
                fm = yaml.safe_load(parts[1])
                if not isinstance(fm, dict):
                    continue
            except yaml.YAMLError:
                continue

            skill_name = fm.get("name", "")
            description = fm.get("description", "")
            if not skill_name:
                continue

            # Convert skill name (speckit-plan) to dot format (speckit.plan)
            # for prompt wrappers and prompts.yml.
            dot_name = self._skill_name_to_dot_name(skill_name)

            prompt_filename = f"{dot_name}.prompt.md"
            # Wrapper must call the concrete skill name (hyphenated), not dotted form.
            prompt_content = self._render_prompt_wrapper(skill_name)
            prompt_file = self.write_file_and_record(
                prompt_content,
                prompts_dir / prompt_filename,
                project_root,
                manifest,
            )
            created.append(prompt_file)

            prompt_entries.append({
                "name": dot_name,
                "description": description,
                "content_file": f"prompts/{prompt_filename}",
            })

        return created, prompt_entries

    @staticmethod
    def _read_prompts_yml(path: Path) -> list[dict[str, str]]:
        """Read prompt entries from an existing ``prompts.yml``.

        Returns an empty list if the file is missing, malformed, or
        contains no valid prompt entries.
        """
        if not path.exists():
            return []
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            return []
        if not isinstance(data, dict):
            return []
        prompts = data.get("prompts")
        if not isinstance(prompts, list):
            return []
        return [dict(item) for item in prompts if isinstance(item, dict)]

    @staticmethod
    def _merge_prompt_entries(
        existing: list[dict[str, str]],
        generated: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Merge *generated* entries into *existing*, preserving user additions.

        - Existing entries whose ``name`` matches a generated entry are
          replaced in-place (preserving the user's ordering).
        - Generated entries not already present are appended at the end.
        - User-added entries (no matching generated name) are kept as-is.
        """
        generated_by_name = {e["name"]: e for e in generated if e.get("name")}

        merged: list[dict[str, str]] = []
        seen: set[str] = set()

        for entry in existing:
            name = entry.get("name", "")
            if name in generated_by_name:
                merged.append(generated_by_name[name])
                seen.add(name)
            else:
                merged.append(entry)

        for entry in generated:
            if entry.get("name", "") not in seen:
                merged.append(entry)

        return merged

    def _merge_prompts_manifest(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        prompt_entries: list[dict[str, str]],
    ) -> Path | None:
        """Write ``prompts.yml``, merging with any existing user entries."""
        if not prompt_entries:
            return None

        prompts_yml = project_root / ".rovodev" / "prompts.yml"
        existing = self._read_prompts_yml(prompts_yml)
        merged = self._merge_prompt_entries(existing, prompt_entries)

        content = yaml.safe_dump(
            {"prompts": merged},
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=10_000,
        )
        return self.write_file_and_record(
            content, prompts_yml, project_root, manifest,
        )

    # -- setup() -----------------------------------------------------------

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install RovoDev skills, then generate prompt wrappers and manifest.

        1. ``SkillsIntegration.setup()`` generates skill files and
           upserts the context section.
        2. Generate prompt wrappers and ``prompts.yml``.
        """
        created = super().setup(project_root, manifest, parsed_options, **opts)


        # Generate prompt wrappers + merge prompts.yml
        prompt_files, prompt_entries = self._generate_prompt_files(
            project_root, manifest, created
        )
        created.extend(prompt_files)

        manifest_file = self._merge_prompts_manifest(
            project_root, manifest, prompt_entries
        )
        if manifest_file:
            created.append(manifest_file)

        return created

