"""RovoDev integration — Atlassian Rovo Dev via ``acli rovodev``.

Extends ``SkillsIntegration`` to generate skill files under
``.rovodev/skills/`` and additionally generates prompt wrappers
under ``.rovodev/prompts/`` and a ``prompts.yml`` manifest.
"""

from __future__ import annotations

import os
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
        "install_url": "https://www.atlassian.com/software/rovo-dev",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".rovodev/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }

    # -- CLI dispatch ------------------------------------------------------

    def _resolve_executable(self) -> str:
        """Return the binary to invoke (``acli``).

        RovoDev is invoked as ``acli rovodev …`` — ``acli`` is the executable
        and ``rovodev`` is a subcommand. The base implementation falls back
        to ``self.key`` (``"rovodev"``), which is the wrong binary, so we
        override the fallback to ``"acli"`` while still honouring the
        standard ``SPECKIT_INTEGRATION_ROVODEV_EXECUTABLE`` env-var override.
        """
        env_name = (
            f"SPECKIT_INTEGRATION_{self.key.upper().replace('-', '_')}_EXECUTABLE"
        )
        override = os.environ.get(env_name, "").strip()
        return override if override else "acli"

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        """Build non-interactive ACLI args for RovoDev.

        RovoDev supports a positional ``message`` for non-interactive runs.
        ``output_json`` maps to ``--output-schema`` so dispatch callers can
        request structured output.

        The integration currently does not apply ``model`` overrides because
        the expected config shape for ``--config-override`` is not yet wired
        in this adapter.

        Honours the standard env-var contract:
          - ``SPECKIT_INTEGRATION_ROVODEV_EXECUTABLE`` overrides ``acli``
          - ``SPECKIT_INTEGRATION_ROVODEV_EXTRA_ARGS`` injects extra CLI flags
        """
        _ = model
        args = [self._resolve_executable(), "rovodev", "run", prompt]
        self._apply_extra_args_env_var(args)
        if output_json:
            args.extend([
                "--output-schema",
                '{"type": "object", "properties": {"result": {"type": "string"}}}',
            ])
        return args


    # -- Prompt wrapper + manifest generation ------------------------------

    @staticmethod
    def _render_prompt_wrapper(skill_name: str) -> str:
        return f"use skill {skill_name} $ARGUMENTS\n"

    def _generate_prompt_files(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        skill_paths: list[Path],
    ) -> tuple[list[Path], list[dict[str, str]]]:
        """Create thin prompt wrappers for each SKILL.md.

        Skill name is derived from the parent directory name
        (e.g. ``.rovodev/skills/speckit-plan/SKILL.md`` → ``speckit-plan``).

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

            skill_name = skill_path.parent.name
            if not skill_name:
                continue

            prompt_filename = f"{skill_name}.prompt.md"
            prompt_file = self.write_file_and_record(
                self._render_prompt_wrapper(skill_name),
                prompts_dir / prompt_filename,
                project_root,
                manifest,
            )
            created.append(prompt_file)

            prompt_entries.append({
                "name": skill_name,
                "description": f"Invoke {skill_name} skill",
                "content_file": f"prompts/{prompt_filename}",
            })

        return created, prompt_entries

    @staticmethod
    def _read_prompts_yml(path: Path) -> list[dict[str, Any]]:
        """Read prompt entries from an existing ``prompts.yml``.

        Returns an empty list if the file is missing, malformed, or
        contains no valid prompt entries.
        """
        if not path.exists():
            return []
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError, UnicodeError):
            return []
        if not isinstance(data, dict):
            return []
        prompts = data.get("prompts")
        if not isinstance(prompts, list):
            return []
        return [dict(item) for item in prompts if isinstance(item, dict)]

    @staticmethod
    def _merge_prompt_entries(
        existing: list[dict[str, Any]],
        generated: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Merge *generated* entries into *existing*, preserving user additions.

        - Existing entries whose ``name`` matches a generated entry are
          replaced in-place (preserving the user's ordering).
        - Generated entries not already present are appended at the end.
        - User-added entries (no matching generated name) are kept as-is.
        """
        generated_by_name = {e["name"]: e for e in generated if e.get("name")}

        merged: list[dict[str, Any]] = []
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

        1. ``SkillsIntegration.setup()`` generates the skill files.
        2. Generates prompt wrappers and ``prompts.yml`` for each skill
           created in step 1.
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
