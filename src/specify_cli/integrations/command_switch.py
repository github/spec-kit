"""The ``specify integration switch`` command."""
from __future__ import annotations

import os

import typer

from .._console import console
from ..integration_runtime import invoke_prefix_for_integration as _invoke_prefix_for_integration, invoke_separator_for_integration as _invoke_separator_for_integration
from ..integration_state import (
    dedupe_integration_keys as _dedupe_integration_keys,
    default_integration_key as _default_integration_key,
    installed_integration_keys as _installed_integration_keys,
    integration_settings as _integration_settings,
)
from ._commands import integration_app
from ._helpers import _MANIFEST_READ_ERRORS, _SharedTemplateRefreshError, _clear_init_options_for_integration, _cli_error_detail, _cli_phase_label, _get_speckit_version, _read_integration_json, _register_extensions_for_agent, _register_presets_for_agent, _remove_integration_json, _resolve_integration_options, _resolve_script_type, _set_default_integration, _set_default_integration_or_exit, _unregister_extensions_for_agent, _unregister_presets_for_agent, _write_integration_json


@integration_app.command("switch")
def integration_switch(
    target: str = typer.Argument(help="Integration key to switch to"),
    script: str | None = typer.Option(None, "--script", help="Script type: sh, ps, or py (default: from init-options.json or platform default)"),
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
        _register_extensions_for_agent(
            project_root,
            target,
            continuing=(
                "The integration switch succeeded, but installed extensions may "
                "need re-registration."
            ),
        )
        _register_presets_for_agent(
            project_root,
            target,
            continuing=(
                "The integration switch succeeded, but installed presets may "
                "need re-registration."
            ),
        )
        console.print(f"\n[green]✓[/green] Default integration set to [bold]{target}[/bold].")
        raise typer.Exit(0)

    selected_script = _resolve_script_type(project_root, script)

    # Resolve and validate target options before uninstalling the current
    # integration. Invalid options must not leave the project partially
    # switched with the previous integration already removed.
    target_raw_options, target_parsed_options = _resolve_integration_options(
        target_integration, current, target, integration_options
    )
    target_integration.is_skills_mode(target_parsed_options, project_root)

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
        _unregister_extensions_for_agent(
            project_root,
            installed_key,
            continuing="Continuing with integration switch; old extension artifacts may need manual cleanup.",
        )

        # Unregister preset commands/skills for the old agent for the same
        # reason: without this, a preset's command overrides (including
        # custom preset commands) and skill mirrors rendered for
        # installed_key would remain orphaned in its directory once a
        # different, possibly not-yet-installed integration becomes active
        # (#2948). Scoped strictly to installed_key; other agents' files,
        # tracking, and the preset packs themselves are untouched.
        _unregister_presets_for_agent(
            project_root,
            installed_key,
            continuing="Continuing with integration switch; old preset artifacts may need manual cleanup.",
        )

        # Clear metadata so a failed Phase 2 doesn't leave stale references
        installed_keys = [installed for installed in installed_keys if installed != installed_key]
        _clear_init_options_for_integration(project_root, installed_key)
        if installed_keys:
            fallback_key = installed_keys[0]
            fallback_integration = get_integration(fallback_key)
            if fallback_integration is not None:
                (
                    fallback_raw_options,
                    fallback_parsed_options,
                ) = _resolve_integration_options(
                    fallback_integration, current, fallback_key, None
                )
                _set_default_integration_or_exit(
                    project_root,
                    current,
                    fallback_key,
                    fallback_integration,
                    installed_keys,
                    raw_options=fallback_raw_options,
                    parsed_options=fallback_parsed_options,
                )
            else:
                _write_integration_json(
                    project_root, fallback_key, installed_keys, _integration_settings(current)
                )
        else:
            _remove_integration_json(project_root)
        current = _read_integration_json(project_root)

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
            target_integration, current, target, target_parsed_options,
            project_root=project_root,
        ),
        invoke_prefix=_invoke_prefix_for_integration(
            target_integration, target, target_parsed_options, project_root
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

    from ..events import resolve_events
    events_map = resolve_events(
        target_integration.key,
        target_integration.config,
        project_root,
        target_parsed_options,
    )
    try:
        target_integration.setup(
            project_root, manifest,
            parsed_options=target_parsed_options,
            script_type=selected_script,
            raw_options=target_raw_options,
            events=events_map,
        )
        manifest.save()
        _set_default_integration(
            project_root,
            current,
            target_integration.key,
            target_integration,
            _dedupe_integration_keys([*installed_keys, target_integration.key]),
            script_type=selected_script,
            raw_options=target_raw_options,
            parsed_options=target_parsed_options,
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
                    # Under active-only registration the fallback may never
                    # have received any extension/preset artifacts (it was
                    # installed while another integration was active), and
                    # Phase 1 already unregistered the outgoing agent's
                    # artifacts. Rescaffold so the restored default is
                    # actually usable. Both helpers are best-effort and
                    # cannot raise past this point.
                    _register_extensions_for_agent(
                        project_root,
                        fallback_key,
                        continuing="The switch was rolled back; installed extensions may need re-registration.",
                    )
                    _register_presets_for_agent(
                        project_root,
                        fallback_key,
                        continuing="The switch was rolled back; installed presets may need re-registration.",
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

    # Re-register extension commands for the new agent so previously-installed
    # extensions are available in it. Done after the try/except (the switch has
    # committed) so this best-effort step can never trigger the rollback above.
    _register_extensions_for_agent(
        project_root,
        target,
        continuing="The integration switch succeeded, but installed extensions may need re-registration.",
    )
    _register_presets_for_agent(
        project_root,
        target,
        continuing="The integration switch succeeded, but installed presets may need re-registration.",
    )

    name = (target_integration.config or {}).get("name", target)
    console.print(f"\n[green]✓[/green] Switched to integration '{name}'")
