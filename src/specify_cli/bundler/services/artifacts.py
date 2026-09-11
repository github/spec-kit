"""Component-scoped preimages of manager-generated outputs and backups."""
from __future__ import annotations

import os
import shutil
from contextlib import ExitStack
from pathlib import Path
from typing import TYPE_CHECKING

from ..._init_options import MISSING_INIT_OPTIONS_FILE, resolve_active_agent_for_registration
from ...agents import CommandRegistrar
from ...shared_infra import _validate_safe_shared_directory
from .. import BundlerError
from ..models.snapshot import ArtifactSnapshot, ComponentSnapshot

if TYPE_CHECKING:
    from ...extensions import ExtensionManager
    from ...presets import PresetManager


def snapshot_generated_artifacts(
    snapshot: ComponentSnapshot,
    project_root: Path,
    manager: PresetManager | ExtensionManager,
) -> ComponentSnapshot:
    from ...presets import PresetManager

    with ExitStack() as cleanup:
        cleanup.callback(snapshot.close)
        registrar = CommandRegistrar()
        recorded = snapshot.metadata.get("registered_commands", {})
        if not isinstance(recorded, dict) or any(
            not isinstance(agent, str) or not isinstance(names, list)
            or any(not isinstance(name, str) for name in names)
            for agent, names in recorded.items()
        ):
            raise BundlerError(f"Invalid command provenance for {snapshot.component.label()}.")
        commands = {agent: list(names) for agent, names in recorded.items()}
        resolved = resolve_active_agent_for_registration(project_root)
        active = resolved if isinstance(resolved, str) else None
        if resolved is MISSING_INIT_OPTIONS_FILE:
            targets = [
                agent for agent, config in registrar.AGENT_CONFIGS.items()
                if (not config.get("detect_dir") or (project_root / config["detect_dir"]).is_dir())
                and registrar._resolve_agent_dir(agent, config, project_root).is_dir()
            ]
        else:
            targets = [active] if active is not None and active in registrar.AGENT_CONFIGS else []
        is_preset = isinstance(manager, PresetManager)
        if isinstance(manager, PresetManager):
            manifest = manager.get_pack(snapshot.component.id)
            definitions = (
                [entry for entry in manifest.templates if entry.get("type") == "command"]
                if manifest is not None else []
            )
        else:
            manifest = manager.get_extension(snapshot.component.id)
            definitions = manifest.commands if manifest is not None else []
        if manifest is None:
            raise BundlerError(f"Missing installed manifest for {snapshot.component.label()}.")
        provided_names = {
            name for definition in definitions
            for name in [definition["name"], *definition.get("aliases", [])]
        }
        for target in targets:
            commands.setdefault(target, []).extend(sorted(provided_names))

        paths = {
            path.parent if path.name == "SKILL.md" else path
            for path, _ in registrar.iter_command_artifacts(commands, project_root)
        }
        skills = snapshot.metadata.get("registered_skills", {} if is_preset else [])
        if isinstance(manager, PresetManager):
            if isinstance(skills, list):
                skills = manager._infer_legacy_skill_provenance(
                    skills, snapshot.component.id, fallback_agent=active or ""
                )
            for agent, names in skills.items():
                directory = manager._safe_skills_dir_for_agent(agent)
                if directory is not None:
                    paths.update(
                        directory / name for name in names
                        if manager._is_safe_registry_skill_name(name)
                    )
            active_skills = manager._resolve_agent_skills_dir(active) if active else None
        else:
            paths.add(manager.extensions_dir / ".backup" / snapshot.component.id)
            paths.update(manager._find_extension_skill_dirs(
                skills, snapshot.component.id, create_skills_dir=False
            ))
            active_skills = manager._get_skills_dir(create=False)
        if active_skills is not None:
            paths.update(
                active_skills / name
                for command in provided_names
                for name in PresetManager._skill_names_for_command(command)
            )

        if snapshot.directory is None:
            raise BundlerError(f"Missing payload snapshot for {snapshot.component.label()}.")
        artifact_backup = snapshot.directory.parent / ".artifacts"
        artifact_backup.mkdir()
        roots = (Path(os.path.abspath(project_root)), Path.home())
        captured: list[Path] = []
        for path in sorted({Path(os.path.abspath(p)) for p in paths}, key=lambda p: (len(p.parts), str(p))):
            if any(path.is_relative_to(parent) for parent in captured):
                continue
            root = next((root for root in roots if path.is_relative_to(root)), None)
            if root is None:
                raise BundlerError(f"Artifact is outside the project and home roots: {path}")
            _validate_safe_shared_directory(root, path.parent)
            backup = None
            if path.exists() or path.is_symlink():
                backup = artifact_backup / str(len(captured))
                if path.is_dir():
                    _validate_safe_shared_directory(root, path)
                    shutil.copytree(path, backup, symlinks=True)
                else:
                    shutil.copy2(path, backup, follow_symlinks=False)
            parent = path.parent
            while parent != root and not parent.exists():
                snapshot.absent_artifact_parents.add((root, parent))
                parent = parent.parent
            snapshot.artifacts.append(ArtifactSnapshot(path, backup, root))
            captured.append(path)
        cleanup.pop_all()
    return snapshot


def restore_generated_artifacts(snapshot: ComponentSnapshot) -> None:
    for artifact in snapshot.artifacts:
        path = artifact.path
        _validate_safe_shared_directory(artifact.trusted_root, path.parent)
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.exists():
            shutil.rmtree(path)
        if artifact.backup is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            if artifact.backup.is_dir() and not artifact.backup.is_symlink():
                shutil.copytree(artifact.backup, path, symlinks=True)
            else:
                shutil.copy2(artifact.backup, path, follow_symlinks=False)
    for root, parent in sorted(
        snapshot.absent_artifact_parents, key=lambda entry: len(entry[1].parts), reverse=True
    ):
        _validate_safe_shared_directory(root, parent)
        if parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
