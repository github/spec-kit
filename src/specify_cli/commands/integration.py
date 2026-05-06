"""specify integration * commands."""
import json
import os
import sys
from pathlib import Path
from typing import Any

import typer
from rich.table import Table

from .._console import console
from .._fs import save_init_options, load_init_options
from .._helpers import (
    _install_shared_infra, ensure_executable_scripts,
    get_speckit_version, _parse_integration_options,
    SCRIPT_TYPE_CHOICES,
)

integration_app = typer.Typer(
    name="integration",
    help="Manage coding agent integrations",
    add_completion=False,
)

integration_catalog_app = typer.Typer(
    name="catalog",
    help="Manage integration catalogs",
    add_completion=False,
)
integration_app.add_typer(integration_catalog_app, name="catalog")

INTEGRATION_JSON = ".specify/integration.json"
INTEGRATION_STATE_SCHEMA = 1


def _call_refresh_shared_templates(
    project_root: Path,
    invoke_separator: str,
    force: bool = False,
) -> None:
    """Call _refresh_shared_templates via sys.modules so monkeypatching works."""
    _specify_cli = sys.modules.get("specify_cli")
    if _specify_cli and hasattr(_specify_cli, "_refresh_shared_templates"):
        _specify_cli._refresh_shared_templates(project_root, invoke_separator, force=force)
    else:
        from .. import _refresh_shared_templates
        _refresh_shared_templates(project_root, invoke_separator, force=force)


def _read_integration_json(project_root: Path) -> dict[str, Any]:
    """Load ``.specify/integration.json``.  Returns ``{}`` when missing."""
    path = project_root / INTEGRATION_JSON
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[red]Error:[/red] {path} contains invalid JSON.")
        console.print(f"Please fix or delete {INTEGRATION_JSON} and retry.")
        console.print(f"[dim]Details:[/dim] {exc}")
        raise typer.Exit(1)
    except OSError as exc:
        console.print(f"[red]Error:[/red] Could not read {path}.")
        console.print(f"Please fix file permissions or delete {INTEGRATION_JSON} and retry.")
        console.print(f"[dim]Details:[/dim] {exc}")
        raise typer.Exit(1)
    if not isinstance(data, dict):
        console.print(f"[red]Error:[/red] {path} must contain a JSON object, got {type(data).__name__}.")
        console.print(f"Please fix or delete {INTEGRATION_JSON} and retry.")
        raise typer.Exit(1)
    return data


def _read_integration_state(project_root: Path) -> dict[str, Any]:
    """Read integration.json and migrate to v1 schema if needed.

    Validates schema version and exits with error if unsupported.
    Returns empty dict when no integration is installed.
    """
    from ..integrations import INTEGRATION_REGISTRY

    data = _read_integration_json(project_root)
    if not data:
        return {}

    schema = data.get("integration_state_schema")

    # Schema version guard
    if isinstance(schema, int) and schema > INTEGRATION_STATE_SCHEMA:
        console.print(
            f"[red]Error:[/red] integration.json uses schema {schema}, "
            f"but this CLI only supports schema {INTEGRATION_STATE_SCHEMA}."
        )
        raise typer.Exit(1)

    # Legacy migration from v0 (no schema version field)
    if schema is None:
        integration_key = data.get("integration") or ""
        settings: dict[str, Any] = {}
        installed: list[str] = []
        if integration_key:
            installed = [integration_key]
            integration = INTEGRATION_REGISTRY.get(integration_key)
            if integration:
                settings[integration_key] = {
                    "invoke_separator": integration.effective_invoke_separator(None),
                }
        return {
            "integration_state_schema": INTEGRATION_STATE_SCHEMA,
            "integration": integration_key,
            "default_integration": integration_key,
            "installed_integrations": installed,
            "integration_settings": settings,
            "version": data.get("version", ""),
        }

    return data


def _build_integration_state(
    default_key: str,
    installed: list[str],
    settings: dict[str, Any],
) -> dict[str, Any]:
    return {
        "integration_state_schema": INTEGRATION_STATE_SCHEMA,
        "integration": default_key,
        "default_integration": default_key,
        "installed_integrations": installed,
        "integration_settings": settings,
        "version": get_speckit_version(),
    }


def _write_integration_state(project_root: Path, state: dict[str, Any]) -> None:
    dest = project_root / INTEGRATION_JSON
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _remove_integration_json(project_root: Path) -> None:
    """Remove ``.specify/integration.json`` if it exists."""
    path = project_root / INTEGRATION_JSON
    if path.exists():
        path.unlink()


def _normalize_script_type(script_type: str, source: str) -> str:
    """Normalize and validate a script type from CLI/config sources."""
    normalized = script_type.strip().lower()
    if normalized in SCRIPT_TYPE_CHOICES:
        return normalized
    console.print(
        f"[red]Error:[/red] Invalid script type {script_type!r} from {source}. "
        f"Expected one of: {', '.join(sorted(SCRIPT_TYPE_CHOICES.keys()))}."
    )
    raise typer.Exit(1)


def _resolve_script_type(project_root: Path, script_type: str | None) -> str:
    """Resolve the script type from the CLI flag or init-options.json."""
    if script_type:
        return _normalize_script_type(script_type, "--script")
    opts = load_init_options(project_root)
    saved = opts.get("script")
    if isinstance(saved, str) and saved.strip():
        return _normalize_script_type(saved, ".specify/init-options.json")
    return "ps" if os.name == "nt" else "sh"


def _update_init_options_for_integration(
    project_root: Path,
    integration: Any,
    script_type: str | None = None,
) -> None:
    """Update ``init-options.json`` to reflect *integration* as the active one."""
    from ..integrations.base import SkillsIntegration
    opts = load_init_options(project_root)
    opts["integration"] = integration.key
    opts["ai"] = integration.key
    opts["context_file"] = integration.context_file
    if script_type:
        opts["script"] = script_type
    if isinstance(integration, SkillsIntegration) or getattr(integration, "_skills_mode", False):
        opts["ai_skills"] = True
    else:
        opts.pop("ai_skills", None)
    save_init_options(project_root, opts)


def _ensure_speckit_project(project_root: Path) -> None:
    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)


@integration_app.command("list")
def integration_list(
    catalog: bool = typer.Option(False, "--catalog", help="Browse full catalog (built-in + community)"),
):
    """List available integrations and installed status."""
    from ..integrations import INTEGRATION_REGISTRY

    project_root = Path.cwd()
    _ensure_speckit_project(project_root)

    state = _read_integration_state(project_root)
    installed_keys: list[str] = state.get("installed_integrations", [])
    default_key: str = state.get("default_integration") or state.get("integration") or ""

    if catalog:
        from ..integrations.catalog import IntegrationCatalog, IntegrationCatalogError

        ic = IntegrationCatalog(project_root)
        try:
            entries = ic.search()
        except IntegrationCatalogError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1)

        if not entries:
            console.print("[yellow]No integrations found in catalog.[/yellow]")
            return

        table = Table(title="Integration Catalog")
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Version")
        table.add_column("Source")
        table.add_column("Status")

        for entry in sorted(entries, key=lambda e: e["id"]):
            eid = entry["id"]
            cat_name = entry.get("_catalog_name", "")
            install_allowed = entry.get("_install_allowed", True)
            if eid == default_key:
                status = "[green]installed[/green]"
            elif eid in INTEGRATION_REGISTRY:
                status = "built-in"
            elif install_allowed is False:
                status = "discovery-only"
            else:
                status = ""
            table.add_row(
                eid,
                entry.get("name", eid),
                entry.get("version", ""),
                cat_name,
                status,
            )

        console.print(table)
        return

    table = Table(title="Coding Agent Integrations")
    table.add_column("Key")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("CLI Required")
    table.add_column("Multi-install Safe")

    for key in sorted(INTEGRATION_REGISTRY.keys()):
        integration = INTEGRATION_REGISTRY[key]
        cfg = integration.config or {}
        name = cfg.get("name", key)
        requires_cli = cfg.get("requires_cli", False)

        if key == default_key and key in installed_keys:
            status = "[green]installed (default)[/green]"
        elif key in installed_keys:
            status = "[green]installed[/green]"
        else:
            status = ""

        cli_req = "yes" if requires_cli else "no (IDE)"
        multi_safe = "yes" if integration.multi_install_safe else "no"
        table.add_row(key, name, status, cli_req, multi_safe)

    console.print(table)

    if default_key:
        console.print(f"\n[dim]Current integration:[/dim] [cyan]{default_key}[/cyan]")
        if len(installed_keys) > 1:
            others = [k for k in installed_keys if k != default_key]
            console.print(f"[dim]Also installed:[/dim] {', '.join(others)}")
    else:
        console.print("\n[yellow]No integration currently installed.[/yellow]")
        console.print("Install one with: [cyan]specify integration install <key>[/cyan]")


@integration_app.command("install")
def integration_install(
    key: str = typer.Argument(help="Integration key to install (e.g. claude, copilot)"),
    script: str | None = typer.Option(None, "--script", help="Script type: sh or ps (default: from init-options.json or platform default)"),
    force: bool = typer.Option(False, "--force", help="Force install even alongside non-multi-safe integrations"),
    integration_options: str | None = typer.Option(None, "--integration-options", help='Options for the integration'),
):
    """Install an integration into an existing project."""
    from ..integrations import INTEGRATION_REGISTRY, get_integration
    from ..integrations.manifest import IntegrationManifest

    project_root = Path.cwd()
    _ensure_speckit_project(project_root)

    integration = get_integration(key)
    if integration is None:
        console.print(f"[red]Error:[/red] Unknown integration '{key}'")
        available = ", ".join(sorted(INTEGRATION_REGISTRY.keys()))
        console.print(f"Available integrations: {available}")
        raise typer.Exit(1)

    state = _read_integration_state(project_root)
    installed_keys: list[str] = list(state.get("installed_integrations", []))
    default_key: str = state.get("default_integration") or state.get("integration") or ""
    settings: dict[str, Any] = dict(state.get("integration_settings", {}))

    # Already installed (same key)
    if key in installed_keys:
        console.print(f"[yellow]Integration '{key}' is already installed.[/yellow]")
        console.print(f"Run [cyan]specify integration upgrade {key}[/cyan] to upgrade, or")
        console.print(f"    [cyan]specify integration uninstall {key}[/cyan] to remove it.")
        raise typer.Exit(0)

    # Another integration is installed — check multi-install compatibility
    if installed_keys:
        all_existing_safe = all(
            INTEGRATION_REGISTRY[k].multi_install_safe
            for k in installed_keys
            if k in INTEGRATION_REGISTRY
        )
        new_is_safe = integration.multi_install_safe

        if not (all_existing_safe and new_is_safe):
            if not force:
                installed_str = ", ".join(installed_keys)
                console.print("[red]Error:[/red] Integration cannot be installed alongside existing ones.")
                console.print(f"Installed integrations: {installed_str}")
                console.print(f"Default integration: {default_key}")
                console.print(
                    "Only multi-install safe integrations can be installed alongside others."
                )
                console.print("Use [cyan]--force[/cyan] to override.")
                raise typer.Exit(1)

    selected_script = _resolve_script_type(project_root, script)

    # Build parsed options
    parsed_options: dict[str, Any] | None = None
    if integration_options:
        parsed_options = _parse_integration_options(integration, integration_options)

    invoke_sep = integration.effective_invoke_separator(parsed_options)
    _install_shared_infra(project_root, selected_script, invoke_separator=invoke_sep)
    if os.name != "nt":
        ensure_executable_scripts(project_root)

    manifest = IntegrationManifest(
        integration.key, project_root, version=get_speckit_version()
    )

    try:
        integration.setup(
            project_root, manifest,
            parsed_options=parsed_options,
            script_type=selected_script,
            raw_options=integration_options,
        )
        manifest.save()

        # Build new state
        new_installed = installed_keys + [key]
        # Populate settings for all installed integrations
        for k in new_installed:
            if k not in settings:
                reg = INTEGRATION_REGISTRY.get(k)
                if reg:
                    settings[k] = {"invoke_separator": reg.effective_invoke_separator(None)}

        new_default = default_key if default_key in new_installed else (new_installed[0] if new_installed else "")
        new_state = _build_integration_state(new_default, new_installed, settings)
        _write_integration_state(project_root, new_state)

        # Update init-options only if this is the default (first) integration
        if not default_key:
            _update_init_options_for_integration(project_root, integration, script_type=selected_script)

    except Exception as exc:
        try:
            integration.teardown(project_root, manifest, force=True)
        except Exception as rollback_err:
            console.print(f"[yellow]Warning:[/yellow] Failed to roll back integration changes: {rollback_err}")
        console.print(f"[red]Error:[/red] Failed to install integration: {exc}")
        raise typer.Exit(1)

    name = (integration.config or {}).get("name", key)
    console.print(f"\n[green]✓[/green] Integration '{name}' installed successfully")


# Keep 'add' as hidden alias for backward compatibility
@integration_app.command("add", hidden=True)
def integration_add(
    key: str = typer.Argument(help="Integration key to add (e.g. claude, copilot)"),
    script: str | None = typer.Option(None, "--script"),
    force: bool = typer.Option(False, "--force"),
    integration_options: str | None = typer.Option(None, "--integration-options"),
):
    """Alias for 'install'."""
    return integration_install(key=key, script=script, force=force, integration_options=integration_options)


@integration_app.command("uninstall")
def integration_uninstall(
    key: str = typer.Argument(None, help="Integration key to uninstall (default: current default integration)"),
    force: bool = typer.Option(False, "--force", help="Remove files even if modified"),
):
    """Uninstall an integration, safely preserving modified files."""
    from ..integrations import get_integration
    from ..integrations.manifest import IntegrationManifest

    project_root = Path.cwd()
    _ensure_speckit_project(project_root)

    state = _read_integration_state(project_root)
    installed_keys: list[str] = list(state.get("installed_integrations", []))
    default_key: str = state.get("default_integration") or state.get("integration") or ""
    settings: dict[str, Any] = dict(state.get("integration_settings", {}))

    if key is None:
        if not default_key:
            console.print("[yellow]No integration is currently installed.[/yellow]")
            raise typer.Exit(0)
        key = default_key

    if key not in installed_keys:
        console.print(f"[red]Error:[/red] Integration '{key}' is not installed.")
        raise typer.Exit(1)

    integration = get_integration(key)

    manifest_path = project_root / ".specify" / "integrations" / f"{key}.manifest.json"
    if not manifest_path.exists():
        console.print(f"[yellow]No manifest found for integration '{key}'. Nothing to uninstall.[/yellow]")
        # Clean up state anyway
        new_installed = [k for k in installed_keys if k != key]
        settings.pop(key, None)
        if not new_installed:
            _remove_integration_json(project_root)
            opts = load_init_options(project_root)
            if opts.get("integration") == key or opts.get("ai") == key:
                opts.pop("integration", None)
                opts.pop("ai", None)
                opts.pop("ai_skills", None)
                opts.pop("context_file", None)
                save_init_options(project_root, opts)
        else:
            new_default = default_key if default_key in new_installed else new_installed[0]
            new_state = _build_integration_state(new_default, new_installed, settings)
            _write_integration_state(project_root, new_state)
        raise typer.Exit(0)

    try:
        manifest = IntegrationManifest.load(key, project_root)
    except (ValueError, FileNotFoundError) as exc:
        console.print(f"[red]Error:[/red] Integration manifest for '{key}' is unreadable.")
        console.print(f"Manifest: {manifest_path}")
        console.print(
            f"To recover, delete the unreadable manifest, run "
            f"[cyan]specify integration uninstall {key}[/cyan] to clear stale metadata, "
            f"then run [cyan]specify integration install {key}[/cyan] to regenerate."
        )
        console.print(f"[dim]Details:[/dim] {exc}")
        raise typer.Exit(1)

    removed, skipped = manifest.uninstall(project_root, force=force)

    if integration:
        integration.remove_context_section(project_root)

    # Compute new installed state
    new_installed = [k for k in installed_keys if k != key]
    settings.pop(key, None)

    name = (integration.config or {}).get("name", key) if integration else key

    if not new_installed:
        _remove_integration_json(project_root)
        opts = load_init_options(project_root)
        if opts.get("integration") == key or opts.get("ai") == key:
            opts.pop("integration", None)
            opts.pop("ai", None)
            opts.pop("ai_skills", None)
            opts.pop("context_file", None)
            save_init_options(project_root, opts)
    else:
        # Set new default if we removed the current default
        if key == default_key:
            new_default = new_installed[0]
            new_default_integration = get_integration(new_default)
            if new_default_integration:
                new_sep = new_default_integration.effective_invoke_separator(None)
                try:
                    _call_refresh_shared_templates(project_root, new_sep, force=False)
                except Exception:
                    pass  # Template refresh failure is non-fatal during uninstall
                _update_init_options_for_integration(project_root, new_default_integration)
        else:
            new_default = default_key

        new_state = _build_integration_state(new_default, new_installed, settings)
        _write_integration_state(project_root, new_state)

    console.print(f"\n[green]✓[/green] Integration '{name}' uninstalled")
    if removed:
        console.print(f"  Removed {len(removed)} file(s)")
    if skipped:
        console.print(f"\n[yellow]⚠[/yellow]  {len(skipped)} modified file(s) were preserved:")
        for path in skipped:
            rel = path.relative_to(project_root) if path.is_absolute() else path
            console.print(f"    {rel}")


@integration_app.command("use")
def integration_use(
    target: str = typer.Argument(help="Integration key to set as default"),
    force: bool = typer.Option(False, "--force", help="Force refresh of modified templates"),
):
    """Set the default integration (must already be installed)."""
    from ..integrations import INTEGRATION_REGISTRY, get_integration

    project_root = Path.cwd()
    _ensure_speckit_project(project_root)

    target_integration = get_integration(target)
    if target_integration is None:
        console.print(f"[red]Error:[/red] Unknown integration '{target}'")
        available = ", ".join(sorted(INTEGRATION_REGISTRY.keys()))
        console.print(f"Available integrations: {available}")
        raise typer.Exit(1)

    state = _read_integration_state(project_root)
    installed_keys: list[str] = list(state.get("installed_integrations", []))
    settings: dict[str, Any] = dict(state.get("integration_settings", {}))

    if target not in installed_keys:
        console.print(f"[red]Error:[/red] Integration '{target}' is not installed.")
        console.print(f"Install it first with: [cyan]specify integration install {target}[/cyan]")
        raise typer.Exit(1)

    # Refresh templates atomically (before persisting state)
    new_sep = target_integration.effective_invoke_separator(None)
    try:
        _call_refresh_shared_templates(project_root, new_sep, force=force)
    except Exception as exc:
        console.print(f"[red]Error:[/red] Failed to refresh shared templates: {exc}")
        raise typer.Exit(1)

    # Persist state
    new_state = _build_integration_state(target, installed_keys, settings)
    _write_integration_state(project_root, new_state)
    _update_init_options_for_integration(project_root, target_integration)

    name = (target_integration.config or {}).get("name", target)
    console.print(f"\n[green]✓[/green] Default integration set to '{name}'")


@integration_app.command("switch")
def integration_switch(
    target: str = typer.Argument(help="Integration key to switch to"),
    script: str | None = typer.Option(None, "--script", help="Script type: sh or ps"),
    force: bool = typer.Option(False, "--force", help="Force overwrite of modified files"),
    integration_options: str | None = typer.Option(None, "--integration-options", help="Options for the target integration"),
):
    """Switch the active integration (installs if not present, sets default if installed)."""
    from ..integrations import INTEGRATION_REGISTRY, get_integration
    from ..integrations.manifest import IntegrationManifest

    project_root = Path.cwd()
    _ensure_speckit_project(project_root)

    target_integration = get_integration(target)
    if target_integration is None:
        console.print(f"[red]Error:[/red] Unknown integration '{target}'")
        available = ", ".join(sorted(INTEGRATION_REGISTRY.keys()))
        console.print(f"Available integrations: {available}")
        raise typer.Exit(1)

    state = _read_integration_state(project_root)
    installed_keys: list[str] = list(state.get("installed_integrations", []))
    default_key: str = state.get("default_integration") or state.get("integration") or ""
    settings: dict[str, Any] = dict(state.get("integration_settings", {}))

    # Case 1: Target is the current default
    if target == default_key:
        if not force:
            console.print(f"[yellow]Integration '{target}' is already the default integration.[/yellow]")
            raise typer.Exit(0)
        # Force refresh of shared templates
        new_sep = target_integration.effective_invoke_separator(
            _parse_integration_options(target_integration, integration_options) if integration_options else None
        )
        try:
            _call_refresh_shared_templates(project_root, new_sep, force=True)
        except Exception as exc:
            console.print(f"[red]Error:[/red] Failed to refresh shared templates: {exc}")
            raise typer.Exit(1)
        console.print("[green]✓[/green] managed shared templates refreshed")
        raise typer.Exit(0)

    # Case 2: Target is already installed (but not default)
    if target in installed_keys:
        if integration_options:
            console.print(
                "[red]Error:[/red] --integration-options cannot be used when switching to an already-installed integration."
            )
            raise typer.Exit(1)
        # Act like "use" command
        new_sep = target_integration.effective_invoke_separator(None)
        try:
            _call_refresh_shared_templates(project_root, new_sep, force=force)
        except Exception as exc:
            console.print(f"[red]Error:[/red] Failed to refresh shared templates: {exc}")
            raise typer.Exit(1)
        new_state = _build_integration_state(target, installed_keys, settings)
        _write_integration_state(project_root, new_state)
        _update_init_options_for_integration(project_root, target_integration)
        name = (target_integration.config or {}).get("name", target)
        console.print(f"\n[green]✓[/green] Switched to integration '{name}'")
        return

    # Case 3: Full switch — uninstall current default, install new target
    selected_script = _resolve_script_type(project_root, script)

    # Phase 1: Uninstall current default (if any)
    if default_key and default_key in installed_keys:
        current_integration = get_integration(default_key)
        manifest_path = project_root / ".specify" / "integrations" / f"{default_key}.manifest.json"

        if manifest_path.exists():
            try:
                old_manifest = IntegrationManifest.load(default_key, project_root)
            except (ValueError, FileNotFoundError) as exc:
                console.print(f"[red]Error:[/red] Could not read integration manifest for '{default_key}': {manifest_path}")
                console.print(f"[dim]{exc}[/dim]")
                console.print(
                    f"To recover, delete the unreadable manifest at {manifest_path}, "
                    f"run [cyan]specify integration uninstall {default_key}[/cyan], then retry."
                )
                raise typer.Exit(1)
            console.print(f"Uninstalling current integration: [cyan]{default_key}[/cyan]")
            removed, skipped = old_manifest.uninstall(project_root, force=force)
            if current_integration:
                current_integration.remove_context_section(project_root)
            if removed:
                console.print(f"  Removed {len(removed)} file(s)")
            if skipped:
                console.print(f"  [yellow]⚠[/yellow]  {len(skipped)} modified file(s) preserved")
        elif current_integration is None and not manifest_path.exists():
            pass  # No manifest and unknown integration — skip uninstall
        else:
            console.print(f"[red]Error:[/red] Integration '{default_key}' is installed but has no manifest.")
            console.print(
                f"Run [cyan]specify integration uninstall {default_key}[/cyan] to clear metadata, "
                f"then retry [cyan]specify integration switch {target}[/cyan]."
            )
            raise typer.Exit(1)

    # Update state: remove old default, determine fallback
    new_installed_before_target = [k for k in installed_keys if k != default_key]
    settings.pop(default_key, None)

    # Determine fallback default (for atomicity — if phase 2 fails)
    fallback_default = new_installed_before_target[0] if new_installed_before_target else ""
    if fallback_default:
        # Write intermediate state with fallback as default
        fallback_state = _build_integration_state(fallback_default, new_installed_before_target, settings)
        _write_integration_state(project_root, fallback_state)
        fallback_integration = get_integration(fallback_default)
        if fallback_integration:
            _update_init_options_for_integration(project_root, fallback_integration)
            try:
                fallback_sep = fallback_integration.effective_invoke_separator(None)
                _call_refresh_shared_templates(project_root, fallback_sep, force=False)
            except Exception:
                pass  # Non-fatal
    else:
        _remove_integration_json(project_root)
        opts = load_init_options(project_root)
        opts.pop("integration", None)
        opts.pop("ai", None)
        opts.pop("ai_skills", None)
        opts.pop("context_file", None)
        save_init_options(project_root, opts)

    # Build parsed options for target
    parsed_options: dict[str, Any] | None = None
    if integration_options:
        parsed_options = _parse_integration_options(target_integration, integration_options)

    invoke_sep = target_integration.effective_invoke_separator(parsed_options)
    _install_shared_infra(project_root, selected_script, invoke_separator=invoke_sep)
    if os.name != "nt":
        ensure_executable_scripts(project_root)

    # Phase 2: Install target integration
    console.print(f"Installing integration: [cyan]{target}[/cyan]")
    manifest = IntegrationManifest(
        target_integration.key, project_root, version=get_speckit_version()
    )

    try:
        target_integration.setup(
            project_root, manifest,
            parsed_options=parsed_options,
            script_type=selected_script,
            raw_options=integration_options,
        )
        manifest.save()

        # Build final state
        final_installed = new_installed_before_target + [target]
        settings[target] = {"invoke_separator": target_integration.effective_invoke_separator(parsed_options)}
        final_state = _build_integration_state(target, final_installed, settings)
        _write_integration_state(project_root, final_state)
        _update_init_options_for_integration(project_root, target_integration, script_type=selected_script)

    except Exception as exc:
        try:
            target_integration.teardown(project_root, manifest, force=True)
        except Exception as rollback_err:
            console.print(f"[yellow]Warning:[/yellow] Failed to roll back integration '{target}': {rollback_err}")
        console.print(f"[red]Error:[/red] Failed to install integration '{target}': {exc}")
        raise typer.Exit(1)

    # Migrate extension commands to new integration
    try:
        _migrate_extension_commands(project_root, default_key, target, parsed_options, selected_script)
    except Exception:
        pass  # Extension migration failure is non-fatal for the switch itself

    name = (target_integration.config or {}).get("name", target)
    console.print(f"\n[green]✓[/green] Switched to integration '{name}'")


def _migrate_extension_commands(
    project_root: Path,
    old_key: str,
    new_key: str,
    parsed_options: dict[str, Any] | None,
    script_type: str,
) -> None:
    """Migrate enabled extensions to the new integration's command format."""
    registry_path = project_root / ".specify" / "extensions" / ".registry"
    if not registry_path.exists():
        return

    try:
        from ..extensions import ExtensionManager
        manager = ExtensionManager(project_root)

        # Remove old integration's commands and skills
        if old_key:
            manager.unregister_agent_artifacts(old_key)

        # Register extensions for new integration
        if new_key:
            manager.register_enabled_extensions_for_agent(new_key)
    except Exception:
        pass


@integration_app.command("upgrade")
def integration_upgrade(
    key: str | None = typer.Argument(None, help="Integration key to upgrade (default: current integration)"),
    force: bool = typer.Option(False, "--force", help="Force upgrade even if files are modified"),
    script: str | None = typer.Option(None, "--script", help="Script type: sh or ps"),
    integration_options: str | None = typer.Option(None, "--integration-options", help="Options for the integration"),
):
    """Upgrade an integration by reinstalling with diff-aware file handling."""
    from ..integrations import get_integration
    from ..integrations.manifest import IntegrationManifest

    project_root = Path.cwd()
    _ensure_speckit_project(project_root)

    state = _read_integration_state(project_root)
    installed_keys: list[str] = list(state.get("installed_integrations", []))
    default_key: str = state.get("default_integration") or state.get("integration") or ""
    settings: dict[str, Any] = dict(state.get("integration_settings", {}))

    if key is None:
        if not default_key:
            console.print("[yellow]No integration is currently installed.[/yellow]")
            raise typer.Exit(0)
        key = default_key

    if key not in installed_keys:
        console.print(f"[red]Error:[/red] Integration '{key}' is not installed.")
        raise typer.Exit(1)

    integration = get_integration(key)
    if integration is None:
        console.print(f"[red]Error:[/red] Unknown integration '{key}'")
        raise typer.Exit(1)

    manifest_path = project_root / ".specify" / "integrations" / f"{key}.manifest.json"
    if not manifest_path.exists():
        console.print(f"[yellow]No manifest found for integration '{key}'. Nothing to upgrade.[/yellow]")
        console.print(f"Run [cyan]specify integration install {key}[/cyan] to perform a fresh install.")
        raise typer.Exit(0)

    try:
        old_manifest = IntegrationManifest.load(key, project_root)
    except (ValueError, FileNotFoundError) as exc:
        console.print(f"[red]Error:[/red] Integration manifest for '{key}' is unreadable: {exc}")
        raise typer.Exit(1)

    # Detect modified files via manifest hashes
    modified = old_manifest.check_modified()
    if modified and not force:
        console.print(f"[yellow]⚠[/yellow]  {len(modified)} file(s) have been modified since installation:")
        for rel in modified:
            console.print(f"    {rel}")
        console.print("\nUse [cyan]--force[/cyan] to overwrite modified files, or resolve manually.")
        raise typer.Exit(1)

    selected_script = _resolve_script_type(project_root, script)

    parsed_options: dict[str, Any] | None = None
    if integration_options:
        parsed_options = _parse_integration_options(integration, integration_options)

    invoke_sep = integration.effective_invoke_separator(parsed_options)
    is_default = (key == default_key)

    # When upgrading a non-default integration, use the default's separator for
    # shared infra so templates stay consistent with the active integration.
    # Don't force-overwrite templates for non-default upgrades.
    if is_default:
        _install_shared_infra(project_root, selected_script, force=force, invoke_separator=invoke_sep)
    else:
        default_integration = None
        from ..integrations import get_integration as _get_int
        if default_key:
            default_integration = _get_int(default_key)
        default_sep = default_integration.effective_invoke_separator(None) if default_integration else invoke_sep
        _install_shared_infra(project_root, selected_script, force=False, invoke_separator=default_sep)
    if os.name != "nt":
        ensure_executable_scripts(project_root)

    # Reinstall
    console.print(f"Upgrading integration: [cyan]{key}[/cyan]")
    new_manifest = IntegrationManifest(key, project_root, version=get_speckit_version())

    # Save state snapshots for rollback
    int_json_path = project_root / INTEGRATION_JSON
    init_options_path = project_root / ".specify" / "init-options.json"
    before_state_text = int_json_path.read_text(encoding="utf-8") if int_json_path.exists() else None
    before_options_text = init_options_path.read_text(encoding="utf-8") if init_options_path.exists() else None
    before_manifest_text = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else None

    try:
        integration.setup(
            project_root,
            new_manifest,
            parsed_options=parsed_options,
            script_type=selected_script,
            raw_options=integration_options,
        )
        new_manifest.save()

        # Update settings for this integration
        settings[key] = {"invoke_separator": invoke_sep}
        new_state = _build_integration_state(default_key, installed_keys, settings)

        # If this is the default integration, refresh templates (atomically)
        if is_default:
            try:
                _call_refresh_shared_templates(project_root, invoke_sep, force=force)
            except Exception as exc:
                # Rollback everything
                if before_state_text is not None:
                    int_json_path.write_text(before_state_text, encoding="utf-8")
                if before_options_text is not None:
                    init_options_path.write_text(before_options_text, encoding="utf-8")
                if before_manifest_text is not None:
                    manifest_path.write_text(before_manifest_text, encoding="utf-8")
                console.print(f"[red]Error:[/red] Failed to refresh shared templates: {exc}")
                raise typer.Exit(1)

        _write_integration_state(project_root, new_state)
        if is_default:
            _update_init_options_for_integration(project_root, integration, script_type=selected_script)

    except typer.Exit:
        raise
    except Exception as exc:
        console.print(f"[red]Error:[/red] Failed to upgrade integration: {exc}")
        console.print("[yellow]The previous integration files may still be in place.[/yellow]")
        raise typer.Exit(1)

    # Remove stale files from old manifest that are not in the new one
    old_files = old_manifest.files
    new_files = new_manifest.files
    stale_keys = set(old_files) - set(new_files)
    if stale_keys:
        stale_manifest = IntegrationManifest(key, project_root, version="stale-cleanup")
        stale_manifest._files = {k: old_files[k] for k in stale_keys}
        stale_removed, _ = stale_manifest.uninstall(project_root, force=True)
        if stale_removed:
            console.print(f"  Removed {len(stale_removed)} stale file(s) from previous install")

    name = (integration.config or {}).get("name", key)
    console.print(f"\n[green]✓[/green] Integration '{name}' upgraded successfully")


def _handle_catalog_error(exc: Exception, project_root: Path) -> None:
    """Format and print catalog errors with helpful tips."""
    from ..integrations.catalog import IntegrationValidationError

    console.print(f"[red]Error:[/red] {exc}")

    env_url = os.environ.get("SPECKIT_INTEGRATION_CATALOG_URL", "").strip()

    if env_url:
        console.print("\n[bold]Tips:[/bold]")
        console.print("  • If using a custom catalog URL, ensure it is reachable and valid JSON.")
        console.print("  • Check your SPECKIT_INTEGRATION_CATALOG_URL environment variable. unset it to use the configured catalog files (.specify/integration-catalogs.yml or ~/.specify/integration-catalogs.yml).")
    elif isinstance(exc, IntegrationValidationError):
        console.print("\n[dim]Tip: Check the configuration file path shown above (.specify/integration-catalogs.yml or ~/.specify/integration-catalogs.yml) for errors.[/dim]")
    else:
        console.print("\n[dim]Tip: The catalog may be temporarily unavailable. Try again when online.[/dim]")

    raise typer.Exit(1)


@integration_app.command("info")
def integration_info(
    key: str = typer.Argument(..., help="Integration key to get info about"),
):
    """Show detailed information about an integration."""
    from ..integrations import get_integration
    from ..integrations.catalog import IntegrationCatalog

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    _read_integration_json(project_root)

    integration = get_integration(key)
    if integration:
        cfg = integration.config or {}
        console.print(f"\n[bold cyan]Integration: {cfg.get('name', key)}[/bold cyan]\n")
        console.print(f"  Key:          {key}")
        console.print(f"  Folder:       {cfg.get('folder', '')}")
        console.print(f"  Requires CLI: {'yes' if cfg.get('requires_cli') else 'no'}")
        if cfg.get("install_url"):
            console.print(f"  Install URL:  {cfg['install_url']}")
        if integration.context_file:
            console.print(f"  Context File: {integration.context_file}")
        console.print("\n  [green]Built-in integration[/green]")
        console.print()
        return

    ic = IntegrationCatalog(project_root)
    try:
        entry = ic.get_integration_info(key)
    except Exception as exc:
        _handle_catalog_error(exc, project_root)

    if not entry:
        console.print(f"[red]Error:[/red] Integration '{key}' not found")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]Integration: {entry.get('name', key)}[/bold cyan]\n")
    console.print(f"  Key:          {key}")
    version = entry.get('version', '?')
    if version != '?' and not version.startswith('v'):
        version = f"v{version}"
    console.print(f"  Version:      {version}")
    console.print(f"  Description:  {entry.get('description', '')}")
    if entry.get("author"):
        console.print(f"  Author:       {entry['author']}")
    if entry.get("tags"):
        console.print(f"  Tags:         {', '.join(entry['tags'])}")

    if entry.get("_install_allowed", True):
        console.print("\n  [yellow]Available in catalog[/yellow]")
        console.print(f"  Install with: [cyan]specify integration install {key}[/cyan]")
    else:
        console.print("\n  [dim]Not directly installable (community catalog)[/dim]")

    console.print()


@integration_app.command("search")
def integration_search(
    query: str = typer.Argument(None, help="Search query"),
    tag: str = typer.Option(None, "--tag", help="Filter by tag"),
    author: str = typer.Option(None, "--author", help="Filter by author"),
):
    """Search for integrations in the catalog."""
    from ..integrations.catalog import IntegrationCatalog

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    _read_integration_json(project_root)

    ic = IntegrationCatalog(project_root)
    try:
        results = ic.search(query=query, tag=tag, author=author)
    except Exception as exc:
        _handle_catalog_error(exc, project_root)

    if not results:
        console.print("[yellow]No integrations found matching your criteria.[/yellow]")
        console.print("\nTry broadening your search (e.g., [cyan]specify integration search <term>[/cyan]) or check [cyan]specify integration catalog list[/cyan]")
        return

    console.print(f"\n[bold cyan]Found {len(results)} integration(s):[/bold cyan]\n")
    table = Table()
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Description")

    has_discovery_only = False
    for entry in sorted(results, key=lambda e: e["id"]):
        v = entry.get("version", "")
        if v and not v.startswith("v"):
            v = f"v{v}"

        install_allowed = entry.get("_install_allowed", True)
        name = entry.get("name", entry["id"])
        if not install_allowed:
            name = f"{name} [yellow]*[/yellow]"
            has_discovery_only = True

        table.add_row(
            entry["id"],
            name,
            v,
            entry.get("description", "")[:60] + "..." if len(entry.get("description", "")) > 60 else entry.get("description", ""),
        )

    console.print(table)
    if has_discovery_only:
        console.print("\n[yellow]*[/yellow] = Not directly installable (community catalog)")
        console.print("Note: Only built-in integration IDs can be installed; community integrations are discovery-only.")

    console.print("\nView details with: [cyan]specify integration info <id>[/cyan]")
    console.print()


@integration_catalog_app.command("list")
def integration_catalog_list():
    """List all active integration catalogs."""
    from ..integrations.catalog import IntegrationCatalog

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    _read_integration_json(project_root)

    ic = IntegrationCatalog(project_root)

    env_url = os.environ.get("SPECKIT_INTEGRATION_CATALOG_URL", "").strip()
    if env_url:
        console.print("[yellow]SPECKIT_INTEGRATION_CATALOG_URL is set[/yellow]")
        console.print("[dim]This supersedes configured catalog files and is non-removable via CLI.[/dim]\n")

    try:
        active = ic.get_active_catalogs()
    except Exception as exc:
        _handle_catalog_error(exc, project_root)

    console.print("[bold cyan]Integration Catalog Sources[/bold cyan]\n")
    console.print("[bold cyan]Active catalog sources[/bold cyan]")
    console.print("[bold cyan]Project catalog sources:[/bold cyan]\n")

    config_path = project_root / ".specify" / "integration-catalogs.yml"
    has_config = config_path.exists()

    for i, entry in enumerate(active):
        install_str = "[green]install allowed[/green]" if entry.install_allowed else "[yellow]discovery only[/yellow]"
        prefix = f"[{i}] " if has_config and not env_url else ""
        console.print(f"  {prefix}[bold]{entry.name}[/bold] (priority {entry.priority})")
        if entry.description:
            console.print(f"     {entry.description}")
        console.print(f"     URL: {entry.url}")
        console.print(f"     Install: {install_str}")
        console.print()

    if env_url:
        pass
    elif has_config:
        console.print(f"[dim]Config: {config_path.relative_to(project_root)}[/dim]")
    else:
        console.print("[dim]No project-level catalog sources configured. Using built-in defaults. (non-removable)[/dim]")

    if env_url or config_path.exists():
        is_default = (
            len(active) == 2
            and active[0].url == IntegrationCatalog.DEFAULT_CATALOG_URL
            and active[1].url == IntegrationCatalog.COMMUNITY_CATALOG_URL
        )
        if not is_default:
            console.print("\n[yellow]Warning:[/yellow] Using a custom integration catalog.")
            console.print("Only use catalogs from sources you trust.")


@integration_catalog_app.command("add")
def integration_catalog_add(
    url: str = typer.Argument(help="Catalog URL (must use HTTPS)"),
    name: str | None = typer.Option(None, "--name", help="Catalog name"),
):
    """Add a catalog to .specify/integration-catalogs.yml."""
    from ..integrations.catalog import IntegrationCatalog, IntegrationCatalogError

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    url = url.strip()
    ic = IntegrationCatalog(project_root)
    _read_integration_json(project_root)
    try:
        ic.add_catalog(url, name=name)
    except IntegrationCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"Catalog source added: {url}")
    console.print("Config saved to .specify/integration-catalogs.yml")


@integration_catalog_app.command("remove")
def integration_catalog_remove(
    target: str = typer.Argument(help="Catalog name or index to remove (from 'catalog list')"),
):
    """Remove a catalog from .specify/integration-catalogs.yml."""
    from ..integrations.catalog import IntegrationCatalog, IntegrationCatalogError

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    ic = IntegrationCatalog(project_root)
    _read_integration_json(project_root)
    try:
        # Try integer index first
        try:
            idx = int(target)
            name = ic.remove_catalog(idx)
        except ValueError:
            name = ic.remove_catalog(target)
    except IntegrationCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"Catalog source '{name}' removed")
