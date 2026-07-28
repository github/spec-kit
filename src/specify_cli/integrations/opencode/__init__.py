"""opencode integration.

opencode discovers agent extensions from two locations:

- **Skills** (native, recommended): ``.opencode/skills/<name>/SKILL.md`` at the
  project level and ``~/.config/opencode/skills/`` globally. Skills carry
  ``name`` + ``description`` frontmatter and are invoked as ``/speckit-<name>``.
- **Commands** (legacy): ``.opencode/commands/speckit.<name>.md`` slash-command
  files, with ``.opencode/command/`` as a deprecated predecessor.

By default this integration installs markdown **commands** (unchanged historic
behaviour). Pass ``--skills`` via ``--integration-options`` to install native
opencode **skills** (``.opencode/skills/speckit-<name>/SKILL.md``) instead —
the layout modern opencode loads automatically. The two modes are mutually
exclusive, mirroring the Copilot ``--skills`` integration.
"""

from __future__ import annotations

from typing import Any

from ..base import IntegrationOption, MarkdownIntegration, SkillsIntegration


class _OpencodeSkillsHelper(SkillsIntegration):
    """Internal skills-mode installer for opencode.

    Not registered in the integration registry — only used as a delegate by
    :class:`OpencodeIntegration` when ``--skills`` is passed. Installs
    ``speckit-<name>/SKILL.md`` under ``.opencode/skills/``.
    """

    key = "opencode"
    config = {
        "name": "opencode",
        "folder": ".opencode/",
        "commands_subdir": "skills",
        "install_url": "https://opencode.ai",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".opencode/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    multi_install_safe = True


class OpencodeIntegration(MarkdownIntegration):
    """Integration for opencode.

    Default mode installs markdown commands in ``.opencode/commands/``.
    With ``--skills`` it installs native opencode skills in
    ``.opencode/skills/speckit-<name>/SKILL.md``.
    """

    key = "opencode"
    config = {
        "name": "opencode",
        "folder": ".opencode/",
        "commands_subdir": "commands",
        "install_url": "https://opencode.ai",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".opencode/commands",
        "legacy_dir": ".opencode/command",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }

    # Mutable flag set by setup() — indicates the active scaffolding mode.
    _skills_mode: bool = False

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=False,
                help="Install native opencode skills (.opencode/skills/speckit-<name>/SKILL.md) instead of commands",
            ),
        ]

    def effective_invoke_separator(
        self, parsed_options: dict[str, Any] | None = None
    ) -> str:
        """Return ``"-"`` when skills mode is requested, ``"."`` otherwise."""
        if parsed_options and parsed_options.get("skills"):
            return "-"
        if self._skills_mode:
            return "-"
        return self.invoke_separator

    def build_command_invocation(self, command_name: str, args: str = "") -> str:
        """Skills mode uses ``/speckit-<stem>``; commands mode uses ``/speckit.<stem>``."""
        if self._skills_mode:
            stem = command_name
            if stem.startswith("speckit."):
                stem = stem[len("speckit."):]
            invocation = "/speckit-" + stem.replace(".", "-")
            if args:
                invocation = f"{invocation} {args}"
            return invocation
        return super().build_command_invocation(command_name, args)

    def post_process_skill_content(self, content: str) -> str:
        """Delegate to the skills helper for shared hook-guidance injection."""
        return _OpencodeSkillsHelper().post_process_skill_content(content)

    def setup(
        self,
        project_root,
        manifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ):
        """Install commands (default) or native skills (``--skills``)."""
        parsed_options = parsed_options or {}
        self._skills_mode = bool(parsed_options.get("skills"))
        if self._skills_mode:
            return self._setup_skills(project_root, manifest, parsed_options, **opts)
        return super().setup(project_root, manifest, parsed_options, **opts)

    def _setup_skills(
        self,
        project_root,
        manifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ):
        """Skills mode: delegate to ``_OpencodeSkillsHelper`` then post-process."""
        helper = _OpencodeSkillsHelper()
        created = SkillsIntegration.setup(
            helper, project_root, manifest, parsed_options, **opts
        )

        skills_dir = helper.skills_dest(project_root).resolve()
        for path in created:
            try:
                path.resolve().relative_to(skills_dir)
            except ValueError:
                continue
            if path.name != "SKILL.md":
                continue
            content = path.read_text(encoding="utf-8")
            updated = self.post_process_skill_content(content)
            if updated != content:
                path.write_bytes(updated.encode("utf-8"))
                self.record_file_in_manifest(path, project_root, manifest)

        return created

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        args = [self._resolve_executable(), "run"]
        # Apply operator-injected extra args before the prompt-derived
        # --command and the canonical --format/-m flags so Spec Kit's
        # later appends remain authoritative under repeated-flag CLI
        # semantics.
        self._apply_extra_args_env_var(args)

        message = prompt
        if prompt.startswith("/"):
            command, _, remainder = prompt[1:].partition(" ")
            if command:
                args.extend(["--command", command])
                message = remainder

        if model:
            args.extend(["-m", model])
        if output_json:
            args.extend(["--format", "json"])
        if message:
            args.append(message)
        return args
