"""External-adapter preparation and rollback shared by public lifecycle commands."""

from __future__ import annotations

import hashlib
import inspect
import os
import shutil
import stat
import tempfile
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from functools import wraps
from pathlib import Path
from typing import Any

import typer
from rich.markup import escape

from .._console import console
from ..integration_state import (
    default_integration_key,
    installed_integration_keys,
    try_read_integration_json,
)
from . import BUILTIN_INTEGRATION_KEYS, INTEGRATION_REGISTRY, installer
from ._file_changes import file_change_observer

_init_directory: ContextVar[tuple[Path, bool, list[Path]] | None] = ContextVar(
    "external_integration_init_directory", default=None
)
_success_messages: ContextVar[list[str] | None] = ContextVar(
    "external_integration_success_messages", default=None
)


def lifecycle_success(message: str) -> None:
    """Report success only after an external package transaction commits."""
    pending = _success_messages.get()
    if pending is None:
        console.print(message)
    else:
        pending.append(message)


def initial_directory_state(path: Path) -> tuple[bool, list[Path]] | None:
    """Init validation sees the directory before the lifecycle lock created it."""
    state = _init_directory.get()
    if state is not None and state[0] == path:
        return state[1], state[2]
    return None


def _file_identity(path: Path):
    if path.is_symlink():
        return ("link", os.readlink(path))
    try:
        mode = path.stat().st_mode
    except FileNotFoundError:
        return None
    if stat.S_ISDIR(mode):
        return ("directory", tuple(
            (child.name, _file_identity(child)) for child in sorted(path.iterdir())
        ))
    if not stat.S_ISREG(mode):
        raise installer.IntegrationInstallError(f"Unsupported integration output: {path}")
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return ("file", digest)


class _FileJournal:
    """Restore observed owned writes, never every file under an output root."""

    def __init__(self, root: Path, paths: list[Path], backup: Path, existing: set[int]):
        self.root = root
        self.paths = paths
        self.backup = backup
        self.existing = existing
        self.changes: dict[Path, tuple[Path | None, Any]] = {}
        self.pending: set[Path] = set()

    def safe_path(self, path: Path) -> Path:
        path = path.absolute()
        relative = path.relative_to(self.root).as_posix()
        # A removable leaf symlink is owned as a link, not as its target.
        if "/" in relative:
            installer.safe_project_path(self.root, relative.rsplit("/", 1)[0])
        return path

    def observe(self, path: Path, before: bool) -> None:
        path = self.safe_path(path)
        if (
            before and path in self.changes and path not in self.pending
            and _file_identity(path) != self.changes[path][1]
        ):
            raise installer.IntegrationInstallError(
                f"Integration output changed during the operation; refusing to overwrite {path}"
            )
        if path not in self.changes:
            saved = None
            if before:
                if path.exists() or path.is_symlink():
                    saved = self.backup / "writes" / str(len(self.changes))
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    if path.is_symlink():
                        saved.symlink_to(os.readlink(path))
                    elif path.is_dir():
                        shutil.copytree(path, saved, symlinks=True)
                    else:
                        shutil.copy2(path, saved)
            else:
                # record_existing() follows a write performed by an adapter.
                for index, scope in enumerate(self.paths):
                    if path == scope or scope in path.parents:
                        candidate = self.backup / str(index) / path.relative_to(scope)
                        if index in self.existing and (candidate.exists() or candidate.is_symlink()):
                            saved = candidate
                        break
                else:
                    raise installer.IntegrationInstallError(
                        f"Integration output {path} must use manifest.record_file() "
                        "or the host file-writing helpers outside its declared output root"
                    )
            self.changes[path] = (saved, _file_identity(path))
        if not before:
            saved, _ = self.changes[path]
            self.changes[path] = (saved, _file_identity(path))
            self.pending.discard(path)
        else:
            self.pending.add(path)


def _restore_snapshots(root: Path, journal: _FileJournal) -> list[Path]:
    conflicts = []
    for path, (saved, written_identity) in reversed(tuple(journal.changes.items())):
        journal.safe_path(path)
        if path not in journal.pending and _file_identity(path) != written_identity:
            conflicts.append(path)
            continue
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        elif path.exists() or path.is_symlink():
            path.unlink()
        if saved is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            if saved.is_symlink():
                path.symlink_to(os.readlink(saved))
            elif saved.is_dir():
                shutil.copytree(saved, path, symlinks=True)
            else:
                shutil.copy2(saved, path)
        else:
            parent = path.parent
            while parent != root:
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent
    return conflicts


@contextmanager
def _transaction(
    root: Path, target: str | None,
    expected_state: dict[str, Any] | None, expected_records: dict[str, dict[str, Any]],
):
    """Journal operation-owned writes under an inter-process integration lock."""
    from ..shared_infra import _exclusive_project_lock
    from .manifest import IntegrationManifest

    folders = {
        ".specify/integrations", ".specify/templates", ".specify/scripts",
        ".specify/.gitignore",
    }
    state, error = try_read_integration_json(root)
    if error:
        raise installer.IntegrationInstallError(f"Cannot read integration state: {error.detail}")
    for key in installed_integration_keys(state or {}):
        integration = INTEGRATION_REGISTRY.get(key)
        folder = (integration.config or {}).get("folder") if integration else None
        if folder:
            folders.add(folder.rstrip("/"))
        manifest_path = root / ".specify" / "integrations" / f"{key}.manifest.json"
        if manifest_path.exists():
            manifest = IntegrationManifest.load(key, root)
            for relative in manifest.files:
                installer.safe_project_path(root, relative)
                folders.add(relative)
    for integration in INTEGRATION_REGISTRY.values():
        if type(integration).__module__.startswith(installer._MODULE_PREFIX):
            folders.add(integration.config["folder"].rstrip("/"))
    target_integration = INTEGRATION_REGISTRY.get(target)
    target_folder = (target_integration.config or {}).get("folder") if target_integration else None
    if target_folder:
        folders.add(target_folder.rstrip("/"))
    paths = [installer.safe_project_path(root, folder) for folder in sorted(folders)]
    paths = [path for path in paths if not any(other != path and other in path.parents for other in paths)]
    backup = Path(tempfile.mkdtemp(prefix="speckit-integration-rollback-"))
    preserve_backup = False
    try:
        root.mkdir(parents=True, exist_ok=True)
        with _exclusive_project_lock(root, ".integration-install.lock", context="integration"):
            current_state, state_error = try_read_integration_json(root)
            if state_error or current_state != expected_state or installer.read_records(root) != expected_records:
                raise installer.IntegrationInstallError(
                    "Integration state changed while preparing the operation; retry with the current project state"
                )
            existing = set()
            for index, path in enumerate(paths):
                if path.exists():
                    existing.add(index)
                    if path.is_dir():
                        shutil.copytree(path, backup / str(index), symlinks=True)
                    else:
                        shutil.copy2(path, backup / str(index))
            journal = _FileJournal(root, paths, backup, existing)
            token = file_change_observer.set(journal.observe)
            try:
                yield
            except BaseException as operation_error:
                try:
                    # Restoration itself must not add writes to the journal.
                    file_change_observer.reset(token)
                    token = None
                    conflicts = _restore_snapshots(root, journal)
                    if conflicts:
                        preserve_backup = True
                        console.print(
                            "[yellow]Warning:[/yellow] Preserved concurrent edits to "
                            f"{escape(str(conflicts))}. Recovery snapshots retained at {escape(str(backup))}"
                        )
                except (OSError, installer.IntegrationInstallError) as restore_error:
                    preserve_backup = True
                    raise installer.IntegrationInstallError(
                        f"Integration operation failed ({operation_error}); rollback failed "
                        f"({restore_error}). Recovery snapshots retained at {backup}; "
                        f"snapshot indexes correspond to {[str(path) for path in paths]}"
                    ) from operation_error
                raise
            finally:
                if token is not None:
                    file_change_observer.reset(token)
    finally:
        if not preserve_backup:
            shutil.rmtree(backup)


def external_lifecycle(operation: str):
    """Add package preparation to existing handlers without duplicating setup."""
    def decorate(handler):
        signature = inspect.signature(handler)

        @wraps(handler)
        def invoke(*args, **kwargs):
            values = signature.bind_partial(*args, **kwargs).arguments
            loaded = False
            if operation == "init":
                project_name = values.get("project_name")
                here = values.get("here", False) or project_name == "."
                if (here and project_name not in (None, ".")) or (not here and not project_name):
                    return handler(*args, **kwargs)
                root = Path.cwd() if here else Path(project_name).resolve()
                key = values.get("integration")
            else:
                from .. import _require_specify_project

                root = _require_specify_project()
                key = values.get("target" if operation == "switch" else "key")
            recovery_token = None
            try:
                records = installer.read_records(root)
                state, error = try_read_integration_json(root)
                if error:
                    raise installer.IntegrationInstallError(f"Cannot read integration state: {error.detail}")
                key = key or default_integration_key(state or {})
                try:
                    installer.load_installed_integrations(root)
                except installer.IntegrationInstallError:
                    if operation not in {"upgrade", "uninstall"} or not values.get("force") or key not in records:
                        raise
                    recovery_token = installer.recovery_exclusion.set((root.resolve(), key))
                    installer.load_installed_integrations(root)
                    console.print(
                        f"[yellow]Warning:[/yellow] Recovering integration '{escape(key)}' "
                        "from validated ownership metadata without loading its failed implementation."
                    )
                loaded = True
                download = (
                    isinstance(key, str)
                    and key not in BUILTIN_INTEGRATION_KEYS
                    and (
                        (operation == "upgrade" and key in records)
                        or (
                            operation in {"init", "install", "switch"}
                            and key not in INTEGRATION_REGISTRY
                        )
                    )
                )
                if not records and not download:
                    return handler(*args, **kwargs)
                with ExitStack() as stack:
                    messages: list[str] = []
                    message_token = _success_messages.set(messages)
                    stack.callback(_success_messages.reset, message_token)
                    candidate = None
                    if download:
                        package, record = stack.enter_context(
                            installer.catalog_package(
                                root, key, trusted=values.get("trust_integration", False)
                            )
                        )
                        candidate = (package, record)
                        stack.enter_context(installer.prepared_adapter(root, key, package, record))
                        if recovery_token is not None:
                            installer.recovery_exclusion.set(None)
                    if operation == "init":
                        token = _init_directory.set(
                            (root, root.exists(), list(root.iterdir()) if root.is_dir() else [])
                        )
                        stack.callback(_init_directory.reset, token)
                    with _transaction(root, key, state, records):
                        try:
                            result = handler(*args, **kwargs)
                        except typer.Exit as exc:
                            if exc.exit_code != 0:
                                raise
                            if candidate:
                                exited_state, exited_error = try_read_integration_json(root)
                                if exited_error:
                                    raise installer.IntegrationInstallError(exited_error.detail) from exc
                                if key not in installed_integration_keys(exited_state or {}):
                                    raise
                            result = None
                        new_state, new_error = try_read_integration_json(root)
                        if new_error:
                            raise installer.IntegrationInstallError(
                                f"Cannot read integration state after {operation}: {new_error.detail}"
                            )
                        remaining = installed_integration_keys(new_state or {})
                        if candidate:
                            if key not in remaining:
                                raise installer.IntegrationInstallError(
                                    f"Integration {operation} did not install the requested adapter '{key}'"
                                )
                            # End temporary registration before loading durable code.
                            installer._pending_root = None
                            installer.unload_installed_integrations()
                            installer.persist_package(root, key, *candidate)
                        for removed in records.keys() - set(remaining):
                            if operation == "uninstall":
                                from ._helpers import (
                                    _unregister_extensions_for_agent,
                                    _unregister_presets_for_agent,
                                )

                                _unregister_extensions_for_agent(
                                    root, removed,
                                    continuing="The adapter was removed, but extension artifacts may need manual cleanup.",
                                )
                                _unregister_presets_for_agent(
                                    root, removed,
                                    continuing="The adapter was removed, but preset artifacts may need manual cleanup.",
                                )
                            installer.remove_package(root, removed)
                        if operation == "uninstall" and key in records and key == default_integration_key(state or {}):
                            fallback = default_integration_key(new_state or {})
                            if fallback:
                                from ._helpers import (
                                    _register_extensions_for_agent,
                                    _register_presets_for_agent,
                                )

                                _register_extensions_for_agent(
                                    root, fallback,
                                    continuing="The fallback integration was selected, but extensions may need re-registration.",
                                )
                                _register_presets_for_agent(
                                    root, fallback,
                                    continuing="The fallback integration was selected, but presets may need re-registration.",
                                )
                        if not candidate:
                            installer.load_installed_integrations(root)
                    for message in messages:
                        console.print(message)
                    return result
            except typer.Exit:
                raise
            except (Exception, SystemExit) as exc:
                console.print(f"[red]Error:[/red] Integration {operation} failed: {escape(str(exc))}")
                raise typer.Exit(1) from exc
            finally:
                # prepared_adapter's context exits after the transaction; restore
                # durable registrations rather than leave the candidate cached.
                if loaded:
                    try:
                        installer.load_installed_integrations(root)
                    except (installer.IntegrationInstallError, OSError) as exc:
                        console.print(
                            f"[red]Error:[/red] Could not reload integration state after {operation}: {escape(str(exc))}"
                        )
                        raise typer.Exit(1) from exc
                    finally:
                        if recovery_token is not None:
                            installer.recovery_exclusion.reset(recovery_token)
                elif recovery_token is not None:
                    installer.recovery_exclusion.reset(recovery_token)

        return invoke
    return decorate
