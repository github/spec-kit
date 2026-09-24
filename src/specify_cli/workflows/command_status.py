"""Command handler for ``specify workflow status``."""

from __future__ import annotations

from . import _commands as cli


def _render_scopes(scopes: dict, indent: str) -> None:
    """Render nested composition scopes indented in the human status view."""
    colors = {
        "completed": "green",
        "failed": "red",
        "aborted": "red",
        "paused": "yellow",
        "running": "blue",
    }
    for key, record in scopes.items():
        if not isinstance(record, dict):
            continue
        s = record.get("status", "unknown")
        sc = colors.get(s, "white")
        cli.console.print(
            f"{indent}[{sc}]●[/{sc}] {key}: {s} "
            f"[dim]({record.get('workflow_id', '?')})[/dim]"
        )
        nested = record.get("workflow_scopes")
        if isinstance(nested, dict) and nested:
            _render_scopes(nested, indent + "  ")


@cli.workflow_app.command("status")
def workflow_status(
    run_id: str | None = cli.typer.Argument(
        None, help="Run ID to inspect (shows all if omitted)"
    ),
    json_output: bool = cli.typer.Option(
        False,
        "--json",
        help="Emit run status as a single JSON object instead of formatted text.",
    ),
):
    """Show workflow run status."""
    from .engine import WorkflowEngine

    project_root = cli._require_specify_project()
    engine = WorkflowEngine(project_root)

    if run_id:
        # Route errors to stderr under --json so the stdout JSON stream stays
        # parseable (mirrors `workflow run`/`workflow resume`); both handlers
        # fire before the json_output branch below.
        err = cli._error_console(json_output)
        try:
            from .engine import RunState

            state = RunState.load(run_id, project_root)
        except FileNotFoundError:
            err.print(f"[red]Error:[/red] Run not found: {run_id}")
            raise cli.typer.Exit(1)
        except ValueError as exc:
            err.print(f"[red]Error:[/red] {cli._escape_markup(str(exc))}")
            raise cli.typer.Exit(1)
        except OSError as exc:
            # An unreadable state.json (bad permissions, a directory in its
            # place, I/O error) must fail as cleanly as the malformed-JSON
            # case above -- `workflow resume` already handles OSError here.
            err.print(f"[red]Error:[/red] {cli._escape_markup(str(exc))}")
            raise cli.typer.Exit(1)

        if json_output:
            # Build on the shared run/resume payload so the common fields
            # (including current_step_index) stay identical across commands.
            payload = {
                **cli._workflow_run_payload(state),
                "created_at": state.created_at,
                "updated_at": state.updated_at,
                "steps": {
                    sid: sd.get("status", "unknown")
                    for sid, sd in state.step_results.items()
                },
            }
            cli._emit_workflow_json(payload)
            return

        status_colors = {
            "completed": "green",
            "paused": "yellow",
            "failed": "red",
            "aborted": "red",
            "running": "blue",
            "created": "dim",
        }
        color = status_colors.get(state.status.value, "white")

        cli.console.print(f"\n[bold cyan]Workflow Run: {state.run_id}[/bold cyan]")
        cli.console.print(f"  Workflow: {state.workflow_id}")
        cli.console.print(f"  Status:   [{color}]{state.status.value}[/{color}]")
        cli.console.print(f"  Created:  {state.created_at}")
        cli.console.print(f"  Updated:  {state.updated_at}")

        if state.current_step_id:
            cli.console.print(f"  Current:  {state.current_step_id}")

        err_msg = cli._failed_step_error(state)
        if err_msg:
            cli.console.print(f"  [red]Error:    {cli._escape_markup(err_msg)}[/red]")

        if state.step_results:
            cli.console.print(f"\n  [bold]Steps ({len(state.step_results)}):[/bold]")
            for step_id, step_data in state.step_results.items():
                s = step_data.get("status", "unknown")
                sc = {"completed": "green", "failed": "red", "paused": "yellow"}.get(
                    s, "white"
                )
                cli.console.print(f"    [{sc}]●[/{sc}] {step_id}: {s}")

        if getattr(state, "workflow_scopes", None):
            cli.console.print("\n  [bold]Workflow scopes:[/bold]")
            _render_scopes(state.workflow_scopes, "    ")
    else:
        runs = engine.list_runs()

        if json_output:
            payload = {
                "runs": [
                    {
                        "run_id": r["run_id"],
                        "workflow_id": r.get("workflow_id"),
                        "status": r.get("status", "unknown"),
                        "updated_at": r.get("updated_at"),
                    }
                    for r in runs
                ]
            }
            cli._emit_workflow_json(payload)
            return

        if not runs:
            cli.console.print("[yellow]No workflow runs found.[/yellow]")
            return

        cli.console.print("\n[bold cyan]Workflow Runs:[/bold cyan]\n")
        for run_data in runs:
            s = run_data.get("status", "unknown")
            sc = {
                "completed": "green",
                "failed": "red",
                "paused": "yellow",
                "running": "blue",
            }.get(s, "white")
            cli.console.print(
                f"  [{sc}]●[/{sc}] {run_data['run_id']}  "
                f"{run_data.get('workflow_id', '?')}  "
                f"[{sc}]{s}[/{sc}]  "
                f"[dim]{run_data.get('updated_at', '?')}[/dim]"
            )
