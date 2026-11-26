"""Command handler for ``specify workflow resume``."""

from __future__ import annotations

from . import _command_resume_state as resume_state
from . import _commands as cli


class _ResumeTerminal(Exception):
    """A resume outcome held until the lock context has been left."""

    def __init__(self, render) -> None:
        super().__init__()
        self.render = render


def _defer_resume(render) -> None:
    raise _ResumeTerminal(render)


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
    from ..integrations.installer import IntegrationInstallError
    from ._execution import CheckpointError
    from .engine import RunState, WorkflowEngine, _resume_run_lock

    project_root = cli._require_specify_project(load_integrations=False)
    cli._load_project_workflow_plugins_or_exit(
        project_root, json_output=json_output, run_id=run_id
    )
    try:
        engine = WorkflowEngine(project_root)
        with cli._stdout_to_stderr_when(json_output):
            engine._load_integrations()
    except (IntegrationInstallError, OSError) as exc:
        cli._fail_integration_load(exc, json_output=json_output, run_id=run_id)
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

    def _resume_under_lock() -> None:
        # Pre-load the persisted run state so a run started from an installed
        # workflow that has since been disabled cannot resume unchecked --
        # engine.resume() replays the run directly from disk with no registry
        # awareness at all, which would otherwise bypass the same disabled
        # guard `workflow run` enforces. Runs without installed_workflow_id
        # (a direct/non-installed source, or a run persisted before this field
        # existed) are unaffected and resume exactly as before.
        # Terminal output is deferred until the lock context exits. Checkpoint
        # writes and resume execution stay inside this ownership.
        try:
            pre_state = RunState.load(run_id, project_root)
        except FileNotFoundError:
            def render_missing() -> None:
                err.print(f"[red]Error:[/red] Run not found: {run_id}")
                raise cli.typer.Exit(1)
            _defer_resume(render_missing)
        except ValueError as exc:
            def render_invalid(exc: ValueError = exc) -> None:
                err.print(f"[red]Error:[/red] {cli._escape_markup(str(exc))}")
                raise cli.typer.Exit(1)
            _defer_resume(render_invalid)
        except OSError as exc:
            def render_load(exc: OSError = exc) -> None:
                err.print(f"[red]Resume failed:[/red] {cli._escape_markup(str(exc))}")
                raise cli.typer.Exit(1)
            _defer_resume(render_load)

        if pre_state.installed_workflow_id is not None:
            try:
                owner_root = resume_state._resolve_run_owner_root(
                    pre_state.installed_registry_root, project_root
                )
            except ValueError as exc:
                def render_owner(exc: ValueError = exc) -> None:
                    err.print(f"[red]Error:[/red] {cli._escape_markup(str(exc))}")
                    raise cli.typer.Exit(1)
                _defer_resume(render_owner)
            cli._require_enabled_workflow(owner_root, pre_state.installed_workflow_id, err)
        elif not pre_state.installed_origin_tracked:
            if cli._require_enabled_workflow(project_root, pre_state.workflow_id, err):
                pre_state.installed_workflow_id = pre_state.workflow_id
            pre_state.installed_origin_tracked = True
            try:
                pre_state.save()
            except (OSError, CheckpointError) as exc:
                def render_save(exc: Exception = exc) -> None:
                    err.print(f"[red]Resume failed:[/red] {cli._escape_markup(str(exc))}")
                    raise cli.typer.Exit(1)
                _defer_resume(render_save)

        try:
            with cli._stdout_to_stderr_when(json_output):
                state = engine._resume_owned(run_id, inputs or None)
        except FileNotFoundError as exc:
            execution_state = engine._execution_state.get()
            def render_missing_run(
                exc: FileNotFoundError = exc,
                execution_state: RunState | None = execution_state,
            ) -> None:
                if execution_state is not None:
                    cli._fail_workflow_execution(
                        exc, json_output=json_output, state=execution_state, resume=True,
                    )
                cli._fail_integration_load(
                    FileNotFoundError(f"Run not found: {run_id}"),
                    json_output=json_output,
                    run_id=run_id,
                )
            _defer_resume(render_missing_run)
        except IntegrationInstallError as exc:
            execution_state = engine._execution_state.get()
            def render_integration(
                exc: IntegrationInstallError = exc,
                execution_state: RunState | None = execution_state,
            ) -> None:
                if execution_state is None:
                    cli._fail_integration_load(exc, json_output=json_output, run_id=run_id)
                cli._fail_workflow_execution(
                    exc, json_output=json_output, state=execution_state, resume=True,
                )
            _defer_resume(render_integration)
        except OSError as exc:
            execution_state = engine._execution_state.get()
            def render_execution(
                exc: OSError = exc,
                execution_state: RunState | None = execution_state,
            ) -> None:
                cli._fail_workflow_execution(
                    exc, json_output=json_output, state=execution_state, resume=True,
                )
            _defer_resume(render_execution)
        except ValueError as exc:
            execution_state = engine._execution_state.get()
            def render_recorded_value(
                exc: ValueError = exc,
                execution_state: RunState | None = execution_state,
            ) -> None:
                cli._fail_recorded_run(
                    exc, json_output=json_output, state=execution_state, resume=True,
                )
                err.print(f"[red]Error:[/red] {cli._escape_markup(str(exc))}")
                raise cli.typer.Exit(1)
            _defer_resume(render_recorded_value)
        except Exception as exc:
            execution_state = engine._execution_state.get()
            def render_recorded(
                exc: Exception = exc,
                execution_state: RunState | None = execution_state,
            ) -> None:
                cli._fail_recorded_run(
                    exc, json_output=json_output, state=execution_state, resume=True,
                )
                err.print(f"[red]Resume failed:[/red] {cli._escape_markup(str(exc))}")
                raise cli.typer.Exit(1)
            _defer_resume(render_recorded)

        def render_success(state: RunState = state) -> None:
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

        _defer_resume(render_success)

    try:
        with _resume_run_lock(project_root, run_id):
            _resume_under_lock()
    except _ResumeTerminal as pending:
        pending.render()
    except FileNotFoundError:
        err.print(f"[red]Error:[/red] Run not found: {run_id}")
        raise cli.typer.Exit(1)
    except ValueError as exc:
        err.print(f"[red]Error:[/red] {cli._escape_markup(str(exc))}")
        raise cli.typer.Exit(1)
    except OSError as exc:
        if json_output:
            cli._fail_integration_load(exc, json_output=True, run_id=run_id)
        err.print(f"[red]Resume failed:[/red] {cli._escape_markup(str(exc))}")
        raise cli.typer.Exit(1)
