"""specify integration switch / upgrade command handlers."""
from __future__ import annotations

import os
from pathlib import PurePath

import typer

from .._console import console
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
    _SharedTemplateRefreshError,
    _clear_init_options_for_integration,
    _cli_error_detail,
    _cli_phase_label,
    _get_speckit_version,
    _read_integration_json,
    _refresh_init_options_speckit_version,
    _remove_integration_json,
    _resolve_integration_options,
    _resolve_integration_script_type,
    _resolve_script_type,
    _set_default_integration,
    _set_default_integration_or_exit,
    _update_init_options_for_integration,
    _write_integration_json,
)


@integration_app.command("switch")
def integration_switch(
    target: str = typer.Argument(help="Integration key to switch to"),
    script: str | None = typer.Option(None, "--script", help="Script type: sh or ps (default: from init-options.json or platform default)"),
    force: bool = typer.Option(False, "--force", help="Force removal of modified files during uninstall of the previous integration"),
    refresh_shared_infra: bool = typer.Option(False, "--refresh-shared-infra", help="Also overwrite shared infrastructure files even if you customized them (otherwise customizations are preserved)"),
    integration_options: str | None = typer.Option(None, "--integration-options", help='Options for the target integration'),
):
    """Switch from the current integration to a different one."""
    from . import INTEGRATION_REGISTRY, get_integration
    from .manifest import IntegrationManifest
    from .. import _print_cli_warning, _require_specify_project, _install_shared_infra_or_exit

    project_root = _require_specify_project()
    target_integration = get_integration(target)
    if target_integration is None:
        console.print(f"[red]Error:[/red] Unknown integration '{target}'")
        available = ", ".join(sorted(INTEGRATION_REGISTRY.keys()))
        console.print(f"Available integrations: {available}")
        raise typer.Exit(1)

    current = _read_integration_json(project_root)
    installed_keys = _installed_integration_keys(current)
    installed_key = _default_integration_key(current)

    if installed_key == target:
        if integration_options is not None:
            console.print(
                "[red]Error:[/red] --integration-options cannot be used when switching "
                "to an already installed integration."
            )
            console.print(
                f"Run [cyan]specify integration upgrade {target} --integration-options ...[/cyan] "
                "to update managed files/options."
            )
            raise typer.Exit(1)
        if force:
            raw_options, parsed_options = _resolve_integration_options(
                target_integration, current, target, None
            )
            _set_default_integration_or_exit(
                project_root,
                current,
                target,
                target_integration,
                installed_keys,
                raw_options=raw_options,
                parsed_options=parsed_options,
                refresh_templates_force=True,
            )
            console.print(
                f"\n[green]✓[/green] Default integration remains [bold]{target}[/bold]; "
                "shared infrastructure refreshed."
            )
            raise typer.Exit(0)
        console.print(f"[yellow]Integration '{target}' is already the default integration. Nothing to switch.[/yellow]")
        raise typer.Exit(0)

    if target in installed_keys:
        if integration_options is not None:
            console.print(
                "[red]Error:[/red] --integration-options cannot be used when switching "
                "to an already installed integration."
            )
            console.print(
                f"Run [cyan]specify integration upgrade {target} --integration-options ...[/cyan] "
                f"to update managed files/options, then [cyan]specify integration use {target}[/cyan]."
            )
            raise typer.Exit(1)
        raw_options, parsed_options = _resolve_integration_options(
            target_integration, current, target, None
        )
        _set_default_integration_or_exit(
            project_root,
            current,
            target,
            target_integration,
            installed_keys,
            raw_options=raw_options,
            parsed_options=parsed_options,
            refresh_templates_force=force,
        )
        console.print(f"\n[green]✓[/green] Default integration set to [bold]{target}[/bold].")
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
            except _MANIFEST_READ_ERRORS as exc:
                console.print(f"[red]Error:[/red] Could not read integration manifest for '{installed_key}': {manifest_path}")
                console.print(f"[dim]{exc}[/dim]")
                console.print(
                    f"To recover, delete the unreadable manifest at {manifest_path}, "
                    f"run [cyan]specify integration uninstall {installed_key}[/cyan], then retry."
                )
                raise typer.Exit(1)
            removed, skipped = current_integration.teardown(
                project_root, old_manifest, force=force,
            )
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
            except _MANIFEST_READ_ERRORS as exc:
                console.print(f"[yellow]Warning:[/yellow] Could not read manifest for '{installed_key}': {exc}")
        else:
            console.print(f"[red]Error:[/red] Integration '{installed_key}' is installed but has no manifest.")
            console.print(
                f"Run [cyan]specify integration uninstall {installed_key}[/cyan] to clear metadata, "
                f"then retry [cyan]specify integration switch {target}[/cyan]."
            )
            raise typer.Exit(1)

        # Unregister extension commands for the old agent so they don't
        # remain as orphans in the old agent's directory.
        try:
            from ..extensions import ExtensionManager

            ext_mgr = ExtensionManager(project_root)
            ext_mgr.unregister_agent_artifacts(installed_key)
        except Exception as ext_err:
            _print_cli_warning(
                "clean up extension artifacts for",
                "integration",
                installed_key,
                ext_err,
                continuing="Continuing with integration switch; old extension artifacts may need manual cleanup.",
            )

        # Clear metadata so a failed Phase 2 doesn't leave stale references
        installed_keys = [installed for installed in installed_keys if installed != installed_key]
        _clear_init_options_for_integration(project_root, installed_key)
        if installed_keys:
            fallback_key = installed_keys[0]
            fallback_integration = get_integration(fallback_key)
            if fallback_integration is not None:
                raw_options, parsed_options = _resolve_integration_options(
                    fallback_integration, current, fallback_key, None
                )
                _set_default_integration_or_exit(
                    project_root,
                    current,
                    fallback_key,
                    fallback_integration,
                    installed_keys,
                    raw_options=raw_options,
                    parsed_options=parsed_options,
                )
            else:
                _write_integration_json(
                    project_root, fallback_key, installed_keys, _integration_settings(current)
                )
        else:
            _remove_integration_json(project_root)
        current = _read_integration_json(project_root)

    # Build parsed options from --integration-options so the integration
    # can determine its effective invoke separator before shared infra
    # is installed.
    raw_options, parsed_options = _resolve_integration_options(
        target_integration, current, target, integration_options
    )

    # Refresh shared infrastructure to the current CLI version. Switching
    # integrations is exactly when stale vendored shared scripts (e.g.
    # update-agent-context.sh that pre-dates the target integration's
    # supported-agent list) would silently break the new integration.
    #
    # Use refresh_managed=True so only files that match their previously
    # recorded hash are overwritten — user customizations are detected via
    # hash divergence and preserved with a warning. Pass
    # --refresh-shared-infra to overwrite customizations as well. See #2293.
    _install_shared_infra_or_exit(
        project_root,
        selected_script,
        force=refresh_shared_infra,
        refresh_managed=True,
        invoke_separator=_invoke_separator_for_integration(
            target_integration, current, target, parsed_options
        ),
        refresh_hint=(
            "To overwrite customizations, re-run with "
            "[cyan]specify integration switch ... --refresh-shared-infra[/cyan]."
        ),
    )
    if os.name != "nt":
        from .. import ensure_executable_scripts
        ensure_executable_scripts(project_root)

    # Phase 2: Install target integration
    console.print(f"Installing integration: [cyan]{target}[/cyan]")
    manifest = IntegrationManifest(
        target_integration.key, project_root, version=_get_speckit_version()
    )

    try:
        target_integration.setup(
            project_root, manifest,
            parsed_options=parsed_options,
            script_type=selected_script,
            raw_options=raw_options,
        )
        manifest.save()
        _set_default_integration(
            project_root,
            current,
            target_integration.key,
            target_integration,
            _dedupe_integration_keys([*installed_keys, target_integration.key]),
            script_type=selected_script,
            raw_options=raw_options,
            parsed_options=parsed_options,
        )

        # Re-register extension commands for the new agent so that
        # previously-installed extensions are available in the new integration.
        try:
            from ..extensions import ExtensionManager

            ext_mgr = ExtensionManager(project_root)
            ext_mgr.register_enabled_extensions_for_agent(target)
        except Exception as ext_err:
            _print_cli_warning(
                "register extension artifacts for",
                "integration",
                target,
                ext_err,
                continuing="The integration switch succeeded, but installed extensions may need re-registration.",
            )

    except Exception as exc:
        # Attempt rollback of any files written by setup
        try:
            target_integration.teardown(project_root, manifest, force=True)
        except Exception as rollback_err:
            # Suppress so the original setup error remains the primary failure
            _print_cli_warning(
                "rollback",
                "integration",
                target,
                rollback_err,
                continuing="The original switch failure is still the primary error.",
            )
        if installed_keys:
            fallback_key = installed_keys[0]
            fallback_integration = get_integration(fallback_key)
            if fallback_integration is not None:
                raw_options, parsed_options = _resolve_integration_options(
                    fallback_integration, current, fallback_key, None
                )
                try:
                    _set_default_integration(
                        project_root,
                        current,
                        fallback_key,
                        fallback_integration,
                        installed_keys,
                        raw_options=raw_options,
                        parsed_options=parsed_options,
                    )
                except _SharedTemplateRefreshError as restore_err:
                    console.print(
                        f"[yellow]Warning:[/yellow] Failed to restore default "
                        f"integration '{fallback_key}': {restore_err}"
                    )
            else:
                _write_integration_json(
                    project_root, fallback_key, installed_keys, _integration_settings(current)
                )
        else:
            _remove_integration_json(project_root)
        console.print(
            f"[red]Error:[/red] Failed to {_cli_phase_label('install', 'integration', target)} "
            f"during switch: {_cli_error_detail(exc)}"
        )
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
    from . import get_integration
    from .manifest import IntegrationManifest
    from .. import _require_specify_project, _install_shared_infra_or_exit, _install_shared_infra

    project_root = _require_specify_project()
    current = _read_integration_json(project_root)
    installed_key = _default_integration_key(current)
    installed_keys = _installed_integration_keys(current)

    if key is None:
        if not installed_key:
            console.print("[yellow]No integration is currently installed.[/yellow]")
            raise typer.Exit(0)
        key = installed_key

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
    except _MANIFEST_READ_ERRORS as exc:
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

    selected_script = _resolve_integration_script_type(project_root, current, key, script)

    # Build parsed options from --integration-options so the integration
    # can determine its effective invoke separator before shared infra
    # is installed.
    raw_options, parsed_options = _resolve_integration_options(
        integration, current, key, integration_options
    )

    # Ensure shared infrastructure is up to date; --force overwrites existing files.
    infra_integration = integration
    infra_key = key
    infra_parsed = parsed_options
    if installed_key and installed_key != key:
        default_integration = get_integration(installed_key)
        if default_integration is not None:
            infra_integration = default_integration
            infra_key = installed_key
            _, infra_parsed = _resolve_integration_options(
                default_integration, current, installed_key, None
            )
    _install_shared_infra_or_exit(
        project_root,
        selected_script,
        force=force,
        invoke_separator=_invoke_separator_for_integration(
            infra_integration, current, infra_key, infra_parsed
        ),
    )
    if os.name != "nt":
        from .. import ensure_executable_scripts
        ensure_executable_scripts(project_root)

    # Phase 1: Install new files (overwrites existing; old-only files remain)
    console.print(f"Upgrading integration: [cyan]{key}[/cyan]")
    new_manifest = IntegrationManifest(key, project_root, version=_get_speckit_version())

    try:
        integration.setup(
            project_root,
            new_manifest,
            parsed_options=parsed_options,
            script_type=selected_script,
            raw_options=raw_options,
        )
        settings = _with_integration_setting(
            current,
            key,
            integration,
            script_type=selected_script,
            raw_options=raw_options,
            parsed_options=parsed_options,
        )
        if installed_key == key:
            try:
                _install_shared_infra(
                    project_root,
                    selected_script,
                    invoke_separator=_invoke_separator_for_integration(
                        integration, {"integration_settings": settings}, key, parsed_options
                    ),
                    force=force,
                    refresh_managed=True,
                )
            except (ValueError, OSError) as exc:
                raise _SharedTemplateRefreshError(
                    f"Failed to refresh shared infrastructure for '{key}': {exc}"
                ) from exc
            if os.name != "nt":
                from .. import ensure_executable_scripts
                ensure_executable_scripts(project_root)
        new_manifest.save()
        _write_integration_json(project_root, installed_key, installed_keys, settings)
        if installed_key == key:
            _update_init_options_for_integration(project_root, integration, script_type=selected_script)
        else:
            _refresh_init_options_speckit_version(project_root)
    except Exception as exc:
        # Don't teardown — setup overwrites in-place, so teardown would
        # delete files that were working before the upgrade.  Just report.
        console.print(f"[red]Error:[/red] Failed to {_cli_phase_label('upgrade', 'integration', key)}.")
        console.print(f"[dim]Details:[/dim] {_cli_error_detail(exc)}")
        console.print("[yellow]The previous integration files may still be in place.[/yellow]")
        raise typer.Exit(1)

    # Phase 2: Remove stale files from old manifest that are not in the new one
    old_files = old_manifest.files
    new_files = new_manifest.files
    # Exclude integration-declared paths that use conditional manifest tracking
    # (e.g. merge targets like .vscode/settings.json) so they are never deleted
    # as "stale" while still being actively managed.  Manifest keys are stored
    # in POSIX form, so normalize the exclusions the same way before subtracting
    # (an integration may build paths with os.path.join / backslashes).
    exclusions = {PurePath(p).as_posix() for p in integration.stale_cleanup_exclusions()}
    stale_keys = (set(old_files) - set(new_files)) - exclusions
    if stale_keys:
        stale_manifest = IntegrationManifest(key, project_root, version="stale-cleanup")
        stale_manifest._files = {k: old_files[k] for k in stale_keys}
        stale_removed, _ = stale_manifest.uninstall(project_root, force=True)
        if stale_removed:
            console.print(f"  Removed {len(stale_removed)} stale file(s) from previous install")

    name = (integration.config or {}).get("name", key)
    console.print(f"\n[green]✓[/green] Integration '{name}' upgraded successfully")
