"""CLI handlers for ``specify workflow overlay *`` and ``specify workflow resolve``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
import yaml

from ..._console import console, err_console
from . import WorkflowResolver
from .schema import _RESERVED_OVERLAY_WORKFLOW_IDS, _SAFE_ID_PATTERN, validate_overlay_yaml


def _validate_overlay_id_or_exit(id_value: str, label: str) -> None:
    """Validate a single-segment overlay/workflow id from CLI arguments."""
    if not isinstance(id_value, str) or not id_value:
        err_console.print(f"[red]Error:[/red] {label} is required and must be a non-empty string.")
        raise typer.Exit(1)
    if not _SAFE_ID_PATTERN.match(id_value):
        err_console.print(
            f"[red]Error:[/red] Invalid {label} {id_value!r}: "
            "only lowercase letters, digits, and hyphens are allowed."
        )
        raise typer.Exit(1)


def _validate_workflow_id_or_exit(workflow_id: str) -> None:
    """Validate a workflow id, treating the overlay root as reserved."""
    _validate_overlay_id_or_exit(workflow_id, "workflow ID")
    if workflow_id in _RESERVED_OVERLAY_WORKFLOW_IDS:
        err_console.print(
            f"[red]Error:[/red] Invalid workflow ID {workflow_id!r}: "
            "reserved name."
        )
        raise typer.Exit(1)


def _overlay_root(project_root: Path) -> Path:
    """Return the project-local overlay root directory."""
    return project_root / ".specify" / "workflows" / "overlays"


def _project_overlay_dir(project_root: Path, workflow_id: str) -> Path:
    """Return the project-local overlay directory for a workflow id.

    Raises typer.Exit if the resolved path escapes the overlay root.
    """
    _validate_workflow_id_or_exit(workflow_id)
    root = _overlay_root(project_root)
    target = root / workflow_id
    return _ensure_contained_dir(target, root)


def _ensure_contained_dir(path: Path, root: Path) -> Path:
    """Ensure *path* resolves inside *root* and is not a symlink.

    Returns *path* if safe. Raises typer.Exit on traversal or symlink.
    """
    if path.is_symlink():
        err_console.print(
            f"[red]Error:[/red] Refusing to use symlinked path {path}."
        )
        raise typer.Exit(1)
    try:
        resolved = path.resolve()
        root_resolved = root.resolve()
        resolved.relative_to(root_resolved)
    except ValueError:
        err_console.print(
            f"[red]Error:[/red] Path traversal detected: {path} is outside the allowed directory."
        )
        raise typer.Exit(1)
    return path


def _find_overlay_file(project_root: Path, workflow_id: str, overlay_id: str) -> Path | None:
    """Locate a project-local overlay file by workflow id and overlay id."""
    _validate_workflow_id_or_exit(workflow_id)
    _validate_overlay_id_or_exit(overlay_id, "overlay ID")
    overlay_dir = _project_overlay_dir(project_root, workflow_id)
    for suffix in (".yml", ".yaml"):
        candidate = overlay_dir / f"{overlay_id}{suffix}"
        candidate = _ensure_contained_path(candidate, _overlay_root(project_root))
        if candidate.is_file():
            if candidate.is_symlink():
                err_console.print(
                    f"[red]Error:[/red] Refusing to read symlinked overlay file {candidate}."
                )
                raise typer.Exit(1)
            return candidate
    return None


def _ensure_contained_path(path: Path, root: Path) -> Path:
    """Return *path* only if it resolves inside *root*; otherwise raise typer.Exit."""
    try:
        resolved = path.resolve()
        root_resolved = root.resolve()
        resolved.relative_to(root_resolved)
    except ValueError:
        err_console.print(
            f"[red]Error:[/red] Path traversal detected: {path} is outside the allowed directory."
        )
        raise typer.Exit(1)
    return path


def _validate_priority(priority: int) -> None:
    """Validate a user-supplied priority value."""
    if isinstance(priority, bool) or not isinstance(priority, int):
        err_console.print("[red]Error:[/red] Priority must be an integer.")
        raise typer.Exit(1)
    if priority < 1:
        err_console.print("[red]Error:[/red] Priority must be >= 1.")
        raise typer.Exit(1)


def _read_overlay(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Read and parse an overlay YAML file, returning (data, errors)."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [f"Failed to read {path}: {exc}"]
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        return None, [f"Invalid YAML in {path}: {exc}"]
    if not isinstance(data, dict):
        return None, [f"Overlay {path} must be a YAML mapping."]
    return data, []


def workflow_overlay_add(
    project_root: Path,
    source: Path,
    priority: int | None = None,
) -> Path | None:
    """Add a project-local overlay from a YAML file.

    Returns the path of the installed overlay file, or None on failure.
    """
    data, errors = _read_overlay(source)
    if data is None:
        for err in errors:
            err_console.print(f"[red]Error:[/red] {err}")
        return None

    # Apply --priority override before validation so a valid CLI priority
    # can fix a missing or invalid priority in the file.
    if priority is not None:
        _validate_priority(priority)
        data["priority"] = priority

    overlay, validation_errors = validate_overlay_yaml(data)
    if overlay is None:
        err_console.print("[red]Error:[/red] Overlay validation failed:")
        for err in validation_errors:
            err_console.print(f"  \u2022 {err}")
        return None

    target_dir = _project_overlay_dir(project_root, overlay.extends)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = _ensure_contained_path(
        target_dir / f"{overlay.id}.yml", _overlay_root(project_root)
    )

    try:
        target_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    except OSError as exc:
        err_console.print(f"[red]Error:[/red] Failed to write overlay: {exc}")
        return None

    console.print(
        f"[green]\u2713[/green] Overlay '{overlay.id}' added for workflow '{overlay.extends}'"
    )
    return target_path


def _update_overlay_field(
    project_root: Path,
    workflow_id: str,
    overlay_id: str,
    field: str,
    value: Any,
) -> bool:
    """Update a single field in a project-local overlay file."""
    path = _find_overlay_file(project_root, workflow_id, overlay_id)
    if path is None:
        err_console.print(
            f"[red]Error:[/red] Overlay '{overlay_id}' not found for workflow '{workflow_id}'"
        )
        return False

    data, errors = _read_overlay(path)
    if data is None:
        for err in errors:
            err_console.print(f"[red]Error:[/red] {err}")
        return False

    data[field] = value
    overlay, validation_errors = validate_overlay_yaml(data)
    if overlay is None:
        err_console.print("[red]Error:[/red] Overlay validation failed:")
        for err in validation_errors:
            err_console.print(f"  \u2022 {err}")
        return False

    try:
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    except OSError as exc:
        err_console.print(f"[red]Error:[/red] Failed to write overlay: {exc}")
        return False

    return True


def workflow_overlay_set_priority(
    project_root: Path,
    workflow_id: str,
    overlay_id: str,
    priority: int,
) -> bool:
    """Set the priority of a project-local overlay."""
    _validate_priority(priority)
    if _update_overlay_field(project_root, workflow_id, overlay_id, "priority", priority):
        console.print(
            f"[green]\u2713[/green] Priority of overlay '{overlay_id}' set to {priority}"
        )
        return True
    return False


def workflow_overlay_enable(
    project_root: Path,
    workflow_id: str,
    overlay_id: str,
) -> bool:
    """Enable a project-local overlay."""
    if _update_overlay_field(project_root, workflow_id, overlay_id, "enabled", True):
        console.print(f"[green]\u2713[/green] Overlay '{overlay_id}' enabled")
        return True
    return False


def workflow_overlay_disable(
    project_root: Path,
    workflow_id: str,
    overlay_id: str,
) -> bool:
    """Disable a project-local overlay."""
    if _update_overlay_field(project_root, workflow_id, overlay_id, "enabled", False):
        console.print(f"[green]\u2713[/green] Overlay '{overlay_id}' disabled")
        return True
    return False


def workflow_overlay_remove(
    project_root: Path,
    workflow_id: str,
    overlay_id: str,
) -> bool:
    """Remove a project-local overlay file."""
    path = _find_overlay_file(project_root, workflow_id, overlay_id)
    if path is None:
        err_console.print(
            f"[red]Error:[/red] Overlay '{overlay_id}' not found for workflow '{workflow_id}'"
        )
        return False

    try:
        path.unlink()
    except OSError as exc:
        err_console.print(f"[red]Error:[/red] Failed to remove overlay: {exc}")
        return False

    console.print(f"[green]\u2713[/green] Overlay '{overlay_id}' removed")
    return True


def workflow_overlay_list(project_root: Path, workflow_id: str) -> list[dict[str, Any]] | None:
    """List all overlays for a workflow and print a summary table.

    Returns the raw list data for machine-readable callers, or None on error.
    """
    _validate_workflow_id_or_exit(workflow_id)
    resolver = WorkflowResolver(project_root)
    try:
        layers = resolver.collect_all_layers(workflow_id)
    except ValueError as exc:
        err_console.print(f"[red]Error:[/red] {exc}")
        return None
    overlays = [layer for layer in layers if layer.tier != "base"]

    if not overlays:
        console.print(f"[yellow]No overlays found for workflow '{workflow_id}'.[/yellow]")
        return []

    console.print(f"Overlays for workflow '{workflow_id}':")
    rows: list[dict[str, Any]] = []
    for layer in overlays:
        overlay = layer.content
        rows.append({
            "id": overlay.id,
            "source": layer.source,
            "tier": layer.tier,
            "priority": overlay.priority,
            "enabled": overlay.enabled,
            "path": str(layer.path) if layer.path else None,
        })
        enabled_marker = "enabled" if overlay.enabled else "disabled"
        console.print(
            f"  \u2022 {overlay.id} (priority={overlay.priority}, "
            f"source={layer.source}, {enabled_marker})"
        )
    return rows


def workflow_resolve(project_root: Path, workflow_id: str) -> dict[str, Any] | None:
    """Print layer attribution for a resolved workflow.

    Returns a serializable attribution payload.
    """
    _validate_workflow_id_or_exit(workflow_id)
    resolver = WorkflowResolver(project_root)
    try:
        definition, layers, attribution = resolver.resolve_with_layers(workflow_id)
    except FileNotFoundError:
        err_console.print(
            f"[red]Error:[/red] Workflow '{workflow_id}' not found"
        )
        return None
    except ValueError as exc:
        err_console.print(f"[red]Error:[/red] {exc}")
        return None

    console.print(f"Resolved workflow '{workflow_id}':")
    console.print("Layers (highest precedence first):")
    for layer in layers:
        console.print(
            f"  \u2022 [{layer.tier}] {layer.source} (priority={layer.priority})"
        )

    console.print("Step attribution:")
    for composed in attribution:
        console.print(f"  \u2022 {composed.step_id}: {composed.source}")

    return {
        "workflow_id": workflow_id,
        "layers": [
            {
                "source": layer.source,
                "tier": layer.tier,
                "priority": layer.priority,
            }
            for layer in layers
        ],
        "attribution": [
            {"step_id": composed.step_id, "source": composed.source}
            for composed in attribution
        ],
    }
