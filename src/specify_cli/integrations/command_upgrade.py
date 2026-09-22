"""The ``specify integration upgrade`` command and its layout guards."""
from __future__ import annotations

import os
from pathlib import PurePath

import typer

from .._console import console
from ..integration_runtime import (
    invoke_prefix_for_integration as _invoke_prefix_for_integration,
    invoke_separator_for_integration as _invoke_separator_for_integration,
    with_integration_setting as _with_integration_setting,
)
from ..integration_state import default_integration_key as _default_integration_key, installed_integration_keys as _installed_integration_keys
from ._command_upgrade_layout import (
    _PresetRegistryUnreadableError,
    _installed_command_presets_affecting_agent,
    _installed_presets_affecting_agent,
    _legacy_command_root_changed,
    _legacy_command_root_upgrade_pending,
    _manifest_tracks_skill_layout,
)
from ._commands import integration_app
from ._helpers import _MANIFEST_READ_ERRORS, _SharedTemplateRefreshError, _cli_error_detail, _cli_phase_label, _get_speckit_version, _read_integration_json, _refresh_init_options_speckit_version, _register_extensions_for_agent, _register_presets_for_agent, _resolve_integration_options, _resolve_integration_script_type, _unregister_enabled_extension_commands_for_agent, _update_init_options_for_integration, _write_integration_json


@integration_app.command("upgrade")
def integration_upgrade(
    key: str | None = typer.Argument(None, help="Integration key to upgrade (default: current integration)"),
    force: bool = typer.Option(False, "--force", help="Force upgrade even if files are modified"),
    script: str | None = typer.Option(None, "--script", help="Script type: sh, ps, or py (default: from init-options.json or platform default)"),
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

    legacy_command_root_upgrade_pending = _legacy_command_root_upgrade_pending(
        integration,
        old_manifest,
    )

    # Guard: Kilo's legacy command root moves from .kilocode/workflows to
    # .kilo/commands. Preset command artifacts are tracked outside the
    # integration manifest, and their agent-scoped rescaffold is best-effort,
    # not transactional with command-root cleanup. Refuse before setup writes
    # .kilo/commands rather than risking orphaned legacy files or missing
    # registry-tracked overrides in the canonical directory.
    if key == "kilocode" and legacy_command_root_upgrade_pending:
        config = integration.registrar_config or {}
        legacy = config.get("legacy_dir", "legacy command directory")
        canonical = config.get("dir", "canonical command directory")
        try:
            affected_presets = _installed_command_presets_affecting_agent(
                project_root,
                key,
            )
        except _PresetRegistryUnreadableError as exc:
            console.print(
                f"[red]Error:[/red] Cannot migrate '{key}' command directory "
                f"from [cyan]{legacy}[/cyan] to [cyan]{canonical}[/cyan]: "
                "the preset registry could not be read to verify installed presets."
            )
            console.print(f"[dim]Details:[/dim] {_cli_error_detail(exc)}")
            console.print(
                "A command directory migration cannot reconcile preset command "
                "artifacts while the preset registry state is unknown. Fix or "
                "restore [cyan].specify/presets/.registry[/cyan] and retry."
            )
            raise typer.Exit(1)
        if affected_presets:
            preset_list = ", ".join(sorted(affected_presets))
            console.print(
                f"[red]Error:[/red] Cannot migrate '{key}' command directory "
                f"from [cyan]{legacy}[/cyan] to [cyan]{canonical}[/cyan] while "
                f"preset override(s) are installed: [bold]{preset_list}[/bold]."
            )
            console.print(
                "Preset command artifacts cannot yet be reconciled across this "
                "command directory migration, so the upgrade is refused before "
                "changing files."
            )
            console.print(
                "Remove the preset(s), run the upgrade, then reinstall them:\n"
                f"  [cyan]specify preset remove <id>[/cyan]\n"
                f"  [cyan]specify integration upgrade {key} --script {selected_script} --force[/cyan]\n"
                f"  [cyan]specify preset add <id>[/cyan]"
            )
            raise typer.Exit(1)

    # Reject command↔skills layout changes while preset artifacts are tracked
    # for the integration (review #3415). Preset rescaffolding is best-effort:
    # an enabled preset can still have a missing/corrupt manifest or command
    # source, or fail during a write. Phase 2 would otherwise delete the
    # old-layout file before a replacement is known to exist. Refuse before
    # any mutation; same-layout upgrades still rescaffold the active agent.
    if _manifest_tracks_skill_layout(old_manifest) != integration.is_skills_mode(
        parsed_options, project_root
    ):
        try:
            affected_presets = _installed_presets_affecting_agent(project_root, key)
        except _PresetRegistryUnreadableError as exc:
            console.print(
                f"[red]Error:[/red] Cannot change '{key}' command layout: the "
                f"preset registry could not be read to verify installed presets."
            )
            console.print(f"[dim]Details:[/dim] {_cli_error_detail(exc)}")
            console.print(
                "A layout change cannot reconcile preset artifacts, so the "
                "migration is refused while the preset registry state is "
                "unknown. Fix or restore "
                "[cyan].specify/presets/.registry[/cyan] and retry."
            )
            raise typer.Exit(1)
        if affected_presets:
            preset_list = ", ".join(sorted(affected_presets))
            console.print(
                f"[red]Error:[/red] Cannot change '{key}' command layout while "
                f"preset override(s) are installed: [bold]{preset_list}[/bold]."
            )
            console.print(
                "Preset artifacts cannot be safely reconciled across a "
                "command↔skills layout change, so the migration is refused "
                "before changing files."
            )
            console.print(
                "Remove the preset(s), run the upgrade, then reinstall them:\n"
                f"  [cyan]specify preset remove <id>[/cyan]\n"
                f"  [cyan]specify integration upgrade {key} "
                f"--integration-options \"...\"[/cyan]\n"
                f"  [cyan]specify preset add <id>[/cyan]"
            )
            raise typer.Exit(1)

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
            infra_integration, current, infra_key, infra_parsed,
            project_root=project_root,
        ),
        invoke_prefix=_invoke_prefix_for_integration(
            infra_integration, infra_key, infra_parsed, project_root
        ),
    )
    if os.name != "nt":
        from .. import ensure_executable_scripts
        ensure_executable_scripts(project_root)

    # Phase 1: Install new files (overwrites existing; old-only files remain)
    console.print(f"Upgrading integration: [cyan]{key}[/cyan]")
    new_manifest = IntegrationManifest(key, project_root, version=_get_speckit_version())

    from ..events import resolve_events
    events_map = resolve_events(
        key,
        integration.config,
        project_root,
        parsed_options,
    )
    try:
        integration.setup(
            project_root,
            new_manifest,
            parsed_options=parsed_options,
            script_type=selected_script,
            raw_options=raw_options,
            events=events_map,
        )
        settings = _with_integration_setting(
            current,
            key,
            integration,
            script_type=selected_script,
            raw_options=raw_options,
            parsed_options=parsed_options,
            project_root=project_root,
        )
        if installed_key == key:
            try:
                _install_shared_infra(
                    project_root,
                    selected_script,
                    invoke_separator=_invoke_separator_for_integration(
                        integration, {"integration_settings": settings}, key, parsed_options,
                        project_root=project_root,
                    ),
                    invoke_prefix=_invoke_prefix_for_integration(
                        integration, key, parsed_options, project_root
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
            _update_init_options_for_integration(
                project_root,
                integration,
                script_type=selected_script,
                parsed_options=parsed_options,
            )
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
        # remove_manifest=False: this throwaway manifest shares ``key`` with the
        # real one just saved above (new_manifest.save()).  Letting uninstall()
        # delete ``{key}.manifest.json`` would wipe the freshly-written manifest
        # whenever an upgrade shrinks the tracked file set (e.g. Bob migrating
        # from the legacy commands layout to skills), leaving the integration
        # untracked and un-upgradeable.
        stale_removed, _ = stale_manifest.uninstall(
            project_root, force=True, remove_manifest=False
        )
        if stale_removed:
            console.print(f"  Removed {len(stale_removed)} stale file(s) from previous install")

    legacy_command_root_changed = _legacy_command_root_changed(
        integration,
        project_root,
        old_manifest,
        new_manifest,
    )
    if legacy_command_root_changed:
        _unregister_enabled_extension_commands_for_agent(
            project_root,
            key,
            continuing=(
                "The integration command directory changed, but legacy enabled "
                "extension artifacts may need manual cleanup."
            ),
        )

    # Re-register enabled extensions and presets only when upgrading the
    # active integration. Inactive integrations remain untouched until
    # `use` or `switch` activates and rescaffolds them (#2948). This runs
    # after the core upgrade transaction, so failures remain best-effort.
    if key == installed_key:
        _register_extensions_for_agent(
            project_root,
            key,
            force=True,
            continuing="The integration was upgraded, but installed extensions may need re-registration.",
        )
        _register_presets_for_agent(
            project_root,
            key,
            continuing="The integration was upgraded, but installed presets may need re-registration.",
        )

    name = (integration.config or {}).get("name", key)
    console.print(f"\n[green]✓[/green] Integration '{name}' upgraded successfully")
