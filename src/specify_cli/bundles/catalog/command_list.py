"""Implementation of ``specify bundle catalog list``."""

from __future__ import annotations

from rich.markup import escape as _escape_markup

from ..._console import console
from .. import BundlerError
from .._commands import _fail, _user_config_dir
from ..project import require_project_root
from . import catalog_app


@catalog_app.command("list")
def catalog_list() -> None:
    """Print the active, priority-ordered catalog stack with scope and policy."""
    try:
        project_root = require_project_root()
        from ..catalogs import Scope, load_source_stack

        sources = load_source_stack(project_root, user_config_dir=_user_config_dir())
    except BundlerError as exc:
        _fail(str(exc))
        return

    console.print(
        "\n[bold cyan]Catalog stack[/bold cyan] (highest precedence first):\n"
    )
    only_builtin = all(s.scope == Scope.BUILTIN for s in sources)
    for source in sources:
        console.print(
            f"  [bold]{_escape_markup(str(source.id))}[/bold]  "
            f"priority={source.priority}  "
            f"policy={source.install_policy.value}  scope={source.scope.value}"
        )
        console.print(f"    [dim]{_escape_markup(str(source.url))}[/dim]")
    if only_builtin:
        console.print("\n[dim]Using the built-in default stack.[/dim]")
