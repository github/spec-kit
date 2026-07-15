"""IBM Bob integration.

Bob 2.0 uses the ``.bob/skills/speckit-<name>/SKILL.md`` layout.
The legacy ``.bob/commands/*.md`` layout (Bob 1.x) is available as an
opt-in for projects that have not yet migrated, via
``--integration-options "--legacy-commands"``.

Deprecation cycle:
  This release:  Skills layout is the default; legacy ``.bob/commands/``
                 is opt-in via ``--legacy-commands``.
  Next cycle:    ``--legacy-commands`` flag removed.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

from ..base import IntegrationBase, IntegrationOption, MarkdownIntegration, SkillsIntegration
from ..manifest import IntegrationManifest


def _warn_legacy_commands_deprecated() -> None:
    """Warn that Bob's legacy markdown layout is being phased out."""
    warnings.warn(
        "Bob legacy commands mode (.bob/commands/) is deprecated and will be "
        "removed in a future Spec Kit release. Omit --legacy-commands to use "
        "the default skills layout (.bob/skills/).",
        UserWarning,
        stacklevel=3,
    )


class _BobMarkdownHelper(MarkdownIntegration):
    """Internal helper used when Bob is scaffolded in legacy commands mode.

    Not registered in the integration registry — only used as a delegate
    by ``BobIntegration`` when ``--legacy-commands`` is passed.
    """

    key = "bob"
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


class _BobSkillsHelper(SkillsIntegration):
    """Internal helper used when Bob is scaffolded in skills mode.

    Not registered in the integration registry — only used as a delegate
    by ``BobIntegration`` for skills-mode setup.
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


class BobIntegration(IntegrationBase):
    """Integration for IBM Bob IDE.

    Default mode: installs ``.bob/skills/speckit-<name>/SKILL.md`` files
    (Bob 2.0 skills layout).

    Legacy mode (``--legacy-commands``): installs
    ``.bob/commands/speckit.<name>.md`` files (Bob 1.x layout — deprecated).

    Extends ``IntegrationBase`` directly so that ``isinstance(integration,
    SkillsIntegration)`` is ``False`` and consumers such as
    ``_update_init_options_for_integration`` and the ``specify init``
    next-steps builder derive the effective mode from ``_skills_mode``
    rather than the class hierarchy.  ``invoke_separator = "-"`` is set
    explicitly to match the skills-default behaviour expected by
    ``CommandRegistrar.AGENT_CONFIGS``.
    """

    key = "bob"
    invoke_separator = "-"

    def effective_invoke_separator(
        self, parsed_options: dict[str, Any] | None = None
    ) -> str:
        """Return the invocation separator for the selected Bob layout."""
        if parsed_options and parsed_options.get("legacy_commands"):
            return "."
        return "-"

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

    @property
    def _skills_mode(self) -> bool:
        """True when the instance is configured in skills (default) mode.

        Derived from the current ``registrar_config`` so that the value
        reflects whichever mode ``setup()`` last activated, without relying
        on mutable instance state that is unavailable in a fresh process
        (e.g. ``specify integration use bob`` or ``_set_default_integration``).
        """
        rc = self.registrar_config or {}
        return rc.get("extension") == "/SKILL.md"

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

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install Bob commands.

        Default: skills layout (``.bob/skills/speckit-<name>/SKILL.md``).
        When ``parsed_options["legacy_commands"]`` is truthy, falls back to
        the deprecated ``.bob/commands/speckit.<name>.md`` layout.
        """
        parsed_options = parsed_options or {}
        if parsed_options.get("legacy_commands"):
            self.registrar_config = dict(_BobMarkdownHelper.registrar_config)
            _warn_legacy_commands_deprecated()
            return self._setup_legacy(project_root, manifest, parsed_options, **opts)
        self.registrar_config = dict(_BobSkillsHelper.registrar_config)
        return SkillsIntegration.setup(
            _BobSkillsHelper(), project_root, manifest, parsed_options, **opts
        )

    def _setup_legacy(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Legacy mode: ``.bob/commands/speckit.<name>.md`` layout."""
        helper = _BobMarkdownHelper()
        return MarkdownIntegration.setup(helper, project_root, manifest, parsed_options, **opts)
