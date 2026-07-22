"""specify integration switch / upgrade command handlers."""
from __future__ import annotations

import json
import os
from pathlib import Path, PurePath

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
    _register_extensions_for_agent,
    _remove_integration_json,
    _resolve_integration_options,
    _resolve_integration_script_type,
    _resolve_script_type,
    _set_default_integration,
    _set_default_integration_or_exit,
    _unregister_extensions_for_agent,
    _update_init_options_for_integration,
    _write_integration_json,
)


def _manifest_tracks_skill_layout(manifest) -> bool:
    """Return True when *manifest* tracks any skills-layout artifact.

    A skill scaffold is written as ``.../speckit-<name>/SKILL.md``, so a
    manifest whose tracked files include a ``/SKILL.md`` key is in the skills
    layout; otherwise it is in the command layout. Used by ``upgrade`` to
    detect a dual-mode agent (e.g. Bob) flipping between the legacy commands
    layout and the skills layout so orphaned extension artifacts from the old
    layout can be reconciled.
    """
    return any(str(rel).endswith("/SKILL.md") for rel in manifest.files)


class _PresetRegistryUnreadableError(Exception):
    """Raised when an existing preset registry cannot be read or parsed.

    Distinct from a *genuinely absent* registry (no presets installed): an
    unreadable registry means we cannot verify whether preset overrides would
    be orphaned by a layout change, so the migration must be rejected rather
    than proceeding on a false "no presets" assumption.
    """


def _installed_presets_affecting_agent(project_root, agent_key: str) -> list[str]:
    """Return IDs of installed presets with artifacts registered for *agent_key*.

    Presets register command overrides for every detected agent and mirror
    skills for the active skills agent, tracking the result in each preset's
    ``registered_commands`` / ``registered_skills`` metadata. There is no
    agent-scoped preset re-registration mechanism, so a command↔skills *layout
    change* cannot reconcile those artifacts (see ``integration_upgrade``).
    Callers use this to detect the unsafe case and reject the migration rather
    than silently orphaning preset files / leaving stale registry entries.

    Fails **closed**: a genuinely absent registry (no presets ever installed)
    returns an empty list, but if the registry file exists and cannot be read
    or parsed (e.g. a permission error or corruption) this raises
    :class:`_PresetRegistryUnreadableError`.  Reporting "no presets" in that
    case would let a ``--force`` layout-changing upgrade delete
    preset-overridden files while their registry state can't be reconciled —
    the exact inconsistency the guard exists to prevent.
    """
    from ..presets import PresetRegistry

    registry_path = (
        Path(project_root) / ".specify" / "presets" / PresetRegistry.REGISTRY_FILE
    )
    # Genuinely absent registry → no presets installed → safe to proceed.
    if not registry_path.exists():
        return []

    # The registry exists: any failure to read or parse it must surface as an
    # error, not be swallowed into an empty ("no presets") result.
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise _PresetRegistryUnreadableError(str(exc)) from exc
    if not isinstance(data, dict) or not isinstance(data.get("presets", {}), dict):
        raise _PresetRegistryUnreadableError(
            "preset registry structure is malformed"
        )

    affected: list[str] = []
    for preset_id, meta in data.get("presets", {}).items():
        # A malformed entry means we cannot verify whether this preset owns
        # artifacts for the agent, so fail closed rather than skip it.
        if not isinstance(meta, dict):
            raise _PresetRegistryUnreadableError(
                f"preset '{preset_id}' entry is malformed"
            )
        registered_commands = meta.get("registered_commands", {})
        if not isinstance(registered_commands, dict):
            raise _PresetRegistryUnreadableError(
                f"preset '{preset_id}' registered_commands is malformed"
            )
        registered_skills = meta.get("registered_skills", [])
        if not isinstance(registered_skills, (list, tuple)):
            raise _PresetRegistryUnreadableError(
                f"preset '{preset_id}' registered_skills is malformed"
            )
        has_commands = bool(registered_commands.get(agent_key))
        has_skills = bool(registered_skills)
        if has_commands or has_skills:
            affected.append(preset_id)
    return affected


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
        _unregister_extensions_for_agent(
            project_root,
            installed_key,
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
            target_integration, current, target, parsed_options,
            project_root=project_root,
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

    # Re-register extension commands for the new agent so previously-installed
    # extensions are available in it. Done after the try/except (the switch has
    # committed) so this best-effort step can never trigger the rollback above.
    _register_extensions_for_agent(
        project_root,
        target,
        continuing="The integration switch succeeded, but installed extensions may need re-registration.",
    )

    name = (target_integration.config or {}).get("name", target)
    console.print(f"\n[green]✓[/green] Switched to integration '{name}'")


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

    # Guard: reject a command↔skills layout change while preset overrides are
    # installed for this agent (review #3415).  A dual-mode agent (e.g. Bob)
    # can flip layout across an upgrade (``--skills`` / ``--legacy-commands``).
    # Extension artifacts are reconciled after the flip (see below), but preset
    # artifacts cannot be: there is no agent-scoped preset re-registration
    # anywhere in the CLI, so migrating would delete a preset's old-layout
    # files without recreating them in the new layout and leave the preset
    # registry claiming artifacts that no longer exist.  Detect the intended
    # layout (``is_skills_mode`` reflects the resolved flags/disk state, so a
    # plain same-layout upgrade is unaffected) and bail out *before* any
    # mutation with an actionable error so the project is never left in a
    # half-migrated, inconsistent state.
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
                "Preset artifacts cannot yet be reconciled across a command↔skills "
                "layout change, so the migration would orphan their files and leave "
                "the preset registry inconsistent."
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

    # Re-register enabled extensions for the upgraded agent so its extension
    # commands are (re)created — including agents installed before this
    # back-fill existed. Mirrors switch for command registration; see #2886.
    # Done after the upgrade has fully settled (Phase 2 included) and outside
    # the try/except above so this best-effort step cannot affect upgrade
    # success.
    #
    # Layout-change reconciliation: a dual-mode agent (e.g. Bob) can flip
    # between the legacy commands layout and the skills layout across an
    # upgrade (``upgrade bob --integration-options "--skills"`` / reverse
    # ``--legacy-commands``). Phase 2 above only removes stale files tracked by
    # the *integration* manifest (core commands); extension artifacts are
    # tracked separately in the extension registry, so the old layout's
    # extension command/skill files would otherwise linger as orphans. When the
    # layout actually changed, first unregister the agent's extension artifacts
    # (removing old-layout files and clearing per-agent registry entries) so the
    # re-registration below recreates them in the new layout. ``upgrade``s that
    # don't change layout skip this to avoid needless remove/re-add churn.
    #
    # Only the *active* integration is reconciled this way (``installed_key ==
    # key``).  ``ExtensionManager.unregister_agent_artifacts`` treats the
    # per-extension ``registered_skills`` list as belonging to the passed agent
    # and, when that agent's skills directory is absent, falls back to scanning
    # every agent's skills directory — so running it for a *secondary*
    # (non-active) agent could delete or untrack the *active* agent's extension
    # skills.  The subsequent re-registration cannot repair that because
    # extension skill rendering is intentionally scoped to the active agent
    # (#2948).  Extension skills only ever exist for the active agent, so
    # skipping the unregister for a secondary agent orphans nothing new: a
    # secondary agent only has extension *command* files, which the
    # re-registration below rewrites in place regardless of layout.
    #
    # Known limitation: preset command/skill artifacts are NOT reconciled on a
    # layout change. There is no agent-scoped preset re-registration mechanism
    # anywhere in the CLI — ``use`` / ``switch`` / ``upgrade`` never reconcile
    # presets for any agent (presets are only (un)registered at preset
    # install/remove time). Rather than silently orphan them, the guard near
    # the top of this function rejects a layout-changing upgrade while preset
    # overrides are installed, so control only reaches here (with a changed
    # layout) when no preset artifacts are at stake. Full preset reconciliation
    # would require a new cross-cutting PresetManager subsystem affecting every
    # dual-layout agent, which is out of scope for this Bob migration.
    if (
        installed_key == key
        and _manifest_tracks_skill_layout(old_manifest)
        != _manifest_tracks_skill_layout(new_manifest)
    ):
        _unregister_extensions_for_agent(
            project_root,
            key,
            continuing=(
                "The integration layout changed, but old-layout extension "
                "artifacts may need manual cleanup."
            ),
        )
    _register_extensions_for_agent(
        project_root,
        key,
        continuing="The integration was upgraded, but installed extensions may need re-registration.",
    )

    name = (integration.config or {}).get("name", key)
    console.print(f"\n[green]✓[/green] Integration '{name}' upgraded successfully")
