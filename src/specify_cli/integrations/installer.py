"""Trusted project-local adapter packages, separate from generated artifacts."""

from __future__ import annotations

import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import inspect
import itertools
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import threading
from collections import Counter
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from pathlib import Path, PureWindowsPath
from typing import Any

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from .._download_security import (
    archive_format_from_name,
    is_https_or_localhost_http,
    is_safe_download_redirect,
    normalize_archive_member_name,
    read_response_limited,
    safe_extract_archive,
)
from . import (
    BUILTIN_INTEGRATION_KEYS,
    INTEGRATION_REGISTRY,
    IntegrationCatalog,
    IntegrationDescriptor,
    IntegrationDescriptorError,
)
from ._file_changes import after_file_change, before_file_change
from .base import IntegrationBase

_MODULE_PREFIX = "_speckit_installed_integration_"
_loaded_identity: tuple[Any, ...] | None = None
_loading: ContextVar[bool] = ContextVar("integration_loading", default=False)
_registry_lock = threading.RLock()
_module_sequence = itertools.count()
_pinned_names: Counter[str] = Counter()
dispatch_registry: ContextVar[dict[str, IntegrationBase] | None] = ContextVar(
    "integration_dispatch_registry", default=None
)
_pending_root: Path | None = None
_RECORD = ".specify/integrations/packages.json"
_PACKAGES = ".specify/integrations/packages"
_source_packages: dict[str, tuple[Path, dict[str, str]]] = {}
recovery_exclusion: ContextVar[tuple[Path, str] | None] = ContextVar(
    "integration_recovery_exclusion", default=None
)


class IntegrationInstallError(ValueError):
    """An external integration cannot safely be installed or loaded."""


def registry_synchronized(handler):
    @wraps(handler)
    def invoke(*args, **kwargs):
        with _registry_lock:
            return handler(*args, **kwargs)
    return invoke


def _namespace(integration: IntegrationBase) -> str:
    return type(integration).__module__.split(".", 1)[0]


def _discard_unused_imports() -> None:
    retained = {_namespace(value) for value in INTEGRATION_REGISTRY.values()} | set(_pinned_names)
    for name in tuple(sys.modules):
        if name.startswith(_MODULE_PREFIX) and name.split(".", 1)[0] not in retained:
            del sys.modules[name]
    for name in tuple(_source_packages):
        if name not in retained:
            del _source_packages[name]
    if not _source_packages and _source_finder in sys.meta_path:
        sys.meta_path.remove(_source_finder)


@contextmanager
def project_integrations(project_root: Path):
    """Pin a project snapshot without serializing independent agent processes."""
    with _registry_lock:
        load_installed_integrations(project_root)
        snapshot = dict(INTEGRATION_REGISTRY)
        names = {
            _namespace(value) for value in snapshot.values()
            if _namespace(value).startswith(_MODULE_PREFIX)
        }
        _pinned_names.update(names)
    token = dispatch_registry.set(snapshot)
    try:
        yield
    finally:
        dispatch_registry.reset(token)
        with _registry_lock:
            _pinned_names.subtract(names)
            for name in names:
                if _pinned_names[name] == 0:
                    del _pinned_names[name]
            _discard_unused_imports()


def project_dispatch(handler):
    signature = inspect.signature(handler)

    @wraps(handler)
    def invoke(*args, **kwargs):
        context = signature.bind(*args, **kwargs).arguments["context"]
        root = Path(context.project_root) if context.project_root else Path.cwd()
        with project_integrations(root):
            return handler(*args, **kwargs)
    return invoke


class _VerifiedSourceLoader(importlib.machinery.SourceFileLoader):
    """Compile the verified bytes, never untracked or stale cached bytecode."""

    def __init__(self, name: str, package: Path, relative: str, digest: str):
        path = safe_project_path(package, relative)
        super().__init__(name, str(path))
        self.digest = digest

    def get_code(self, fullname: str):
        source = self.get_data(self.path)
        if hashlib.sha256(source).hexdigest() != self.digest:
            raise IntegrationInstallError(f"Integration source has been modified: {self.path}")
        return self.source_to_code(source, self.path)


class _VerifiedSourceFinder(importlib.abc.MetaPathFinder):
    """Scope relative imports to the installed package's recorded Python files."""

    @registry_synchronized
    def find_spec(self, fullname, path=None, target=None):
        for namespace, (package, hashes) in _source_packages.items():
            if not fullname.startswith(namespace + "."):
                continue
            stem = fullname[len(namespace) + 1:].replace(".", "/")
            for relative, locations in (
                (f"{stem}/__init__.py", [str(package / stem)]),
                (f"{stem}.py", None),
            ):
                if relative in hashes:
                    loader = _VerifiedSourceLoader(fullname, package, relative, hashes[relative])
                    return importlib.util.spec_from_file_location(
                        fullname, loader.path, loader=loader,
                        submodule_search_locations=locations,
                    )
            if any(relative.startswith(stem + "/") for relative in hashes):
                spec = importlib.machinery.ModuleSpec(fullname, loader=None, is_package=True)
                spec.submodule_search_locations = [str(safe_project_path(package, stem))]
                return spec
            raise ModuleNotFoundError(
                f"Integration module {fullname!r} requires a recorded Python source file"
            )
        return None


_source_finder = _VerifiedSourceFinder()


def validate_key(key: str) -> None:
    if (
        not isinstance(key, str)
        or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", key)
        or key in {"con", "prn", "aux", "nul"}
        or re.fullmatch(r"(com|lpt)[1-9]", key)
    ):
        raise IntegrationInstallError(f"Invalid integration ID: {key!r}")


def safe_project_path(root: Path, relative: str, *, allow_leaf_symlink: bool = False) -> Path:
    """Reject non-canonical paths and symlinked ancestors before accessing them."""
    path = Path(relative)
    if (
        not relative
        or "\\" in relative
        or ":" in relative
        or path.is_absolute()
        or PureWindowsPath(relative).drive
        or any(part in {"", ".", ".."} for part in relative.split("/"))
    ):
        raise IntegrationInstallError(f"Unsafe integration path: {relative!r}")
    normalize_archive_member_name(relative, error_type=IntegrationInstallError)
    current = root
    for part in path.parts:
        current /= part
        if current.is_symlink():
            if allow_leaf_symlink and current == root / path:
                continue
            if current == root / ".specify":
                raise IntegrationInstallError(f"Refusing to use symlinked .specify directory: {current}")
            raise IntegrationInstallError(f"Symlinked integration path: {current}")
    return current


def package_hashes(package: Path) -> dict[str, str]:
    """Bound package traversal and reject links or non-regular retained files."""
    if package.is_symlink() or not package.is_dir():
        raise IntegrationInstallError(f"Invalid integration package directory: {package}")
    hashes: dict[str, str] = {}
    count = total = 0
    pending = [(package, 0)]
    while pending:
        directory, depth = pending.pop()
        if depth > 32:
            raise IntegrationInstallError("Integration package exceeds depth limit (32)")
        with os.scandir(directory) as entries:
            for entry in entries:
                relative = Path(entry.path).relative_to(package).as_posix()
                safe_project_path(package, relative)
                mode = entry.stat(follow_symlinks=False).st_mode
                if stat.S_ISLNK(mode):
                    raise IntegrationInstallError(f"Integration package contains symlink: {entry.path}")
                if entry.name == "__pycache__" and stat.S_ISDIR(mode):
                    continue
                count += 1
                if count > 512:
                    raise IntegrationInstallError("Integration package exceeds entry limit (512)")
                if stat.S_ISDIR(mode):
                    pending.append((Path(entry.path), depth + 1))
                elif stat.S_ISREG(mode):
                    size = entry.stat(follow_symlinks=False).st_size
                    total += size
                    if size > 10 * 1024 * 1024 or total > 50 * 1024 * 1024:
                        raise IntegrationInstallError("Integration package exceeds size limit")
                    with open(entry.path, "rb") as stream:
                        digest = hashlib.file_digest(stream, "sha256").hexdigest()
                    hashes[relative] = digest
                else:
                    raise IntegrationInstallError(f"Unsupported integration file: {entry.path}")
    if not {"integration.yml", "__init__.py"} <= hashes.keys():
        raise IntegrationInstallError("Integration package requires root integration.yml and __init__.py")
    return hashes


def read_records(root: Path) -> dict[str, dict[str, Any]]:
    safe_project_path(root, _PACKAGES)
    path = safe_project_path(root, _RECORD)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError, UnicodeError) as exc:
        raise IntegrationInstallError(f"Cannot read installed integration packages: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != "1.0" or not isinstance(data.get("packages"), dict):
        raise IntegrationInstallError("Invalid installed integration package registry")
    records = data["packages"]
    for key, record in records.items():
        validate_key(key)
        if key in BUILTIN_INTEGRATION_KEYS:
            raise IntegrationInstallError(f"External package collides with built-in integration '{key}'")
        if not isinstance(record, dict):
            raise IntegrationInstallError(f"Integration '{key}' has invalid package metadata")
        for field in ("id", "name", "version", "description", "catalog", "download_url"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise IntegrationInstallError(
                    f"Integration '{key}' has invalid package metadata: {field}"
                )
        if not isinstance(record.get("requires"), dict):
            raise IntegrationInstallError(f"Integration '{key}' has invalid package metadata: requires")
        if not isinstance(record.get("files"), dict):
            raise IntegrationInstallError(f"Integration '{key}' has invalid package hashes")
        for relative, digest in record["files"].items():
            if not isinstance(relative, str) or not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
                raise IntegrationInstallError(f"Integration '{key}' has invalid package hashes")
            normalize_archive_member_name(relative, error_type=IntegrationInstallError)
    return records


def write_records(root: Path, records: dict[str, dict[str, Any]]) -> None:
    path = safe_project_path(root, _RECORD)
    before_file_change(path, removal=not records)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        path.unlink(missing_ok=True)
        after_file_change(path)
        return
    with tempfile.NamedTemporaryFile(dir=path.parent, mode="w", encoding="utf-8", delete=False) as stream:
        temporary = Path(stream.name)
        json.dump({"schema_version": "1.0", "packages": records}, stream, indent=2)
        stream.write("\n")
    try:
        os.replace(temporary, path)
        after_file_change(path)
    finally:
        temporary.unlink(missing_ok=True)


def _trust_store(root: Path) -> Path:
    home = Path.home().absolute()
    if any(path.is_symlink() for path in (home, *home.parents)):
        raise IntegrationInstallError("Refusing symlinked integration trust directory")
    home = home.resolve()
    project = root.resolve()
    if home == project or project in home.parents:
        raise IntegrationInstallError("Integration local trust state must be outside the project")
    return safe_project_path(home, ".specify/integration-trust.json")


def _trust_identity(root: Path, key: str, hashes: dict[str, str]) -> str:
    payload = json.dumps(
        [os.path.normcase(str(root.resolve())), key, hashes],
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_trust_state(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as stream:
            content = stream.read(1024 * 1024 + 1)
        if len(content) > 1024 * 1024:
            raise ValueError("trust registry exceeds size limit")
        data = json.loads(content)
    except FileNotFoundError:
        return {"schema_version": "1.0", "grants": [], "recovery": {}}
    except (OSError, ValueError, UnicodeError) as exc:
        raise IntegrationInstallError(f"Cannot read integration local trust state: {exc}") from exc
    if (
        not isinstance(data, dict) or data.get("schema_version") != "1.0"
        or not isinstance(data.get("grants"), list)
        or any(not isinstance(item, str) or not re.fullmatch(r"[a-f0-9]{64}", item) for item in data["grants"])
    ):
        raise IntegrationInstallError("Invalid integration local trust state")
    recovery = data.get("recovery", {})
    if not isinstance(recovery, dict):
        raise IntegrationInstallError("Invalid integration local recovery ownership")
    for identity, binding in recovery.items():
        if (
            not isinstance(identity, str)
            or not re.fullmatch(r"[a-f0-9]{64}", identity)
            or not isinstance(binding, dict)
            or not isinstance(binding.get("package"), str)
            or not re.fullmatch(r"[a-f0-9]{64}", binding["package"])
            or not isinstance(binding.get("registrar_config"), dict)
            or not isinstance(binding.get("paths"), list)
            or any(not isinstance(path, str) for path in binding["paths"])
        ):
            raise IntegrationInstallError("Invalid integration local recovery ownership")
        if "files" in binding and (
            not isinstance(binding["files"], dict)
            or any(
                not isinstance(name, str) or not isinstance(digest, str)
                or not re.fullmatch(r"[a-f0-9]{64}", digest)
                for name, digest in binding["files"].items()
            )
        ):
            raise IntegrationInstallError("Invalid integration local recovery package hashes")
    data["recovery"] = recovery
    return data


def _read_trust(path: Path) -> set[str]:
    return set(_read_trust_state(path)["grants"])


def _recovery_identity(root: Path, key: str) -> str:
    value = json.dumps([os.path.normcase(str(root.resolve())), key])
    return hashlib.sha256(value.encode()).hexdigest()


def _grant_trust(
    root: Path, key: str, record: dict[str, Any], *, record_ownership: bool = False,
) -> None:
    """Persist this user's explicit consent, bound to the project and package."""
    from ..shared_infra import _exclusive_project_lock
    from .manifest import IntegrationManifest

    path = _trust_store(root)
    with _exclusive_project_lock(path.parent.parent, ".integration-trust.lock", context="integration trust"):
        path = _trust_store(root)
        data = _read_trust_state(path)
        identity = _trust_identity(root, key, record["files"])
        data["grants"] = sorted(set(data["grants"]) | {identity})
        if record_ownership:
            data["recovery"][_recovery_identity(root, key)] = {
                "package": identity,
                "files": dict(record["files"]),
                "registrar_config": record["registrar_config"],
                "paths": sorted(IntegrationManifest.load(key, root).files),
            }
        with tempfile.NamedTemporaryFile(dir=path.parent, mode="w", encoding="utf-8", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, indent=2)
            stream.write("\n")
        try:
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def recovery_metadata(root: Path, key: str, record: dict[str, Any]) -> dict[str, Any] | None:
    """Authorize cleanup from user-local ownership, never mutable project claims."""
    from .manifest import IntegrationManifest

    trust = _read_trust_state(_trust_store(root))
    binding = trust["recovery"].get(_recovery_identity(root, key))
    if binding is None:
        return None
    if "files" in binding and binding["package"] != _trust_identity(root, key, binding["files"]):
        raise IntegrationInstallError(f"Integration '{key}' recovery package identity has been modified")
    if binding["package"] not in trust["grants"]:
        return None
    if record.get("registrar_config") != binding["registrar_config"]:
        raise IntegrationInstallError(f"Integration '{key}' recovery ownership metadata has been modified")
    config = binding["registrar_config"]
    _validate_registrar_config(key, config)

    def validate_cleanup(relative: str, *, leaf: bool = False) -> None:
        path = safe_project_path(root, relative, allow_leaf_symlink=leaf)
        parts = tuple(part.casefold() for part in path.relative_to(root).parts)
        if not leaf and parts[0] in {".git", ".specify"}:
            raise IntegrationInstallError("Reserved recovery ownership directory")
        for other in INTEGRATION_REGISTRY.values():
            if other.key != key and any(_paths_overlap(relative, folder) for folder in _output_roots(other)):
                raise IntegrationInstallError(
                    f"Integration '{key}' recovery ownership overlaps '{other.key}'"
                )

    validate_cleanup(config["dir"])
    if "legacy_dir" in config:
        validate_cleanup(config["legacy_dir"])
    manifest = safe_project_path(root, f".specify/integrations/{key}.manifest.json")
    if manifest.exists():
        paths = IntegrationManifest.load(key, root).files
        if not set(paths) <= set(binding["paths"]):
            raise IntegrationInstallError(f"Integration '{key}' manifest recovery ownership has been modified")
        for relative in paths:
            validate_cleanup(relative, leaf=True)
    return binding


def _refresh_configs() -> None:
    """Mutate cached dictionaries in place so compatibility aliases stay live."""
    agent_module = sys.modules.get("specify_cli._agent_config")
    if agent_module is not None:
        agent_module.AGENT_CONFIG.clear()
        agent_module.AGENT_CONFIG.update(agent_module._build_agent_config())
    agents = sys.modules.get("specify_cli.agents")
    if agents is not None:
        registrar = agents.CommandRegistrar
        configs = agents._build_agent_configs()
        for cls in (registrar, *registrar.__subclasses__()):
            cls.AGENT_CONFIGS.clear()
            cls.AGENT_CONFIGS.update(configs)
            cls._configs_loaded = True


@registry_synchronized
def unload_installed_integrations() -> None:
    global _loaded_identity
    for key in tuple(INTEGRATION_REGISTRY):
        if type(INTEGRATION_REGISTRY[key]).__module__.startswith(_MODULE_PREFIX):
            del INTEGRATION_REGISTRY[key]
    _discard_unused_imports()
    _loaded_identity = None
    _refresh_configs()


def _descriptor(package: Path, key: str, info: dict[str, Any]) -> IntegrationDescriptor:
    try:
        descriptor = IntegrationDescriptor(package / "integration.yml")
    except IntegrationDescriptorError as exc:
        raise IntegrationInstallError(str(exc)) from exc
    validate_key(descriptor.id)
    if descriptor.id != key or info.get("_declared_id", info.get("id", key)) != key:
        raise IntegrationInstallError(f"Integration descriptor/catalog identity does not match '{key}'")
    metadata = descriptor.data["integration"]
    for field in ("name", "version", "description", "author", "repository", "license"):
        if field in info and info[field] != metadata.get(field):
            raise IntegrationInstallError(f"Integration '{key}' catalog/descriptor {field} mismatch")
    if "requires" in info and info["requires"] != descriptor.data["requires"]:
        raise IntegrationInstallError(f"Integration '{key}' catalog/descriptor requirements mismatch")
    from .._assets import get_speckit_version

    host_version = get_speckit_version()
    if not SpecifierSet(descriptor.requires_speckit_version).contains(host_version, prereleases=True):
        raise IntegrationInstallError(
            f"Integration '{key}' requires Spec Kit {descriptor.requires_speckit_version}; installed {host_version}"
        )
    return descriptor


def _paths_overlap(first: str, second: str) -> bool:
    left = tuple(part.casefold() for part in Path(first).parts)
    right = tuple(part.casefold() for part in Path(second).parts)
    return left[:len(right)] == right or right[:len(left)] == left


def _output_roots(integration: IntegrationBase) -> list[str]:
    return [
        path.rstrip("/") for path in (
            (integration.config or {}).get("folder"),
            (integration.registrar_config or {}).get("legacy_dir"),
        )
        if isinstance(path, str) and path
    ]


def _validate_output_paths(integration: IntegrationBase, project_root: Path) -> None:
    config = integration.config
    folder = config["folder"].rstrip("/")
    destination = f"{folder}/{config['commands_subdir']}"
    paths = [folder, destination, integration.registrar_config["dir"]]
    if "legacy_dir" in integration.registrar_config:
        paths.append(integration.registrar_config["legacy_dir"])
    for relative in paths:
        if relative.startswith("~"):
            raise IntegrationInstallError(f"Integration '{integration.key}' output must be project-local")
        safe_project_path(project_root, relative)
        if Path(relative).parts[0].casefold() in {".specify", ".git"}:
            raise IntegrationInstallError(f"Integration '{integration.key}' output uses reserved directory")


def _validate_registrar_config(key: str, registrar: Any) -> None:
    if not isinstance(registrar, dict):
        raise IntegrationInstallError(f"Integration '{key}' requires a registrar_config mapping")
    for field in ("dir", "format", "args", "extension"):
        if not isinstance(registrar.get(field), str) or not registrar[field].strip():
            raise IntegrationInstallError(f"Integration '{key}' registrar_config.{field} must be a non-empty string")
    if registrar["format"] not in {"markdown", "toml", "yaml"}:
        raise IntegrationInstallError(f"Integration '{key}' has unsupported registration format")
    if not re.fullmatch(r"\.[A-Za-z0-9][A-Za-z0-9_.-]*", registrar["extension"]) and not (
        registrar["format"] == "markdown" and registrar["extension"] == "/SKILL.md"
    ):
        raise IntegrationInstallError(f"Integration '{key}' has unsafe registration extension")
    if "invoke_separator" in registrar and (
        not isinstance(registrar["invoke_separator"], str) or not registrar["invoke_separator"]
    ):
        raise IntegrationInstallError(f"Integration '{key}' registrar_config.invoke_separator must be a non-empty string")
    if "dev_no_symlink" in registrar and not isinstance(registrar["dev_no_symlink"], bool):
        raise IntegrationInstallError(f"Integration '{key}' registrar_config.dev_no_symlink must be a boolean")
    if "legacy_dir" in registrar and (
        not isinstance(registrar["legacy_dir"], str) or not registrar["legacy_dir"].strip()
    ):
        raise IntegrationInstallError(f"Integration '{key}' registrar_config.legacy_dir must be a non-empty string")


def _validate_implementation(
    integration: IntegrationBase, descriptor: IntegrationDescriptor, project_root: Path,
) -> None:
    key = descriptor.id
    config = integration.config
    registrar = integration.registrar_config
    if not isinstance(config, dict):
        raise IntegrationInstallError(f"Integration '{key}' requires a config mapping")
    _validate_registrar_config(key, registrar)
    if config.get("name") != descriptor.name:
        raise IntegrationInstallError(f"Integration '{key}' class/descriptor name mismatch")
    if getattr(integration, "version", descriptor.version) != descriptor.version:
        raise IntegrationInstallError(f"Integration '{key}' class/descriptor version mismatch")
    for field in ("folder", "commands_subdir", "install_url"):
        if not isinstance(config.get(field), str) or not config[field].strip():
            raise IntegrationInstallError(f"Integration '{key}' config.{field} must be a non-empty string")
    if not isinstance(config.get("requires_cli"), bool):
        raise IntegrationInstallError(f"Integration '{key}' config.requires_cli must be a boolean")
    folder = config["folder"].rstrip("/")
    destination = f"{folder}/{config['commands_subdir']}"
    _validate_output_paths(integration, project_root)
    if registrar["dir"] != destination:
        raise IntegrationInstallError(f"Integration '{key}' registration directory does not match config")
    if not isinstance(integration.multi_install_safe, bool):
        raise IntegrationInstallError(f"Integration '{key}' multi_install_safe must be a boolean")
    if not isinstance(integration.invoke_separator, str) or not integration.invoke_separator:
        raise IntegrationInstallError(f"Integration '{key}' invoke_separator must be a non-empty string")
    if not isinstance(integration.dev_no_symlink, bool):
        raise IntegrationInstallError(f"Integration '{key}' dev_no_symlink must be a boolean")
    if integration.multi_install_safe:
        roots = _output_roots(integration)
        for other in INTEGRATION_REGISTRY.values():
            if other.key != key and any(
                _paths_overlap(path, other_folder)
                for path in roots for other_folder in _output_roots(other)
            ):
                raise IntegrationInstallError(f"Integration '{key}' multi-install root overlaps '{other.key}'")
    signature = inspect.signature(integration.build_exec_args)
    execution_parameters = ("model", "output_json", "integration_args", "integration_options", "project_root")
    for parameter in execution_parameters:
        if parameter not in signature.parameters and not any(
            item.kind == inspect.Parameter.VAR_KEYWORD for item in signature.parameters.values()
        ):
            raise IntegrationInstallError(f"Integration '{key}' build_exec_args must accept {parameter}")
    try:
        signature.bind("Sample prompt", **dict.fromkeys(execution_parameters))
    except TypeError as exc:
        raise IntegrationInstallError(
            f"Integration '{key}' build_exec_args must accept the host execution signature: {exc}"
        ) from exc


def _import_package(
    package: Path, descriptor: IntegrationDescriptor, hashes: dict[str, str], project_root: Path,
) -> IntegrationBase:
    key = descriptor.id
    if key in BUILTIN_INTEGRATION_KEYS or key in INTEGRATION_REGISTRY:
        raise IntegrationInstallError(f"Integration '{key}' is already registered or built-in")
    identity = hashlib.sha256(str(package.resolve()).encode()).hexdigest()[:16]
    module_name = f"{_MODULE_PREFIX}{key.replace('-', '_')}_{identity}_{next(_module_sequence)}"
    loader = _VerifiedSourceLoader(module_name, package, "__init__.py", hashes["__init__.py"])
    spec = importlib.util.spec_from_file_location(
        module_name, loader.path, loader=loader, submodule_search_locations=[str(package)]
    )
    if spec is None or spec.loader is None:
        raise IntegrationInstallError(f"Cannot load integration '{key}'")
    before = dict(INTEGRATION_REGISTRY)
    module = importlib.util.module_from_spec(spec)
    _source_packages[module_name] = (package, hashes)
    if _source_finder not in sys.meta_path:
        sys.meta_path.insert(0, _source_finder)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        if INTEGRATION_REGISTRY != before:
            raise IntegrationInstallError("External integrations must not register through import side effects")
        classes = {
            value for value in vars(module).values()
            if isinstance(value, type) and issubclass(value, IntegrationBase)
            and not inspect.isabstract(value)
            and (value.__module__ == module_name or value.__module__.startswith(module_name + "."))
        }
        if len(classes) != 1:
            raise IntegrationInstallError(f"Integration '{key}' must export exactly one IntegrationBase subclass")
        cls = classes.pop()
        if cls.key != key:
            raise IntegrationInstallError(f"Integration '{key}' class key mismatch: {cls.key!r}")
        integration = cls()
        _validate_implementation(integration, descriptor, project_root)
        return integration
    except BaseException as exc:
        INTEGRATION_REGISTRY.clear()
        INTEGRATION_REGISTRY.update(before)
        for name in tuple(sys.modules):
            if name == module_name or name.startswith(module_name + "."):
                del sys.modules[name]
        _source_packages.pop(module_name, None)
        if isinstance(exc, (KeyboardInterrupt, GeneratorExit)):
            raise
        raise IntegrationInstallError(f"Failed to load integration '{key}': {exc}") from exc


@registry_synchronized
def load_installed_integrations(project_root: Path) -> list[str]:
    global _loaded_identity
    if _loading.get():
        return []
    root = Path(project_root).resolve()
    if _pending_root is not None:
        if root != _pending_root:
            raise IntegrationInstallError("Cannot change projects during integration installation")
        return [
            key for key, integration in INTEGRATION_REGISTRY.items()
            if type(integration).__module__.startswith(_MODULE_PREFIX)
        ]
    loading_token = _loading.set(True)
    try:
        records = read_records(root)
        recovery = recovery_exclusion.get()
        excluded = recovery[1] if recovery is not None and recovery[0] == root else None
        selected = {key: info for key, info in records.items() if key != excluded}
        base = safe_project_path(root, _PACKAGES)
        if base.is_dir():
            for child in base.iterdir():
                if child.name.startswith(".install-"):
                    continue
                if child.name not in records:
                    raise IntegrationInstallError(f"Unregistered integration package: {child.name}")
        identity: list[Any] = [str(root), excluded]
        descriptors = {}
        grants = _read_trust(_trust_store(root)) if selected else set()
        for key, info in sorted(selected.items()):
            package = safe_project_path(root, f"{_PACKAGES}/{key}")
            hashes = package_hashes(package)
            if hashes != info["files"]:
                raise IntegrationInstallError(f"Integration '{key}' installed package has been modified")
            if _trust_identity(root, key, hashes) not in grants:
                raise IntegrationInstallError(
                    f"Integration '{key}' has no local trust decision for this project and package. "
                    f"Review its source and run integration upgrade {key} --force --trust-integration "
                    "from an install-enabled catalog to authorize it."
                )
            descriptors[key] = _descriptor(package, key, info)
            identity.append((key, tuple(sorted(hashes.items()))))
        if tuple(identity) == _loaded_identity and all(
            key in INTEGRATION_REGISTRY for key in selected
        ):
            for key in selected:
                _validate_output_paths(INTEGRATION_REGISTRY[key], root)
            return list(selected)
        unload_installed_integrations()
        for key in sorted(selected):
            INTEGRATION_REGISTRY[key] = _import_package(
                safe_project_path(root, f"{_PACKAGES}/{key}"), descriptors[key], records[key]["files"], root
            )
            safe_project_path(root, INTEGRATION_REGISTRY[key].config["folder"].rstrip("/"))
        _loaded_identity = tuple(identity)
        _refresh_configs()
        if excluded is not None and excluded in records:
            binding = recovery_metadata(root, excluded, records[excluded])
            config = binding["registrar_config"] if binding is not None else None
            if config is not None:
                _validate_registrar_config(excluded, config)
                directory = config.get("dir")
                if not isinstance(directory, str):
                    raise IntegrationInstallError("Invalid persisted adapter registration directory")
                safe_project_path(root, directory)
                if Path(directory).parts[0].casefold() in {".git", ".specify"}:
                    raise IntegrationInstallError("Reserved persisted adapter registration directory")
                agents = sys.modules.get("specify_cli.agents")
                if agents is not None:
                    for registrar in (agents.CommandRegistrar, *agents.CommandRegistrar.__subclasses__()):
                        registrar.AGENT_CONFIGS[excluded] = dict(config)
        return list(selected)
    except BaseException:
        unload_installed_integrations()
        raise
    finally:
        _loading.reset(loading_token)


@contextmanager
def catalog_package(root: Path, key: str, *, trusted: bool = False):
    """Download and validate without executing code before explicit consent."""
    validate_key(key)
    if key in BUILTIN_INTEGRATION_KEYS:
        raise IntegrationInstallError(f"Cannot replace built-in integration '{key}'")
    catalog = IntegrationCatalog(root)
    with tempfile.TemporaryDirectory(prefix="speckit-integration-catalog-") as cache:
        catalog.cache_dir = Path(cache)
        info = catalog.get_integration_info(key)
    if info is None:
        raise IntegrationInstallError(f"Unknown integration '{key}' (not found in catalog)")
    if info.get("_install_allowed") is not True:
        raise IntegrationInstallError(f"Integration '{key}' is from a discovery-only catalog")
    url = info.get("download_url")
    if not isinstance(url, str) or not is_https_or_localhost_http(url):
        raise IntegrationInstallError("Integration download_url must use HTTPS or loopback HTTP")
    digest = info.get("sha256")
    if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", digest)):
        raise IntegrationInstallError("Integration sha256 must be a 64-character hex digest")
    for field in ("name", "version", "description"):
        if not isinstance(info.get(field), str) or not info[field].strip():
            raise IntegrationInstallError(f"Integration catalog entry requires {field}")
    try:
        Version(info["version"])
    except ValueError as exc:
        raise IntegrationInstallError(f"Invalid catalog integration version: {exc}") from exc
    if not trusted:
        import typer

        from .._console import console

        console.print(
            "External integration packages execute Python with your user permissions. "
            "Review the package and source before trusting it."
        )
        try:
            consent = typer.confirm(f"Trust integration '{key}' from {url}?", default=False)
        except (typer.Abort, EOFError) as exc:
            raise IntegrationInstallError("Installation requires consent or --trust-integration") from exc
        if not consent:
            raise IntegrationInstallError("Integration installation cancelled; source not trusted")
    from ..authentication.github_http import resolve_github_release_asset_api_url
    from ..authentication.http import github_provider_hosts, open_url

    def reject_insecure_download_redirect(old_url: str, new_url: str) -> None:
        if not is_safe_download_redirect(old_url, new_url):
            raise IntegrationInstallError("Integration download has an unsafe redirect")

    resolved_url = resolve_github_release_asset_api_url(
        url, open_url, timeout=30, github_hosts=github_provider_hosts(),
        redirect_validator=reject_insecure_download_redirect,
    )
    with tempfile.TemporaryDirectory(prefix="speckit-integration-") as temporary:
        directory = Path(temporary)
        with open_url(
            resolved_url or url, timeout=30,
            extra_headers={"Accept": "application/octet-stream"} if resolved_url else None,
            redirect_validator=reject_insecure_download_redirect,
        ) as response:
            final_url = response.geturl()
            if not is_https_or_localhost_http(final_url):
                raise IntegrationInstallError("Integration download redirected to an insecure URL")
            requested_format = archive_format_from_name(url)
            final_format = archive_format_from_name(final_url)
            if requested_format and final_format and requested_format != final_format:
                raise IntegrationInstallError("Integration archive URL format mismatch")
            content_type = response.headers.get("Content-Type")
            content = read_response_limited(response, error_type=IntegrationInstallError, label="integration archive")
        if digest and hashlib.sha256(content).hexdigest() != digest.lower():
            raise IntegrationInstallError("Integration archive SHA-256 mismatch")
        archive = directory / "download.archive"
        archive.write_bytes(content)
        extracted = directory / "extracted"
        safe_extract_archive(
            archive, extracted, source_name=url if requested_format else final_url,
            content_type=content_type, error_type=IntegrationInstallError,
        )
        package = extracted
        if not (package / "integration.yml").is_file():
            children = list(extracted.iterdir())
            if len(children) == 1 and children[0].is_dir():
                package = children[0]
        hashes = package_hashes(package)
        descriptor = _descriptor(package, key, info)
        for tool in descriptor.tools:
            if tool.get("required", True) and shutil.which(tool["name"]) is None:
                raise IntegrationInstallError(f"Integration '{key}' requires missing tool '{tool['name']}'")
        yield package, {
            **descriptor.data["integration"],
            "requires": descriptor.data["requires"],
            "catalog": info["_catalog_name"],
            "download_url": url,
            "sha256": digest,
            "files": hashes,
        }


def persist_package(root: Path, key: str, package: Path, record: dict[str, Any]) -> None:
    """Stage on the destination filesystem; caller owns lifecycle rollback."""
    base = safe_project_path(root, _PACKAGES)
    base.mkdir(parents=True, exist_ok=True)
    destination = safe_project_path(root, f"{_PACKAGES}/{key}")
    with tempfile.TemporaryDirectory(dir=base, prefix=".install-") as temporary:
        staged = Path(temporary) / key
        shutil.copytree(package, staged, ignore=shutil.ignore_patterns("__pycache__"))
        if package_hashes(staged) != record["files"]:
            raise IntegrationInstallError("Integration package changed while staging")
        before_file_change(destination)
        if destination.exists():
            shutil.rmtree(destination)
        os.replace(staged, destination)
        after_file_change(destination)
        records = read_records(root)
        records[key] = record
        write_records(root, records)
        _grant_trust(root, key, record)
    load_installed_integrations(root)
    _grant_trust(root, key, record, record_ownership=True)


def remove_package(root: Path, key: str) -> None:
    records = read_records(root)
    if key not in records:
        return
    directory = safe_project_path(root, f"{_PACKAGES}/{key}")
    before_file_change(directory, removal=True)
    try:
        shutil.rmtree(directory)
    except FileNotFoundError:
        if directory.exists():
            raise
    after_file_change(directory)
    del records[key]
    write_records(root, records)
    load_installed_integrations(root)


@contextmanager
def prepared_adapter(root: Path, key: str, package: Path, record: dict[str, Any]):
    """Expose a trusted candidate only for its project's lifecycle transaction."""
    global _pending_root, _loaded_identity
    _loaded_identity = None
    INTEGRATION_REGISTRY.pop(key, None)
    descriptor = _descriptor(package, key, record)
    integration = _import_package(package, descriptor, record["files"], root)
    safe_project_path(root, integration.config["folder"].rstrip("/"))
    INTEGRATION_REGISTRY[key] = integration
    record["registrar_config"] = {
        **integration.registrar_config,
        "invoke_separator": integration.invoke_separator,
        "dev_no_symlink": integration.dev_no_symlink,
    }
    _pending_root = root.resolve()
    _refresh_configs()
    try:
        yield integration
    finally:
        if _pending_root is not None:
            _pending_root = None
            unload_installed_integrations()
