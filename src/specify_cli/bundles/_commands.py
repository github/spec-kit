"""Shared infrastructure and registration for ``specify bundle`` commands.

Command handlers live in ``command_*.py`` modules. The nested ``catalog``
namespace registers through ``bundles.catalog``; domain behavior remains in
Typer-free modules in this package.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.markup import escape as _escape_markup

from .._console import err_console
from . import BundlerError
from .project import active_integration
from .records import load_records

bundle_app = typer.Typer(
    name="bundle",
    help="Discover, install, and author Spec Kit bundles",
    add_completion=False,
)


def _fail(message: str) -> None:
    """Print an actionable error to stderr and exit non-zero."""
    # Use the stderr console so the error never lands on stdout, which under
    # ``--json`` carries the machine-readable payload and must stay parseable.
    # Escape the message: every caller passes ``str(exc)`` from a BundlerError
    # that interpolates untrusted data (a CLI argument, a catalog url, a
    # bundle.yml field), so a '[...]' in it would be parsed as a Rich style tag
    # -- silently swallowing the text, or raising MarkupError on an unbalanced
    # closer and replacing the whole message with a traceback.
    err_console.print(f"[red]Error:[/red] {_escape_markup(message)}", style=None)
    raise typer.Exit(code=1)


def _user_config_dir() -> Path:
    # User-scope Spec Kit config lives under ~/.specify (same convention as
    # auth.json, extension/preset catalogs). Passing this through to the source
    # stack is what makes the documented project > user > built-in precedence
    # reachable from the CLI.
    return Path.home() / ".specify"


def _build_stack(project_root: Path, *, offline: bool):
    from .adapters import make_catalog_fetcher
    from .catalog_stack import CatalogStack

    fetcher = make_catalog_fetcher(allow_network=not offline)
    return CatalogStack.load(project_root, fetcher, user_config_dir=_user_config_dir())


def _speckit_version() -> str:
    from .._assets import get_speckit_version

    return get_speckit_version()


def _trust_level(verified: bool) -> str:
    """Trust framing for a catalog entry (FR-010): org-curated vs community."""
    return "verified" if verified else "community"


def _trust_badge(verified: bool) -> str:
    return "[green]✔ verified[/green]" if verified else "[yellow]community[/yellow]"


def _default_script_type() -> str:
    """OS-appropriate default script flavor (FR-013)."""
    import os

    return "ps" if os.name == "nt" else "sh"


def _run_init(integration: str, *, script_type: str, offline: bool = False) -> None:
    """Idempotently scaffold a Spec Kit project here via the existing ``init`` machinery.

    Reuses the real ``specify init`` command callback in-process (Principle I)
    with ``--here --force`` so it is non-interactive and merges into the current
    directory.
    """
    from .. import app

    init_cb = next(
        c.callback
        for c in app.registered_commands
        if c.callback and c.callback.__name__ == "init"
    )
    try:
        init_cb(
            project_name=None,
            script_type=script_type,
            ignore_agent_tools=True,
            here=True,
            force=True,
            skip_tls=False,
            debug=False,
            github_token=None,
            offline=offline,
            preset=None,
            integration=integration,
            integration_options=None,
            extensions=None,
            trust_extension_urls=False,
        )
    except typer.Exit as exc:
        if exc.exit_code:
            raise BundlerError(
                f"Failed to initialize a Spec Kit project (integration '{integration}')."
            ) from exc


def _resolve_init_integration(override: str | None, manifest) -> str:
    """Precedence (FR-013): explicit override → bundle-declared → default."""
    from .._agent_config import resolve_default_init_integration

    if override:
        return override
    if manifest is not None and manifest.integration is not None:
        return manifest.integration.id
    return resolve_default_init_integration()


def _bundle_overlaps(project_root: Path, manifest, *, offline: bool) -> list[str]:
    """Return informational overlaps between *manifest* and installed bundles."""
    if manifest is None:
        return []
    try:
        from .conflict import detect_conflicts

        report = detect_conflicts(
            manifest,
            active_integration(project_root),
            load_records(project_root),
        )
        return list(report.overlaps)
    except BundlerError:
        return []


def register(app: typer.Typer) -> None:
    """Attach the bundle command group to the root Typer app."""
    from .catalog import register as register_catalog

    register_catalog(bundle_app)

    # isort: off
    from . import command_search  # noqa: F401 — registers handler via decorator
    from . import command_info  # noqa: F401 — registers handler via decorator
    from . import command_list  # noqa: F401 — registers handler via decorator
    from . import command_install  # noqa: F401 — registers handler via decorator
    from . import command_add  # noqa: F401 — registers handler via decorator
    from . import command_update  # noqa: F401 — registers handler via decorator
    from . import command_remove  # noqa: F401 — registers handler via decorator
    from . import command_validate  # noqa: F401 — registers handler via decorator
    from . import command_build  # noqa: F401 — registers handler via decorator
    from . import command_init  # noqa: F401 — registers handler via decorator
    # isort: on

    app.add_typer(bundle_app, name="bundle")
