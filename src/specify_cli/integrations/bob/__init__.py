"""IBM Bob integration.

Bob 2.0 uses the ``.bob/skills/speckit-<name>/SKILL.md`` layout by default.
The legacy ``.bob/commands/*.md`` layout (Bob 1.x) remains available as an
opt-in via ``--integration-options "--legacy-commands"``.

Bob is a *dual-mode* integration: whether it scaffolds skills or commands is
a per-project **configuration** decision (the ``--legacy-commands`` option,
persisted as ``ai_skills`` in init-options), not a property of the class.
It therefore extends :class:`IntegrationBase` (like Copilot, the other
dual-mode agent) and resolves the mode through the ``is_skills_mode`` hook,
delegating the actual scaffolding to a per-layout helper.

Deprecation cycle:
  This release:  Skills layout is the default; legacy ``.bob/commands/`` is
                 opt-in via ``--legacy-commands``.
  Next cycle:    ``--legacy-commands`` flag removed.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import typer

from ..base import (
    IntegrationBase,
    IntegrationOption,
    MarkdownIntegration,
    SkillsIntegration,
)
from ..manifest import IntegrationManifest


def _validate_mode_options(parsed_options: dict[str, Any] | None) -> None:
    """Reject ``--skills`` and ``--legacy-commands`` used together.

    The two flags select opposite layouts, so combining them is ambiguous.
    Fail fast with the same clean exit-1 UX as other bad-option paths rather
    than silently letting one win.
    """
    opts = parsed_options or {}
    if opts.get("skills") and opts.get("legacy_commands"):
        from ..._console import console

        console.print(
            "[red]Error:[/red] --skills and --legacy-commands are mutually "
            "exclusive; pass only one."
        )
        raise typer.Exit(1)


def _warn_legacy_commands_deprecated() -> None:
    warnings.warn(
        "Bob legacy commands mode (.bob/commands/) is deprecated and will be "
        "removed in a future Spec Kit release. Omit --legacy-commands to use "
        "the default skills layout (.bob/skills/).",
        UserWarning,
        stacklevel=3,
    )


class _BobSkillsHelper(SkillsIntegration):
    """Default-mode helper: ``.bob/skills/speckit-<name>/SKILL.md``.

    Not registered in the integration registry — used only as a delegate by
    :class:`BobIntegration` for skills-mode ``setup()``.
    """

    key = "bob"
    config = {
        "name": "IBM Bob",
        "folder": ".bob/",
        "commands_subdir": "skills",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".bob/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }

    def post_process_skill_content(self, content: str) -> str:
        """Bob skills are intent-activated; no slash-command note is needed."""
        return content


class _BobMarkdownHelper(MarkdownIntegration):
    """Legacy-mode helper: ``.bob/commands/speckit.<name>.md`` (Bob 1.x).

    Not registered in the integration registry — used only as a delegate by
    :class:`BobIntegration` when ``--legacy-commands`` is passed.  Declares
    ``invoke_separator="."`` so command-reference tokens render as Bob 1.x
    ``/speckit.<name>`` invocations.
    """

    key = "bob"
    invoke_separator = "."
    config = {
        "name": "IBM Bob",
        "folder": ".bob/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".bob/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
        "invoke_separator": ".",
    }


class BobIntegration(IntegrationBase):
    """Integration for IBM Bob IDE (dual-mode; skills by default).

    Whether a project uses the skills or the legacy commands layout is a
    configuration choice resolved by :meth:`is_skills_mode`, not the class
    hierarchy.  ``setup()`` delegates to the matching helper.

    ``registrar_config`` mirrors the *commands* layout (``extension: ".md"``,
    ``dir: ".bob/commands"``) — the same pattern Copilot uses — so that
    ``CommandRegistrar.AGENT_CONFIGS["bob"]`` drives extension/preset
    registration into ``.bob/commands/`` for legacy-mode projects, while
    skills-mode projects have that command registration transparently skipped
    (``skills_mode_active`` becomes ``True`` because ``ai_skills=True`` and
    ``extension != "/SKILL.md"``) and receive extension skills instead.
    ``invoke_separator = "-"`` matches the default (skills) layout.
    """

    key = "bob"
    invoke_separator = "-"
    config = {
        "name": "IBM Bob",
        "folder": ".bob/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".bob/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=False,
                help=(
                    "Force the default skills layout (.bob/skills/), overriding "
                    "on-disk auto-detection. Use this to migrate a legacy "
                    "commands install to skills, e.g. "
                    "`integration upgrade bob --integration-options \"--skills\"`"
                ),
            ),
            IntegrationOption(
                "--legacy-commands",
                is_flag=True,
                default=False,
                help=(
                    "Scaffold commands as legacy .bob/commands/*.md files "
                    "(Bob 1.x layout, deprecated) instead of the default "
                    "skills layout"
                ),
            ),
        ]

    def is_skills_mode(
        self,
        parsed_options: dict[str, Any] | None = None,
        project_root: Path | None = None,
    ) -> bool:
        """Bob is skills-first; ``--legacy-commands`` opts out.

        Precedence:

        1. Explicit ``--skills`` wins — it *forces* skills mode regardless of
           what is already on disk.  This is the supported migration / opt-in
           path: ``integration upgrade bob --integration-options "--skills"``
           converts a legacy commands install to the skills layout (setup()
           scaffolds ``.bob/skills`` and the upgrade's stale-file pass removes
           the old ``.bob/commands`` files).
        2. Explicit ``--legacy-commands`` opts out to the Bob 1.x layout.
        3. Otherwise, when a *project_root* is supplied, the layout is inferred
           from **managed Spec Kit artifacts** (see below).
        4. A fresh project (no managed artifacts, no flags) defaults to skills.

        The disk-detection fallback exists because on ``use`` / ``switch`` /
        ``upgrade`` (without an explicit ``--skills`` / ``--legacy-commands``)
        *parsed_options* is typically empty: no flag was passed, and existing
        Bob 1.x installs never persisted a ``legacy_commands`` option to
        recover.  This is independent of whether ``setup()`` runs — ``upgrade``
        *does* call :meth:`setup` (see ``_migrate_commands.integration_upgrade``),
        but it passes those same empty *parsed_options*, so without disk
        detection the mode would resolve to the skills default.  Defaulting to
        skills there would rewrite such a project's ``ai_skills`` flag to
        ``True`` even though it still only contains a command layout, silently
        switching its extension / command-reference handling.  So the layout is
        inferred from managed Spec Kit artifacts, not the mere presence of a
        ``.bob/skills/`` directory: a user may keep unrelated Bob 2 skills in
        ``.bob/skills/`` while their Spec Kit commands still live in
        ``.bob/commands/speckit.*.md``.  We therefore treat the project as
        legacy (command) mode only when managed Spec Kit command files exist
        and no managed Spec Kit skills (``speckit-*`` skill dirs) do.  Passing
        ``--skills`` overrides this so users are never trapped in legacy mode.
        """
        opts = parsed_options or {}
        _validate_mode_options(opts)
        if opts.get("skills", False):
            return True
        if opts.get("legacy_commands", False):
            return False
        if project_root is not None:
            bob_dir = Path(project_root) / ".bob"
            has_managed_skills = any((bob_dir / "skills").glob("speckit-*"))
            has_managed_commands = any((bob_dir / "commands").glob("speckit.*.md"))
            if has_managed_commands and not has_managed_skills:
                return False
        return True

    def effective_invoke_separator(
        self,
        parsed_options: dict[str, Any] | None = None,
        project_root: Path | None = None,
    ) -> str:
        """``"."`` for the legacy commands layout, ``"-"`` for skills.

        *project_root* lets the ``use`` / ``switch`` / ``upgrade`` path — which
        refreshes shared infrastructure *before* persisting init-options —
        detect an already-installed legacy layout, so core command references
        are rendered with the correct separator instead of defaulting to the
        skills ``-``.
        """
        return "-" if self.is_skills_mode(parsed_options, project_root) else "."

    def invoke_separator_for_mode(self, skills_enabled: bool) -> str:
        """Resolve the command-ref separator from a project's persisted mode.

        Skills projects render ``/speckit-<cmd>``; legacy command projects
        render Bob 1.x ``/speckit.<cmd>``.  Extension/preset registration
        consults this (via the persisted ``ai_skills`` flag) so both layouts
        get the correct separator despite sharing one static ``AGENT_CONFIGS``
        entry.
        """
        return "-" if skills_enabled else "."

    def post_process_skill_content(self, content: str) -> str:
        """Bob skills are intent-activated; no slash-command note is injected.

        Preset/extension skill generators call this on the *registered*
        ``BobIntegration`` instance, not on :class:`_BobSkillsHelper`, so the
        no-op must be repeated here (delegating to the helper) — otherwise
        those paths would inherit ``IntegrationBase``'s default and inject
        ``/speckit-*`` hook guidance that core Bob skills intentionally omit.
        """
        return _BobSkillsHelper().post_process_skill_content(content)

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        parsed_options = parsed_options or {}
        if self.is_skills_mode(parsed_options, project_root):
            return _BobSkillsHelper().setup(
                project_root, manifest, parsed_options, **opts
            )
        _warn_legacy_commands_deprecated()
        return MarkdownIntegration.setup(
            _BobMarkdownHelper(), project_root, manifest, parsed_options, **opts
        )
