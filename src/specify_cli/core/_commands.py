"""specify core * command handlers — app object and register() entry point.

See ``specs/001-core-info/contracts/core-info-cli.md`` for the CLI
contract (invocation syntax, streams, exit codes). See
``specs/001-core-info/data-model.md`` for the emitted JSON shape.
"""
from __future__ import annotations

import json
import sys

import typer

core_app = typer.Typer(
    name="core",
    help="Inspect the core (baseline) inventory shipped inside specify-cli.",
    add_completion=False,
)


@core_app.command("info")
def core_info(
    json_flag: bool = typer.Option(
        False,
        "--json",
        help="Emit the baseline inventory as JSON to standard output.",
    ),
) -> None:
    """Emit the baseline commands, templates, and scripts.

    With ``--json``: writes the inventory document to stdout and exits 0.
    Without ``--json``: prints a hint pointing at the JSON flag and exits
    non-zero — this feature ships JSON-only, per FR-002 / SC-005.

    On any packaging inconsistency (missing shipped file, unparseable
    frontmatter, script with zero runtimes), emits a JSON error envelope
    on stderr, leaves stdout empty, and exits 1 (FR-012).
    """
    if not json_flag:
        sys.stderr.write(
            "specify core info: this command ships JSON output only. "
            "Re-run with --json.\n"
        )
        raise typer.Exit(code=2)

    from . import CoreInventoryError, build_core_inventory  # lazy

    try:
        inventory = build_core_inventory()
    except CoreInventoryError as exc:
        sys.stderr.write(json.dumps(exc.to_envelope(), sort_keys=False) + "\n")
        raise typer.Exit(code=1) from exc

    sys.stdout.write(json.dumps(inventory, indent=2, sort_keys=False) + "\n")


def register(app: typer.Typer) -> None:
    """Attach the core command group to the root Typer app."""
    app.add_typer(core_app, name="core")
