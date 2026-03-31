"""Base classes for AI-assistant integrations.

Provides:
- ``IntegrationOption`` — declares a CLI option an integration accepts.
- ``IntegrationBase`` — abstract base every integration must implement.
- ``MarkdownIntegration`` — concrete base for standard Markdown-format
  integrations (the common case — subclass, set three class attrs, done).
"""

from __future__ import annotations

import shutil
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .manifest import IntegrationManifest


# ---------------------------------------------------------------------------
# IntegrationOption
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IntegrationOption:
    """Declares an option that an integration accepts via ``--integration-options``.

    Attributes:
        name:      The flag name (e.g. ``"--commands-dir"``).
        is_flag:   ``True`` for boolean flags (``--skills``).
        required:  ``True`` if the option must be supplied.
        default:   Default value when not supplied (``None`` → no default).
        help:      One-line description shown in ``specify integrate info``.
    """

    name: str
    is_flag: bool = False
    required: bool = False
    default: Any = None
    help: str = ""


# ---------------------------------------------------------------------------
# IntegrationBase — abstract base class
# ---------------------------------------------------------------------------

class IntegrationBase(ABC):
    """Abstract base class every integration must implement.

    Subclasses must set the following class-level attributes:

    * ``key``              — unique identifier, matches actual CLI tool name
    * ``config``           — dict compatible with ``AGENT_CONFIG`` entries
    * ``registrar_config`` — dict compatible with ``CommandRegistrar.AGENT_CONFIGS``

    And may optionally set:

    * ``context_file``     — path (relative to project root) of the agent
                             context/instructions file (e.g. ``"CLAUDE.md"``)
    """

    # -- Must be set by every subclass ------------------------------------

    key: str = ""
    """Unique integration key — should match the actual CLI tool name."""

    config: dict[str, Any] | None = None
    """Metadata dict matching the ``AGENT_CONFIG`` shape."""

    registrar_config: dict[str, Any] | None = None
    """Registration dict matching ``CommandRegistrar.AGENT_CONFIGS`` shape."""

    # -- Optional ---------------------------------------------------------

    context_file: str | None = None
    """Relative path to the agent context file (e.g. ``CLAUDE.md``)."""

    # -- Public API -------------------------------------------------------

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        """Return options this integration accepts. Default: none."""
        return []

    def templates_dir(self) -> Path:
        """Return the path to this integration's bundled templates.

        By convention, templates live in a ``templates/`` subdirectory next
        to the integration's ``__init__.py``.
        """
        import inspect

        module_file = inspect.getfile(type(self))
        return Path(module_file).resolve().parent / "templates"

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install integration files into *project_root*.

        Returns the list of files created.  The default implementation
        copies every file from ``templates_dir()`` into the commands
        directory derived from ``config``, recording each in *manifest*.
        """
        created: list[Path] = []
        tpl_dir = self.templates_dir()
        if not tpl_dir.is_dir():
            return created

        if not self.config:
            raise ValueError(
                f"{type(self).__name__}.config is not set; integration "
                "subclasses must define a non-empty 'config' mapping."
            )
        folder = self.config.get("folder")
        if not folder:
            raise ValueError(
                f"{type(self).__name__}.config is missing required 'folder' entry."
            )

        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )
        subdir = self.config.get("commands_subdir", "commands")
        dest = (project_root / folder / subdir).resolve()
        # Ensure destination stays within the project root
        try:
            dest.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Integration destination {dest} escapes "
                f"project root {project_root_resolved}"
            ) from exc

        dest.mkdir(parents=True, exist_ok=True)

        for src_file in sorted(tpl_dir.iterdir()):
            if src_file.is_file():
                dst_file = dest / src_file.name
                dst_resolved = dst_file.resolve()
                rel = dst_resolved.relative_to(project_root_resolved)
                shutil.copy2(src_file, dst_file)
                manifest.record_existing(rel)
                created.append(dst_file)

        return created

    def teardown(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        *,
        force: bool = False,
    ) -> tuple[list[Path], list[Path]]:
        """Uninstall integration files from *project_root*.

        Delegates to ``manifest.uninstall()`` which only removes files
        whose hash still matches the recorded value (unless *force*).

        Returns ``(removed, skipped)`` file lists.
        """
        return manifest.uninstall(project_root, force=force)

    # -- Convenience helpers for subclasses -------------------------------

    def install(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """High-level install — calls ``setup()`` and returns created files."""
        return self.setup(
            project_root, manifest, parsed_options=parsed_options, **opts
        )

    def uninstall(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        *,
        force: bool = False,
    ) -> tuple[list[Path], list[Path]]:
        """High-level uninstall — calls ``teardown()``."""
        return self.teardown(project_root, manifest, force=force)


# ---------------------------------------------------------------------------
# MarkdownIntegration — covers ~20 standard agents
# ---------------------------------------------------------------------------

class MarkdownIntegration(IntegrationBase):
    """Concrete base for integrations that use standard Markdown commands.

    Subclasses only need to set ``key``, ``config``, ``registrar_config``
    (and optionally ``context_file``).  Everything else is inherited.

    The default ``setup()`` from ``IntegrationBase`` copies templates
    into the agent's commands directory — which is correct for the
    standard Markdown case.
    """

    # MarkdownIntegration inherits IntegrationBase.setup() as-is.
    # Future stages may add markdown-specific path rewriting here.
    pass
