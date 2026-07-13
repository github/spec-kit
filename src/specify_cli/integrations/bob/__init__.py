"""IBM Bob integration.

Bob 2.0 supports the ``.bob/skills/speckit-<name>/SKILL.md`` layout.
The legacy ``.bob/commands/*.md`` layout (Bob 1.x) remains the default
for this release and will be deprecated in a future Spec Kit release.

Deprecation cycle:
  This release:  Markdown layout is default; skills layout is opt-in via
                 ``--integration-options "--skills"``.
  Next cycle:    Skills layout becomes default; markdown remains opt-in.
  Cycle after:   Markdown layout removed.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

from ..base import IntegrationBase, IntegrationOption, SkillsIntegration
from ..manifest import IntegrationManifest


def _warn_legacy_markdown_default() -> None:
    """Warn that Bob's default markdown scaffold is being phased out."""
    warnings.warn(
        "Bob legacy markdown mode (.bob/commands/) is deprecated and will stop "
        "being the default in a future Spec Kit release; pass "
        '--integration-options "--skills" to opt in to Bob skills mode now.',
        UserWarning,
        stacklevel=3,
    )


class _BobSkillsHelper(SkillsIntegration):
    """Internal helper used when Bob is scaffolded in skills mode.

    Not registered in the integration registry — only used as a delegate
    by ``BobIntegration`` when ``--skills`` is passed.
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

    Default mode: installs ``.bob/commands/speckit.<name>.md`` files
    (Bob 1.x markdown layout — legacy, will be deprecated).

    Skills mode (``--skills``): installs
    ``.bob/skills/speckit-<name>/SKILL.md`` files (Bob 2.0 layout).
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

    # Mutable flag set by setup() — indicates the active scaffolding mode.
    _skills_mode: bool = False

    def effective_invoke_separator(
        self, parsed_options: dict[str, Any] | None = None
    ) -> str:
        """Return ``"-"`` when skills mode is requested, ``"."`` otherwise."""
        if parsed_options and parsed_options.get("skills"):
            return "-"
        if self._skills_mode:
            return "-"
        return self.invoke_separator

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=False,
                help=(
                    "Scaffold commands as agent skills "
                    "(.bob/skills/speckit-<name>/SKILL.md) instead of "
                    "the legacy .bob/commands/*.md layout"
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

        When ``parsed_options["skills"]`` is truthy, delegates to skills
        scaffolding (``.bob/skills/speckit-<name>/SKILL.md``).
        Otherwise uses the default ``.bob/commands/speckit.<name>.md`` layout
        and emits a deprecation warning.
        """
        parsed_options = parsed_options or {}
        self._skills_mode = bool(parsed_options.get("skills"))
        if self._skills_mode:
            return self._setup_skills(project_root, manifest, parsed_options, **opts)
        if "skills" not in parsed_options:
            _warn_legacy_markdown_default()
        return self._setup_default(project_root, manifest, parsed_options, **opts)

    def _setup_default(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Default mode: ``.bob/commands/speckit.<name>.md`` layout."""
        from ..base import MarkdownIntegration

        return MarkdownIntegration.setup(self, project_root, manifest, parsed_options, **opts)

    def _setup_skills(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Skills mode: delegate to ``_BobSkillsHelper``."""
        helper = _BobSkillsHelper()
        return SkillsIntegration.setup(helper, project_root, manifest, parsed_options, **opts)
