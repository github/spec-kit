"""Command handler for ``specify workflow definition``."""

from __future__ import annotations

import sys

from .._installed_list_json import InstalledListJSONCommand, emit_json_error
from .._project import ProjectResolutionError, resolve_specify_project_root
from . import _commands as cli


def _require_json_flag(json_output: bool) -> None:
    if not json_output:
        print(
            "specify workflow definition requires --json for now; "
            "text output is not yet implemented.",
            file=sys.stderr,
        )
        raise cli.typer.Exit(2)


@cli.workflow_app.command("definition", cls=InstalledListJSONCommand)
def workflow_definition(
    run_id: str = cli.typer.Argument(..., help="Run ID to inspect"),
    json_output: bool = cli.typer.Option(
        False,
        "--json",
        help="Emit the run's workflow definition as a JSON object on stdout.",
    ),
):
    """Show the workflow definition a run was started with."""
    _require_json_flag(json_output)
    try:
        project_root = resolve_specify_project_root()
    except ProjectResolutionError as exc:
        emit_json_error(exc)
    if error := cli._workflow_storage_error(project_root):
        emit_json_error(ValueError(error))
    try:
        state = cli._load_run_state(run_id, project_root)
    except ValueError as exc:
        emit_json_error(exc)

    try:
        definition = state.load_definition()
        scopes = state.load_workflow_scopes()
    except FileNotFoundError:
        emit_json_error(ValueError(f"Run {state.run_id} has no persisted workflow definition"))
    except (OSError, ValueError) as exc:
        emit_json_error(ValueError(f"Invalid workflow definition for run {state.run_id}: {exc}"))

    cli._emit_workflow_json(
        {
            "run_id": state.run_id,
            "definition": definition.data,
            "workflow_scopes": [
                {"scope_path": path, "workflow_id": workflow_id, "definition": d.data}
                for path, workflow_id, d in scopes
            ],
        }
    )
