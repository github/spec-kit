"""Command handler for ``specify workflow run``."""

from __future__ import annotations

from . import _commands as cli
from . import _command_run_ownership as run_ownership


@cli.workflow_app.command("run")
def workflow_run(
    source: str = cli.typer.Argument(..., help="Workflow ID or YAML file path"),
    input_values: list[str] | None = cli.typer.Option(
        None, "--input", "-i", help="Input values as key=value pairs"
    ),
    json_output: bool = cli.typer.Option(
        False,
        "--json",
        help="Emit the run outcome as a single JSON object instead of formatted text.",
    ),
):
    """Run a workflow from an installed ID or local YAML path."""
    from . import load_custom_steps
    from .engine import WorkflowEngine, is_valid_workflow_id

    source_path = cli.Path(source).expanduser()
    is_file_source = (
        source_path.suffix.lower() in (".yml", ".yaml") and source_path.is_file()
    )

    if is_file_source:
        # When running a YAML file directly, use cwd as project root without
        # requiring a .specify/ project directory — unless SPECIFY_INIT_DIR
        # explicitly names a project, in which case the strict override applies.
        override = cli._resolve_init_dir_override()
        project_root = override if override is not None else cli.Path.cwd()
        cli._reject_unsafe_workflow_storage(project_root)
    else:
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

    err = cli._error_console(json_output)

    registered_id: str | None = None
    registry_root = project_root
    if not is_file_source:
        # Reject path-equivalent spellings ("align-wf/", "align-wf/.") that
        # would miss the registry lookup yet still load the installed file,
        # bypassing the disabled check below.
        if (
            source in cli._RESERVED_WORKFLOW_IDS
            or not is_valid_workflow_id(source)
        ):
            err.print(
                f"[red]Error:[/red] Invalid workflow ID: {cli._escape_markup(repr(source))}"
            )
            raise cli.typer.Exit(1)
        registered_id = source
    else:
        # A direct YAML path may still point at an installed workflow's own
        # file (lexically, or via a symlinked alias pointing into installed
        # storage); map it back to its owning project and ID so the
        # disabled check below can't be silently bypassed.
        owner_root, owner_id = run_ownership._resolve_installed_workflow_ownership(
            source_path, err
        )
        if owner_id is not None:
            registry_root = owner_root
            registered_id = owner_id

    if registered_id is not None:
        cli._require_enabled_workflow(registry_root, registered_id, err)

    try:
        definition = engine.load_workflow(source_path if is_file_source else source)
    except FileNotFoundError:
        err.print(f"[red]Error:[/red] Workflow not found: {source}")
        raise cli.typer.Exit(1)
    except ValueError as exc:
        err.print(f"[red]Error:[/red] Invalid workflow: {cli._escape_markup(str(exc))}")
        raise cli.typer.Exit(1)

    # Validate
    errors = engine.validate(definition)
    if errors:
        err.print("[red]Workflow validation failed:[/red]")
        for verr in errors:
            err.print(f"  • {cli._escape_markup(str(verr))}")
        raise cli.typer.Exit(1)

    # Parse inputs
    inputs = cli._parse_input_values(input_values, json_output=json_output)

    if not json_output:
        cli.console.print(
            f"\n[bold cyan]Running workflow:[/bold cyan] {definition.name} ({definition.id})"
        )
        cli.console.print(f"[dim]Version: {definition.version}[/dim]\n")

    try:
        with cli._stdout_to_stderr_when(json_output):
            state = engine.execute(
                definition,
                inputs,
                installed_workflow_id=registered_id,
                # Only persist an explicit root when the installed workflow
                # genuinely belongs to a *different* project than the one
                # whose runs/ directory holds this run's own state (a
                # direct external workflow-file invocation) -- the common
                # case (an installed workflow run from its own project)
                # leaves this None so resume re-derives the owning root
                # from wherever the project currently is, transparently
                # surviving a project rename/move instead of baking in a
                # stale absolute path at run start.
                installed_registry_root=(
                    registry_root.resolve(strict=True)
                    if registered_id
                    and not run_ownership._same_existing_path(
                        registry_root, project_root
                    )
                    else None
                ),
            )
    except ValueError as exc:
        err.print(f"[red]Error:[/red] {cli._escape_markup(str(exc))}")
        raise cli.typer.Exit(1)
    except Exception as exc:
        err.print(f"[red]Workflow failed:[/red] {cli._escape_markup(str(exc))}")
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
    cli.console.print(f"[dim]Run ID: {state.run_id}[/dim]")

    err_msg = cli._failed_step_error(state)
    if err_msg:
        cli.console.print(f"[red]Error:[/red] {cli._escape_markup(err_msg)}")

    if state.status.value == "paused":
        cli.console.print(
            f"\nResume with: [cyan]specify workflow resume {state.run_id}[/cyan]"
        )

    raise cli.typer.Exit(cli._run_outcome_exit_code(state.status.value))
