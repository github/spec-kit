"""Hermes Agent integration — skills-based agent.

Hermes Agent (https://github.com/NousResearch/hermes-agent) is an open-source
AI agent framework by Nous Research.  It stores skills in
``~/.hermes/skills/`` (user-global) rather than a project-local directory.

Usage::

    specify init my-project --integration hermes
    specify init --here --ai hermes
"""

from __future__ import annotations

from pathlib import Path
from shutil import rmtree
from typing import Any

import yaml

from ..base import IntegrationOption, SkillsIntegration
from ..manifest import IntegrationManifest


class HermesIntegration(SkillsIntegration):
    """Integration for Hermes Agent skills.

    Hermes loads skills from ``~/.hermes/skills/`` (user home directory)
    rather than a project-local path.  Skills are installed directly to
    the global directory — no project-local copies are created since
    Hermes discovers them globally.  A project-local marker directory
    (``.hermes/skills/`` empty) is created so extension commands (e.g.
    git) can detect Hermes as an active integration.  Uninstall removes
    both the marker and all global ``speckit-*`` skills, matching the
    standard integration teardown behaviour.
    """

    key = "hermes"
    config = {
        "name": "Hermes Agent",
        "folder": ".hermes/",
        "commands_subdir": "skills",
        "install_url": "https://github.com/NousResearch/hermes-agent",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": "~/.hermes/skills",
        "detect_dir": ".hermes/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    context_file = "AGENTS.md"

    # -- Helpers -----------------------------------------------------------

    @staticmethod
    def _hermes_home_skills_dir() -> Path:
        """Return ``~/.hermes/skills/`` — the global skills directory."""
        return Path.home() / ".hermes" / "skills"

    # -- Options -----------------------------------------------------------

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for Hermes Agent)",
            ),
        ]

    # -- Setup -------------------------------------------------------------

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install command templates as global Hermes skills.

        Writes each skill directly to
        ``~/.hermes/skills/speckit-<name>/SKILL.md`` where Hermes
        discovers them at runtime.  No project-local SKILL.md copies are
        created — the global directory is the single source of truth.
        A project-local marker (``.hermes/skills/`` empty) is created
        so extension commands (e.g. git) can detect Hermes as an active
        integration.
        """
        templates = self.list_command_templates()
        if not templates:
            return []

        # Safety check: verify manifest project_root matches (standard pattern)
        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        script_type = opts.get("script_type", "sh")
        arg_placeholder = (
            self.registrar_config.get("args", "$ARGUMENTS")
            if self.registrar_config
            else "$ARGUMENTS"
        )

        global_skills_dir = self._hermes_home_skills_dir()
        global_skills_dir.mkdir(parents=True, exist_ok=True)

        created: list[Path] = []

        for src_file in templates:
            raw = src_file.read_text(encoding="utf-8")

            # Derive the skill name from the template stem
            command_name = src_file.stem  # e.g. "plan"
            skill_name = f"speckit-{command_name.replace('.', '-')}"

            # Parse frontmatter for description
            frontmatter: dict[str, Any] = {}
            if raw.startswith("---"):
                parts = raw.split("---", 2)
                if len(parts) >= 3:
                    try:
                        fm = yaml.safe_load(parts[1])
                        if isinstance(fm, dict):
                            frontmatter = fm
                    except yaml.YAMLError:
                        pass

            # Process body through the standard template pipeline
            processed_body = self.process_template(
                raw,
                self.key,
                script_type,
                arg_placeholder,
                context_file=self.context_file or "",
                invoke_separator=self.invoke_separator,
            )
            # Strip the processed frontmatter — we rebuild it for skills.
            if processed_body.startswith("---"):
                parts = processed_body.split("---", 2)
                if len(parts) >= 3:
                    processed_body = parts[2]

            # Select description
            description = frontmatter.get("description", "")
            if not description:
                description = f"Spec Kit: {command_name} workflow"

            # Build SKILL.md with manually formatted frontmatter
            def _quote(v: str) -> str:
                escaped = v.replace("\\", "\\\\").replace('"', '\\"')
                return f'"{escaped}"'

            skill_content = (
                f"---\n"
                f"name: {_quote(skill_name)}\n"
                f"description: {_quote(description)}\n"
                f"compatibility: "
                f"{_quote('Requires spec-kit project structure with .specify/ directory')}\n"
                f"metadata:\n"
                f"  author: {_quote('github-spec-kit')}\n"
                f"  source: {_quote('templates/commands/' + src_file.name)}\n"
                f"---\n"
                f"{processed_body}"
            )

            skill_content = self.post_process_skill_content(skill_content)

            # Write directly to global ~/.hermes/skills/speckit-<name>/SKILL.md
            skill_dir = global_skills_dir / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_file = skill_dir / "SKILL.md"
            normalized = skill_content.replace("\r\n", "\n")
            skill_file.write_bytes(normalized.encode("utf-8"))
            created.append(skill_file)

        # Upsert managed context section into the agent context file
        self.upsert_context_section(project_root)

        # Create project-local marker directory so extension commands
        # (e.g. git) can detect Hermes as an active integration.
        # Hermes itself ignores this directory — skills live globally.
        (project_root / ".hermes" / "skills").mkdir(parents=True, exist_ok=True)

        return created

    # -- Uninstall ---------------------------------------------------------

    def teardown(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        *,
        force: bool = False,
    ) -> tuple[list[Path], list[Path]]:
        """Uninstall integration files including global Hermes skills.

        Removes the managed context section from AGENTS.md, removes the
        project-local marker directory (if empty), delegates to
        ``manifest.uninstall()`` for project-local tracked files, and
        removes all ``speckit-*`` skills under ``~/.hermes/skills/``.

        Global skills are always removed on teardown — this matches the
        standard integration behaviour where all files created by the
        integration are removed on ``specify integration uninstall``.
        """
        # Remove managed context section from AGENTS.md
        self.remove_context_section(project_root)

        # Delegate to manifest for project-local tracked files (scripts,
        # templates, context entries tracked in the manifest).
        removed, skipped = manifest.uninstall(project_root, force=force)

        # Remove project-local marker directory if empty
        local_skills_dir = project_root / ".hermes" / "skills"
        if local_skills_dir.is_dir() and not any(local_skills_dir.iterdir()):
            local_skills_dir.rmdir()
            hermes_dir = project_root / ".hermes"
            if hermes_dir.is_dir() and not any(hermes_dir.iterdir()):
                hermes_dir.rmdir()

        # Remove all global Hermes skills for speckit — these are always
        # removed on uninstall regardless of the force flag, matching the
        # standard behaviour where all integration files are cleaned up.
        global_skills_dir = self._hermes_home_skills_dir()
        if global_skills_dir.is_dir():
            for skill_dir in sorted(global_skills_dir.iterdir()):
                if skill_dir.is_dir() and skill_dir.name.startswith("speckit-"):
                    try:
                        rmtree(skill_dir)
                        removed.append(skill_dir)
                    except OSError:
                        skipped.append(skill_dir)

        return removed, skipped

    # -- CLI dispatch ------------------------------------------------------

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        """Build Hermes CLI invocation for programmatic dispatch.

        Uses ``hermes chat -Q -q`` for one-shot queries in quiet mode,
        mapping slash-command invocations to the appropriate skill-based
        dispatch.
        """
        args = [self._resolve_executable(), "chat", "-Q"]

        if model:
            args.extend(["-m", model])
        if output_json:
            args.append("--json")

        # If prompt starts with a slash command, pass it directly
        # so Hermes can dispatch to the appropriate skill.
        if prompt.startswith("/"):
            command, _, remainder = prompt[1:].partition(" ")
            if command:
                args.extend(["-s", command])
                if remainder:
                    args.extend(["-q", remainder])
            else:
                args.extend(["-q", prompt])
        else:
            args.extend(["-q", prompt])

        return args
