"""Command handler for ``specify workflow resume``."""

from __future__ import annotations

from . import _commands as cli
from . import _command_resume_state as resume_state


@cli.workflow_app.command("resume")
def workflow_resume(
    run_id: str = cli.typer.Argument(..., help="Run ID to resume"),
    input_values: list[str] | None = cli.typer.Option(
        None, "--input", "-i", help="Updated input values as key=value pairs"
    ),
    json_output: bool = cli.typer.Option(
        False,
        "--json",
        help="Emit the resume outcome as a single JSON object instead of formatted text.",
    ),
):
    """Resume a paused or failed workflow run."""
    from . import load_custom_steps
    from .engine import RunState, WorkflowEngine

    project_root = cli._require_specify_project()
    load_custom_steps(project_root)
    engine = WorkflowEngine(project_root)
    if not json_output:
        # Escape the literal bracket (\[) so Rich renders `[<step id>]` instead
        # of parsing it as a style tag named after the step id -- which it
        # silently swallows (losing the only identifying content on the line),
        # applies as formatting when the id happens to be a real style such as
        # `bold`, or raises MarkupError when the id forms a closing tag (`/`),
        # failing the whole run. Escape the interpolated values too, since both
        # come from workflow YAML. Mirrors the `\[<type>]` step-graph precedent
        # in workflow_info below.
        engine.on_step_start = lambda sid, label: cli.console.print(
            f"  \u25b8 \\[{cli._escape_markup(str(sid))}] "
            f"{cli._escape_markup(str(label))} \u2026"
        )

    inputs = cli._parse_input_values(input_values, json_output=json_output)
    err = cli._error_console(json_output)

    # Pre-load the persisted run state so a run started from an installed
    # workflow that has since been disabled cannot resume unchecked --
    # engine.resume() replays the run directly from disk with no registry
    # awareness at all, which would otherwise bypass the same disabled
    # guard `workflow run` enforces. Runs without installed_workflow_id
    # (a direct/non-installed source, or a run persisted before this field
    # existed) are unaffected and resume exactly as before.
    try:
        pre_state = RunState.load(run_id, project_root)
    except FileNotFoundError:
        err.print(f"[red]Error:[/red] Run not found: {run_id}")
        raise cli.typer.Exit(1)
    except ValueError as exc:
        err.print(f"[red]Error:[/red] {cli._escape_markup(str(exc))}")
        raise cli.typer.Exit(1)
    except OSError as exc:
        err.print(f"[red]Resume failed:[/red] {cli._escape_markup(str(exc))}")
        raise cli.typer.Exit(1)

    if pre_state.installed_workflow_id is not None:
        try:
            owner_root = resume_state._resolve_run_owner_root(
                pre_state.installed_registry_root, project_root
            )
        except ValueError as exc:
            err.print(f"[red]Error:[/red] {cli._escape_markup(str(exc))}")
            raise cli.typer.Exit(1)
        cli._require_enabled_workflow(owner_root, pre_state.installed_workflow_id, err)
    elif not pre_state.installed_origin_tracked:
        if cli._require_enabled_workflow(project_root, pre_state.workflow_id, err):
            pre_state.installed_workflow_id = pre_state.workflow_id
        pre_state.installed_origin_tracked = True
        try:
            pre_state.save()
        except OSError as exc:
            err.print(f"[red]Resume failed:[/red] {cli._escape_markup(str(exc))}")
            raise cli.typer.Exit(1)

    try:
        with cli._stdout_to_stderr_when(json_output):
            state = engine.resume(run_id, inputs or None)
    except FileNotFoundError:
        err.print(f"[red]Error:[/red] Run not found: {run_id}")
        raise cli.typer.Exit(1)
    except ValueError as exc:
        err.print(f"[red]Error:[/red] {cli._escape_markup(str(exc))}")
        raise cli.typer.Exit(1)
    except Exception as exc:
        err.print(f"[red]Resume failed:[/red] {cli._escape_markup(str(exc))}")
        raise cli.typer.Exit(1)

    if json_output:
        cli._emit_workflow_json(cli._workflow_run_payload(state))
        raise cli.typer.Exit(cli._run_outcome_exit_code(state.status.value))

    status_colors = {
        "completed": "green",
        "paused": "yellow",
        "failed": "red",
        "aborted": "red",
    }
    color = status_colors.get(state.status.value, "white")
    cli.console.print(f"\n[{color}]Status: {state.status.value}[/{color}]")

    err_msg = cli._failed_step_error(state)
    if err_msg:
        cli.console.print(f"[red]Error:[/red] {cli._escape_markup(err_msg)}")

    raise cli.typer.Exit(cli._run_outcome_exit_code(state.status.value))
