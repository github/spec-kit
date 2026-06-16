"""specify integration install / uninstall command handlers."""
from __future__ import annotations

import os

import typer

from .._console import console
from .._utils import _display_project_path
from ..integration_runtime import (
    invoke_separator_for_integration as _invoke_separator_for_integration,
    with_integration_setting as _with_integration_setting,
)
from ..integration_state import (
    dedupe_integration_keys as _dedupe_integration_keys,
    default_integration_key as _default_integration_key,
    installed_integration_keys as _installed_integration_keys,
    integration_settings as _integration_settings,
)
from ._commands import integration_app
from ._helpers import (
    _MANIFEST_READ_ERRORS,
    _clear_init_options_for_integration,
    _cli_error_detail,
    _cli_phase_label,
    _get_speckit_version,
    _read_integration_json,
    _refresh_init_options_speckit_version,
    _remove_integration_json,
    _resolve_integration_options,
    _resolve_script_type,
    _set_default_integration_or_exit,
    _update_init_options_for_integration,
    _write_integration_json,
)


@integration_app.command("install")
def integration_install(
    key: str = typer.Argument(help="Integration key to install (e.g. claude, copilot)"),
    script: str | None = typer.Option(None, "--script", help="Script type: sh or ps (default: from init-options.json or platform default)"),
    force: bool = typer.Option(False, "--force", help="Allow multi-install when integrations are not declared safe"),
    integration_options: str | None = typer.Option(None, "--integration-options", help='Options for the integration (e.g. --integration-options="--commands-dir .myagent/cmds")'),
):
    """Install an integration into an existing project."""
    from . import INTEGRATION_REGISTRY, get_integration
    from .manifest import IntegrationManifest
    from .. import _require_specify_project, _install_shared_infra_or_exit

    project_root = _require_specify_project()
    integration = get_integration(key)
    if integration is None:
        console.print(f"[red]Error:[/red] Unknown integration '{key}'")
        available = ", ".join(sorted(INTEGRATION_REGISTRY.keys()))
        console.print(f"Available integrations: {available}")
        raise typer.Exit(1)

    current = _read_integration_json(project_root)
    default_key = _default_integration_key(current)
    installed_keys = _installed_integration_keys(current)

    if key in installed_keys:
        console.print(f"[yellow]Integration '{key}' is already installed.[/yellow]")
        if default_key == key:
            console.print("It is already the default integration.")
        else:
            console.print(
                f"To make it the default integration, run "
                f"[cyan]specify integration use {key}[/cyan]."
            )
        console.print(
            f"To refresh its managed files or options, run "
            f"[cyan]specify integration upgrade {key}[/cyan]."
        )
        console.print("No files were changed.")
        raise typer.Exit(0)

    if installed_keys and not force:
        unsafe_keys = []
        for installed_key in installed_keys:
            installed_integration = get_integration(installed_key)
            if not installed_integration or not getattr(installed_integration, "multi_install_safe", False):
                unsafe_keys.append(installed_key)
        if unsafe_keys or not getattr(integration, "multi_install_safe", False):
            console.print(
                f"[red]Error:[/red] Installed integrations: {', '.join(installed_keys)}."
            )
            if default_key:
                console.print(f"Default integration: [cyan]{default_key}[/cyan].")
            console.print(
                "Installing multiple integrations is only automatic when all involved "
                "integrations are declared multi-install safe."
            )
            console.print(
                f"To replace the default integration, run "
                f"[cyan]specify integration switch {key}[/cyan]."
            )
            console.print(
                f"To install '{key}' alongside the existing integrations anyway, "
                "retry the same install command with [cyan]--force[/cyan]."
            )
            raise typer.Exit(1)

    selected_script = _resolve_script_type(project_root, script)

    # Build parsed options from --integration-options so the integration
    # can determine its effective invoke separator before shared infra
    # is installed.
    raw_options, parsed_options = _resolve_integration_options(
        integration, current, key, integration_options
    )

    # Ensure shared infrastructure is present (safe to run unconditionally;
    # _install_shared_infra merges missing files without overwriting).
    infra_integration = integration
    infra_key = key
    infra_parsed = parsed_options
    if default_key:
        default_integration = get_integration(default_key)
        if default_integration is not None:
            infra_integration = default_integration
            infra_key = default_key
            _, infra_parsed = _resolve_integration_options(
                default_integration, current, default_key, None
            )
    _install_shared_infra_or_exit(
        project_root,
        selected_script,
        invoke_separator=_invoke_separator_for_integration(
            infra_integration, current, infra_key, infra_parsed
        ),
    )
    if os.name != "nt":
        from .. import ensure_executable_scripts
        ensure_executable_scripts(project_root)

    manifest = IntegrationManifest(
        integration.key, project_root, version=_get_speckit_version()
    )

    try:
        integration.setup(
            project_root, manifest,
            parsed_options=parsed_options,
            script_type=selected_script,
            raw_options=raw_options,
        )
        manifest.save()
        new_installed = _dedupe_integration_keys([*installed_keys, integration.key])
        new_default = default_key or integration.key
        settings = _with_integration_setting(
            current,
            integration.key,
            integration,
            script_type=selected_script,
            raw_options=raw_options,
            parsed_options=parsed_options,
        )
        _write_integration_json(project_root, new_default, new_installed, settings)
        if new_default == integration.key:
            _update_init_options_for_integration(project_root, integration, script_type=selected_script)
        else:
            _refresh_init_options_speckit_version(project_root)

    except Exception as exc:
        # Attempt rollback of any files written by setup
        try:
            integration.teardown(project_root, manifest, force=True)
        except Exception as rollback_err:
            # Suppress so the original setup error remains the primary failure
            from .. import _print_cli_warning
            _print_cli_warning(
                "rollback",
                "integration",
                key,
                rollback_err,
                continuing="The original install failure is still the primary error.",
            )
        if installed_keys:
            _write_integration_json(
                project_root, default_key, installed_keys, _integration_settings(current)
            )
        else:
            _remove_integration_json(project_root)
        console.print(
            f"[red]Error:[/red] Failed to {_cli_phase_label('install', 'integration', key)}: "
            f"{_cli_error_detail(exc)}"
        )
        raise typer.Exit(1)

    name = (integration.config or {}).get("name", key)
    console.print(f"\n[green]✓[/green] Integration '{name}' installed successfully")
    if default_key:
        console.print(f"[dim]Default integration remains:[/dim] [cyan]{default_key}[/cyan]")


@integration_app.command("uninstall")
def integration_uninstall(
    key: str = typer.Argument(None, help="Integration key to uninstall (default: current integration)"),
    force: bool = typer.Option(False, "--force", help="Remove files even if modified"),
):
    """Uninstall an integration, safely preserving modified files."""
    from . import get_integration
    from .manifest import IntegrationManifest
    from .. import _require_specify_project

    project_root = _require_specify_project()
    current = _read_integration_json(project_root)
    default_key = _default_integration_key(current)
    installed_keys = _installed_integration_keys(current)

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
        remaining = [installed for installed in installed_keys if installed != key]
        new_default = default_key if default_key != key else (remaining[0] if remaining else None)
        if remaining:
            if default_key == key and new_default and (new_integration := get_integration(new_default)):
                raw_options, parsed_options = _resolve_integration_options(
                    new_integration, current, new_default, None
                )
                _set_default_integration_or_exit(
                    project_root,
                    current,
                    new_default,
                    new_integration,
                    remaining,
                    raw_options=raw_options,
                    parsed_options=parsed_options,
                )
            else:
                _write_integration_json(
                    project_root, new_default, remaining, _integration_settings(current)
                )
        else:
            _remove_integration_json(project_root)
        if default_key == key:
            _clear_init_options_for_integration(project_root, key)
        raise typer.Exit(0)

    try:
        manifest = IntegrationManifest.load(key, project_root)
    except _MANIFEST_READ_ERRORS as exc:
        console.print(f"[red]Error:[/red] Integration manifest for '{key}' is unreadable.")
        console.print(f"Manifest: {manifest_path}")
        console.print(
            f"To recover, delete the unreadable manifest, run "
            f"[cyan]specify integration uninstall {key}[/cyan] to clear stale metadata, "
            f"then run [cyan]specify integration install {key}[/cyan] to regenerate."
        )
        console.print(f"[dim]Details:[/dim] {exc}")
        raise typer.Exit(1)

    if not integration:
        console.print(
            f"[yellow]Warning:[/yellow] Integration '{key}' not found "
            "in registry. Falling back to manifest-based cleanup."
        )
        removed, skipped = manifest.uninstall(project_root, force=force)
    else:
        removed, skipped = integration.teardown(project_root, manifest, force=force)

    remaining = [installed for installed in installed_keys if installed != key]
    new_default = default_key if default_key != key else (remaining[0] if remaining else None)
    if remaining:
        if default_key == key and new_default and (new_integration := get_integration(new_default)):
            raw_options, parsed_options = _resolve_integration_options(
                new_integration, current, new_default, None
            )
            _set_default_integration_or_exit(
                project_root,
                current,
                new_default,
                new_integration,
                remaining,
                raw_options=raw_options,
                parsed_options=parsed_options,
            )
        else:
            _write_integration_json(
                project_root, new_default, remaining, _integration_settings(current)
            )
    else:
        _remove_integration_json(project_root)

    if default_key == key:
        _clear_init_options_for_integration(project_root, key)

    name = (integration.config or {}).get("name", key) if integration else key
    console.print(f"\n[green]✓[/green] Integration '{name}' uninstalled")
    if removed:
        console.print(f"  Removed {len(removed)} file(s)")
    if skipped:
        console.print(f"\n[yellow]⚠[/yellow]  {len(skipped)} modified file(s) were preserved:")
        for path in skipped:
            rel = _display_project_path(project_root, path)
            console.print(f"    {rel}")
