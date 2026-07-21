"""CLI handlers for ``specify workflow overlay *`` and ``specify workflow resolve``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
import yaml

from ..._console import console, err_console
from ...extensions import normalize_priority
from .._commands import (
    _commit_workflow_file,
    _discard_committed_backup_file,
    _reject_unsafe_dir,
    _reject_unsafe_workflow_storage,
    _safe_discard_staged_workflow_file,
    _stage_workflow_file,
)
from . import WorkflowResolver
from .schema import _RESERVED_WORKFLOW_IDS, _SAFE_ID_PATTERN, validate_overlay_yaml


def _validate_overlay_id_or_exit(id_value: str, label: str) -> None:
    """Validate a single-segment overlay/workflow id from CLI arguments."""
    if not isinstance(id_value, str) or not id_value:
        err_console.print(f"[red]Error:[/red] {label} is required and must be a non-empty string.")
        raise typer.Exit(1)
    if not _SAFE_ID_PATTERN.fullmatch(id_value):
        err_console.print(
            f"[red]Error:[/red] Invalid {label} {id_value!r}: "
            "only lowercase letters, digits, and hyphens are allowed."
        )
        raise typer.Exit(1)


def _validate_workflow_id_or_exit(workflow_id: str) -> None:
    """Validate a workflow id, treating the overlay root as reserved."""
    _validate_overlay_id_or_exit(workflow_id, "workflow ID")
    if workflow_id in _RESERVED_WORKFLOW_IDS:
        err_console.print(
            f"[red]Error:[/red] Invalid workflow ID {workflow_id!r}: "
            "reserved name."
        )
        raise typer.Exit(1)


def _overlay_root(project_root: Path) -> Path:
    """Return the project-local overlay root after rejecting unsafe ancestors."""
    _reject_unsafe_workflow_storage(project_root)
    root = project_root / ".specify" / "workflows" / "overlays"
    _reject_unsafe_dir(root, ".specify/workflows/overlays")
    return root


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
    _reject_unsafe_dir(root, ".specify/workflows/overlays")
    if path.is_symlink():
        err_console.print(
            f"[red]Error:[/red] Refusing to use symlinked path {path}."
        )
        raise typer.Exit(1)
    if path.exists() and not path.is_dir():
        err_console.print(
            f"[red]Error:[/red] Overlay directory path is not a directory: {path}."
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
    """Locate a project-local overlay file by its manifest ID, not filename.

    Scans all YAML files in the overlay directory and matches on the ``id``
    field inside each manifest. This aligns with ``ProjectOverlaySource.collect()``
    which also derives identity from the manifest, not the filename.
    """
    _validate_workflow_id_or_exit(workflow_id)
    _validate_overlay_id_or_exit(overlay_id, "overlay ID")
    overlay_dir = _project_overlay_dir(project_root, workflow_id)
    if not overlay_dir.is_dir():
        return None
    try:
        entries = sorted(overlay_dir.iterdir())
    except OSError:
        return None
    matches: list[Path] = []
    for path in entries:
        if not path.is_file() or path.suffix not in (".yml", ".yaml"):
            continue
        if path.is_symlink():
            continue
        data, _ = _read_overlay(path)
        if data is None:
            continue
        if data.get("id") == overlay_id:
            matches.append(path)
    if len(matches) > 1:
        paths = ", ".join(str(path) for path in matches)
        err_console.print(
            f"[red]Error:[/red] Duplicate overlay ID '{overlay_id}' in {paths}. "
            "Resolve the duplicate manifest IDs before continuing."
        )
        raise typer.Exit(1)
    return matches[0] if matches else None


def _ensure_contained_path(path: Path, root: Path) -> Path:
    """Return *path* only if it resolves inside *root*; otherwise raise typer.Exit."""
    _reject_unsafe_dir(root, ".specify/workflows/overlays")
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


def _read_overlay(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Read and parse an overlay YAML file, returning (data, errors)."""
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
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
    _reject_unsafe_workflow_storage(project_root)
    data, errors = _read_overlay(source)
    if data is None:
        for err in errors:
            err_console.print(f"[red]Error:[/red] {err}")
        return None

    # Apply --priority override before validation so a valid CLI priority
    # can fix a missing or invalid priority in the file.
    if priority is not None:
        if isinstance(priority, bool) or not isinstance(priority, int) or priority < 1:
            err_console.print("[red]Error:[/red] Priority must be >= 1.")
            return None
        data["priority"] = normalize_priority(priority)

    overlay, validation_errors = validate_overlay_yaml(data)
    if overlay is None:
        err_console.print("[red]Error:[/red] Overlay validation failed:")
        for err in validation_errors:
            err_console.print(f"  \u2022 {err}")
        return None
    data["priority"] = overlay.priority

    target_dir = _project_overlay_dir(project_root, overlay.extends)
    # Reuse an existing .yaml file so we don't create a duplicate .yml layer.
    existing = _find_overlay_file(project_root, overlay.extends, overlay.id)
    if existing is not None:
        target_path = existing
    else:
        target_path = _ensure_contained_path(
            target_dir / f"{overlay.id}.yml", _overlay_root(project_root)
        )

    backup: Path | None = None
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        existed_before = target_path.exists()
        staged = _stage_workflow_file(target_path.parent)
        try:
            staged.write_bytes(yaml.safe_dump(data, sort_keys=False).encode("utf-8"))
            backup = _commit_workflow_file(staged, target_path, existed_before)
        except BaseException:
            _safe_discard_staged_workflow_file(
                staged, target_path.parent, existed_before
            )
            raise
    except OSError as exc:
        err_console.print(f"[red]Error:[/red] Failed to write overlay: {exc}")
        return None
    _discard_committed_backup_file(backup)

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
    _reject_unsafe_workflow_storage(project_root)
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

    backup: Path | None = None
    try:
        existed_before = path.exists()
        staged = _stage_workflow_file(path.parent)
        try:
            staged.write_bytes(yaml.safe_dump(data, sort_keys=False).encode("utf-8"))
            backup = _commit_workflow_file(staged, path, existed_before)
        except BaseException:
            _safe_discard_staged_workflow_file(staged, path.parent, existed_before)
            raise
    except OSError as exc:
        err_console.print(f"[red]Error:[/red] Failed to write overlay: {exc}")
        return False
    _discard_committed_backup_file(backup)

    return True


def workflow_overlay_set_priority(
    project_root: Path,
    workflow_id: str,
    overlay_id: str,
    priority: int,
) -> bool:
    """Set the priority of a project-local overlay."""
    if isinstance(priority, bool) or not isinstance(priority, int) or priority < 1:
        err_console.print("[red]Error:[/red] Priority must be >= 1.")
        raise typer.Exit(1)
    normalized_priority = normalize_priority(priority)
    if _update_overlay_field(
        project_root, workflow_id, overlay_id, "priority", normalized_priority
    ):
        console.print(
            f"[green]\u2713[/green] Priority of overlay '{overlay_id}' set to {normalized_priority}"
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
    _reject_unsafe_workflow_storage(project_root)
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
    _reject_unsafe_workflow_storage(project_root)
    _validate_workflow_id_or_exit(workflow_id)
    resolver = WorkflowResolver(project_root)
    try:
        layers = resolver.collect_all_layers(workflow_id, include_disabled=True)
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
            "priority": normalize_priority(overlay.priority),
            "enabled": overlay.enabled,
            "path": str(layer.path) if layer.path else None,
        })
        enabled_marker = "enabled" if overlay.enabled else "disabled"
        console.print(
            f"  \u2022 {overlay.id} (priority={normalize_priority(overlay.priority)}, "
            f"source={layer.source}, {enabled_marker})"
        )
    return rows


def workflow_resolve(project_root: Path, workflow_id: str) -> dict[str, Any] | None:
    """Print layer attribution for a resolved workflow.

    Returns a serializable attribution payload.
    """
    _reject_unsafe_workflow_storage(project_root)
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
        priority = (
            "n/a" if layer.tier == "base" else str(normalize_priority(layer.priority))
        )
        console.print(
            f"  \u2022 [{layer.tier}] {layer.source} "
            f"(priority={priority})"
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
                "priority": (
                    None
                    if layer.tier == "base"
                    else normalize_priority(layer.priority)
                ),
            }
            for layer in layers
        ],
        "attribution": [
            {"step_id": composed.step_id, "source": composed.source}
            for composed in attribution
        ],
    }
