"""specify event * command handlers."""

from __future__ import annotations

from pathlib import Path
import sys
import typer

event_app = typer.Typer(
    name="event",
    help="Manage and execute event-driven commands",
    add_completion=False,
)


@event_app.command("run")
def event_run(
    command_name: str = typer.Argument(..., help="Name of the command to execute"),
    event_name: str = typer.Argument(..., help="Canonical event name (e.g., session_start)"),
    timeout: int = typer.Argument(
        120, help="Per-handler timeout in seconds (passed through from the native hook config)"
    ),
):
    """Resolve and run an event-driven command script with stdin payload."""
    from ..events import resolve_and_run_event_command

    # Read payload from stdin if available (capped at 1 MiB to prevent DoS).
    MAX_STDIN_BYTES = 1 * 1024 * 1024
    if not sys.stdin.isatty():
        raw = sys.stdin.read(MAX_STDIN_BYTES)
        if not sys.stdin.eof:
            raise typer.Exit(
                code=1,
                message="stdin payload exceeds 1 MiB limit; "
                "truncate or pipe a smaller payload",
            )
        payload = raw
    else:
        payload = "{}"

    # Run the event command
    project_root = Path.cwd()  # The agent runs events from project root
    exit_code = resolve_and_run_event_command(
        command_name, event_name, payload, project_root, timeout=timeout
    )
    raise typer.Exit(code=exit_code)


def register(app: typer.Typer) -> None:
    app.add_typer(event_app, name="event")
