"""CLI for installing workflow function packages."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from .. import _archive_install as archive
from .. import _commands as cli
from . import function_app
from . import installer


def _install_from_url(project_root: Path, function_id: str, url: str, force: bool) -> dict:
    """Install a function package archive from a direct URL."""
    return archive.install_from_archive_url(
        archive.ArchiveRequest(project_root, function_id, url, force),
        installer._function_spec(),
        archive.ArchiveHooks(
            preflight=lambda root, fid, force: installer.check_installable(
                root, fid, force=force
            ),
            resolve_root=lambda extracted: installer.resolve_package_root(extracted),
            install=lambda root, fid, package, force: installer.install_function_package(
                root, fid, package, source="url", force=force
            ),
        ),
    )


@function_app.command("add")
def workflow_function_add(
    function_id: str = cli.typer.Argument(..., help="Function package ID"),
    dev: Annotated[str | None, cli.typer.Option("--dev", help="Install from a local package directory")] = None,
    from_url: Annotated[str | None, cli.typer.Option("--from", help="Install from an archive URL")] = None,
    force: bool = cli.typer.Option(False, "--force", help="Replace an existing installation"),
):
    """Install project workflow expression functions."""
    project_root = cli._require_specify_project()
    if (dev is None) == (from_url is None):
        cli.console.print("[red]Error:[/red] exactly one of --dev or --from is required")
        raise cli.typer.Exit(1)
    try:
        if dev is not None:
            source = Path(dev).expanduser()
            if source.is_symlink() or not source.is_dir():
                raise installer.WorkflowFunctionError(
                    f"--dev source must be a directory: '{source}'"
                )
            installer.install_function_package(
                project_root, function_id, source, source="local", force=force
            )
        else:
            _install_from_url(project_root, function_id, from_url or "", force)
    except installer.WorkflowFunctionError as exc:
        cli._print_package_error(exc)
        raise cli.typer.Exit(1) from exc
    cli.console.print(
        f"[green]✓[/green] Workflow function package '{cli._escape_markup(function_id)}' installed"
    )
