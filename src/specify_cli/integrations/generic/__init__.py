"""Generic integration — bring your own agent.

Requires ``--commands-dir`` to specify the output directory for command
files.  No longer special-cased in the core CLI — just another
integration with its own required option.  ``--skills`` renders the same
templates as ``speckit-<name>/SKILL.md`` directories under that same
directory instead of flat ``speckit.<name>.md`` files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..base import IntegrationOption, MarkdownIntegration, SkillsIntegration, yaml_quote
from ..manifest import IntegrationManifest


class _GenericSkillsHelper(SkillsIntegration):
    """Internal helper supplying skills-mode post-processing for
    ``GenericIntegration`` (e.g. the dot-to-hyphen hook invocation note).

    Not registered in the integration registry — ``GenericIntegration``
    itself renders skills content directly in ``_build_skill_content()``
    and only delegates to this helper's ``post_process_skill_content()``,
    mirroring the pattern ``CopilotIntegration`` uses for its skills mode.
    """

    key = "generic"


class GenericIntegration(MarkdownIntegration):
    """Integration for user-specified (generic) agents."""

    key = "generic"
    config = {
        "name": "Generic (bring your own agent)",
        "folder": None,  # Set dynamically from --commands-dir
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": "",  # Set dynamically from --commands-dir
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--commands-dir",
                required=True,
                help="Directory for command files (e.g. .myagent/commands/)",
            ),
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=False,
                help=(
                    "Render commands as speckit-<name>/SKILL.md directories "
                    "under --commands-dir instead of flat speckit.<name>.md "
                    "files"
                ),
            ),
        ]

    @staticmethod
    def _resolve_commands_dir(
        parsed_options: dict[str, Any] | None,
        opts: dict[str, Any],
    ) -> str:
        """Extract ``--commands-dir`` from parsed options or raw_options.

        Returns the directory string or raises ``ValueError``.
        """
        parsed_options = parsed_options or {}

        # Accept a value only when it is non-BLANK. An empty value resolves to
        # the project root (``project_root / ""``) and a whitespace-only one to
        # a directory literally named " ", so either would silently scatter
        # command files instead of failing with the documented "required"
        # error. ``strip()`` is used ONLY to decide blankness -- the value
        # itself is returned verbatim, so a deliberate (if unusual) padded
        # directory name still targets exactly what the user asked for. Both
        # branches below apply the same rule so they cannot drift apart.
        commands_dir = parsed_options.get("commands_dir")
        if commands_dir and (not isinstance(commands_dir, str) or commands_dir.strip()):
            return commands_dir

        # Fall back to raw_options (--integration-options="--commands-dir ...")
        raw = opts.get("raw_options")
        if raw:
            import shlex
            tokens = shlex.split(raw)
            for i, token in enumerate(tokens):
                if token == "--commands-dir" and i + 1 < len(tokens):
                    candidate = tokens[i + 1]
                    if candidate.strip():
                        return candidate
                if token.startswith("--commands-dir="):
                    candidate = token.split("=", 1)[1]
                    if candidate.strip():
                        return candidate

        raise ValueError(
            "--commands-dir is required for the generic integration"
        )

    def _build_skill_content(
        self, src_file: Path, script_type: str, project_root: Path
    ) -> tuple[str, str]:
        """Render *src_file* as a SKILL.md body.

        Returns ``(skill_name, content)``. Mirrors the frontmatter and
        body shape ``SkillsIntegration.setup()`` produces for other
        skills-format agents, so ``speckit-<name>/SKILL.md`` files
        emitted here follow the same `agentskills.io
        <https://agentskills.io/specification>`_ layout.
        """
        raw = src_file.read_text(encoding="utf-8")
        command_name = src_file.stem
        skill_name = f"speckit-{command_name.replace('.', '-')}"

        frontmatter: dict[str, Any] = {}
        if raw.startswith("---"):
            fm_lines = raw.splitlines(keepends=True)
            fm_close = next(
                (i for i in range(1, len(fm_lines)) if fm_lines[i].rstrip() == "---"),
                None,
            )
            if fm_close is not None:
                try:
                    fm = yaml.safe_load("".join(fm_lines[1:fm_close]))
                    if isinstance(fm, dict):
                        frontmatter = fm
                except yaml.YAMLError:
                    pass

        processed_body = self.process_template(
            raw, self.key, script_type, "$ARGUMENTS",
            project_root=project_root,
            invoke_separator="-",
        )
        if processed_body.startswith("---"):
            body_lines = processed_body.splitlines(keepends=True)
            close_idx = next(
                (i for i in range(1, len(body_lines)) if body_lines[i].rstrip() == "---"),
                None,
            )
            if close_idx is not None:
                processed_body = body_lines[close_idx][3:] + "".join(
                    body_lines[close_idx + 1:]
                )

        description = frontmatter.get("description") or f"Spec Kit: {command_name} workflow"
        skill_content = (
            f"---\n"
            f"name: {yaml_quote(skill_name)}\n"
            f"description: {yaml_quote(description)}\n"
            f"compatibility: {yaml_quote('Requires spec-kit project structure with .specify/ directory')}\n"
            f"metadata:\n"
            f"  author: {yaml_quote('github-spec-kit')}\n"
            f"  source: {yaml_quote('templates/commands/' + src_file.name)}\n"
            f"---\n"
            f"{processed_body}"
        )
        skill_content = _GenericSkillsHelper().post_process_skill_content(skill_content)
        return skill_name, skill_content

    def commands_dest(self, project_root: Path) -> Path:
        """Not supported for GenericIntegration — use setup() directly.

        GenericIntegration is stateless; the output directory comes from
        ``parsed_options`` or ``raw_options`` at call time, not from
        instance state.
        """
        raise ValueError(
            "GenericIntegration.commands_dest() cannot be called directly; "
            "the output directory is resolved from parsed_options in setup()"
        )

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install commands to the user-provided commands directory."""
        commands_dir = self._resolve_commands_dir(parsed_options, opts)

        templates = self.list_command_templates()
        if not templates:
            return []

        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        dest = (project_root / commands_dir).resolve()
        try:
            dest.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Integration destination {dest} escapes "
                f"project root {project_root_resolved}"
            ) from exc
        dest.mkdir(parents=True, exist_ok=True)

        script_type = opts.get("script_type", "sh")
        arg_placeholder = "$ARGUMENTS"
        skills_enabled = bool((parsed_options or {}).get("skills"))
        created: list[Path] = []

        for src_file in templates:
            if skills_enabled:
                skill_name, skill_content = self._build_skill_content(
                    src_file, script_type, project_root
                )
                dst_file = self.write_file_and_record(
                    skill_content, dest / skill_name / "SKILL.md",
                    project_root, manifest
                )
                created.append(dst_file)
                continue

            raw = src_file.read_text(encoding="utf-8")
            processed = self.process_template(
                raw, self.key, script_type, arg_placeholder,
                project_root=project_root,
            )
            dst_name = self.command_filename(src_file.stem)
            dst_file = self.write_file_and_record(
                processed, dest / dst_name, project_root, manifest
            )
            created.append(dst_file)


        return created
