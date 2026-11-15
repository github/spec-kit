"""Function-specific installation rules for workflow function packages.

The staged install flow, copy, locking and replacement are shared with step
packages in :mod:`specify_cli.workflows._package_install`. This module supplies
only what is specific to functions: the ``function.yml`` manifest, the export
name checks (D4) and the registry metadata. Installing never imports the
package.
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Any

from .. import _package_install as _pi
from .._package_install import (
    InstallRequest,
    PackageLimits,
    PackageLocation,
    PackageRules,
    PackageSpec,
)
from ._domain import (
    _RESERVED_FUNCTION_IDS,
    FunctionManifest,
    FunctionRegistry,
    WorkflowFunctionError,
    _validate_function_id,
    parse_function_manifest,
)

_MAX_FUNCTION_PACKAGE_FILES = 512
_MAX_FUNCTION_PACKAGE_BYTES = 50 * 1024 * 1024
_MAX_FUNCTION_PACKAGE_DEPTH = 32

_SOURCES = frozenset({"local", "url"})


def _function_spec() -> PackageSpec:
    """Build the function spec from the module limits at call time."""
    return PackageSpec(
        noun="Function",
        kind_label="Function package",
        error=WorkflowFunctionError,
        limits=PackageLimits(
            _MAX_FUNCTION_PACKAGE_FILES,
            _MAX_FUNCTION_PACKAGE_BYTES,
            _MAX_FUNCTION_PACKAGE_DEPTH,
        ),
    )


@contextlib.contextmanager
def _function_install_transaction(project_root: Path):
    """Serialize function directory and registry mutations (install and remove)."""
    with _pi.install_transaction(project_root, _function_spec()):
        yield


def _resolve_functions_dir(project_root: Path) -> Path:
    """Resolve ``.specify/workflows/functions`` refusing symlinked parents."""
    return _pi.resolve_base_dir(project_root, _function_spec())


def validate_function_package(package_dir: Path, function_id: str) -> FunctionManifest:
    """Validate a materialized package without importing its Python module."""
    package_dir = Path(package_dir)
    _pi.check_package_shape(package_dir, _function_spec(), ("function.yml", "__init__.py"))
    try:
        text = (package_dir / "function.yml").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise WorkflowFunctionError(f"Invalid function.yml: {exc}") from exc
    return parse_function_manifest(text, function_id)


def resolve_package_root(extracted_root: Path) -> Path:
    """Resolve a root-level or single-nested function package directory."""
    return _pi.resolve_package_root(extracted_root, _function_spec(), "function.yml")


def _locate(project_root: Path, function_id: str) -> PackageLocation:
    spec = _function_spec()
    _validate_function_id(function_id)
    base_dir = _resolve_functions_dir(project_root)
    destination = _pi.resolve_destination(base_dir, function_id, spec)
    _pi.reject_unsafe_destination(destination, spec)
    return PackageLocation(base_dir, destination)


def _check_destination(
    registry: FunctionRegistry,
    function_id: str,
    location: PackageLocation,
    *,
    force: bool,
) -> None:
    _pi.check_duplicate(
        registry, function_id, location.destination, force=force, spec=_function_spec()
    )


def _claimed_names(registry: FunctionRegistry, own_id: str) -> dict[str, tuple[str, bool]]:
    """Map each function name to ``(package id, found only on disk)``.

    The registry is not the whole truth: the loader imports every package
    directory it finds, so a hand-copied package or one whose registry entry was
    lost still claims its names. Directories the loader would skip (symlinks,
    missing files, invalid manifests) claim nothing. *own_id* is the package
    being installed or replaced and never conflicts with itself.
    """
    claimed: dict[str, tuple[str, bool]] = {}
    for package_id, metadata in registry.list().items():
        if package_id == own_id or not isinstance(metadata, dict):
            continue
        for item in metadata.get("functions", []):
            name = item.get("name") if isinstance(item, dict) else item
            if isinstance(name, str):
                claimed.setdefault(name, (package_id, False))

    base_dir = registry.base_dir
    try:
        package_dirs = sorted(base_dir.iterdir(), key=lambda path: path.name)
    except OSError:
        return claimed
    for package_dir in package_dirs:
        if package_dir.name == own_id or package_dir.name in _RESERVED_FUNCTION_IDS:
            continue
        manifest_path = package_dir / "function.yml"
        init_path = package_dir / "__init__.py"
        if (
            package_dir.is_symlink()
            or not package_dir.is_dir()
            or manifest_path.is_symlink()
            or init_path.is_symlink()
            or not manifest_path.is_file()
            or not init_path.is_file()
        ):
            continue
        try:
            manifest = parse_function_manifest(
                manifest_path.read_text(encoding="utf-8"), package_dir.name
            )
        except (OSError, UnicodeError, WorkflowFunctionError):
            continue
        for export in manifest.exports:
            claimed.setdefault(export.name, (package_dir.name, True))
    return claimed


def _check_exports(
    registry: FunctionRegistry,
    function_id: str,
    manifest: FunctionManifest,
    *,
    force: bool,
) -> None:
    """Reject exports that shadow a built-in or a package already installed (D4)."""
    from ..expressions.filters import BUILTIN_FILTERS

    claimed = _claimed_names(registry, manifest.id)
    for export in manifest.exports:
        if export.name in BUILTIN_FILTERS:
            raise WorkflowFunctionError(
                f"Workflow function '{export.name}' conflicts with a built-in filter"
            )
        if export.name in claimed:
            package_id, on_disk_only = claimed[export.name]
            where = " (found on disk, not in the registry)" if on_disk_only else ""
            raise WorkflowFunctionError(
                f"Workflow function '{export.name}' is already provided by "
                f"package '{package_id}'{where}"
            )


def check_installable(project_root: Path, function_id: str, *, force: bool = False) -> Path:
    """Advisory preflight used by the CLI before any download."""
    location = _locate(project_root, function_id)
    _check_destination(FunctionRegistry(project_root), function_id, location, force=force)
    return location.destination


def _metadata(manifest: FunctionManifest, source: str) -> dict[str, Any]:
    if source not in _SOURCES:
        raise WorkflowFunctionError("Function install source must be 'local' or 'url'")
    return {
        "name": manifest.name or manifest.id,
        "version": manifest.version,
        "description": manifest.description,
        "source": source,
        "functions": [
            {
                "name": export.name,
                "handler": export.handler,
                "min_args": export.min_args,
                "max_args": export.max_args,
                "description": export.description,
            }
            for export in manifest.exports
        ],
    }


def install_function_package(
    project_root: Path,
    function_id: str,
    package_dir: Path,
    *,
    source: str,
    force: bool = False,
) -> dict[str, Any]:
    """Validate, copy, and register a function package without importing it."""
    rules = PackageRules(
        locate=_locate,
        open_registry=FunctionRegistry,
        check_destination=_check_destination,
        validate=lambda path, fid: validate_function_package(path, fid),
        build_entry=lambda manifest: _metadata(manifest, source),
        check_contents=lambda registry, fid, manifest, *, force: _check_exports(
            registry, fid, manifest, force=force
        ),
    )
    return _pi.install_package(
        InstallRequest(project_root, function_id, Path(package_dir), force),
        _function_spec(),
        rules,
        _pi.StagingOps(
            copy=lambda src, dst: _pi.copy_package_tree(src, dst, _function_spec()),
            publish=lambda *a, **k: _pi.replace_install(*a, spec=_function_spec(), **k),
            transaction=lambda root: _function_install_transaction(root),
        ),
    )
