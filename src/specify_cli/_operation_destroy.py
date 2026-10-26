"""Project-local uninstall planning and execution, independent of delivery adapters."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any

from ._file_policy import project_files, read_project_options
from ._utils import same_path_entry
from .file_helper import FileHelper, FileHelperError
from .integration_state import (
    default_integration_key,
    installed_integration_keys,
    normalize_integration_state,
)
from .integrations.manifest import IntegrationManifest

CONSTITUTION = ".specify/memory/constitution.md"


@dataclass(frozen=True)
class DestroyRequest:
    project_directory: Path
    confirmed: bool = False
    force: bool = False
    dry_run: bool = False
    preserve_constitution: bool = False
    preserve_specs: bool = False
    preserve_all: bool = False

    @property
    def preserved_paths(self) -> tuple[str, ...]:
        paths = []
        if self.preserve_constitution or self.preserve_all:
            paths.append(CONSTITUTION)
        if self.preserve_specs or self.preserve_all:
            paths.append("specs")
        return tuple(paths)


@dataclass(frozen=True)
class DestroyPlan:
    project_directory: Path
    files: tuple[str, ...]
    directories: tuple[str, ...]
    preserved: tuple[str, ...]
    requires_force: tuple[str, ...]
    integrations: tuple[str, ...] = ()
    updated: tuple[str, ...] = ()
    contribution_agents: tuple[str, ...] = ()
    global_scopes: tuple[str, ...] = ()
    global_files: tuple[str, ...] = ()


@dataclass(frozen=True)
class DestroyResult:
    project_directory: str
    dry_run: bool
    removed: tuple[str, ...]
    preserved: tuple[str, ...]
    requires_force: tuple[str, ...] = ()
    directories: tuple[str, ...] = ()
    updated: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    global_scopes: tuple[str, ...] = ()
    global_files: tuple[str, ...] = ()


class DestroyError(ValueError):
    """An expected uninstall failure, with any completed mutations made explicit."""

    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.retryable = False


def _relative(root: Path, path: Path, *, allow_specs: bool = False) -> str:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Destroy cannot remove non-project path: {path}") from exc
    text = relative.as_posix()
    if (
        text in {"", "."}
        or ".." in relative.parts
        or "\\" in text
        or PureWindowsPath(text).drive
        or relative.parts[0].casefold() == ".git"
        or (
            relative.parts[0].casefold() == "specs"
            and not (allow_specs and relative.parts[0] == "specs")
        )
    ):
        raise ValueError(f"Unsafe destroy path: {text}")
    return text


def _read_json(files: FileHelper, relative: str) -> dict[str, Any] | None:
    try:
        text = files.read_text(relative)
    except FileNotFoundError:
        return None
    value = json.loads(text)
    if not isinstance(value, dict):
        raise TypeError(f"{relative} must contain a JSON object")
    return value


def _tree(
    files: FileHelper, relative: str, *, preserve_constitution: bool = False,
) -> tuple[set[str], set[str]]:
    """Inventory a selected tree without traversing descendant symlinks."""
    leaves: set[str] = set()
    directories: set[str] = set()
    path = files.root / relative
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return leaves, directories
    # Validate all ancestors through the helper before inspecting the leaf.
    parent = path.parent
    while parent != files.root:
        if parent.is_symlink():
            raise FileHelperError(f"Refusing destroy through symlinked directory: {parent}")
        parent = parent.parent

    entry = path.lstat()
    if (
        getattr(entry, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
        and not stat.S_ISLNK(mode)
    ):
        raise FileHelperError(f"Unsupported reparse point: {relative}")
    if stat.S_ISLNK(mode):
        if preserve_constitution and same_path_entry(path, files.root / ".specify/memory"):
            raise FileHelperError("Cannot preserve constitution through symlinked .specify/memory")
        if not files.allow_symlinks:
            raise FileHelperError(f"Refusing symlink during destroy: {relative}")
        leaves.add(relative)
    elif stat.S_ISREG(mode):
        files.read_bytes(relative)
        leaves.add(relative)
    elif stat.S_ISDIR(mode):
        with os.scandir(path) as entries:
            children = sorted(entry.name for entry in entries)
        for name in children:
            child = f"{relative}/{name}"
            if preserve_constitution and same_path_entry(files.root / child, files.root / CONSTITUTION):
                if not (path / name).is_file() and not (path / name).is_symlink():
                    raise ValueError(f"{CONSTITUTION} must be a file")
                continue
            child_files, child_dirs = _tree(
                files, child, preserve_constitution=preserve_constitution,
            )
            leaves.update(child_files)
            directories.update(child_dirs)
        directories.add(relative)
    else:
        raise FileHelperError(f"Unsupported filesystem object: {relative}")
    return leaves, directories


def _project_artifacts(
    files: FileHelper, request: DestroyRequest,
) -> tuple[set[str], set[str], tuple[str, ...]]:
    selected = request.preserved_paths
    leaves, directories = _tree(
        files, ".specify", preserve_constitution=CONSTITUTION in selected,
    )
    preserved = tuple(
        name for name in selected
        if (files.root / name).exists() or (files.root / name).is_symlink()
    )
    if CONSTITUTION in preserved:
        directories = _without_constitution_parents(files.root, directories)
    if "specs" not in selected:
        specs = files.root / "specs"
        if specs.exists() and not specs.is_dir() and not specs.is_symlink():
            raise ValueError("specs must be a directory; refusing to remove a non-directory specs entry")
        spec_files, spec_directories = _tree(files, "specs")
        leaves.update(spec_files)
        directories.update(spec_directories)
    return leaves, directories, preserved


def _without_constitution_parents(root: Path, directories: set[str]) -> set[str]:
    return {
        name for name in directories
        if not any(same_path_entry(root / name, root / ancestor) for ancestor in (".specify", ".specify/memory"))
    }


def _contribution_paths(
    root: Path, metadata_files: FileHelper, files: FileHelper, bindings: dict[str, dict | None],
    global_scopes: dict[str, Path],
) -> tuple[set[Path], dict[str, set[str]], set[str], set[Path]]:
    from .agents import CommandRegistrar
    from .integrations import BUILTIN_INTEGRATION_KEYS

    registrar = CommandRegistrar()
    paths: set[Path] = set()
    hashes: dict[str, set[str]] = {}
    agents: set[str] = set()
    global_paths: set[Path] = set()
    preset_claims: dict[Path, tuple[set[str], set[str]]] = {}
    active_generic = read_project_options(root).get("ai") == "generic"
    for kind in ("extensions", "presets"):
        relative = f".specify/{kind}/.registry"
        registry = _read_json(metadata_files, relative)
        if registry is None:
            package_dir = root / ".specify" / kind
            if package_dir.exists() and any(
                child.is_dir() and not child.name.startswith(".")
                for child in package_dir.iterdir()
            ):
                raise ValueError(f"Missing {relative}; cannot identify contributed agent artifacts")
            continue
        records = registry.get(kind)
        if not isinstance(records, dict):
            raise TypeError(f"{relative}: {kind} must be an object")
        for identifier, record in records.items():
            if not isinstance(record, dict):
                raise TypeError(f"Invalid {kind} record: {identifier}")
            override_sources: dict[str, str] = {}
            if kind == "presets":
                from .presets import PresetManager

                override_sources = PresetManager(root).skill_ownership_sources(identifier)
            generic_hashes = record.get("generic_artifact_hashes", {})
            if not isinstance(generic_hashes, dict):
                raise TypeError(f"Invalid generic_artifact_hashes for {identifier}")
            for name, digest in generic_hashes.items():
                if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
                    raise ValueError(f"Invalid generic artifact digest for {identifier}: {name}")
                relative = _relative(root, root / name)
                hashes.setdefault(relative, set()).add(digest.lower())
                paths.add(root / name)
            commands = record.get("registered_commands", {})
            skills = record.get("registered_skills", {})
            if not isinstance(commands, dict):
                raise TypeError(f"Invalid registered_commands for {identifier}")
            if kind == "extensions" and isinstance(skills, dict) and skills:
                raise TypeError(f"Invalid registered_skills for extension {identifier}: expected a list")
            if isinstance(skills, list):
                # Legacy extension skills were mirrored to every detected agent.
                names_by_agent = {
                    agent: skills for agent in BUILTIN_INTEGRATION_KEYS
                    if agent in registrar.AGENT_CONFIGS
                }
                for agent, binding in bindings.items():
                    if binding and binding["registrar_config"]["extension"] == "/SKILL.md":
                        names_by_agent[agent] = skills
                if "generic" in commands or active_generic:
                    names_by_agent["generic"] = skills
            elif isinstance(skills, dict):
                names_by_agent = skills
            else:
                raise TypeError(f"Invalid registered_skills for {identifier}")
            for agent in commands.keys() | names_by_agent.keys():
                if agent == "generic" and generic_hashes:
                    agents.add(agent)
                    continue
                cmd_names = commands.get(agent, [])
                skill_names = names_by_agent.get(agent, [])
                if not all(
                    isinstance(names, list) and all(isinstance(name, str) for name in names)
                    for names in (cmd_names, skill_names)
                ):
                    raise ValueError(f"Invalid artifact names for {identifier}")
                if not cmd_names and not skill_names:
                    continue
                binding = bindings.get(agent)
                config = binding["registrar_config"] if binding else None
                command_paths = (
                    registrar.registered_artifact_paths(
                        agent, root, commands=cmd_names, skills=[], registrar_config=config,
                    )
                )
                for path in command_paths:
                    if path.is_relative_to(root):
                        paths.add(path)
                    elif agent in global_scopes and path.is_relative_to(global_scopes[agent]):
                        global_paths.add(path)
                    else:
                        raise ValueError(f"Contribution output is outside its declared uninstall scope: {path}")
                if cmd_names:
                    agents.add(agent)
                for skill in skill_names:
                    candidates = registrar.registered_artifact_paths(
                        agent, root, commands=[], skills=[skill], registrar_config=config,
                    )
                    for candidate in candidates:
                        if kind == "presets":
                            sources, owners = preset_claims.setdefault(candidate, (set(), set()))
                            sources.add(f"preset:{identifier}")
                            override = override_sources.get(skill)
                            if override:
                                sources.add(override)
                            owners.add(agent)
                            continue
                        relative = _relative(root, candidate / "SKILL.md")
                        try:
                            text = files.read_text(relative)
                        except FileNotFoundError:
                            if candidate.exists() and not isinstance(skills, list):
                                raise ValueError(f"Cannot establish skill ownership at {candidate}")
                            continue
                        frontmatter, _ = registrar.parse_frontmatter(text)
                        metadata = frontmatter.get("metadata", {}) if isinstance(frontmatter, dict) else {}
                        source = metadata.get("source") if isinstance(metadata, dict) else None
                        prefix = "extension" if kind == "extensions" else "preset"
                        if source == f"{prefix}:{identifier}":
                            paths.add(candidate)
                            agents.add(agent)
                        elif not isinstance(skills, list):
                            raise ValueError(f"Cannot establish skill ownership at {candidate}")
    for candidate, (sources, owners) in preset_claims.items():
        relative = _relative(root, candidate / "SKILL.md")
        try:
            content = files.read_text(relative)
        except FileNotFoundError:
            if candidate.exists():
                raise ValueError(f"Cannot establish skill ownership at {candidate}")
            continue
        frontmatter, _ = registrar.parse_frontmatter(content)
        metadata = frontmatter.get("metadata", {}) if isinstance(frontmatter, dict) else {}
        source = metadata.get("source") if isinstance(metadata, dict) else None
        if source not in sources:
            raise ValueError(f"Cannot establish skill ownership at {candidate}")
        paths.add(candidate)
        agents.update(owners)
    return paths, hashes, agents, global_paths


def plan_destroy(request: DestroyRequest) -> DestroyPlan:
    """Validate all ownership and paths without changing the project."""
    root = request.project_directory
    if not root.is_absolute():
        raise DestroyError("invalid_project_directory", "project_directory must be absolute")
    try:
        root = root.resolve(strict=True)
        if (Path.home().resolve() / ".specify/integration-trust.json").is_relative_to(root):
            raise ValueError("Destroy cannot target a project containing machine-level integration trust")
        files = project_files(root)
        metadata_files = FileHelper(root)
        specify = root / ".specify"
        if not specify.exists() and not specify.is_symlink():
            return DestroyPlan(root, (), (), (), ())
        if specify.is_symlink() or not specify.is_dir():
            raise ValueError(".specify must be a non-symlinked directory")

        leaves, directories, preserved = _project_artifacts(files, request)

        state = _read_json(metadata_files, ".specify/integration.json")
        if state and state.get("integration_state_schema", 1) != 1:
            raise ValueError("Unsupported integration state schema")
        if state is not None:
            if not {"integration", "default_integration", "installed_integrations"} & state.keys():
                raise ValueError("Integration state has no installation inventory")
            for field in ("integration", "default_integration"):
                if field in state and (
                    not isinstance(state[field], str) or not state[field].strip()
                ):
                    raise ValueError(f"Invalid integration state field: {field}")
            if "installed_integrations" in state and (
                not isinstance(state["installed_integrations"], list)
                or any(
                    not isinstance(key, str) or not key.strip()
                    for key in state["installed_integrations"]
                )
            ):
                raise ValueError("Invalid installed_integrations")
        installed = installed_integration_keys(normalize_integration_state(state)) if state else []
        normalized = normalize_integration_state(state or {})
        default = default_integration_key(normalized)
        order = tuple(key for key in installed if key != default) + ((default,) if default in installed else ())
        if state is None:
            legacy_agent = read_project_options(root).get("ai")
            if isinstance(legacy_agent, str) and legacy_agent:
                raise ValueError(
                    "Legacy integration inventory has no .specify/integration.json. "
                    "Re-run specify init for the recorded integration to migrate before destroy.",
                )
        manifests = sorted(
            name for name in leaves
            if name.startswith(".specify/integrations/") and name.endswith(".manifest.json")
            and len(Path(name).parts) == 3
        )
        from .integrations._operation_uninstall import validate_uninstall_ownership

        bindings = {key: validate_uninstall_ownership(root, key) for key in installed}
        for key in installed:
            if f".specify/integrations/{key}.manifest.json" not in manifests:
                raise ValueError(f"Missing manifest for '{key}'; repair or uninstall that integration first")

        expected: dict[str, set[str]] = {}
        dispatcher_owners: dict[str, tuple[str, bool, str]] = {}
        updated: set[str] = set()
        for manifest_path in manifests:
            key = Path(manifest_path).name.removesuffix(".manifest.json")
            raw = _read_json(metadata_files, manifest_path)
            if raw is None or "files" not in raw or raw.get("integration") != key:
                raise ValueError(f"Invalid ownership manifest: {manifest_path}")
            manifest = IntegrationManifest.load(key, root)
            if key != "speckit" and key not in installed:
                raise ValueError(f"Integration '{key}' has a manifest but no installed integration state")
            from .integrations import BUILTIN_INTEGRATION_KEYS, get_integration

            integration = get_integration(key) if key in BUILTIN_INTEGRATION_KEYS else None
            native_config = getattr(integration, "events_config_file", None) if integration else None
            if native_config in manifest.files:
                from .events import validate_integration_event_cleanup

                validate_integration_event_cleanup(integration, root)
            for name, digest in manifest.files.items():
                if Path(name).as_posix() != name:
                    raise ValueError(f"Noncanonical manifest path: {name}")
                relative = _relative(root, root / name, allow_specs=True)
                if relative == CONSTITUTION or relative == "specs" or relative.startswith("specs/"):
                    # SDD artifacts are handled only by the final project cleanup, not agent teardown.
                    continue
                if relative == ".specify":
                    raise ValueError("Manifests must record files, not the .specify root")
                if not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
                    raise ValueError(f"Invalid manifest digest: {name}")
                mode = manifest.ownership_modes[name]
                if bindings.get(key) is not None:
                    mode = bindings[key].get("ownership_modes", {}).get(name, "shared")
                if relative == ".specify/events.py":
                    dispatcher_owners[key] = (mode, manifest.is_recovered(name), digest)
                if relative.startswith(".specify/"):
                    continue
                if mode != "whole":
                    if (root / name).exists() or (root / name).is_symlink():
                        if integration is not None and getattr(integration, "events_config_file", None) != name:
                            raise ValueError(
                                f"Partial/shared ownership at {name}; no native event cleanup owns this file",
                            )
                        metadata_files.read_bytes(name)
                        updated.add(name)
                    continue
                expected.setdefault(relative, set()).add(digest.lower())

        from .integrations import BUILTIN_INTEGRATION_KEYS, get_integration
        from .integrations.installer import safe_project_path

        global_scopes: dict[str, Path] = {}
        for key in installed:
            integration = get_integration(key) if key in BUILTIN_INTEGRATION_KEYS else None
            directory = (integration.registrar_config or {}).get("dir", "") if integration else ""
            if directory.startswith("~/"):
                global_scopes[key] = safe_project_path(Path.home(), directory[2:])
        contributed, contribution_hashes, contribution_agents, global_paths = _contribution_paths(
            root, metadata_files, files, bindings, global_scopes,
        )
        global_files: set[str] = set()
        if global_paths:
            home_files = FileHelper(Path.home(), allow_symlinks=files.allow_symlinks)
            for path in sorted(global_paths):
                relative = _relative(home_files.root, path)
                # Declared global outputs are inspected here, but only their integration tears them down.
                candidate_leaves, _ = _tree(home_files, relative)
                global_files.update(str(home_files.root / name) for name in candidate_leaves)
        for name, digests in contribution_hashes.items():
            expected.setdefault(name, set()).update(digests)
        requiring_force: set[str] = set()
        dispatcher = root / ".specify/events.py"
        if dispatcher.exists() or dispatcher.is_symlink():
            from .events import dispatcher_content_matches

            claimants = [key for key in order if key in dispatcher_owners]
            if not claimants:
                raise ValueError("Cannot prove managed dispatcher ownership of .specify/events.py; resolve it before destroy")
            mode, recovered, digest = dispatcher_owners[claimants[-1]]
            if mode == "partial" or recovered:
                raise ValueError("Cannot prove managed dispatcher ownership of .specify/events.py; resolve it before destroy")
            if not dispatcher_content_matches(files.read_bytes(".specify/events.py"), digest):
                requiring_force.add(".specify/events.py")
        for candidate in sorted(contributed | {root / name for name in expected}):
            relative = _relative(root, candidate)
            if relative == CONSTITUTION or relative.startswith(".specify/"):
                continue
            candidate_leaves, candidate_dirs = _tree(files, relative)
            if candidate_dirs and relative in expected:
                raise ValueError(f"Manifest file became a directory: {relative}")
            leaves.update(candidate_leaves)
            directories.update(candidate_dirs)
            for name in candidate_leaves:
                path = root / name
                digests = expected.get(name, set())
                if digests and (
                    path.is_symlink() or hashlib.sha256(files.read_bytes(name)).hexdigest() not in digests
                ):
                    requiring_force.add(name)

        # Only prune empty generated ancestors; never traverse unrelated trees.
        for name in tuple(leaves) + tuple(directories):
            parent = Path(name).parent
            while parent != Path("."):
                if CONSTITUTION not in preserved or _without_constitution_parents(root, {parent.as_posix()}):
                    directories.add(parent.as_posix())
                parent = parent.parent
        return DestroyPlan(
            root, tuple(sorted(leaves)),
            tuple(sorted(directories, key=lambda name: (-len(Path(name).parts), name))),
            preserved, tuple(sorted(requiring_force)), order, tuple(sorted(updated)),
            tuple(sorted(contribution_agents)),
            tuple(sorted(str(path) for path in global_scopes.values())),
            tuple(sorted(global_files)),
        )
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        raise DestroyError("invalid_destroy_state", str(exc), project_directory=str(root)) from exc


def destroy_project(request: DestroyRequest) -> DestroyResult:
    """Plan and execute a confirmed project-local uninstall."""
    plan = plan_destroy(request)
    if request.dry_run:
        return DestroyResult(
            str(plan.project_directory), True, plan.files, plan.preserved, plan.requires_force,
            plan.directories, plan.updated, global_scopes=plan.global_scopes,
            global_files=plan.global_files,
        )
    if not plan.files and not plan.directories and not plan.integrations and not plan.updated:
        return DestroyResult(str(plan.project_directory), False, (), plan.preserved)
    if not request.confirmed:
        raise DestroyError(
            "confirmation_required",
            "Destroy deletes project-local Spec Kit files and unpreserved SDD artifacts. "
            "Preview with --dry-run; confirm with --yes.",
        )
    if plan.requires_force and not request.force:
        raise DestroyError(
            "modified_files",
            "Modified or unverified generated files would be deleted. Back them up or retry with --force.",
            paths=list(plan.requires_force),
        )
    files = project_files(plan.project_directory)
    removed: list[str] = []
    warnings: list[str] = []
    uninstalled: list[str] = []
    try:
        from .integrations._operation_uninstall import (
            IntegrationUninstallRequest,
            uninstall_integration,
            unregister_integration_artifacts,
        )

        for key in plan.integrations:
            result = uninstall_integration(IntegrationUninstallRequest(
                plan.project_directory, key, request.force, require_complete=True,
                preserved_paths=(CONSTITUTION, "specs"),
            ))
            warnings.extend(result.warnings)
            uninstalled.append(key)
        for key in set(plan.contribution_agents) - set(plan.integrations):
            warnings.extend(unregister_integration_artifacts(
                plan.project_directory, key, require_complete=True, force=request.force,
            ))
        remaining = [
            name for name in plan.files
            if not name.startswith((".specify/", "specs/")) and name != "specs"
            and ((plan.project_directory / name).exists() or (plan.project_directory / name).is_symlink())
        ]
        remaining.extend(
            name for name in plan.global_files if Path(name).exists() or Path(name).is_symlink()
        )
        if remaining:
            raise DestroyError(
                "cleanup_incomplete", "Integration uninstall preserved generated artifacts; resolve them before destroy.",
                paths=remaining,
            )
        if (plan.project_directory / ".specify/events.py").exists():
            raise DestroyError("cleanup_incomplete", "The event lifecycle preserved .specify/events.py; resolve it before destroy.")
        # Re-inventory only after teardown has released all integration claims.
        leaves, directories, _ = _project_artifacts(files, request)
        spec_leaves = {name for name in leaves if name == "specs" or name.startswith("specs/")}
        spec_directories = {name for name in directories if name == "specs" or name.startswith("specs/")}
        for name in sorted(spec_leaves):
            files.delete(name)
            removed.append(name)
        for name in sorted(spec_directories, key=lambda name: (-len(Path(name).parts), name)):
            files.delete(name)
        leaves.difference_update(spec_leaves)
        directories.difference_update(spec_directories)
        planned_directories = set(plan.directories) - spec_directories
        registries = {name for name in leaves if Path(name).name == ".registry"}
        for name in sorted(leaves - registries, key=lambda name: (name.startswith(".specify/"), name)):
            files.delete(name)
            removed.append(name)
        directories.update(planned_directories)
        if CONSTITUTION in plan.preserved:
            directories = _without_constitution_parents(plan.project_directory, directories)
        metadata_parents = {
            parent.as_posix() for name in registries for parent in Path(name).parents
        }
        # Package trees must disappear before their ownership registries are discarded.
        for name in sorted(directories - metadata_parents, key=lambda name: (-len(Path(name).parts), name)):
            try:
                files.delete(name)
            except FileNotFoundError:
                continue
            except OSError as exc:
                if exc.errno not in {errno.ENOTEMPTY, errno.EEXIST} or name.startswith(".specify/"):
                    raise
        for name in sorted(registries):
            files.delete(name)
            removed.append(name)
        for name in sorted(directories, key=lambda name: (-len(Path(name).parts), name)):
            try:
                files.delete(name)
            except FileNotFoundError:
                # Integration teardown already prunes its empty parent directories.
                continue
            except OSError as exc:
                if (
                    exc.errno not in {errno.ENOTEMPTY, errno.EEXIST}
                    or name == ".specify"
                    or name.startswith(".specify/")
                ):
                    raise
    except DestroyError as exc:
        exc.details["uninstalled_integrations"] = uninstalled
        raise
    except (OSError, ValueError, RuntimeError) as exc:
        raise DestroyError(
            "destroy_failed",
            f"Uninstall stopped: {exc}. Some files may already have been removed.",
            removed=removed,
            uninstalled_integrations=uninstalled,
        ) from exc
    removed.extend(
        name for name in plan.files if name not in removed
        and not (plan.project_directory / name).exists()
        and not (plan.project_directory / name).is_symlink()
    )
    return DestroyResult(
        str(plan.project_directory), False, tuple(removed), plan.preserved,
        updated=plan.updated, warnings=tuple(warnings), global_scopes=plan.global_scopes,
        global_files=tuple(
            name for name in plan.global_files if not Path(name).exists() and not Path(name).is_symlink()
        ),
    )
