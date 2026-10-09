"""Implementation of ``specify extension disable``.

Registered by ``_commands.register()``; shared command infrastructure lives in
``_commands.py``.
"""

from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import _commands


def _disable_hooks(hook_executor, extension_id):
    """Flip every hook owned by *extension_id* to disabled in extensions.yml."""
    config = hook_executor.get_project_config()
    if "hooks" not in config:
        return
    for hook_name in config["hooks"]:
        for hook in config["hooks"][hook_name]:
            if hook.get("extension") == extension_id:
                hook["enabled"] = False
    hook_executor.save_project_config(config)


def _capture_disabled_agent_roots(
    snapshot,
    manager,
    preset_manager,
    project_root,
    extension_id,
    historical_agents,
) -> None:
    """Snapshot every directory this extension's own agents are stripped from.

    ``_capture_preset_artifacts`` derives its agent set from preset ownership,
    so an extension-only agent (for example a native-skill integration that
    never received a preset artifact) would be missed and its files deleted
    without a backup. Capture the resolved command and skill roots for each
    historical agent, including the global skill roots of skills-mode agents.
    """
    from ..agents import CommandRegistrar

    registrar = CommandRegistrar(project_root)
    manifest = manager.get_extension(extension_id)
    for historical_agent in sorted(historical_agents):
        if not historical_agent or historical_agent == "generic":
            continue
        agent_config = registrar.AGENT_CONFIGS.get(historical_agent)
        if agent_config and agent_config.get("extension") != "/SKILL.md":
            directory = registrar._resolve_agent_dir(
                historical_agent, agent_config, project_root
            )
            if directory.is_relative_to(project_root):
                snapshot.capture(directory)
        skills_dir = preset_manager._resolve_agent_skills_dir(historical_agent)
        if skills_dir is None:
            continue
        if skills_dir.is_relative_to(project_root):
            snapshot.capture(skills_dir)
        elif manifest is not None:
            # Global skill root outside the project: capture exactly the
            # concrete skill directories this extension can own, never a
            # raw regex selector name.
            for name in _commands._snapshot_command_candidates(manager, manifest):
                for skill in preset_manager._skill_names_for_command(name):
                    if preset_manager._is_safe_registry_skill_name(skill):
                        snapshot.capture(skills_dir / skill)


@_commands.extension_app.command("disable")
def extension_disable(
    extension: str = typer.Argument(help="Extension ID or name to disable"),
):
    """Disable an extension without removing it."""
    from . import ExtensionManager, HookExecutor

    project_root = _commands._require_specify_project()
    manager = ExtensionManager(project_root)
    hook_executor = HookExecutor(project_root)

    # Resolve extension ID from argument (handles ambiguous names)
    installed = manager.list_installed()
    extension_id, display_name = _commands._resolve_installed_extension(
        extension, installed, "disable"
    )

    # Update registry
    metadata = manager.registry.get(extension_id)
    if not extension_id or metadata is None or not isinstance(metadata, dict):
        console.print(
            f"[red]Error:[/red] Extension '{_escape_markup(str(extension_id))}' "
            "not found in registry (corrupted state)"
        )
        raise typer.Exit(1)

    if not metadata.get("enabled", True):
        console.print(
            f"[yellow]Extension '{_escape_markup(str(display_name))}' is already disabled[/yellow]"
        )
        raise typer.Exit(0)

    affected_commands = _commands._capture_preset_command_names(project_root)

    from .. import load_init_options

    agent = load_init_options(project_root).get("ai")
    refresh_presets_after_commit = False
    if agent == "generic":
        from . import ExtensionError

        try:
            manager.disable_generic_extension_artifacts(extension_id)
        except (ExtensionError, ValueError, OSError) as exc:
            console.print(f"[red]Error:[/red] {_escape_markup(str(exc))}")
            raise typer.Exit(1) from exc
        _disable_hooks(hook_executor, extension_id)
        # The generic integration publishes extension invocations only — it
        # never registers preset command or skill overrides — so its selector
        # refresh keeps the pre-existing best-effort contract.
        refresh_presets_after_commit = True
    else:
        # Cleanup mutates several agents' artifacts, both registries, and the
        # hook config, and it changes which lower layer preset selectors can
        # match. A failure part-way through must not leave the extension
        # enabled with the earlier agents already stripped, nor disabled with
        # artifacts still composed from its layer, so snapshot every touched
        # destination first, reconcile selectors strictly inside the same
        # transaction, and restore everything as a unit on error.
        import copy

        from ..presets import PresetManager
        from ..presets._transaction import _ArtifactSnapshot, _capture_preset_artifacts

        registered = metadata.get("registered_commands", {})
        historical_agents = set(registered) if isinstance(registered, dict) else set()
        if agent:
            historical_agents.add(agent)
        preset_manager = PresetManager(project_root)
        registry_before = copy.deepcopy(manager.registry.data)
        snapshot = _ArtifactSnapshot()
        captured = False
        try:
            _capture_preset_artifacts(preset_manager, snapshot)
            snapshot.capture(project_root / ".specify" / "extensions.yml")
            _capture_disabled_agent_roots(
                snapshot,
                manager,
                preset_manager,
                project_root,
                extension_id,
                historical_agents,
            )
            captured = True
            # Remove each agent's tracked artifacts before flipping enabled so a
            # rollback restores the exact prior ownership state.
            for historical_agent in sorted(historical_agents):
                manager.unregister_agent_artifacts(
                    historical_agent, extension_ids={extension_id}
                )
            manager.registry.update(extension_id, {"enabled": False})
            _disable_hooks(hook_executor, extension_id)
            # Selector-backed outputs are part of this state change: reconcile
            # strictly before committing so a failed reconciliation rolls the
            # disable back instead of leaving a preset-generated command or
            # skill composed from the now-ineligible provider layer.
            _commands._refresh_presets_and_warn(
                project_root, affected_commands, strict=True
            )
        except BaseException as exc:
            manager.registry.data = registry_before
            try:
                if captured:
                    snapshot.restore()
            except Exception as rollback_exc:
                exc.add_note(f"Extension disable rollback failed: {rollback_exc}")
            console.print(
                f"[red]Error:[/red] Could not disable "
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
                        f"Extension disable snapshot cleanup failed: {cleanup_exc}"
                    )
                else:
                    raise

    console.print(
        f"[green]✓[/green] Extension '{_escape_markup(str(display_name))}' disabled"
    )
    console.print("\nCommands will no longer be available. Hooks will not execute.")
    console.print(
        f"To re-enable: specify extension enable {_escape_markup(str(extension_id))}"
    )

    # #1: regenerate native event config so the disabled extension's events
    # are stripped from installed integrations. Preset selector reconciliation
    # already ran inside the disable transaction above.
    _commands._refresh_events_and_warn(project_root)
    if refresh_presets_after_commit:
        _commands._refresh_presets_and_warn(project_root, affected_commands)
