"""specify integration * commands."""
import os
import json
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

INTEGRATION_JSON = ".specify/integration.json"


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


def _write_integration_json(
    project_root: Path,
    integration_key: str,
) -> None:
    """Write ``.specify/integration.json`` for *integration_key*."""
    dest = project_root / INTEGRATION_JSON
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({
        "integration": integration_key,
        "version": get_speckit_version(),
    }, indent=2) + "\n", encoding="utf-8")


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


@integration_app.command("list")
def integration_list(
    catalog: bool = typer.Option(False, "--catalog", help="Browse full catalog (built-in + community)"),
):
    """List available integrations and installed status."""
    from ..integrations import INTEGRATION_REGISTRY

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    current = _read_integration_json(project_root)
    installed_key = current.get("integration")

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
            if eid == installed_key:
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
    table.add_column("Key", style="cyan")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("CLI Required")

    for key in sorted(INTEGRATION_REGISTRY.keys()):
        integration = INTEGRATION_REGISTRY[key]
        cfg = integration.config or {}
        name = cfg.get("name", key)
        requires_cli = cfg.get("requires_cli", False)

        if key == installed_key:
            status = "[green]installed[/green]"
        else:
            status = ""

        cli_req = "yes" if requires_cli else "no (IDE)"
        table.add_row(key, name, status, cli_req)

    console.print(table)

    if installed_key:
        console.print(f"\n[dim]Current integration:[/dim] [cyan]{installed_key}[/cyan]")
    else:
        console.print("\n[yellow]No integration currently installed.[/yellow]")
        console.print("Install one with: [cyan]specify integration install <key>[/cyan]")


@integration_app.command("install")
def integration_install(
    key: str = typer.Argument(help="Integration key to install (e.g. claude, copilot)"),
    script: str | None = typer.Option(None, "--script", help="Script type: sh or ps (default: from init-options.json or platform default)"),
    integration_options: str | None = typer.Option(None, "--integration-options", help='Options for the integration (e.g. --integration-options="--commands-dir .myagent/cmds")'),
):
    """Install an integration into an existing project."""
    from ..integrations import INTEGRATION_REGISTRY, get_integration
    from ..integrations.manifest import IntegrationManifest

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    integration = get_integration(key)
    if integration is None:
        console.print(f"[red]Error:[/red] Unknown integration '{key}'")
        available = ", ".join(sorted(INTEGRATION_REGISTRY.keys()))
        console.print(f"Available integrations: {available}")
        raise typer.Exit(1)

    current = _read_integration_json(project_root)
    installed_key = current.get("integration")

    if installed_key and installed_key == key:
        console.print(f"[yellow]Integration '{key}' is already installed.[/yellow]")
        console.print("Run [cyan]specify integration uninstall[/cyan] first, then reinstall.")
        raise typer.Exit(0)

    if installed_key:
        console.print(f"[red]Error:[/red] Integration '{installed_key}' is already installed.")
        console.print(f"Run [cyan]specify integration uninstall[/cyan] first, or use [cyan]specify integration switch {key}[/cyan].")
        raise typer.Exit(1)

    selected_script = _resolve_script_type(project_root, script)

    # Build parsed options from --integration-options so the integration
    # can determine its effective invoke separator before shared infra
    # is installed.
    parsed_options: dict[str, Any] | None = None
    if integration_options:
        parsed_options = _parse_integration_options(integration, integration_options)

    # Ensure shared infrastructure is present (safe to run unconditionally;
    # _install_shared_infra merges missing files without overwriting).
    _install_shared_infra(project_root, selected_script, invoke_separator=integration.effective_invoke_separator(parsed_options))
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
        _write_integration_json(project_root, integration.key)
        _update_init_options_for_integration(project_root, integration, script_type=selected_script)

    except Exception as exc:
        # Attempt rollback of any files written by setup
        try:
            integration.teardown(project_root, manifest, force=True)
        except Exception as rollback_err:
            # Suppress so the original setup error remains the primary failure
            console.print(f"[yellow]Warning:[/yellow] Failed to roll back integration changes: {rollback_err}")
        _remove_integration_json(project_root)
        console.print(f"[red]Error:[/red] Failed to install integration: {exc}")
        raise typer.Exit(1)

    name = (integration.config or {}).get("name", key)
    console.print(f"\n[green]✓[/green] Integration '{name}' installed successfully")


@integration_app.command("uninstall")
def integration_uninstall(
    key: str = typer.Argument(None, help="Integration key to uninstall (default: current integration)"),
    force: bool = typer.Option(False, "--force", help="Remove files even if modified"),
):
    """Uninstall an integration, safely preserving modified files."""
    from ..integrations import get_integration
    from ..integrations.manifest import IntegrationManifest

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    current = _read_integration_json(project_root)
    installed_key = current.get("integration")

    if key is None:
        if not installed_key:
            console.print("[yellow]No integration is currently installed.[/yellow]")
            raise typer.Exit(0)
        key = installed_key

    if installed_key and installed_key != key:
        console.print(f"[red]Error:[/red] Integration '{key}' is not the currently installed integration ('{installed_key}').")
        raise typer.Exit(1)

    integration = get_integration(key)

    manifest_path = project_root / ".specify" / "integrations" / f"{key}.manifest.json"
    if not manifest_path.exists():
        console.print(f"[yellow]No manifest found for integration '{key}'. Nothing to uninstall.[/yellow]")
        _remove_integration_json(project_root)
        # Clear integration-related keys from init-options.json
        opts = load_init_options(project_root)
        if opts.get("integration") == key or opts.get("ai") == key:
            opts.pop("integration", None)
            opts.pop("ai", None)
            opts.pop("ai_skills", None)
            opts.pop("context_file", None)
            save_init_options(project_root, opts)
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

    # Remove managed context section from the agent context file
    if integration:
        integration.remove_context_section(project_root)

    _remove_integration_json(project_root)

    # Update init-options.json to clear the integration
    opts = load_init_options(project_root)
    if opts.get("integration") == key or opts.get("ai") == key:
        opts.pop("integration", None)
        opts.pop("ai", None)
        opts.pop("ai_skills", None)
        opts.pop("context_file", None)
        save_init_options(project_root, opts)

    name = (integration.config or {}).get("name", key) if integration else key
    console.print(f"\n[green]✓[/green] Integration '{name}' uninstalled")
    if removed:
        console.print(f"  Removed {len(removed)} file(s)")
    if skipped:
        console.print(f"\n[yellow]⚠[/yellow]  {len(skipped)} modified file(s) were preserved:")
        for path in skipped:
            rel = path.relative_to(project_root) if path.is_absolute() else path
            console.print(f"    {rel}")


@integration_app.command("switch")
def integration_switch(
    target: str = typer.Argument(help="Integration key to switch to"),
    script: str | None = typer.Option(None, "--script", help="Script type: sh or ps (default: from init-options.json or platform default)"),
    force: bool = typer.Option(False, "--force", help="Force removal of modified files during uninstall"),
    integration_options: str | None = typer.Option(None, "--integration-options", help='Options for the target integration'),
):
    """Switch from the current integration to a different one."""
    from ..integrations import INTEGRATION_REGISTRY, get_integration
    from ..integrations.manifest import IntegrationManifest

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    target_integration = get_integration(target)
    if target_integration is None:
        console.print(f"[red]Error:[/red] Unknown integration '{target}'")
        available = ", ".join(sorted(INTEGRATION_REGISTRY.keys()))
        console.print(f"Available integrations: {available}")
        raise typer.Exit(1)

    current = _read_integration_json(project_root)
    installed_key = current.get("integration")

    if installed_key == target:
        console.print(f"[yellow]Integration '{target}' is already installed. Nothing to switch.[/yellow]")
        raise typer.Exit(0)

    selected_script = _resolve_script_type(project_root, script)

    # Phase 1: Uninstall current integration (if any)
    if installed_key:
        current_integration = get_integration(installed_key)
        manifest_path = project_root / ".specify" / "integrations" / f"{installed_key}.manifest.json"

        if current_integration and manifest_path.exists():
            console.print(f"Uninstalling current integration: [cyan]{installed_key}[/cyan]")
            try:
                old_manifest = IntegrationManifest.load(installed_key, project_root)
            except (ValueError, FileNotFoundError) as exc:
                console.print(f"[red]Error:[/red] Could not read integration manifest for '{installed_key}': {manifest_path}")
                console.print(f"[dim]{exc}[/dim]")
                console.print(
                    f"To recover, delete the unreadable manifest at {manifest_path}, "
                    f"run [cyan]specify integration uninstall {installed_key}[/cyan], then retry."
                )
                raise typer.Exit(1)
            removed, skipped = old_manifest.uninstall(project_root, force=force)
            current_integration.remove_context_section(project_root)
            if removed:
                console.print(f"  Removed {len(removed)} file(s)")
            if skipped:
                console.print(f"  [yellow]⚠[/yellow]  {len(skipped)} modified file(s) preserved")
        elif not current_integration and manifest_path.exists():
            # Integration removed from registry but manifest exists — use manifest-only uninstall
            console.print(f"Uninstalling unknown integration '{installed_key}' via manifest")
            try:
                old_manifest = IntegrationManifest.load(installed_key, project_root)
                removed, skipped = old_manifest.uninstall(project_root, force=force)
                if removed:
                    console.print(f"  Removed {len(removed)} file(s)")
                if skipped:
                    console.print(f"  [yellow]⚠[/yellow]  {len(skipped)} modified file(s) preserved")
            except (ValueError, FileNotFoundError) as exc:
                console.print(f"[yellow]Warning:[/yellow] Could not read manifest for '{installed_key}': {exc}")
        else:
            console.print(f"[red]Error:[/red] Integration '{installed_key}' is installed but has no manifest.")
            console.print(
                f"Run [cyan]specify integration uninstall {installed_key}[/cyan] to clear metadata, "
                f"then retry [cyan]specify integration switch {target}[/cyan]."
            )
            raise typer.Exit(1)

        # Clear metadata so a failed Phase 2 doesn't leave stale references
        _remove_integration_json(project_root)
        opts = load_init_options(project_root)
        opts.pop("integration", None)
        opts.pop("ai", None)
        opts.pop("ai_skills", None)
        opts.pop("context_file", None)
        save_init_options(project_root, opts)

    # Build parsed options from --integration-options so the integration
    # can determine its effective invoke separator before shared infra
    # is installed.
    parsed_options: dict[str, Any] | None = None
    if integration_options:
        parsed_options = _parse_integration_options(target_integration, integration_options)

    # Ensure shared infrastructure is present (safe to run unconditionally;
    # _install_shared_infra merges missing files without overwriting).
    _install_shared_infra(project_root, selected_script, invoke_separator=target_integration.effective_invoke_separator(parsed_options))
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
        _write_integration_json(project_root, target_integration.key)
        _update_init_options_for_integration(project_root, target_integration, script_type=selected_script)

    except Exception as exc:
        # Attempt rollback of any files written by setup
        try:
            target_integration.teardown(project_root, manifest, force=True)
        except Exception as rollback_err:
            # Suppress so the original setup error remains the primary failure
            console.print(f"[yellow]Warning:[/yellow] Failed to roll back integration '{target}': {rollback_err}")
        _remove_integration_json(project_root)
        console.print(f"[red]Error:[/red] Failed to install integration '{target}': {exc}")
        raise typer.Exit(1)

    name = (target_integration.config or {}).get("name", target)
    console.print(f"\n[green]✓[/green] Switched to integration '{name}'")


@integration_app.command("upgrade")
def integration_upgrade(
    key: str | None = typer.Argument(None, help="Integration key to upgrade (default: current integration)"),
    force: bool = typer.Option(False, "--force", help="Force upgrade even if files are modified"),
    script: str | None = typer.Option(None, "--script", help="Script type: sh or ps (default: from init-options.json or platform default)"),
    integration_options: str | None = typer.Option(None, "--integration-options", help="Options for the integration"),
):
    """Upgrade an integration by reinstalling with diff-aware file handling.

    Compares manifest hashes to detect locally modified files and
    blocks the upgrade unless --force is used.
    """
    from ..integrations import get_integration
    from ..integrations.manifest import IntegrationManifest

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    current = _read_integration_json(project_root)
    installed_key = current.get("integration")

    if key is None:
        if not installed_key:
            console.print("[yellow]No integration is currently installed.[/yellow]")
            raise typer.Exit(0)
        key = installed_key

    if installed_key and installed_key != key:
        console.print(
            f"[red]Error:[/red] Integration '{key}' is not the currently installed integration ('{installed_key}')."
        )
        console.print(f"Use [cyan]specify integration switch {key}[/cyan] instead.")
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

    # Build parsed options from --integration-options so the integration
    # can determine its effective invoke separator before shared infra
    # is installed.
    parsed_options: dict[str, Any] | None = None
    if integration_options:
        parsed_options = _parse_integration_options(integration, integration_options)

    # Ensure shared infrastructure is up to date; --force overwrites existing files.
    _install_shared_infra(project_root, selected_script, force=force, invoke_separator=integration.effective_invoke_separator(parsed_options))
    if os.name != "nt":
        ensure_executable_scripts(project_root)

    # Phase 1: Install new files (overwrites existing; old-only files remain)
    console.print(f"Upgrading integration: [cyan]{key}[/cyan]")
    new_manifest = IntegrationManifest(key, project_root, version=get_speckit_version())

    try:
        integration.setup(
            project_root,
            new_manifest,
            parsed_options=parsed_options,
            script_type=selected_script,
            raw_options=integration_options,
        )
        new_manifest.save()
        _write_integration_json(project_root, key)
        _update_init_options_for_integration(project_root, integration, script_type=selected_script)
    except Exception as exc:
        # Don't teardown — setup overwrites in-place, so teardown would
        # delete files that were working before the upgrade.  Just report.
        console.print(f"[red]Error:[/red] Failed to upgrade integration: {exc}")
        console.print("[yellow]The previous integration files may still be in place.[/yellow]")
        raise typer.Exit(1)

    # Phase 2: Remove stale files from old manifest that are not in the new one
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
