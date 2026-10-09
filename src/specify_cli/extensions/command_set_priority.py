"""Implementation of ``specify extension set-priority``.

Registered by ``_commands.register()``; shared command infrastructure lives in
``_commands.py``.
"""

from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import _commands


@_commands.extension_app.command("set-priority")
def extension_set_priority(
    extension: str = typer.Argument(help="Extension ID or name"),
    priority: int = typer.Argument(help="New priority (lower = higher precedence)"),
):
    """Set the resolution priority of an installed extension."""
    from . import ExtensionManager, normalize_priority

    project_root = _commands._require_specify_project()
    # Validate priority
    if priority < 1:
        console.print(
            "[red]Error:[/red] Priority must be a positive integer (1 or higher)"
        )
        raise typer.Exit(1)

    manager = ExtensionManager(project_root)

    # Resolve extension ID from argument (handles ambiguous names)
    installed = manager.list_installed()
    extension_id, display_name = _commands._resolve_installed_extension(
        extension, installed, "set-priority"
    )

    # Get current metadata
    metadata = manager.registry.get(extension_id)
    if metadata is None or not isinstance(metadata, dict):
        console.print(
            f"[red]Error:[/red] Extension '{_escape_markup(str(extension_id))}' "
            "not found in registry (corrupted state)"
        )
        raise typer.Exit(1)

    raw_priority = metadata.get("priority")
    # Only skip if the stored value is already a valid int equal to requested priority
    # This ensures corrupted values (e.g. "high") get repaired even when setting to default (10)
    # A bool is an int in Python (isinstance(True, int) is True), so exclude it explicitly —
    # mirroring normalize_priority's bool guard — otherwise a corrupted True/False priority
    # equals 1/0 here and is never repaired.
    if (
        isinstance(raw_priority, int)
        and not isinstance(raw_priority, bool)
        and raw_priority == priority
    ):
        console.print(
            f"[yellow]Extension '{_escape_markup(str(display_name))}' already has priority {priority}[/yellow]"
        )
        raise typer.Exit(0)

    old_priority = normalize_priority(raw_priority)

    # Extension reordering can change the lower-layer candidates matched by
    # enabled preset regex selectors, so the new priority is only committed
    # together with the recomposed artifacts. Mirrors the preset priority
    # transaction: snapshot the artifact trees and both registries, run the
    # reconciliation strictly, and roll back to the previous priority on any
    # failure instead of reporting a change that never reached the
    # selector-backed outputs.
    import copy

    from ..presets import PresetManager
    from ..presets._transaction import _ArtifactSnapshot, _capture_preset_artifacts

    preset_manager = PresetManager(project_root)
    registry_before = copy.deepcopy(manager.registry.data)
    snapshot = _ArtifactSnapshot()
    captured = False
    try:
        _capture_preset_artifacts(preset_manager, snapshot)
        captured = True
        manager.registry.update(extension_id, {"priority": priority})
        _commands._refresh_presets_and_warn(project_root, strict=True)
    except BaseException as exc:
        manager.registry.data = registry_before
        try:
            if captured:
                snapshot.restore()
        except Exception as rollback_exc:
            exc.add_note(f"Extension priority rollback failed: {rollback_exc}")
        console.print(
            f"[red]Error:[/red] Could not apply the new priority for "
            f"'{_escape_markup(str(display_name))}': "
            f"{_escape_markup(str(exc))}"
        )
        raise
    finally:
        import sys

        operation_exc = sys.exception()
        try:
            snapshot.close()
        except Exception as cleanup_exc:
            if operation_exc is not None:
                operation_exc.add_note(
                    f"Extension priority snapshot cleanup failed: {cleanup_exc}"
                )
            else:
                raise

    console.print(
        f"[green]✓[/green] Extension '{_escape_markup(str(display_name))}' priority changed: {old_priority} → {priority}"
    )
    console.print(
        "\n[dim]Lower priority = higher precedence in template resolution[/dim]"
    )
