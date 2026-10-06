"""Exact pre-mutation artifact snapshots shared by preset transactions."""

from pathlib import Path
import shutil
import tempfile


class _ArtifactSnapshot:
    """Back up exact artifact trees, including absent paths and symlinks."""

    def __init__(self):
        self._temp = tempfile.TemporaryDirectory(prefix="preset-transaction-")
        self._paths = {}
        self._absent_parents = set()

    def capture(self, path):
        path = Path(path)
        for parent in path.parents:
            if parent.exists():
                break
            self._absent_parents.add(parent)
        if path in self._paths:
            return
        backup = Path(self._temp.name) / str(len(self._paths))
        if path.is_symlink():
            backup.symlink_to(path.readlink())
        elif path.is_dir():
            shutil.copytree(path, backup, symlinks=True)
        elif path.exists():
            shutil.copy2(path, backup)
        self._paths[path] = backup

    def restore(self):
        errors = []
        for path, backup in self._paths.items():
            try:
                if path.is_symlink() or path.is_file():
                    path.unlink()
                elif path.exists():
                    shutil.rmtree(path)
                if backup.is_symlink():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.symlink_to(backup.readlink())
                elif backup.is_dir():
                    shutil.copytree(backup, path, symlinks=True)
                elif backup.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup, path)
            except OSError as exc:
                errors.append(f"{path}: {exc}")
        for parent in sorted(
            self._absent_parents, key=lambda p: len(p.parts), reverse=True
        ):
            if parent.is_dir():
                try:
                    parent.rmdir()
                except OSError as exc:
                    errors.append(f"{parent}: {exc}")
        if errors:
            raise OSError("Could not restore preset artifacts: " + "; ".join(errors))

    def close(self):
        self._temp.cleanup()


def _capture_preset_artifacts(manager, snapshot, extra_commands=()):
    """Use registrar/skill directory resolution, not a second selector parser."""
    from ..agents import CommandRegistrar
    from ..shared_infra import _validate_safe_shared_directory

    root = manager.project_root
    # Registries contain ownership updates for winners other than the reordered
    # preset too. Constitution bytes and provenance must move together.
    snapshot.capture(manager.registry.registry_path)
    snapshot.capture(root / ".specify" / "extensions" / ".registry")
    snapshot.capture(root / ".specify" / "memory")
    snapshot.capture(root / ".github" / "prompts")
    for pack_id in manager.registry.keys():  # noqa: SIM118 - registry is not a mapping
        snapshot.capture(manager.presets_dir / pack_id / ".composed")
    registrar = CommandRegistrar(root)
    for agent, config in registrar.AGENT_CONFIGS.items():
        if config.get("extension") == "/SKILL.md":
            continue
        directory = registrar._resolve_agent_dir(agent, config, root)
        if directory.is_relative_to(root):
            _validate_safe_shared_directory(root, directory)
            snapshot.capture(directory)
        legacy = config.get("legacy_dir")
        if legacy:
            directory = root / legacy
            _validate_safe_shared_directory(root, directory)
            snapshot.capture(directory)
    # Native and skills-mode output roots can be global.
    from .. import load_init_options

    opts = load_init_options(root)
    agents = {opts.get("ai")} if isinstance(opts, dict) else set()
    if not opts:
        # Legacy projects detect every existing integration during registration.
        agents.update(registrar.AGENT_CONFIGS)
    for metadata in manager.registry.list().values():
        commands = metadata.get("registered_commands")
        if isinstance(commands, dict):
            agents.update(commands)
        skills = metadata.get("registered_skills")
        if isinstance(skills, dict):
            agents.update(skills)
    for agent in agents:
        if not isinstance(agent, str) or agent == "generic":
            continue
        directory = manager._resolve_agent_skills_dir(agent)
        validation_root = manager._skills_validation_root(directory)
        if validation_root is None:
            continue
        _validate_safe_shared_directory(validation_root, directory)
        if directory.is_relative_to(root):
            snapshot.capture(directory)
        else:
            from ..artifacts import ArtifactCatalog
            from ..extensions import CORE_COMMAND_NAMES

            names = {f"speckit.{name}" for name in CORE_COMMAND_NAMES}
            names.update(extra_commands)
            names.update(
                artifact.name
                for artifact in ArtifactCatalog(root).list_artifacts()
                if artifact.kind == "command"
            )
            candidates = {
                skill
                for name in names
                for skill in manager._skill_names_for_command(name)
                if manager._is_safe_registry_skill_name(skill)
            }
            if directory.is_dir():
                candidates.update(
                    child.name
                    for child in directory.iterdir()
                    if child.name.startswith(("speckit-", "speckit."))
                )
            for metadata in manager.registry.list().values():
                recorded = metadata.get("registered_skills")
                lists = recorded.values() if isinstance(recorded, dict) else [recorded]
                for values in lists:
                    if isinstance(values, list):
                        candidates.update(
                            name
                            for name in values
                            if manager._is_safe_registry_skill_name(name)
                        )
            for name in candidates:
                snapshot.capture(directory / name)
