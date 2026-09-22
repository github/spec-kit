"""Transactional implementation supporting ``specify extension update``.

The registered CLI adapter lives in ``command_update.py``. Discovery and
archive preparation live in adjacent ``_command_update_*`` modules.
"""
from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
from uuid import uuid4

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from .._init_options import is_ai_skills_enabled
from . import _commands
from ._command_update_artifacts import preflight_update_archive
from ._command_update_discovery import discover_updates


def run_update_command(extension: str | None) -> None:
    """Run discovery, confirmation, and transactional extension updates."""
    from . import (
        ExtensionManager,
        ExtensionCatalog,
        ExtensionError,
        ValidationError,
        CommandRegistrar,
        HookExecutor,
        normalize_priority,
    )

    project_root = _commands._require_specify_project()
    manager = ExtensionManager(project_root)
    catalog = ExtensionCatalog(project_root)
    speckit_version = _commands.get_speckit_version()

    try:
        updates_available, blocked_updates, has_installed = discover_updates(
            manager, catalog, extension
        )
        if not has_installed:
            console.print("[yellow]No extensions installed[/yellow]")
            raise typer.Exit(0)

        if not updates_available:
            if blocked_updates:
                console.print(
                    "\n[yellow]Update(s) exist but require a newer spec-kit "
                    "release — upgrade spec-kit, then rerun "
                    "'specify extension update'.[/yellow]"
                )
            else:
                console.print("\n[green]All extensions are up to date![/green]")
            raise typer.Exit(0)

        # Show available updates
        console.print("\n[bold]Updates available:[/bold]\n")
        for update in updates_available:
            console.print(
                f"  • {_escape_markup(update.extension_id)}: "
                f"{update.installed} → {update.available}"
            )

        console.print()
        confirm = typer.confirm("Update these extensions?")
        if not confirm:
            console.print("Cancelled")
            raise typer.Exit(0)

        # Perform updates with atomic backup/restore
        console.print()
        updated_extensions = []
        failed_updates = []
        registrar = CommandRegistrar()
        hook_executor = HookExecutor(project_root)
        from ..agents import CommandRegistrar as _AgentReg  # used in backup and rollback paths

        # UNSET sentinel: backup not yet captured (exception before backup step)
        UNSET = object()

        for update in updates_available:
            extension_id = update.extension_id
            ext_name = update.name
            safe_ext_name = _escape_markup(str(ext_name))
            console.print(f"📦 Updating {safe_ext_name}...")

            # Backup paths
            backup_root = manager.extensions_dir / ".backup"
            backup_key = hashlib.sha256(
                extension_id.encode("utf-8")
            ).hexdigest()[:16]
            backup_base = (
                backup_root
                / f"update-{backup_key}-{uuid4().hex}"
            )
            backup_ext_dir = backup_base / "extension"
            backup_commands_dir = backup_base / "commands"
            backup_skills_dir = backup_base / "skills"
            backup_config_dir = backup_base / "config"

            # Store backup state
            backup_registry_entry = None  # None means registry entry not yet captured
            backup_installed = UNSET  # Original installed list from extensions.yml
            backup_hooks = None  # None means backup step 4 not yet reached; {} or {...} means backup was captured
            backed_up_command_files = {}
            backed_up_command_symlinks = {}
            backed_up_skill_dirs = {}
            new_command_dirs_absent_before_update = []
            new_command_paths_absent_before_update = []
            new_skill_names = []
            new_skill_paths_absent_before_update = []
            # Validation failures must not rewrite an untouched installation.
            installation_modified = False
            zip_cleanup_error = None
            backup_created_by_attempt = False

            def backup_command_artifact(original_file, backup_file):
                """Back up one command artifact once, preserving its full path."""
                nonlocal backup_created_by_attempt
                original_key = str(original_file)
                if original_key in backed_up_command_files:
                    return
                if original_file.is_symlink():
                    backed_up_command_symlinks[original_key] = os.readlink(
                        original_file
                    )
                else:
                    if original_file.stat().st_nlink > 1:
                        raise RuntimeError(
                            "Cannot safely update hard-linked generated "
                            f"artifact '{original_file}'"
                        )
                    backup_created_by_attempt = True
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(original_file, backup_file)
                backed_up_command_files[original_key] = str(backup_file)

            def restore_command_artifact(original_path, backup_path):
                """Restore one regular file or symlink without following it."""
                original_key = str(original_path)
                original_file = Path(original_path)
                backup_file = Path(backup_path)
                symlink_state = backed_up_command_symlinks.get(
                    original_key
                )

                if symlink_state is not None:
                    if original_file.is_symlink() or original_file.is_file():
                        original_file.unlink()
                    elif original_file.exists():
                        raise RuntimeError(
                            "Command rollback found an unexpected directory "
                            f"at '{original_file}'"
                        )
                    original_file.parent.mkdir(parents=True, exist_ok=True)
                    os.symlink(symlink_state, original_file)
                    return

                if not backup_file.is_file() or backup_file.is_symlink():
                    raise RuntimeError(
                        "Command rollback backup is missing for "
                        f"'{original_file}'"
                    )
                if original_file.is_symlink() or original_file.is_file():
                    original_file.unlink()
                elif original_file.exists():
                    raise RuntimeError(
                        "Command rollback found an unexpected directory "
                        f"at '{original_file}'"
                    )
                original_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_file, original_file)

            def remember_absent_parent_dirs(artifact_path, root_dir):
                """Remember absent parents a failed renderer may create."""
                boundary = root_dir.parent
                if root_dir.is_relative_to(project_root):
                    boundary = project_root
                parent = artifact_path.parent
                while parent != boundary:
                    if parent.exists() or parent.is_symlink():
                        break
                    new_command_dirs_absent_before_update.append(parent)
                    parent = parent.parent

            def backup_extension_skills(skill_names, *, skills_dir=None):
                """Back up every owned skill directory that remove() may delete."""
                nonlocal backup_created_by_attempt
                for skill_dir in manager._find_extension_skill_dirs(
                    skill_names,
                    extension_id,
                    skills_dir=skills_dir,
                    create_skills_dir=False,
                ):
                    original_key = str(skill_dir)
                    if original_key in backed_up_skill_dirs:
                        continue
                    backup_created_by_attempt = True
                    backup_skills_dir.mkdir(parents=True, exist_ok=True)
                    backup_skill_dir = backup_skills_dir / str(
                        len(backed_up_skill_dirs)
                    )
                    shutil.copytree(skill_dir, backup_skill_dir, symlinks=True)
                    backed_up_skill_dirs[original_key] = str(backup_skill_dir)

            try:
                if backup_root.is_symlink():
                    raise RuntimeError(
                        "Cannot safely create update backup under symlinked "
                        f"directory '{backup_root}'"
                    )
                if backup_base.exists() or backup_base.is_symlink():
                    raise RuntimeError(
                        "Cannot safely reuse an existing update backup "
                        f"directory '{backup_base}'"
                    )

                # 1. Backup registry entry (always, even if extension dir doesn't exist)
                backup_registry_entry = manager.registry.get(extension_id)

                # 2. Backup extension directory
                extension_dir = manager.extensions_dir / extension_id
                if extension_dir.exists():
                    backup_created_by_attempt = True
                    backup_base.mkdir(parents=True, exist_ok=True)
                    if backup_ext_dir.exists():
                        shutil.rmtree(backup_ext_dir)
                    shutil.copytree(extension_dir, backup_ext_dir)

                    # Backup config files separately so they can be restored
                    # after a successful install (install_from_directory clears dest dir).
                    config_files = list(extension_dir.glob("*-config.yml")) + list(
                        extension_dir.glob("*-config.local.yml")
                    )
                    for cfg_file in config_files:
                        backup_config_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(cfg_file, backup_config_dir / cfg_file.name)

                # 3. Backup command files for all agents
                registered_commands = backup_registry_entry.get("registered_commands", {}) if isinstance(backup_registry_entry, dict) else {}
                for agent_name, cmd_names in registered_commands.items():
                    if agent_name not in registrar.AGENT_CONFIGS:
                        continue
                    agent_config = registrar.AGENT_CONFIGS[agent_name]
                    commands_dir = _AgentReg._resolve_agent_dir(
                        agent_name, agent_config, project_root
                    )
                    dirs_to_backup = [commands_dir]
                    legacy = agent_config.get("legacy_dir")
                    if legacy:
                        legacy_dir = project_root / legacy
                        if (
                            legacy_dir.exists()
                            and legacy_dir != commands_dir
                        ):
                            dirs_to_backup.append(legacy_dir)

                    for cmd_name in cmd_names:
                        output_name = _AgentReg._compute_output_name(
                            agent_name, cmd_name, agent_config
                        )
                        names_to_backup = [output_name]
                        if (
                            output_name != cmd_name
                            and _AgentReg._is_safe_command_name(cmd_name)
                        ):
                            names_to_backup.append(cmd_name)

                        for dir_index, target_dir in enumerate(
                            dirs_to_backup
                        ):
                            for name in names_to_backup:
                                cmd_file = (
                                    target_dir
                                    / f"{name}{agent_config['extension']}"
                                )
                                try:
                                    _AgentReg._ensure_inside(
                                        cmd_file, target_dir
                                    )
                                except ValueError:
                                    continue
                                if (
                                    cmd_file.exists()
                                    or cmd_file.is_symlink()
                                ):
                                    # Keep both the directory location and
                                    # relative path unique. unregister_commands()
                                    # removes legacy and canonical copies, and
                                    # skills agents place every SKILL.md in its
                                    # own command subdirectory.
                                    backup_cmd_path = (
                                        backup_commands_dir
                                        / agent_name
                                        / f"location-{dir_index}"
                                        / cmd_file.relative_to(target_dir)
                                    )
                                    backup_command_artifact(
                                        cmd_file, backup_cmd_path
                                    )

                        # Also backup copilot prompt files
                        if agent_name == "copilot":
                            prompts_dir = (
                                project_root / ".github" / "prompts"
                            )
                            prompt_file = (
                                prompts_dir / f"{cmd_name}.prompt.md"
                            )
                            try:
                                _AgentReg._ensure_inside(
                                    prompt_file, prompts_dir
                                )
                            except ValueError:
                                continue
                            if prompt_file.exists() or prompt_file.is_symlink():
                                backup_prompt_path = (
                                    backup_commands_dir
                                    / "copilot-prompts"
                                    / prompt_file.relative_to(prompts_dir)
                                )
                                backup_command_artifact(
                                    prompt_file, backup_prompt_path
                                )

                raw_registered_skills = (
                    backup_registry_entry.get("registered_skills", [])
                    if isinstance(backup_registry_entry, dict)
                    else []
                )
                registered_skills = manager._valid_name_list(raw_registered_skills)
                backup_extension_skills(registered_skills)

                # 4. Backup hooks and installed list from extensions.yml
                # get_project_config() always normalizes installed->[] and hooks->{},
                # so no sentinel is needed to distinguish key-absent from key-empty.
                config = hook_executor.get_project_config()
                if isinstance(config, dict):
                    import copy
                    # Deep-copy so nested mapping entries (e.g. version-pin dicts)
                    # are not affected by in-place mutations during the update.
                    backup_installed = copy.deepcopy(config.get("installed", []))
                    backup_hooks = {}
                    for hook_name, hook_list in config.get("hooks", {}).items():
                        if not isinstance(hook_list, list):
                            continue
                        ext_hooks = [h for h in hook_list if isinstance(h, dict) and h.get("extension") == extension_id]
                        if ext_hooks:
                            backup_hooks[hook_name] = ext_hooks

                # 5. Acquire the new version. Bundled extensions install from
                # the copy shipped with the running spec-kit release (they
                # have no download URL); everything else downloads. Both are
                # packaged as archives so the identical validation,
                # backup/rollback, and install pipeline below applies.
                if update.bundled_dir is not None:
                    archive_path = _commands._archive_extension_directory(
                        update.bundled_dir
                    )
                else:
                    archive_path = catalog.download_extension(extension_id)
                try:
                    preflight = preflight_update_archive(
                        manager,
                        archive_path,
                        extension_id,
                        update.available,
                        speckit_version,
                    )
                    new_command_names = preflight.command_names
                    new_skill_names = preflight.skill_names

                    # Command rendering happens before hook registration and
                    # registry.add(). Preserve every candidate output that
                    # already exists, and remember paths that are absent now so
                    # rollback can remove files created before registry state is
                    # available. Include aliases and Copilot companion prompts.
                    for (
                        agent_name,
                        commands_dir,
                    ) in manager._command_registration_targets().items():
                        agent_config = registrar.AGENT_CONFIGS[agent_name]
                        for command_name in new_command_names:
                            output_name = _AgentReg._compute_output_name(
                                agent_name, command_name, agent_config
                            )
                            command_file = (
                                commands_dir
                                / f"{output_name}{agent_config['extension']}"
                            )
                            _AgentReg._ensure_inside(command_file, commands_dir)
                            backup_command_path = (
                                backup_commands_dir
                                / agent_name
                                / command_file.relative_to(commands_dir)
                            )
                            if command_file.exists() or command_file.is_symlink():
                                backup_command_artifact(
                                    command_file, backup_command_path
                                )
                            else:
                                new_command_paths_absent_before_update.append(
                                    command_file
                                )
                                remember_absent_parent_dirs(
                                    command_file, commands_dir
                                )

                            if agent_name == "copilot":
                                prompts_dir = (
                                    project_root / ".github" / "prompts"
                                )
                                prompt_file = (
                                    prompts_dir / f"{command_name}.prompt.md"
                                )
                                _AgentReg._ensure_inside(
                                    prompt_file, prompts_dir
                                )
                                if prompt_file.is_symlink():
                                    raise RuntimeError(
                                        "Cannot safely update symlinked Copilot "
                                        f"prompt artifact '{prompt_file}'"
                                    )
                                backup_prompt_path = (
                                    backup_commands_dir
                                    / "copilot-prompts"
                                    / prompt_file.relative_to(prompts_dir)
                                )
                                if (
                                    prompt_file.exists()
                                    or prompt_file.is_symlink()
                                ):
                                    backup_command_artifact(
                                        prompt_file, backup_prompt_path
                                    )
                                else:
                                    new_command_paths_absent_before_update.append(
                                        prompt_file
                                    )
                                    remember_absent_parent_dirs(
                                        prompt_file, prompts_dir
                                    )

                    new_command_paths_absent_before_update = list(
                        dict.fromkeys(
                            new_command_paths_absent_before_update
                        )
                    )
                    new_command_dirs_absent_before_update = list(
                        dict.fromkeys(
                            new_command_dirs_absent_before_update
                        )
                    )

                    # A newly introduced command may reuse an existing
                    # extension-owned skill directory that was not present in
                    # the old registry. Back it up before cleanup can touch it.
                    backup_extension_skills(new_skill_names)
                    new_skills_dir = manager._get_skills_dir(create=False)
                    if new_skills_dir is not None:
                        # Unscoped removal deliberately ignores home-scoped
                        # outputs because the flat registry cannot establish
                        # project ownership. The active install can still
                        # replace a marker-owned skill in its explicit root,
                        # so back up that exact project/home target separately.
                        backup_extension_skills(
                            list(
                                dict.fromkeys(
                                    registered_skills + new_skill_names
                                )
                            ),
                            skills_dir=new_skills_dir,
                        )
                        init_options = _commands.load_init_options(project_root)
                        if (
                            isinstance(init_options, dict)
                            and is_ai_skills_enabled(init_options)
                            and isinstance(init_options.get("ai"), str)
                            and init_options["ai"]
                        ):
                            # resolve_active_skills_dir() first creates the
                            # configured project-local skills marker. Some
                            # agents (notably Hermes) then redirect rendered
                            # skills to a different global root, so snapshot
                            # both locations for exact rollback.
                            from .. import _get_skills_dir

                            configured_skills_dir = _get_skills_dir(
                                project_root, init_options["ai"]
                            )
                            remember_absent_parent_dirs(
                                configured_skills_dir / ".update-marker",
                                configured_skills_dir,
                            )
                        new_skills_root = new_skills_dir.resolve()
                        for skill_name in new_skill_names:
                            skill_path = new_skills_dir / skill_name
                            resolved_skill_path = skill_path.resolve(strict=False)
                            resolved_skill_path.relative_to(new_skills_root)
                            if not (
                                skill_path.exists() or skill_path.is_symlink()
                            ):
                                new_skill_paths_absent_before_update.append(
                                    skill_path
                                )
                                remember_absent_parent_dirs(
                                    skill_path / "SKILL.md",
                                    new_skills_dir,
                                )

                    new_command_dirs_absent_before_update = list(
                        dict.fromkeys(
                            new_command_dirs_absent_before_update
                        )
                    )

                    # 7. Remove old extension (handles command file cleanup and registry removal)
                    installation_modified = True
                    manager.remove(extension_id, keep_config=True)

                    # 8. Install new version
                    _ = manager.install_from_zip(
                        archive_path,
                        speckit_version,
                        catalog_name=update.catalog_name,
                    )

                    # Restore user config files from backup after successful install.
                    new_extension_dir = manager.extensions_dir / extension_id
                    if backup_config_dir.exists() and new_extension_dir.exists():
                        for cfg_file in backup_config_dir.iterdir():
                            if cfg_file.is_file():
                                shutil.copy2(cfg_file, new_extension_dir / cfg_file.name)

                    # 9. Restore metadata from backup (installed_at, enabled state)
                    if backup_registry_entry and isinstance(backup_registry_entry, dict):
                        # Copy current registry entry to avoid mutating internal
                        # registry state before explicit restore().
                        current_metadata = manager.registry.get(extension_id)
                        if current_metadata is None or not isinstance(current_metadata, dict):
                            raise RuntimeError(
                                f"Registry entry for '{extension_id}' missing or corrupted after install — update incomplete"
                            )
                        new_metadata = dict(current_metadata)

                        # Preserve the original installation timestamp
                        if "installed_at" in backup_registry_entry:
                            new_metadata["installed_at"] = backup_registry_entry["installed_at"]

                        # Preserve the original priority (normalized to handle corruption)
                        if "priority" in backup_registry_entry:
                            new_metadata["priority"] = normalize_priority(backup_registry_entry["priority"])

                        # If extension was disabled before update, disable it again
                        if not backup_registry_entry.get("enabled", True):
                            new_metadata["enabled"] = False

                        # Use restore() instead of update() because update() always
                        # preserves the existing installed_at, ignoring our override
                        manager.registry.restore(extension_id, new_metadata)

                        # Also disable hooks in extensions.yml if extension was disabled
                        if not backup_registry_entry.get("enabled", True):
                            config = hook_executor.get_project_config()
                            if "hooks" in config:
                                for hook_name in config["hooks"]:
                                    for hook in config["hooks"][hook_name]:
                                        if hook.get("extension") == extension_id:
                                            hook["enabled"] = False
                                hook_executor.save_project_config(config)
                finally:
                    # Archive cleanup is housekeeping: never replace an install
                    # error or roll back an already committed update because a
                    # scanner temporarily locks the download on Windows.
                    try:
                        archive_path.unlink(missing_ok=True)
                    except OSError as error:
                        zip_cleanup_error = error

                # 10. Clean up backup on success. The update has committed at
                # this point, so a locked backup file must not trigger rollback
                # of an otherwise successful installation.
                cleanup_error = None
                if backup_created_by_attempt and backup_base.exists():
                    try:
                        shutil.rmtree(backup_base)
                    except OSError as error:
                        cleanup_error = error

                console.print(
                    f"   [green]✓[/green] Updated to v{update.available}"
                )
                if cleanup_error is not None:
                    console.print(
                        "   [yellow]Warning:[/yellow] Could not fully remove "
                        "update backup: "
                        f"{_escape_markup(str(cleanup_error))}"
                    )
                    console.print(
                        "   [dim]Backup may remain at: "
                        f"{_escape_markup(str(backup_base))}[/dim]"
                    )
                if zip_cleanup_error is not None:
                    console.print(
                        "   [yellow]Warning:[/yellow] Could not remove "
                        "downloaded update archive: "
                        f"{_escape_markup(str(zip_cleanup_error))}"
                    )
                updated_extensions.append(ext_name)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                console.print(f"   [red]✗[/red] Failed: {_escape_markup(str(e))}")
                failed_updates.append((ext_name, str(e)))
                if zip_cleanup_error is not None:
                    console.print(
                        "   [yellow]Warning:[/yellow] Could not remove "
                        "downloaded update archive: "
                        f"{_escape_markup(str(zip_cleanup_error))}"
                    )

                if not installation_modified:
                    if backup_created_by_attempt and backup_base.exists():
                        try:
                            shutil.rmtree(backup_base)
                        except OSError as cleanup_error:
                            console.print(
                                "   [yellow]Warning:[/yellow] Could not remove "
                                "untouched-update backup: "
                                f"{_escape_markup(str(cleanup_error))}"
                            )
                    continue

                # Rollback on failure
                console.print(f"   [yellow]↩[/yellow] Rolling back {safe_ext_name}...")

                try:
                    # Restore extension directory
                    # Only perform destructive rollback if backup exists (meaning we
                    # actually modified the extension). This avoids deleting a valid
                    # installation when failure happened before changes were made.
                    extension_dir = manager.extensions_dir / extension_id
                    if backup_ext_dir.exists():
                        if extension_dir.exists():
                            shutil.rmtree(extension_dir)
                        shutil.copytree(backup_ext_dir, extension_dir)

                    # Remove any NEW command files created by failed install
                    # (files that weren't in the original backup). Registration
                    # writes before registry.add(), so start with the paths that
                    # were absent at the destructive boundary instead of relying
                    # only on a possibly missing new registry entry.
                    for command_path in new_command_paths_absent_before_update:
                        if command_path.is_symlink() or command_path.is_file():
                            command_path.unlink()
                        elif command_path.exists():
                            raise RuntimeError(
                                "Command rollback found an unexpected directory "
                                f"at '{command_path}'"
                            )
                    new_registered_skills = []
                    try:
                        new_registry_entry = manager.registry.get(extension_id)
                        if new_registry_entry is None or not isinstance(new_registry_entry, dict):
                            new_registered_commands = {}
                        else:
                            new_registered_commands = new_registry_entry.get("registered_commands", {})
                            new_registered_skills = manager._valid_name_list(
                                new_registry_entry.get("registered_skills", [])
                            )
                        for agent_name, cmd_names in new_registered_commands.items():
                            if agent_name not in registrar.AGENT_CONFIGS:
                                continue
                            agent_config = registrar.AGENT_CONFIGS[agent_name]
                            commands_dir = _AgentReg._resolve_agent_dir(
                                agent_name, agent_config, project_root
                            )

                            for cmd_name in cmd_names:
                                output_name = _AgentReg._compute_output_name(agent_name, cmd_name, agent_config)
                                cmd_file = commands_dir / f"{output_name}{agent_config['extension']}"
                                # Delete if it exists and wasn't in our backup
                                if cmd_file.exists() and str(cmd_file) not in backed_up_command_files:
                                    cmd_file.unlink()

                                # Also handle copilot prompt files
                                if agent_name == "copilot":
                                    prompt_file = project_root / ".github" / "prompts" / f"{cmd_name}.prompt.md"
                                    if prompt_file.exists() and str(prompt_file) not in backed_up_command_files:
                                        prompt_file.unlink()
                    except KeyError:
                        pass  # No new registry entry exists, nothing to clean up

                    # Restore command artifacts that existed before the update
                    # before extension-skill cleanup inspects ownership. A
                    # failed skills registrar may have overwritten a user's
                    # pre-existing SKILL.md with extension metadata; restoring
                    # it first prevents the conservative skill unregistrar from
                    # misclassifying and deleting the user's whole directory.
                    for original_path, backup_path in backed_up_command_files.items():
                        restore_command_artifact(
                            original_path, backup_path
                        )

                    # Skill generation happens before hooks and registry.add(),
                    # so a failed install may have created skills that are not
                    # recorded in any registry entry yet. Derive names from the
                    # preflighted manifest as well as any partial new entry.
                    skills_to_remove = list(
                        dict.fromkeys(new_skill_names + new_registered_skills)
                    )
                    # A write failure can leave a partial skill without valid
                    # ownership metadata, which the normal conservative
                    # unregistrar intentionally refuses to delete. Paths that
                    # were absent at the destructive boundary are safe to
                    # remove directly during rollback.
                    for skill_path in new_skill_paths_absent_before_update:
                        if skill_path.is_symlink() or skill_path.is_file():
                            skill_path.unlink()
                        elif skill_path.exists():
                            shutil.rmtree(skill_path)
                    manager._unregister_extension_skills(
                        skills_to_remove, extension_id
                    )

                    # Restore all original registered skill artifacts after
                    # removing skills created by the failed installation.
                    for original_path, backup_path in backed_up_skill_dirs.items():
                        backup_skill_dir = Path(backup_path)
                        if not backup_skill_dir.is_dir():
                            raise RuntimeError(
                                "Skill rollback backup is missing for "
                                f"'{original_path}'"
                            )
                        original_skill_dir = Path(original_path)
                        if (
                            original_skill_dir.is_symlink()
                            or original_skill_dir.is_file()
                        ):
                            original_skill_dir.unlink()
                        elif original_skill_dir.exists():
                            shutil.rmtree(original_skill_dir)
                        original_skill_dir.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copytree(
                            backup_skill_dir,
                            original_skill_dir,
                            symlinks=True,
                        )

                    # Remove empty artifact directories that did not exist at
                    # the destructive boundary. Do this after skill cleanup and
                    # restoration so newly created skills roots and their
                    # project-local parents can also be removed exactly.
                    for command_dir in sorted(
                        new_command_dirs_absent_before_update,
                        key=lambda path: len(path.parts),
                        reverse=True,
                    ):
                        if command_dir.is_dir() and not command_dir.is_symlink():
                            try:
                                command_dir.rmdir()
                            except OSError:
                                # Preserve any non-empty directory: other
                                # content may belong to the user.
                                pass

                    # Restore metadata in extensions.yml (hooks and installed list).
                    # Only run if backup step 4 was reached (backup_hooks is not None);
                    # otherwise we have no safe baseline to restore from and could corrupt
                    # the config by removing pre-existing hooks.
                    if backup_hooks is not None:
                        config = hook_executor.get_project_config()
                        if not isinstance(config, dict):
                            config = {}

                        modified = False

                        # 1. Restore hooks in extensions.yml
                        if not isinstance(config.get("hooks"), dict):
                            config["hooks"] = {}
                            modified = True

                        # Remove any hooks for this extension added by the failed install
                        for hook_name in list(config["hooks"].keys()):
                            hooks_list = config["hooks"][hook_name]
                            if not isinstance(hooks_list, list):
                                config["hooks"][hook_name] = []
                                modified = True
                                continue

                            original_len = len(hooks_list)
                            config["hooks"][hook_name] = [
                                h for h in hooks_list
                                if isinstance(h, dict) and h.get("extension") != extension_id
                            ]
                            if len(config["hooks"][hook_name]) != original_len:
                                modified = True

                        # Add back the backed-up hooks
                        if backup_hooks:
                            for hook_name, hooks in backup_hooks.items():
                                if not isinstance(config["hooks"].get(hook_name), list):
                                    config["hooks"][hook_name] = []
                                config["hooks"][hook_name].extend(hooks)
                                modified = True

                        # 2. Restore installed list in extensions.yml
                        if backup_installed is not UNSET:
                            if config.get("installed") != backup_installed:
                                config["installed"] = backup_installed
                                modified = True

                        if modified:
                            hook_executor.save_project_config(config)

                    # Restore registry entry (use restore() since entry was removed)
                    if backup_registry_entry:
                        manager.registry.restore(extension_id, backup_registry_entry)

                    # Backup cleanup is post-rollback housekeeping. A locked
                    # file (notably on Windows) must not turn successfully
                    # restored state into a contradictory "Rollback failed".
                    cleanup_error = None
                    if backup_created_by_attempt and backup_base.exists():
                        try:
                            shutil.rmtree(backup_base)
                        except OSError as error:
                            cleanup_error = error
                    console.print("   [green]✓[/green] Rollback successful")
                    if cleanup_error is not None:
                        console.print(
                            "   [yellow]Warning:[/yellow] Could not fully "
                            "remove rollback backup: "
                            f"{_escape_markup(str(cleanup_error))}"
                        )
                        console.print(
                            "   [dim]Backup may remain at: "
                            f"{_escape_markup(str(backup_base))}[/dim]"
                        )
                except Exception as rollback_error:
                    console.print(f"   [red]✗[/red] Rollback failed: {_escape_markup(str(rollback_error))}")
                    console.print(f"   [dim]Backup preserved at: {_escape_markup(str(backup_base))}[/dim]")

        # Summary
        console.print()
        if updated_extensions:
            console.print(f"[green]✓[/green] Successfully updated {len(updated_extensions)} extension(s)")
        if failed_updates:
            console.print(f"[red]✗[/red] Failed to update {len(failed_updates)} extension(s):")
            for ext_name, error in failed_updates:
                console.print(f"   • {_escape_markup(str(ext_name))}: {_escape_markup(str(error))}")
            raise typer.Exit(1)

        # S4: regenerate native event config after a successful update. An
        # update replaces the installed extension.yml, so any added/removed/
        # changed event declarations would otherwise leave native configs
        # stale until a manual integration upgrade.
        if updated_extensions:
            _commands._refresh_events_and_warn(project_root)

    except ValidationError as e:
        console.print(f"\n[red]Validation Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)
    except ExtensionError as e:
        console.print(f"\n[red]Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)
