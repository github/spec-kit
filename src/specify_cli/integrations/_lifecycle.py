"""External-adapter preparation and rollback shared by public lifecycle commands."""

from __future__ import annotations

import inspect
import shutil
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


def _restore_snapshots(root: Path, paths: list[Path], backup: Path, existing: set[int]) -> None:
    for index, path in enumerate(paths):
        installer.safe_project_path(root, path.relative_to(root).as_posix())
        if path == root / ".specify":
            # Keep the lock inode alive while restoring its siblings.
            path.mkdir(parents=True, exist_ok=True)
            for child in path.iterdir():
                if child.name == ".integration-install.lock":
                    continue
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child)
                else:
                    child.unlink()
            if index in existing:
                shutil.copytree(
                    backup / str(index), path, dirs_exist_ok=True, symlinks=True,
                    ignore=shutil.ignore_patterns(".integration-install.lock"),
                )
        else:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            elif path.exists() or path.is_symlink():
                path.unlink()
            if index in existing:
                if (backup / str(index)).is_dir():
                    shutil.copytree(backup / str(index), path, symlinks=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup / str(index), path)


@contextmanager
def _transaction(
    root: Path, target: str | None,
    expected_state: dict[str, Any] | None, expected_records: dict[str, dict[str, Any]],
):
    """Snapshot declared output roots and metadata under an inter-process lock."""
    from ..shared_infra import _exclusive_project_lock
    from .manifest import IntegrationManifest

    folders = {".specify"}
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
                folders.add(Path(relative).parts[0])
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
        specify_existed = (root / ".specify").exists()
        root.mkdir(parents=True, exist_ok=True)
        with _exclusive_project_lock(root, ".integration-install.lock", context="integration"):
            current_state, state_error = try_read_integration_json(root)
            if state_error or current_state != expected_state or installer.read_records(root) != expected_records:
                raise installer.IntegrationInstallError(
                    "Integration state changed while preparing the operation; retry with the current project state"
                )
            existing = set()
            for index, path in enumerate(paths):
                if path.exists() and (path != root / ".specify" or specify_existed):
                    existing.add(index)
                    if path.is_dir():
                        shutil.copytree(path, backup / str(index), symlinks=True)
                    else:
                        shutil.copy2(path, backup / str(index))
            try:
                yield
            except BaseException as operation_error:
                try:
                    _restore_snapshots(root, paths, backup, existing)
                except (OSError, installer.IntegrationInstallError) as restore_error:
                    preserve_backup = True
                    raise installer.IntegrationInstallError(
                        f"Integration operation failed ({operation_error}); rollback failed "
                        f"({restore_error}). Recovery snapshots retained at {backup}; "
                        f"snapshot indexes correspond to {[str(path) for path in paths]}"
                    ) from operation_error
                raise
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
            try:
                installer.load_installed_integrations(root)
                loaded = True
                records = installer.read_records(root)
                state, error = try_read_integration_json(root)
                if error:
                    raise installer.IntegrationInstallError(f"Cannot read integration state: {error.detail}")
                key = key or default_integration_key(state or {})
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

        return invoke
    return decorate
