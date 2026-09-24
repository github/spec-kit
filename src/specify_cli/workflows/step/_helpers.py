"""Shared validation helpers for workflow step commands."""

from __future__ import annotations

from .. import _commands as cli

# Custom step packages contain executable Python, metadata, and optional helper
# files downloaded one-by-one rather than as an archive. Mirror the archive
# ceilings so a catalog cannot turn individually valid files into an unbounded
# aggregate download.
_MAX_STEP_PACKAGE_FILES = 512
_MAX_STEP_PACKAGE_BYTES = 50 * 1024 * 1024  # 50 MiB

_RESERVED_STEP_IDS: frozenset[str] = frozenset({".cache", "step-registry.json"})

_WINDOWS_RESERVED_NAMES: frozenset[str] = frozenset(
    {
        "con",
        "prn",
        "aux",
        "nul",
        "com1",
        "com2",
        "com3",
        "com4",
        "com5",
        "com6",
        "com7",
        "com8",
        "com9",
        "lpt1",
        "lpt2",
        "lpt3",
        "lpt4",
        "lpt5",
        "lpt6",
        "lpt7",
        "lpt8",
        "lpt9",
    }
)

_WINDOWS_INVALID_CHARS: frozenset[str] = frozenset('<>:"|?*')


def _validate_step_id_or_exit(step_id: str) -> None:
    """Validate that ``step_id`` is a single safe path component.

    Rejects empty strings, whitespace-only strings, leading/trailing whitespace,
    path separators, ``.``/``..`` components, dotfile prefixes, reserved names,
    Windows-invalid filename characters, trailing dots/spaces, and Windows
    reserved device names. Exits with code 1 on failure.
    """
    # Strip the stem (before first dot) for Windows reserved-name check
    stem = step_id.split(".")[0].lower() if step_id else ""
    if (
        not step_id
        or not step_id.strip()
        or step_id != step_id.strip()
        or "/" in step_id
        or "\\" in step_id
        or step_id in (".", "..")
        or step_id.startswith(".")
        or step_id.endswith(".")
        or step_id.endswith(" ")
        or step_id.lower() in _RESERVED_STEP_IDS
        or stem in _WINDOWS_RESERVED_NAMES
        or any(c in _WINDOWS_INVALID_CHARS for c in step_id)
        or any(ord(c) < 32 for c in step_id)
    ):
        cli.console.print(
            f"[red]Error:[/red] Invalid step id '{step_id}': must be a single safe "
            "path component (no separators, no leading dot, not a reserved name, "
            "no invalid filename characters)"
        )
        raise cli.typer.Exit(1)


def _resolve_steps_base_dir_or_exit(project_root: cli.Path) -> cli.Path:
    """Resolve .specify/workflows/steps while refusing symlinked parent directories."""
    project_root_resolved = project_root.resolve()
    steps_base_dir_unresolved = project_root / ".specify" / "workflows" / "steps"

    current = project_root
    for part in (".specify", "workflows", "steps"):
        current = current / part
        if current.is_symlink():
            cli.console.print(
                f"[red]Error:[/red] Refusing to use symlinked step directory '{current}'"
            )
            raise cli.typer.Exit(1)
        if current.exists() and not current.is_dir():
            cli.console.print(
                f"[red]Error:[/red] Step directory path is not a directory: '{current}'"
            )
            raise cli.typer.Exit(1)

    steps_base_dir = steps_base_dir_unresolved.resolve()
    try:
        steps_base_dir.relative_to(project_root_resolved)
    except ValueError:
        cli.console.print(
            f"[red]Error:[/red] Step directory escapes project root: '{steps_base_dir}'"
        )
        raise cli.typer.Exit(1)

    return steps_base_dir
