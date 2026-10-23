"""CLI adapter for ``specify destroy``."""

from __future__ import annotations

import json
import logging
import os
import sys
import warnings
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import asdict, replace
from io import StringIO
from pathlib import Path
from typing import Annotated

import typer
from rich.markup import escape
from typer.core import TyperCommand

from ._console import console
from ._operation_destroy import (
    DestroyError,
    DestroyRequest,
    DestroyResult,
    destroy_project,
)

try:
    from typer._click.exceptions import UsageError as _UsageError
except ModuleNotFoundError as error:
    if error.name != "typer._click":
        raise
    from click import UsageError as _UsageError

logger = logging.getLogger(__name__)


def _emit_json_error(code: str, message: str, details: dict[str, object]) -> None:
    typer.echo(json.dumps({"error": {
        "code": code, "message": message, "details": details,
    }}), err=True)


class _DestroyCommand(TyperCommand):
    """Keep argument parsing failures on the destroy JSON contract."""

    def make_context(self, info_name, args, parent=None, **extra):
        json_output = "--json" in args
        try:
            return super().make_context(info_name, args, parent=parent, **extra)
        except _UsageError as exc:
            if json_output:
                _emit_json_error("invalid_arguments", exc.format_message(), {})
                raise typer.Exit(exc.exit_code) from exc
            raise


def _stdin_is_interactive() -> bool:
    return sys.stdin.isatty()


def _invoke_operation(request: DestroyRequest, *, json_output: bool) -> DestroyResult:
    if not json_output:
        return destroy_project(request)
    diagnostics = StringIO()
    with (
        redirect_stdout(diagnostics), redirect_stderr(diagnostics),
        console.capture() as captured,
        warnings.catch_warnings(record=True) as recorded,
    ):
        warnings.simplefilter("always")
        result = destroy_project(request)
    messages = tuple(str(warning.message) for warning in recorded)
    for text in (captured.get().strip(), diagnostics.getvalue().strip()):
        if text:
            messages += (text,)
    return replace(result, warnings=result.warnings + messages)


def destroy(
    project: Annotated[Path | None, typer.Option(
        "--project", help="Project root (default: cwd or SPECIFY_INIT_DIR).",
    )] = None,
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without changing files."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm deletion of project-local Spec Kit files."),
    force: bool = typer.Option(False, "--force", help="Also remove modified/unverified whole-owned agent files."),
    json_output: bool = typer.Option(False, "--json", help="Emit a JSON result or error; never prompt."),
    preserve_constitution: bool = typer.Option(
        False, "--preserve-constitution", help="Keep .specify/memory/constitution.md unchanged.",
    ),
    preserve_specs: bool = typer.Option(
        False, "--preserve-specs", help="Keep the project-local specs/ directory unchanged.",
    ),
    preserve_all: bool = typer.Option(
        False, "--preserve-all", help="Keep both the constitution and specs; still uninstall tooling.",
    ),
) -> None:
    """Uninstall Spec Kit and remove .specify/ and specs/ unless explicitly preserved."""
    try:
        root = (project or Path(os.environ.get("SPECIFY_INIT_DIR") or Path.cwd())).absolute()
        request = DestroyRequest(
            root, confirmed=yes, force=force, dry_run=True,
            preserve_constitution=preserve_constitution, preserve_specs=preserve_specs,
            preserve_all=preserve_all,
        )
        preview = _invoke_operation(request, json_output=json_output)
        if not json_output:
            console.print(f"Project: {escape(preview.project_directory)}")
            console.print("Remove unpreserved .specify/ contents, specs/, and recorded agent artifacts:")
            if "specs" not in request.preserved_paths and any(
                name == "specs" or name.startswith("specs/")
                for name in (*preview.removed, *preview.directories)
            ):
                console.print("[yellow]Warning:[/yellow] Project specifications in specs/ will be deleted.")
            for name in preview.removed:
                console.print(f"  {escape(name)}")
            for name in preview.preserved:
                console.print(f"Preserve: {escape(name)}")
            for name in preview.updated:
                console.print(f"Remove managed integration entries from: {escape(name)}")
            for name in preview.global_scopes:
                console.print(f"Integration uninstall also manages home-scoped outputs in: {escape(name)}")
            for name in preview.global_files:
                console.print(f"  {escape(name)}")
            if not preview.removed and preview.directories:
                console.print("Remove empty Spec Kit directories.")
            if preview.requires_force:
                console.print("[yellow]Modified/unverified files require --force:[/yellow]")
                for name in preview.requires_force:
                    console.print(f"  {escape(name)}")
        if dry_run:
            result = preview
        else:
            confirmed = yes
            if (
                (preview.removed or preview.directories or preview.updated)
                and not yes and not json_output and _stdin_is_interactive()
            ):
                confirmed = typer.confirm(
                    "Delete the planned files and directories? "
                    "Unpreserved content in .specify/ and specs/ will be lost.",
                    default=False,
                )
                if not confirmed:
                    console.print("Uninstall cancelled; no files changed.")
                    return
            result = _invoke_operation(
                replace(request, confirmed=confirmed, dry_run=False), json_output=json_output,
            )
        if json_output:
            typer.echo(json.dumps(asdict(result), indent=2))
        elif dry_run:
            console.print("Dry run; no files changed.")
        else:
            for warning in result.warnings:
                console.print(f"[yellow]Warning:[/yellow] {escape(warning)}")
            console.print("[green]Spec Kit project uninstall complete.[/green]")
    except DestroyError as exc:
        if json_output:
            _emit_json_error(exc.code, exc.message, exc.details)
        else:
            console.print(f"[red]Error:[/red] {escape(exc.message)}")
        raise typer.Exit(1) from exc
    except Exception as exc:
        logger.debug("Unexpected destroy failure", exc_info=True)
        message = "Unable to uninstall project-local Spec Kit."
        if json_output:
            _emit_json_error("internal_error", message, {})
        else:
            console.print(f"[red]Error:[/red] {message}")
        raise typer.Exit(1) from exc


def register(app: typer.Typer) -> None:
    """Register the root uninstall command."""
    app.command(cls=_DestroyCommand)(destroy)
