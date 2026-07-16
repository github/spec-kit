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

from ..base import (
    IntegrationBase,
    IntegrationOption,
    MarkdownIntegration,
    SkillsIntegration,
)
from ..manifest import IntegrationManifest


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

        On ``use`` / ``switch`` / ``upgrade`` no ``setup()`` runs and
        *parsed_options* is typically empty (existing Bob 1.x installs never
        stored ``legacy_commands``).  Defaulting to skills there would rewrite
        such a project's ``ai_skills`` flag to ``True`` even though it still
        only contains ``.bob/commands/`` — silently switching its extension /
        command-reference handling to the skills layout.  So when a
        *project_root* is supplied, an already-installed legacy layout
        (``.bob/commands/`` present, ``.bob/skills/`` absent) is preserved
        until an explicit upgrade actually creates ``.bob/skills/``.  A fresh
        project (no ``.bob/`` layout yet) still defaults to skills.
        """
        if (parsed_options or {}).get("legacy_commands", False):
            return False
        if project_root is not None:
            bob_dir = Path(project_root) / ".bob"
            if (bob_dir / "commands").is_dir() and not (bob_dir / "skills").is_dir():
                return False
        return True

    def effective_invoke_separator(
        self, parsed_options: dict[str, Any] | None = None
    ) -> str:
        """``"."`` for the legacy commands layout, ``"-"`` for skills."""
        return "-" if self.is_skills_mode(parsed_options) else "."

    def invoke_separator_for_mode(self, skills_enabled: bool) -> str:
        """Resolve the command-ref separator from a project's persisted mode.

        Skills projects render ``/speckit-<cmd>``; legacy command projects
        render Bob 1.x ``/speckit.<cmd>``.  Extension/preset registration
        consults this (via the persisted ``ai_skills`` flag) so both layouts
        get the correct separator despite sharing one static ``AGENT_CONFIGS``
        entry.
        """
        return "-" if skills_enabled else "."

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        parsed_options = parsed_options or {}
        if self.is_skills_mode(parsed_options):
            return _BobSkillsHelper().setup(
                project_root, manifest, parsed_options, **opts
            )
        _warn_legacy_commands_deprecated()
        return MarkdownIntegration.setup(
            _BobMarkdownHelper(), project_root, manifest, parsed_options, **opts
        )
