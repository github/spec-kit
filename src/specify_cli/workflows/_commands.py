"""specify workflow * command handlers — app objects and register().

Moved out of __init__.py (PR-8/8). Handlers reference `_require_specify_project`
(kept in the package root) through the thin shim below, which re-fetches from
the parent package at call time so test monkeypatching of
`specify_cli._require_specify_project` keeps working.
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.markup import escape as _escape_markup

from .._console import console, err_console
from .._project import _resolve_init_dir_override

workflow_app = typer.Typer(
    name="workflow",
    help="Manage and run automation workflows",
    add_completion=False,
)

workflow_catalog_app = typer.Typer(
    name="catalog",
    help="Manage workflow catalogs",
    add_completion=False,
)
workflow_app.add_typer(workflow_catalog_app, name="catalog")

workflow_step_app = typer.Typer(
    name="step",
    help="Manage workflow step types",
    add_completion=False,
)
workflow_app.add_typer(workflow_step_app, name="step")

workflow_step_catalog_app = typer.Typer(
    name="catalog",
    help="Manage step catalogs",
    add_completion=False,
)
workflow_step_app.add_typer(workflow_step_catalog_app, name="catalog")


def _error_console(json_output: bool):
    """Console for error text: stderr under ``--json`` so the JSON stdout
    stream stays parseable, the normal console otherwise. Mirrors the
    stderr-only error routing already used by ``specify bundle``.
    """
    return err_console if json_output else console


def _parse_input_values(
    input_values: list[str] | None, *, json_output: bool = False
) -> dict[str, Any]:
    """Parse repeated ``key=value`` CLI inputs into a dict.

    Shared by ``workflow run`` and ``workflow resume``. Exits with an error
    on any entry missing ``=``.
    """
    inputs: dict[str, Any] = {}
    for kv in input_values or []:
        if "=" not in kv:
            _error_console(json_output).print(
                f"[red]Error:[/red] Invalid input format: {kv!r} (expected key=value)"
            )
            raise typer.Exit(1)
        key, _, value = kv.partition("=")
        inputs[key.strip()] = value.strip()
    return inputs


def _reject_unsafe_dir(path: Path, label: str) -> None:
    """Refuse to proceed when *path* is a symlink or an existing non-directory.

    A symlinked ``.specify`` (or ``.specify/workflows``) could redirect
    workflow writes outside the project root, so any command that creates or
    writes files beneath it must bail first. Absence is tolerated — the caller
    creates the directory — only an existing-but-wrong target is rejected.
    """
    if path.is_symlink():
        err_console.print(f"[red]Error:[/red] Refusing to use symlinked {label} path")
        raise typer.Exit(1)
    if path.exists() and not path.is_dir():
        err_console.print(f"[red]Error:[/red] {label} path exists but is not a directory")
        raise typer.Exit(1)


def _reject_unsafe_workflow_storage(project_root: Path) -> None:
    """Refuse symlinked workflow storage directories before workflow commands run."""
    _reject_unsafe_dir(project_root / ".specify", ".specify")
    _reject_unsafe_dir(project_root / ".specify" / "workflows", ".specify/workflows")
    _reject_unsafe_dir(
        project_root / ".specify" / "workflows" / "runs",
        ".specify/workflows/runs",
    )


_WORKFLOW_ID_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
_RESERVED_WORKFLOW_IDS: frozenset[str] = frozenset({"runs", "steps"})


def _validate_workflow_id_or_exit(workflow_id: str) -> None:
    """Validate that ``workflow_id`` is a safe installed-workflow directory name."""
    if (
        workflow_id in _RESERVED_WORKFLOW_IDS
        or not _WORKFLOW_ID_PATTERN.match(workflow_id)
    ):
        console.print(
            f"[red]Error:[/red] Invalid workflow ID: {_escape_markup(repr(workflow_id))}"
        )
        raise typer.Exit(1)


def _safe_workflow_id_dir(workflows_dir: Path, workflow_id: str) -> Path:
    """Validate the per-id install directory before any write and return it.

    Installs write to ``workflows_dir / <id> / workflow.yml``. The ``<id>``
    segment comes from a workflow YAML or catalog key, so it must be checked
    before ``mkdir``/copy/download follows a symlink outside the project root.
    Rejects, with a clean ``typer.Exit``:

    - an ``<id>`` that is a symlink or an existing non-directory
      (the latter would otherwise make ``mkdir`` raise);
    - an ``<id>`` that is not a single workflow-id path segment or collides
      with internal workflow storage directories;
    - an ``<id>`` that escapes ``workflows_dir`` (path traversal);
    - an ``<id>/workflow.yml`` leaf that is a symlink or an existing
      non-file (either would otherwise make the later write/copy raise).

    The symlink/non-directory check runs *before* ``resolve()`` so a symlinked
    ``<id>`` reports as a symlink rather than misleadingly as path traversal.
    ``workflow_id`` is markup-escaped in output to avoid Rich markup injection.
    """
    safe_id = _escape_markup(workflow_id)
    _validate_workflow_id_or_exit(workflow_id)

    dest_dir = workflows_dir / workflow_id
    _reject_unsafe_dir(dest_dir, f".specify/workflows/{safe_id}")
    try:
        dest_dir.resolve().relative_to(workflows_dir.resolve())
    except ValueError:
        # Escape the repr (not the raw id) so backslashes added by repr cannot
        # re-expose markup brackets to Rich.
        console.print(
            f"[red]Error:[/red] Invalid workflow ID: {_escape_markup(repr(workflow_id))}"
        )
        raise typer.Exit(1)
    workflow_yml = dest_dir / "workflow.yml"
    if workflow_yml.is_symlink():
        console.print(
            "[red]Error:[/red] Refusing to write through symlinked "
            f".specify/workflows/{safe_id}/workflow.yml"
        )
        raise typer.Exit(1)
    if workflow_yml.exists() and not workflow_yml.is_file():
        console.print(
            "[red]Error:[/red] "
            f".specify/workflows/{safe_id}/workflow.yml exists but is not a file"
        )
        raise typer.Exit(1)
    return dest_dir


# Root helper re-fetched at call time so test monkeypatching of
# `specify_cli._require_specify_project` keeps working after the move.
def _require_specify_project(*args, **kwargs):
    from .. import _require_specify_project as _f

    project_root = _f(*args, **kwargs)
    _reject_unsafe_workflow_storage(project_root)
    return project_root


def _workflow_run_payload(state: Any) -> dict[str, Any]:
    """Machine-readable summary of a run/resume outcome."""
    payload = {
        "run_id": state.run_id,
        "workflow_id": state.workflow_id,
        "status": state.status.value,
        "current_step_id": state.current_step_id,
        "current_step_index": state.current_step_index,
    }
    gate = _gate_outcome(state)
    if gate is not None:
        payload["gate"] = gate
    return payload


def _is_gate_step(step: dict[str, Any]) -> bool:
    """Whether a recorded step result is a gate.

    Prefers the persisted ``type`` field, but when it is absent — a run paused
    by an older version, whose step record predates ``type`` being stored —
    falls back to the gate's unique output signature: only ``GateStep`` writes
    an ``on_reject`` key. A record carrying a *different* known ``type`` is not
    a gate, so the fallback applies only when ``type`` is missing entirely.
    """
    step_type = step.get("type")
    if step_type == "gate":
        return True
    if step_type:
        return False
    output = step.get("output")
    return isinstance(output, dict) and "on_reject" in output


def _gate_outcome(state: Any) -> dict[str, Any] | None:
    """Gate detail for the structured outcome, when the run rests at a gate.

    A paused or gate-aborted run is otherwise indistinguishable from any
    other pause/abort in the machine-readable payload; surfacing the gate's
    prompt, options, and (after an interactive choice) the decision lets
    orchestrators drive review gates without parsing the human-facing stream.
    """
    # Two run states rest *on* a gate: `paused` (awaiting a decision) and
    # `aborted` (a gate rejected with `on_reject: abort` — the only path that
    # sets ABORTED, leaving current_step_id on that gate). Any other status —
    # notably `completed`/`failed` — must be suppressed: current_step_id is
    # not cleared when a run whose last executed step was a gate moves on, so
    # without this guard it would surface stale detail (run/resume/status).
    if getattr(state.status, "value", state.status) not in ("paused", "aborted"):
        return None
    step = (getattr(state, "step_results", None) or {}).get(state.current_step_id)
    if not isinstance(step, dict) or not _is_gate_step(step):
        return None
    output = step.get("output") or {}
    # `message`, `options`, and `choice` may be non-string YAML literals in an
    # unvalidated workflow (GateStep coerces none of them for the payload), so
    # normalise all three for a stable JSON schema: message → str, options →
    # list[str] | None, choice → str | None (None means no decision yet).
    message = output.get("message")
    choice = output.get("choice")
    return {
        "step_id": state.current_step_id,
        "message": None if message is None else str(message),
        "options": _normalize_gate_options(output.get("options")),
        "choice": None if choice is None else str(choice),
    }


def _normalize_gate_options(options: Any) -> list[str] | None:
    """Normalise a gate's ``options`` to a stable ``list[str]`` (or ``None``).

    A valid gate stores a list, but an unvalidated workflow could leave a
    scalar or tuple. ``None`` stays ``None`` (no options); a list/tuple maps
    each element through ``str``; any other scalar becomes a single-element
    list — so the emitted JSON schema is always ``list[str] | None``. A bare
    string is treated as one option, never iterated character-by-character.
    """
    if options is None:
        return None
    if isinstance(options, (list, tuple)):
        return [str(o) for o in options]
    return [str(options)]


def _run_outcome_exit_code(status_value: str) -> int:
    """Exit code for a finished run/resume: non-zero on terminal failure.

    ``failed`` and ``aborted`` map to 1 so scripts and orchestrators can
    rely on the process exit code; ``completed`` and ``paused`` map to 0
    (paused is a legitimate waiting state, not a failure).
    """
    return 1 if status_value in ("failed", "aborted") else 0


def _emit_workflow_json(payload: dict[str, Any]) -> None:
    """Write a workflow payload as machine-readable JSON to stdout.

    Uses the builtin ``print`` rather than ``console.print`` so Rich
    markup interpretation, syntax highlighting, and line-wrapping can
    never alter the emitted JSON.
    """
    print(json.dumps(payload, indent=2))


@contextlib.contextmanager
def _stdout_to_stderr_when(active: bool):
    """Redirect everything written to stdout onto stderr while *active*.

    Suppressing the banner and the step-start callback is not enough to
    keep a ``--json`` stream clean: individual steps may still write to
    stdout while the engine runs — the gate step prints its prompt,
    and the prompt step runs a subprocess that inherits the process's
    stdout file descriptor. Either would corrupt the single JSON object.

    Redirecting at the file-descriptor level (``dup2``) captures both
    Python-level writes and inherited-fd subprocess output, so step
    progress lands on stderr (still visible to a human) while stdout
    carries only the emitted JSON. A no-op when *active* is false.
    """
    if not active:
        yield
        return
    sys.stdout.flush()
    saved_stdout_fd = os.dup(1)
    try:
        os.dup2(2, 1)  # fd 1 (stdout) now points at fd 2 (stderr)
        with contextlib.redirect_stdout(sys.stderr):
            yield
    finally:
        sys.stdout.flush()
        os.dup2(saved_stdout_fd, 1)  # restore the real stdout
        os.close(saved_stdout_fd)


@workflow_app.command("run")
def workflow_run(
    source: str = typer.Argument(..., help="Workflow ID or YAML file path"),
    input_values: list[str] | None = typer.Option(
        None, "--input", "-i", help="Input values as key=value pairs"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit the run outcome as a single JSON object instead of formatted text.",
    ),
):
    """Run a workflow from an installed ID or local YAML path."""
    from . import load_custom_steps
    from .engine import WorkflowEngine

    source_path = Path(source).expanduser()
    is_file_source = source_path.suffix.lower() in (".yml", ".yaml") and source_path.is_file()

    if is_file_source:
        # When running a YAML file directly, use cwd as project root without
        # requiring a .specify/ project directory — unless SPECIFY_INIT_DIR
        # explicitly names a project, in which case the strict override applies.
        override = _resolve_init_dir_override()
        project_root = override if override is not None else Path.cwd()
        _reject_unsafe_workflow_storage(project_root)
    else:
        project_root = _require_specify_project()

    load_custom_steps(project_root)
    engine = WorkflowEngine(project_root)
    if not json_output:
        engine.on_step_start = lambda sid, label: console.print(f"  \u25b8 [{sid}] {label} \u2026")

    err = _error_console(json_output)
    try:
        definition = engine.load_workflow(source_path if is_file_source else source)
    except FileNotFoundError:
        err.print(f"[red]Error:[/red] Workflow not found: {source}")
        raise typer.Exit(1)
    except ValueError as exc:
        err.print(f"[red]Error:[/red] Invalid workflow: {exc}")
        raise typer.Exit(1)

    # Validate
    errors = engine.validate(definition)
    if errors:
        err.print("[red]Workflow validation failed:[/red]")
        for verr in errors:
            err.print(f"  • {verr}")
        raise typer.Exit(1)

    # Parse inputs
    inputs = _parse_input_values(input_values, json_output=json_output)

    if not json_output:
        console.print(f"\n[bold cyan]Running workflow:[/bold cyan] {definition.name} ({definition.id})")
        console.print(f"[dim]Version: {definition.version}[/dim]\n")

    try:
        with _stdout_to_stderr_when(json_output):
            state = engine.execute(definition, inputs)
    except ValueError as exc:
        err.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)
    except Exception as exc:
        err.print(f"[red]Workflow failed:[/red] {exc}")
        raise typer.Exit(1)

    if json_output:
        _emit_workflow_json(_workflow_run_payload(state))
        raise typer.Exit(_run_outcome_exit_code(state.status.value))

    status_colors = {
        "completed": "green",
        "paused": "yellow",
        "failed": "red",
        "aborted": "red",
    }
    color = status_colors.get(state.status.value, "white")
    console.print(f"\n[{color}]Status: {state.status.value}[/{color}]")
    console.print(f"[dim]Run ID: {state.run_id}[/dim]")

    if state.status.value == "paused":
        console.print(f"\nResume with: [cyan]specify workflow resume {state.run_id}[/cyan]")

    raise typer.Exit(_run_outcome_exit_code(state.status.value))


@workflow_app.command("resume")
def workflow_resume(
    run_id: str = typer.Argument(..., help="Run ID to resume"),
    input_values: list[str] | None = typer.Option(
        None, "--input", "-i", help="Updated input values as key=value pairs"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit the resume outcome as a single JSON object instead of formatted text.",
    ),
):
    """Resume a paused or failed workflow run."""
    from . import load_custom_steps
    from .engine import WorkflowEngine

    project_root = _require_specify_project()
    load_custom_steps(project_root)
    engine = WorkflowEngine(project_root)
    if not json_output:
        engine.on_step_start = lambda sid, label: console.print(f"  \u25b8 [{sid}] {label} \u2026")

    inputs = _parse_input_values(input_values, json_output=json_output)
    err = _error_console(json_output)

    try:
        with _stdout_to_stderr_when(json_output):
            state = engine.resume(run_id, inputs or None)
    except FileNotFoundError:
        err.print(f"[red]Error:[/red] Run not found: {run_id}")
        raise typer.Exit(1)
    except ValueError as exc:
        err.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)
    except Exception as exc:
        err.print(f"[red]Resume failed:[/red] {exc}")
        raise typer.Exit(1)

    if json_output:
        _emit_workflow_json(_workflow_run_payload(state))
        raise typer.Exit(_run_outcome_exit_code(state.status.value))

    status_colors = {
        "completed": "green",
        "paused": "yellow",
        "failed": "red",
        "aborted": "red",
    }
    color = status_colors.get(state.status.value, "white")
    console.print(f"\n[{color}]Status: {state.status.value}[/{color}]")

    raise typer.Exit(_run_outcome_exit_code(state.status.value))


@workflow_app.command("status")
def workflow_status(
    run_id: str | None = typer.Argument(None, help="Run ID to inspect (shows all if omitted)"),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit run status as a single JSON object instead of formatted text.",
    ),
):
    """Show workflow run status."""
    from .engine import WorkflowEngine

    project_root = _require_specify_project()
    engine = WorkflowEngine(project_root)

    if run_id:
        try:
            from .engine import RunState
            state = RunState.load(run_id, project_root)
        except FileNotFoundError:
            console.print(f"[red]Error:[/red] Run not found: {run_id}")
            raise typer.Exit(1)

        if json_output:
            # Build on the shared run/resume payload so the common fields
            # (including current_step_index) stay identical across commands.
            payload = {
                **_workflow_run_payload(state),
                "created_at": state.created_at,
                "updated_at": state.updated_at,
                "steps": {
                    sid: sd.get("status", "unknown")
                    for sid, sd in state.step_results.items()
                },
            }
            _emit_workflow_json(payload)
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

        console.print(f"\n[bold cyan]Workflow Run: {state.run_id}[/bold cyan]")
        console.print(f"  Workflow: {state.workflow_id}")
        console.print(f"  Status:   [{color}]{state.status.value}[/{color}]")
        console.print(f"  Created:  {state.created_at}")
        console.print(f"  Updated:  {state.updated_at}")

        if state.current_step_id:
            console.print(f"  Current:  {state.current_step_id}")

        if state.step_results:
            console.print(f"\n  [bold]Steps ({len(state.step_results)}):[/bold]")
            for step_id, step_data in state.step_results.items():
                s = step_data.get("status", "unknown")
                sc = {"completed": "green", "failed": "red", "paused": "yellow"}.get(s, "white")
                console.print(f"    [{sc}]●[/{sc}] {step_id}: {s}")
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
            _emit_workflow_json(payload)
            return

        if not runs:
            console.print("[yellow]No workflow runs found.[/yellow]")
            return

        console.print("\n[bold cyan]Workflow Runs:[/bold cyan]\n")
        for run_data in runs:
            s = run_data.get("status", "unknown")
            sc = {"completed": "green", "failed": "red", "paused": "yellow", "running": "blue"}.get(s, "white")
            console.print(
                f"  [{sc}]●[/{sc}] {run_data['run_id']}  "
                f"{run_data.get('workflow_id', '?')}  "
                f"[{sc}]{s}[/{sc}]  "
                f"[dim]{run_data.get('updated_at', '?')}[/dim]"
            )


@workflow_app.command("list")
def workflow_list():
    """List installed workflows."""
    from .catalog import WorkflowRegistry

    project_root = _require_specify_project()
    registry = WorkflowRegistry(project_root)
    installed = registry.list()

    if not installed:
        console.print("[yellow]No workflows installed.[/yellow]")
        console.print("\nInstall a workflow with:")
        console.print("  [cyan]specify workflow add <workflow-id>[/cyan]")
        return

    console.print("\n[bold cyan]Installed Workflows:[/bold cyan]\n")
    for wf_id, wf_data in installed.items():
        console.print(f"  [bold]{wf_data.get('name', wf_id)}[/bold] ({wf_id}) v{wf_data.get('version', '?')}")
        desc = wf_data.get("description", "")
        if desc:
            console.print(f"    {desc}")
        console.print()


@workflow_app.command("add")
def workflow_add(
    source: str = typer.Argument(..., help="Workflow ID, URL, or local path"),
):
    """Install a workflow from catalog, URL, or local path."""
    from .catalog import WorkflowCatalog, WorkflowRegistry, WorkflowCatalogError
    from .engine import WorkflowDefinition

    project_root = _require_specify_project()
    registry = WorkflowRegistry(project_root)
    workflows_dir = project_root / ".specify" / "workflows"
    # Reject a symlinked .specify / .specify/workflows before any write so an
    # install can't escape the project root (covers the local, URL, and
    # catalog branches below — all write beneath workflows_dir).
    _reject_unsafe_dir(project_root / ".specify", ".specify")
    _reject_unsafe_dir(workflows_dir, ".specify/workflows")

    def _validate_and_install_local(yaml_path: Path, source_label: str) -> None:
        """Validate and install a workflow from a local YAML file."""
        try:
            definition = WorkflowDefinition.from_yaml(yaml_path)
        except (ValueError, yaml.YAMLError) as exc:
            console.print(f"[red]Error:[/red] Invalid workflow YAML: {exc}")
            raise typer.Exit(1)
        if not definition.id or not definition.id.strip():
            console.print("[red]Error:[/red] Workflow definition has an empty or missing 'id'")
            raise typer.Exit(1)

        from .engine import validate_workflow
        errors = validate_workflow(definition)
        if errors:
            console.print("[red]Error:[/red] Workflow validation failed:")
            for err in errors:
                console.print(f"  \u2022 {err}")
            raise typer.Exit(1)

        dest_dir = _safe_workflow_id_dir(workflows_dir, definition.id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(yaml_path, dest_dir / "workflow.yml")
        registry.add(definition.id, {
            "name": definition.name,
            "version": definition.version,
            "description": definition.description,
            "source": source_label,
        })
        console.print(f"[green]✓[/green] Workflow '{definition.name}' ({definition.id}) installed")

    # Try as URL (http/https)
    if source.startswith("http://") or source.startswith("https://"):
        from ipaddress import ip_address
        from urllib.parse import urlparse
        from specify_cli.authentication.http import open_url as _open_url

        try:
            parsed_src = urlparse(source)
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid URL: {_escape_markup(source)}")
            raise typer.Exit(1)
        src_host = parsed_src.hostname or ""
        src_loopback = src_host == "localhost"
        if not src_loopback:
            try:
                src_loopback = ip_address(src_host).is_loopback
            except ValueError:
                # Host is not an IP literal (e.g., a DNS name); keep default non-loopback.
                pass
        if parsed_src.scheme != "https" and not (parsed_src.scheme == "http" and src_loopback):
            console.print("[red]Error:[/red] Only HTTPS URLs are allowed, except HTTP for localhost.")
            raise typer.Exit(1)

        from specify_cli._github_http import resolve_github_release_asset_api_url as _resolve_gh_asset
        from specify_cli.authentication.http import github_provider_hosts as _github_provider_hosts

        _wf_url_extra_headers = None
        _resolved_wf_url = _resolve_gh_asset(
            source, _open_url, timeout=30, github_hosts=_github_provider_hosts()
        )
        if _resolved_wf_url:
            source = _resolved_wf_url
            _wf_url_extra_headers = {"Accept": "application/octet-stream"}

        import tempfile
        try:
            with _open_url(source, timeout=30, extra_headers=_wf_url_extra_headers) as resp:
                final_url = resp.geturl()
                final_parsed = urlparse(final_url)
                final_host = final_parsed.hostname or ""
                final_lb = final_host == "localhost"
                if not final_lb:
                    try:
                        final_lb = ip_address(final_host).is_loopback
                    except ValueError:
                        # Redirect host is not an IP literal; keep loopback as determined above.
                        pass
                if final_parsed.scheme != "https" and not (final_parsed.scheme == "http" and final_lb):
                    console.print(f"[red]Error:[/red] URL redirected to non-HTTPS: {final_url}")
                    raise typer.Exit(1)
                with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as tmp:
                    tmp.write(resp.read())
                    tmp_path = Path(tmp.name)
        except typer.Exit:
            raise
        except Exception as exc:
            console.print(f"[red]Error:[/red] Failed to download workflow: {exc}")
            raise typer.Exit(1)
        try:
            _validate_and_install_local(tmp_path, source)
        finally:
            tmp_path.unlink(missing_ok=True)
        return

    # Try as a local file/directory
    source_path = Path(source)
    if source_path.exists():
        if source_path.is_file() and source_path.suffix in (".yml", ".yaml"):
            _validate_and_install_local(source_path, str(source_path))
            return
        elif source_path.is_dir():
            wf_file = source_path / "workflow.yml"
            if not wf_file.exists():
                console.print(f"[red]Error:[/red] No workflow.yml found in {source}")
                raise typer.Exit(1)
            _validate_and_install_local(wf_file, str(source_path))
            return

    # Try from catalog
    catalog = WorkflowCatalog(project_root)
    try:
        info = catalog.get_workflow_info(source)
    except WorkflowCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    if not info:
        console.print(f"[red]Error:[/red] Workflow '{source}' not found in catalog")
        raise typer.Exit(1)

    if not info.get("_install_allowed", True):
        console.print(f"[yellow]Warning:[/yellow] Workflow '{source}' is from a discovery-only catalog")
        console.print("Direct installation is not enabled for this catalog source.")
        raise typer.Exit(1)

    workflow_url = info.get("url")
    if not workflow_url:
        console.print(f"[red]Error:[/red] Workflow '{source}' does not have an install URL in the catalog")
        raise typer.Exit(1)

    # Validate URL scheme (HTTPS required, HTTP allowed for localhost only)
    from ipaddress import ip_address
    from urllib.parse import urlparse

    parsed_url = urlparse(workflow_url)
    url_host = parsed_url.hostname or ""
    is_loopback = False
    if url_host == "localhost":
        is_loopback = True
    else:
        try:
            is_loopback = ip_address(url_host).is_loopback
        except ValueError:
            # Host is not an IP literal (e.g., a regular hostname); treat as non-loopback.
            pass
    if parsed_url.scheme != "https" and not (parsed_url.scheme == "http" and is_loopback):
        console.print(
            f"[red]Error:[/red] Workflow '{source}' has an invalid install URL. "
            "Only HTTPS URLs are allowed, except HTTP for localhost/loopback."
        )
        raise typer.Exit(1)

    # Reject path traversal, symlinked <id>, and a symlinked workflow.yml leaf
    # before any mkdir/download writes beneath the install directory.
    workflow_dir = _safe_workflow_id_dir(workflows_dir, source)
    workflow_file = workflow_dir / "workflow.yml"

    try:
        from specify_cli.authentication.http import open_url as _open_url
        from specify_cli.authentication.http import github_provider_hosts as _github_provider_hosts
        from specify_cli._github_http import resolve_github_release_asset_api_url as _resolve_gh_asset

        _wf_cat_extra_headers = None
        _resolved_workflow_url = _resolve_gh_asset(
            workflow_url, _open_url, timeout=30, github_hosts=_github_provider_hosts()
        )
        if _resolved_workflow_url:
            workflow_url = _resolved_workflow_url
            _wf_cat_extra_headers = {"Accept": "application/octet-stream"}

        workflow_dir.mkdir(parents=True, exist_ok=True)
        with _open_url(workflow_url, timeout=30, extra_headers=_wf_cat_extra_headers) as response:
            # Validate final URL after redirects
            final_url = response.geturl()
            final_parsed = urlparse(final_url)
            final_host = final_parsed.hostname or ""
            final_loopback = final_host == "localhost"
            if not final_loopback:
                try:
                    final_loopback = ip_address(final_host).is_loopback
                except ValueError:
                    # Host is not an IP literal (e.g., a regular hostname); treat as non-loopback.
                    pass
            if final_parsed.scheme != "https" and not (final_parsed.scheme == "http" and final_loopback):
                if workflow_dir.exists():
                    import shutil
                    shutil.rmtree(workflow_dir, ignore_errors=True)
                console.print(
                    f"[red]Error:[/red] Workflow '{source}' redirected to non-HTTPS URL: {final_url}"
                )
                raise typer.Exit(1)
            workflow_file.write_bytes(response.read())
    except Exception as exc:
        if workflow_dir.exists():
            import shutil
            shutil.rmtree(workflow_dir, ignore_errors=True)
        console.print(f"[red]Error:[/red] Failed to install workflow '{source}' from catalog: {exc}")
        raise typer.Exit(1)

    # Validate the downloaded workflow before registering
    try:
        definition = WorkflowDefinition.from_yaml(workflow_file)
    except (ValueError, yaml.YAMLError) as exc:
        import shutil
        shutil.rmtree(workflow_dir, ignore_errors=True)
        console.print(f"[red]Error:[/red] Downloaded workflow is invalid: {exc}")
        raise typer.Exit(1)

    from .engine import validate_workflow
    errors = validate_workflow(definition)
    if errors:
        import shutil
        shutil.rmtree(workflow_dir, ignore_errors=True)
        console.print("[red]Error:[/red] Downloaded workflow validation failed:")
        for err in errors:
            console.print(f"  \u2022 {err}")
        raise typer.Exit(1)

    # Enforce that the workflow's internal ID matches the catalog key
    if definition.id and definition.id != source:
        import shutil
        shutil.rmtree(workflow_dir, ignore_errors=True)
        console.print(
            f"[red]Error:[/red] Workflow ID in YAML ({definition.id!r}) "
            f"does not match catalog key ({source!r}). "
            f"The catalog entry may be misconfigured."
        )
        raise typer.Exit(1)

    registry.add(source, {
        "name": definition.name or info.get("name", source),
        "version": definition.version or info.get("version", "0.0.0"),
        "description": definition.description or info.get("description", ""),
        "source": "catalog",
        "catalog_name": info.get("_catalog_name", ""),
        "url": workflow_url,
    })
    console.print(f"[green]✓[/green] Workflow '{info.get('name', source)}' installed from catalog")


@workflow_app.command("remove")
def workflow_remove(
    workflow_id: str = typer.Argument(..., help="Workflow ID to uninstall"),
):
    """Uninstall a workflow."""
    from .catalog import WorkflowRegistry

    project_root = _require_specify_project()
    workflows_dir = project_root / ".specify" / "workflows"
    _validate_workflow_id_or_exit(workflow_id)

    registry = WorkflowRegistry(project_root)

    if not registry.is_installed(workflow_id):
        console.print(f"[red]Error:[/red] Workflow '{workflow_id}' is not installed")
        raise typer.Exit(1)

    # Remove workflow files
    workflow_dir_unresolved = workflows_dir / workflow_id
    safe_id = _escape_markup(workflow_id)
    if workflow_dir_unresolved.is_symlink():
        console.print(
            f"[red]Error:[/red] Refusing to remove symlinked "
            f".specify/workflows/{safe_id}"
        )
        raise typer.Exit(1)

    workflow_dir = workflow_dir_unresolved.resolve()
    try:
        rel_parts = workflow_dir.relative_to(workflows_dir.resolve()).parts
    except ValueError:
        console.print(
            f"[red]Error:[/red] Invalid workflow ID: {_escape_markup(repr(workflow_id))}"
        )
        raise typer.Exit(1)
    if rel_parts != (workflow_id,):
        console.print(
            f"[red]Error:[/red] Invalid workflow ID: {_escape_markup(repr(workflow_id))}"
        )
        raise typer.Exit(1)

    if workflow_dir.exists() and not workflow_dir.is_dir():
        console.print(
            f"[red]Error:[/red] .specify/workflows/{safe_id} exists but is not a directory"
        )
        raise typer.Exit(1)

    if workflow_dir.exists():
        import shutil
        try:
            shutil.rmtree(workflow_dir)
        except OSError as exc:
            console.print(
                f"[red]Error:[/red] Failed to remove workflow directory {workflow_dir}: {exc}"
            )
            raise typer.Exit(1)

    registry.remove(workflow_id)
    console.print(f"[green]✓[/green] Workflow '{workflow_id}' removed")


@workflow_app.command("search")
def workflow_search(
    query: str | None = typer.Argument(None, help="Search query"),
    tag: str | None = typer.Option(None, "--tag", help="Filter by tag"),
):
    """Search workflow catalogs."""
    from .catalog import WorkflowCatalog, WorkflowCatalogError

    project_root = _require_specify_project()
    catalog = WorkflowCatalog(project_root)

    try:
        results = catalog.search(query=query, tag=tag)
    except WorkflowCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    if not results:
        console.print("[yellow]No workflows found.[/yellow]")
        return

    console.print(f"\n[bold cyan]Workflows ({len(results)}):[/bold cyan]\n")
    for wf in results:
        console.print(f"  [bold]{wf.get('name', wf.get('id', '?'))}[/bold] ({wf.get('id', '?')}) v{wf.get('version', '?')}")
        desc = wf.get("description", "")
        if desc:
            console.print(f"    {desc}")
        tags = wf.get("tags", [])
        if tags:
            console.print(f"    [dim]Tags: {', '.join(tags)}[/dim]")
        console.print()


@workflow_app.command("info")
def workflow_info(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
):
    """Show workflow details and step graph."""
    from .catalog import WorkflowCatalog, WorkflowRegistry, WorkflowCatalogError
    from .engine import WorkflowEngine

    project_root = _require_specify_project()

    # Check installed first
    registry = WorkflowRegistry(project_root)
    installed = registry.get(workflow_id)

    engine = WorkflowEngine(project_root)

    definition = None
    try:
        definition = engine.load_workflow(workflow_id)
    except FileNotFoundError:
        # Local workflow definition not found on disk; fall back to
        # catalog/registry lookup below.
        pass

    if definition:
        console.print(f"\n[bold cyan]{definition.name}[/bold cyan] ({definition.id})")
        console.print(f"  Version:     {definition.version}")
        if definition.author:
            console.print(f"  Author:      {definition.author}")
        if definition.description:
            console.print(f"  Description: {definition.description}")
        if definition.default_integration:
            console.print(f"  Integration: {definition.default_integration}")
        if installed:
            console.print("  [green]Installed[/green]")

        if definition.inputs:
            console.print("\n  [bold]Inputs:[/bold]")
            for name, inp in definition.inputs.items():
                if isinstance(inp, dict):
                    req = "required" if inp.get("required") else "optional"
                    console.print(f"    {name} ({inp.get('type', 'string')}) — {req}")

        if definition.steps:
            console.print(f"\n  [bold]Steps ({len(definition.steps)}):[/bold]")
            for step in definition.steps:
                stype = step.get("type", "command")
                console.print(f"    → {step.get('id', '?')} [{stype}]")
        return

    # Try catalog
    catalog = WorkflowCatalog(project_root)
    try:
        info = catalog.get_workflow_info(workflow_id)
    except WorkflowCatalogError:
        info = None

    if info:
        console.print(f"\n[bold cyan]{info.get('name', workflow_id)}[/bold cyan] ({workflow_id})")
        console.print(f"  Version:     {info.get('version', '?')}")
        if info.get("description"):
            console.print(f"  Description: {info['description']}")
        if info.get("tags"):
            console.print(f"  Tags:        {', '.join(info['tags'])}")
        console.print("  [yellow]Not installed[/yellow]")
    else:
        console.print(f"[red]Error:[/red] Workflow '{workflow_id}' not found")
        raise typer.Exit(1)


@workflow_catalog_app.command("list")
def workflow_catalog_list():
    """List configured workflow catalog sources."""
    from .catalog import WorkflowCatalog, WorkflowCatalogError

    project_root = _require_specify_project()
    catalog = WorkflowCatalog(project_root)

    try:
        configs = catalog.get_catalog_configs()
    except WorkflowCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Workflow Catalog Sources:[/bold cyan]\n")
    for i, cfg in enumerate(configs):
        install_status = "[green]install allowed[/green]" if cfg["install_allowed"] else "[yellow]discovery only[/yellow]"
        console.print(f"  [{i}] [bold]{cfg['name']}[/bold] — {install_status}")
        console.print(f"      {cfg['url']}")
        if cfg.get("description"):
            console.print(f"      [dim]{cfg['description']}[/dim]")
        console.print()


@workflow_catalog_app.command("add")
def workflow_catalog_add(
    url: str = typer.Argument(..., help="Catalog URL to add"),
    name: str | None = typer.Option(None, "--name", help="Catalog name"),
):
    """Add a workflow catalog source."""
    from .catalog import WorkflowCatalog, WorkflowValidationError

    project_root = _require_specify_project()
    catalog = WorkflowCatalog(project_root)
    try:
        catalog.add_catalog(url, name)
    except WorkflowValidationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Catalog source added: {url}")


@workflow_catalog_app.command("remove")
def workflow_catalog_remove(
    index: int = typer.Argument(..., help="Catalog index to remove (from 'catalog list')"),
):
    """Remove a workflow catalog source by index."""
    from .catalog import WorkflowCatalog, WorkflowValidationError

    project_root = _require_specify_project()
    catalog = WorkflowCatalog(project_root)
    try:
        removed_name = catalog.remove_catalog(index)
    except WorkflowValidationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Catalog source '{removed_name}' removed")


# ===== Workflow Step Commands =====

@workflow_step_app.command("list")
def workflow_step_list():
    """List installed step types (built-in and custom)."""
    from . import STEP_REGISTRY
    from .catalog import StepRegistry

    project_root = _require_specify_project()
    specify_dir = project_root / ".specify"

    # Read installed custom steps from registry only — no dynamic imports
    installed: dict = {}
    if specify_dir.exists():
        registry = StepRegistry(project_root)
        installed = registry.list()

    console.print("\n[bold cyan]Installed Step Types:[/bold cyan]\n")

    built_in = sorted(k for k in STEP_REGISTRY if k not in installed)
    if built_in:
        console.print("  [bold]Built-in:[/bold]")
        for key in built_in:
            console.print(f"    • {key}")
        console.print()

    if installed:
        console.print("  [bold]Custom (installed):[/bold]")
        for key in sorted(installed):
            meta = installed[key] or {}
            name = meta.get("name", key)
            version = meta.get("version", "?")
            console.print(f"    • [bold]{name}[/bold] ({key}) v{version}")
        console.print()

    if not built_in and not installed:
        console.print("[yellow]No step types found.[/yellow]")

    if specify_dir.exists():
        console.print(
            "  Install a new step type with: [cyan]specify workflow step add <id>[/cyan]"
        )


# IDs that map to internal names used under .specify/workflows/steps/ and must
# not be used as custom step IDs (dotfile check is done separately at runtime).
_RESERVED_STEP_IDS: frozenset[str] = frozenset({".cache", "step-registry.json"})

# Windows reserved device names (case-insensitive, with or without extensions)
_WINDOWS_RESERVED_NAMES: frozenset[str] = frozenset({
    "con", "prn", "aux", "nul",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
})

# Characters invalid in filenames on Windows
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
        console.print(
            f"[red]Error:[/red] Invalid step id '{step_id}': must be a single safe "
            "path component (no separators, no leading dot, not a reserved name, "
            "no invalid filename characters)"
        )
        raise typer.Exit(1)


def _resolve_steps_base_dir_or_exit(project_root: Path) -> Path:
    """Resolve .specify/workflows/steps while refusing symlinked parent directories."""
    project_root_resolved = project_root.resolve()
    steps_base_dir_unresolved = project_root / ".specify" / "workflows" / "steps"

    current = project_root
    for part in (".specify", "workflows", "steps"):
        current = current / part
        if current.is_symlink():
            console.print(
                f"[red]Error:[/red] Refusing to use symlinked step directory '{current}'"
            )
            raise typer.Exit(1)
        if current.exists() and not current.is_dir():
            console.print(
                f"[red]Error:[/red] Step directory path is not a directory: '{current}'"
            )
            raise typer.Exit(1)

    steps_base_dir = steps_base_dir_unresolved.resolve()
    try:
        steps_base_dir.relative_to(project_root_resolved)
    except ValueError:
        console.print(
            f"[red]Error:[/red] Step directory escapes project root: '{steps_base_dir}'"
        )
        raise typer.Exit(1)

    return steps_base_dir


@workflow_step_app.command("add")
def workflow_step_add(
    step_id: str = typer.Argument(..., help="Step type ID from catalog"),
):
    """Install a custom step type from the step catalog."""
    from .catalog import StepCatalog, StepCatalogError, StepRegistry, StepValidationError

    project_root = _require_specify_project()

    catalog = StepCatalog(project_root)
    try:
        info = catalog.get_step_info(step_id)
    except StepCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    if not info:
        console.print(f"[red]Error:[/red] Step type '{step_id}' not found in catalog")
        raise typer.Exit(1)

    if not info.get("_install_allowed", True):
        console.print(
            f"[yellow]Warning:[/yellow] Step type '{step_id}' is from a discovery-only catalog"
        )
        console.print("Direct installation is not enabled for this catalog source.")
        raise typer.Exit(1)

    # Reject step IDs that collide with built-in step types
    from . import STEP_REGISTRY as _step_reg
    if step_id in _step_reg:
        console.print(
            f"[red]Error:[/red] Step type '{step_id}' conflicts with a built-in step type"
        )
        raise typer.Exit(1)

    # Reject if already installed
    registry = StepRegistry(project_root)
    if registry.is_installed(step_id):
        console.print(
            f"[red]Error:[/red] Step type '{step_id}' is already installed. "
            "Remove it first with: [cyan]specify workflow step remove "
            f"{step_id}[/cyan]"
        )
        raise typer.Exit(1)

    step_yml_url = info.get("step_yml_url") or info.get("url")
    if not step_yml_url:
        console.print(f"[red]Error:[/red] Catalog entry for '{step_id}' has no URL")
        raise typer.Exit(1)

    # Derive __init__.py URL: replace trailing step.yml with __init__.py
    # or use explicit init_url if provided.
    init_url = info.get("init_url")
    if not init_url:
        if step_yml_url.endswith("step.yml"):
            init_url = step_yml_url[: -len("step.yml")] + "__init__.py"
        else:
            console.print(
                f"[red]Error:[/red] Cannot derive __init__.py URL from '{step_yml_url}'. "
                "Catalog entry should provide 'init_url' or a 'url' ending in 'step.yml'."
            )
            raise typer.Exit(1)

    from urllib.parse import urlparse
    from specify_cli.authentication.http import open_url as _open_url

    def _safe_fetch(url: str) -> bytes:
        parsed = urlparse(url)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
            raise ValueError(f"Refusing to fetch from non-HTTPS URL: {url}")
        if not parsed.hostname:
            raise ValueError(f"Refusing to fetch from URL with no hostname: {url}")
        with _open_url(url, timeout=30) as resp:
            final_url = resp.geturl()
            final_parsed = urlparse(final_url)
            final_is_localhost = final_parsed.hostname in ("localhost", "127.0.0.1", "::1")
            if final_parsed.scheme != "https" and not (
                final_parsed.scheme == "http" and final_is_localhost
            ):
                raise ValueError(f"Redirect to non-HTTPS URL: {final_url}")
            if not final_parsed.hostname:
                raise ValueError(f"Redirect to URL with no hostname: {final_url}")
            return resp.read()

    _validate_step_id_or_exit(step_id)

    steps_base_dir = _resolve_steps_base_dir_or_exit(project_root)
    step_dir = (steps_base_dir / step_id).resolve()
    # Defense-in-depth: ensure the resolved directory is a direct child of
    # steps_base_dir even after symlink resolution.
    try:
        rel_parts = step_dir.relative_to(steps_base_dir).parts
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise typer.Exit(1)
    if rel_parts != (step_id,):
        console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise typer.Exit(1)

    import shutil
    import tempfile

    # Refuse if step_dir already exists (e.g. leftover from a previous failed/manual
    # install that wasn't registered). The user should remove it before retrying.
    if step_dir.exists():
        console.print(
            f"[red]Error:[/red] Step directory already exists at '{step_dir}'. "
            f"Remove it manually or use: [cyan]specify workflow step remove {step_id}[/cyan]"
        )
        raise typer.Exit(1)

    # Create steps_base_dir now so the staging temp dir is on the same filesystem,
    # enabling a truly atomic os.rename() below.
    try:
        steps_base_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = Path(tempfile.mkdtemp(prefix="speckit_step_tmp_", dir=steps_base_dir))
    except OSError as exc:
        console.print(f"[red]Error:[/red] Failed to create staging directory: {exc}")
        raise typer.Exit(1)
    try:
        try:
            step_yml_content = _safe_fetch(step_yml_url)
            init_py_content = _safe_fetch(init_url)
        except Exception as exc:
            console.print(f"[red]Error:[/red] Failed to download step files: {exc}")
            raise typer.Exit(1)

        # Validate step.yml
        try:
            import yaml as _yaml

            meta = _yaml.safe_load(step_yml_content.decode("utf-8")) or {}
        except Exception as exc:
            console.print(f"[red]Error:[/red] Invalid step.yml: {exc}")
            raise typer.Exit(1)

        if not isinstance(meta, dict):
            console.print("[red]Error:[/red] step.yml must be a YAML mapping")
            raise typer.Exit(1)

        step_meta = meta.get("step", {})
        if not isinstance(step_meta, dict):
            console.print("[red]Error:[/red] step.yml 'step' field must be a mapping")
            raise typer.Exit(1)
        type_key = step_meta.get("type_key", "")
        if not type_key:
            console.print("[red]Error:[/red] step.yml missing 'step.type_key' field")
            raise typer.Exit(1)

        if type_key != step_id:
            console.print(
                f"[red]Error:[/red] step.yml type_key ({type_key!r}) does not match "
                f"catalog ID ({step_id!r})"
            )
            raise typer.Exit(1)

        # Write the two required files.
        try:
            (tmp_path / "step.yml").write_bytes(step_yml_content)
            (tmp_path / "__init__.py").write_bytes(init_py_content)
        except OSError as exc:
            console.print(
                f"[red]Error:[/red] Failed to write step files to staging directory: {exc}"
            )
            raise typer.Exit(1)

        # Optionally download additional package files declared in the catalog entry
        # (e.g. helper modules). Each entry in ``extra_files`` is a mapping of
        # relative-path → URL. step.yml and __init__.py are ignored here (already
        # written). Paths are validated to stay within the step package directory to
        # prevent path-traversal attacks.
        extra_files = info.get("extra_files")
        if extra_files is not None and not isinstance(extra_files, dict):
            console.print(
                "[yellow]Warning:[/yellow] Catalog entry 'extra_files' is not a mapping; "
                "additional package files will not be downloaded."
            )
            extra_files = {}
        for rel_path, file_url in (extra_files or {}).items():
            if not isinstance(rel_path, str) or not rel_path.strip():
                console.print(
                    "[red]Error:[/red] Catalog entry 'extra_files' contains an "
                    "empty or non-string path key"
                )
                raise typer.Exit(1)
            if rel_path in ("step.yml", "__init__.py"):
                continue  # already written above
            # Reject dot-path segments ('', '.', '..') that would refer to the
            # package directory itself (IsADirectoryError) or escape it.
            rel_parts = Path(rel_path).parts
            if not rel_parts or any(seg in ("", ".", "..") for seg in rel_parts):
                console.print(
                    f"[red]Error:[/red] extra_files path '{rel_path}' is not a "
                    "valid relative file path"
                )
                raise typer.Exit(1)
            if not isinstance(file_url, str) or not file_url.strip():
                console.print(
                    f"[red]Error:[/red] extra_files entry '{rel_path}' has an "
                    "empty or non-string URL"
                )
                raise typer.Exit(1)
            # Resolve both destination and base to handle any symlinks in tmp_path itself,
            # ensuring the traversal check is robust even on non-canonical paths.
            resolved_base = tmp_path.resolve()
            dest = (tmp_path / rel_path).resolve()
            try:
                dest.relative_to(resolved_base)
            except ValueError:
                console.print(
                    f"[red]Error:[/red] extra_files path '{rel_path}' is outside "
                    "the step package directory"
                )
                raise typer.Exit(1)
            try:
                file_content = _safe_fetch(file_url)
            except Exception as exc:
                console.print(
                    f"[red]Error:[/red] Failed to download extra file '{rel_path}': {exc}"
                )
                raise typer.Exit(1)
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(file_content)
            except OSError as exc:
                console.print(
                    f"[red]Error:[/red] Failed to write extra file '{rel_path}': {exc}"
                )
                raise typer.Exit(1)

        # Atomically rename the staging directory to the final location.
        # Both paths are under steps_base_dir (same filesystem), so os.rename()
        # is atomic on POSIX and won't leave a partially-written directory at
        # step_dir on failure.
        try:
            os.rename(tmp_path, step_dir)
        except OSError as exc:
            console.print(f"[red]Error:[/red] Failed to install step '{step_id}': {exc}")
            raise typer.Exit(1)
    finally:
        # Clean up if the rename hasn't moved tmp_path yet (i.e. on any failure).
        shutil.rmtree(tmp_path, ignore_errors=True)

    step_name = info.get("name") or step_id
    step_version = info.get("version") or step_meta.get("version") or "0.0.0"

    # Register in step registry
    registry = StepRegistry(project_root)
    try:
        registry.add(
            step_id,
            {
                "name": step_name,
                "version": step_version,
                "description": info.get("description", step_meta.get("description", "")),
                "author": info.get("author", step_meta.get("author", "")),
                "source": "catalog",
                "catalog_name": info.get("_catalog_name", ""),
                "type_key": type_key,
            },
        )
    except StepValidationError as exc:
        # Roll back the just-installed directory so the system isn't left with
        # an unregistered step package on disk after a registry write failure
        # (e.g. read-only filesystem, permission denied).
        shutil.rmtree(step_dir, ignore_errors=True)
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(
        f"[green]✓[/green] Step type '{step_name}' ({step_id}) installed"
    )
    console.print(
        "  Use [cyan]specify workflow step list[/cyan] to verify the installation."
    )


@workflow_step_app.command("remove")
def workflow_step_remove(
    step_id: str = typer.Argument(..., help="Step type ID to uninstall"),
):
    """Uninstall a custom step type."""
    from .catalog import StepRegistry, StepValidationError

    project_root = _require_specify_project()

    _validate_step_id_or_exit(step_id)

    registry = StepRegistry(project_root)
    in_registry = registry.is_installed(step_id)

    steps_base_dir = _resolve_steps_base_dir_or_exit(project_root)
    step_dir = (steps_base_dir / step_id).resolve()
    # Defense-in-depth: even though _validate_step_id_or_exit rejects path
    # separators, ensure that the resolved directory is a single child of
    # steps_base_dir and is not steps_base_dir itself.
    try:
        rel_parts = step_dir.relative_to(steps_base_dir).parts
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise typer.Exit(1)
    if rel_parts != (step_id,):
        console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise typer.Exit(1)

    dir_exists = step_dir.exists()

    if not in_registry and not dir_exists:
        console.print(f"[red]Error:[/red] Step type '{step_id}' is not installed")
        raise typer.Exit(1)

    if not in_registry and dir_exists:
        # The registry was likely reset due to corruption.  Warn the user that the
        # directory is being removed even though there is no registry entry, so
        # the orphaned package can be cleaned up and a fresh install attempted.
        console.print(
            f"[yellow]Warning:[/yellow] '{step_id}' has no registry entry "
            "(registry may have been reset). Removing the orphaned directory."
        )

    if dir_exists and not in_registry:
        # No registry write needed; just delete the orphaned directory.
        import shutil
        try:
            shutil.rmtree(step_dir)
        except OSError as exc:
            console.print(
                f"[red]Error:[/red] Failed to remove step directory {step_dir}: {exc}"
            )
            raise typer.Exit(1)
    elif in_registry:
        # Remove the registry entry, then the directory. If the directory
        # delete fails, restore the registry entry so state stays consistent
        # and a future `step add` isn't blocked by an orphaned directory
        # with no registry entry.
        registry_metadata = registry.get(step_id)
        try:
            registry.remove(step_id)
        except StepValidationError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1)
        if dir_exists:
            import shutil
            try:
                shutil.rmtree(step_dir)
            except OSError as exc:
                # Restore the original registry entry verbatim (bypass add()
                # which would overwrite timestamps).
                try:
                    if registry_metadata is not None:
                        registry.data["steps"][step_id] = registry_metadata
                        registry.save()
                except Exception as restore_exc:  # noqa: BLE001
                    console.print(
                        f"[yellow]Warning:[/yellow] Failed to restore registry entry "
                        f"for '{step_id}' after directory removal failure: {restore_exc}"
                    )
                console.print(
                    f"[red]Error:[/red] Failed to remove step directory {step_dir}: {exc}"
                )
                raise typer.Exit(1)
    console.print(f"[green]✓[/green] Step type '{step_id}' uninstalled")


@workflow_step_app.command("search")
def workflow_step_search(
    query: str | None = typer.Argument(None, help="Search query"),
):
    """Search the step type catalog."""
    from .catalog import StepCatalog, StepCatalogError

    project_root = _require_specify_project()

    catalog = StepCatalog(project_root)

    try:
        results = catalog.search(query=query)
    except StepCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    if not results:
        if query:
            console.print(f"[yellow]No step types found matching '{query}'.[/yellow]")
        else:
            console.print("[yellow]No step types found in catalog.[/yellow]")
        return

    console.print(f"\n[bold cyan]Step Types ({len(results)}):[/bold cyan]\n")
    for step in results:
        install_note = (
            "" if step.get("_install_allowed", True) else " [dim](discovery only)[/dim]"
        )
        console.print(
            f"  [bold]{step.get('name', step.get('id', '?'))}[/bold]"
            f" ({step.get('id', '?')}) v{step.get('version', '?')}{install_note}"
        )
        desc = step.get("description", "")
        if desc:
            console.print(f"    {desc}")
        console.print()


@workflow_step_app.command("info")
def workflow_step_info(
    step_id: str = typer.Argument(..., help="Step type ID"),
):
    """Show details for a step type."""
    from . import STEP_REGISTRY
    from .catalog import StepCatalog, StepCatalogError, StepRegistry

    project_root = _require_specify_project()

    registry = StepRegistry(project_root)
    installed_meta = registry.get(step_id)

    # Check if it's a built-in
    builtin_step = STEP_REGISTRY.get(step_id)
    is_builtin = builtin_step is not None and not installed_meta

    if is_builtin:
        console.print(f"\n[bold cyan]{step_id}[/bold cyan] [dim](built-in)[/dim]")
        console.print(f"  Type key: {step_id}")
        console.print("  [green]Built-in step type[/green]")
        return

    if installed_meta:
        console.print(
            f"\n[bold cyan]{installed_meta.get('name', step_id)}[/bold cyan] ({step_id})"
        )
        console.print(f"  Version:     {installed_meta.get('version', '?')}")
        if installed_meta.get("author"):
            console.print(f"  Author:      {installed_meta['author']}")
        if installed_meta.get("description"):
            console.print(f"  Description: {installed_meta['description']}")
        console.print("  [green]Installed[/green]")
        return

    # Try catalog
    catalog = StepCatalog(project_root)
    try:
        info = catalog.get_step_info(step_id)
    except StepCatalogError:
        info = None

    if info:
        console.print(
            f"\n[bold cyan]{info.get('name', step_id)}[/bold cyan] ({step_id})"
        )
        console.print(f"  Version:     {info.get('version', '?')}")
        if info.get("author"):
            console.print(f"  Author:      {info['author']}")
        if info.get("description"):
            console.print(f"  Description: {info['description']}")
        console.print("  [yellow]Not installed[/yellow]")
        console.print(
            f"\n  Install with: [cyan]specify workflow step add {step_id}[/cyan]"
        )
    else:
        console.print(f"[red]Error:[/red] Step type '{step_id}' not found")
        raise typer.Exit(1)


@workflow_step_catalog_app.command("list")
def workflow_step_catalog_list():
    """List configured step catalog sources."""
    from .catalog import StepCatalog, StepCatalogError

    project_root = _require_specify_project()
    catalog = StepCatalog(project_root)

    try:
        configs = catalog.get_catalog_configs()
    except StepCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Step Catalog Sources:[/bold cyan]\n")
    for i, cfg in enumerate(configs):
        install_status = (
            "[green]install allowed[/green]"
            if cfg["install_allowed"]
            else "[yellow]discovery only[/yellow]"
        )
        console.print(f"  [{i}] [bold]{cfg['name']}[/bold] — {install_status}")
        console.print(f"      {cfg['url']}")
        if cfg.get("description"):
            console.print(f"      [dim]{cfg['description']}[/dim]")
        console.print()


@workflow_step_catalog_app.command("add")
def workflow_step_catalog_add(
    url: str = typer.Argument(..., help="Catalog URL to add"),
    name: str | None = typer.Option(None, "--name", help="Catalog name"),
):
    """Add a step catalog source."""
    from .catalog import StepCatalog, StepValidationError

    project_root = _require_specify_project()

    catalog = StepCatalog(project_root)
    try:
        catalog.add_catalog(url, name)
    except StepValidationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Step catalog source added: {url}")


@workflow_step_catalog_app.command("remove")
def workflow_step_catalog_remove(
    index: int = typer.Argument(
        ..., help="Catalog index to remove (from 'step catalog list')"
    ),
):
    """Remove a step catalog source by index."""
    from .catalog import StepCatalog, StepValidationError

    project_root = _require_specify_project()

    catalog = StepCatalog(project_root)
    try:
        removed_name = catalog.remove_catalog(index)
    except StepValidationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Step catalog source '{removed_name}' removed")


def register(app: typer.Typer) -> None:
    """Attach the workflow command group to the root Typer app."""
    app.add_typer(workflow_app, name="workflow")
