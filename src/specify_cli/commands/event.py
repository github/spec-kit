"""specify event * command handlers."""

from __future__ import annotations

from pathlib import Path
import sys
import typer

_MAX_STDIN_BYTES = 10 * 1024 * 1024  # 10 MiB


def _read_stdin_bounded(max_bytes: int = _MAX_STDIN_BYTES) -> str:
    """Read at most *max_bytes* from stdin to prevent unbounded memory use.

    Uses ``sys.stdin.buffer`` so the limit is enforced on raw bytes rather
    than Unicode code points — a 4-byte UTF-8 sequence counts as 4 bytes,
    not 1 character.
    """
    if sys.stdin.isatty():
        return "{}"
    chunks: list[bytes] = []
    total = 0
    while total < max_bytes:
        chunk = sys.stdin.buffer.read(min(max_bytes - total, 65536))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
    return b"".join(chunks).decode("utf-8", errors="replace")


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

    payload = _read_stdin_bounded()

    # Run the event command
    project_root = Path.cwd()  # The agent runs events from project root
    exit_code = resolve_and_run_event_command(
        command_name, event_name, payload, project_root, timeout=timeout
    )
    raise typer.Exit(code=exit_code)


def register(app: typer.Typer) -> None:
    app.add_typer(event_app, name="event")
