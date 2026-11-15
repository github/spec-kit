"""Domain install/validation for custom workflow step packages.

This module owns the step-specific behavior shared by every
``specify workflow step add`` source mode (catalog, ``--dev`` local directory,
and ``--from`` archive URL): step-id validation, ``step.yml`` parsing,
registry entries and built-in collisions. The kind-independent mechanics
(directory and symlink safety, package-tree walking and copying, the staged
install flow, locking and replacement) live in
:mod:`specify_cli.workflows._package_install`; the functions below keep the
established step names as thin bindings to it so existing patch points and
messages are unchanged. It is deliberately CLI-independent -- it never prints
and never raises ``typer.Exit``. Callers receive :class:`StepInstallError` and
decide how to surface it.
"""

from __future__ import annotations

import contextlib
import os
import shutil  # noqa: F401 -- ``installer.shutil`` is an established patch point
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from .._package_install import PackageLocation, PackageSpec

# Custom step packages contain executable Python, metadata, and optional helper
# files. These ceilings apply uniformly to catalog, local, and archive sources.
_MAX_STEP_PACKAGE_FILES = 512
_MAX_STEP_PACKAGE_BYTES = 50 * 1024 * 1024  # 50 MiB
_MAX_STEP_PACKAGE_DEPTH = 32

# Files/dirs never inspected, copied into, or counted as part of an installed
# step package; excluded directories are pruned without being entered. Mirrors
# ``bundles/packager.py`` ``EXCLUDE_NAMES``.
EXCLUDE_NAMES: frozenset[str] = frozenset({".git", "__pycache__", ".DS_Store"})

# Prefix for the private same-filesystem working directory created beneath the
# steps base directory. The leading dot keeps it out of the way, and because it
# contains only a ``staged/`` child (never ``step.yml``/``__init__.py`` at its
# root) the runtime loader never mistakes it for an installable package.
_WORK_DIR_PREFIX = ".speckit-step-install-"

_RESERVED_STEP_IDS: frozenset[str] = frozenset({".cache", "step-registry.json"})

_WINDOWS_RESERVED_NAMES: frozenset[str] = frozenset(
    {
        "con",
        "prn",
        "aux",
        "nul",
        "com1",
        "com2",
        "com3",
        "com4",
        "com5",
        "com6",
        "com7",
        "com8",
        "com9",
        "lpt1",
        "lpt2",
        "lpt3",
        "lpt4",
        "lpt5",
        "lpt6",
        "lpt7",
        "lpt8",
        "lpt9",
    }
)

_WINDOWS_INVALID_CHARS: frozenset[str] = frozenset('<>:"|?*')
_SOURCES: frozenset[str] = frozenset({"catalog", "local", "url"})

class StepInstallError(Exception):
    """User-facing step package install/validation failure."""



def _pi():
    """The shared install module, imported on use.

    ``.github/scripts/validate_community_workflow_step.py`` loads this file on
    its own (outside the package) to reuse the id validator and the limits, so
    nothing relative may be imported at module level.
    """
    from .. import _package_install

    return _package_install


def _step_spec() -> PackageSpec:
    """Build the step spec from the module limits at call time.

    Read at call time so a changed ``_MAX_STEP_PACKAGE_*`` is honored.
    """
    from .catalog import StepValidationError

    shared = _pi()
    return shared.PackageSpec(
        noun="Step",
        kind_label="Step type",
        error=StepInstallError,
        limits=shared.PackageLimits(
            _MAX_STEP_PACKAGE_FILES, _MAX_STEP_PACKAGE_BYTES, _MAX_STEP_PACKAGE_DEPTH
        ),
        registry_errors=(StepValidationError, OSError, TypeError, ValueError),
        excludes=EXCLUDE_NAMES,
    )


@contextlib.contextmanager
def _step_install_transaction(project_root: Path):
    """Serialize step directory and registry mutations (install and remove)."""
    with _pi().install_transaction(project_root, _step_spec()):
        yield


# ---------------------------------------------------------------------------
# Step id + base directory validation
# ---------------------------------------------------------------------------


def validate_step_id(step_id: str) -> None:
    """Validate that ``step_id`` is a single safe path component.

    Rejects empty strings, whitespace-only strings, leading/trailing
    whitespace, path separators, ``.``/``..`` components, dotfile prefixes,
    reserved names, Windows-invalid filename characters, trailing dots/spaces,
    and Windows reserved device names.
    """
    stem = step_id.split(".")[0].lower() if step_id else ""
    if (
        not step_id
        or not step_id.strip()
        or step_id != step_id.strip()
        or "/" in step_id
        or "\\" in step_id
        or step_id in (".", "..")
        or step_id.startswith(".")
        or step_id.endswith((".", " "))
        or step_id.lower() in _RESERVED_STEP_IDS
        or stem in _WINDOWS_RESERVED_NAMES
        or any(c in _WINDOWS_INVALID_CHARS for c in step_id)
        or any(ord(c) < 32 for c in step_id)
    ):
        raise StepInstallError(
            f"Invalid step id '{step_id}': must be a single safe "
            "path component (no separators, no leading dot, not a reserved name, "
            "no invalid filename characters)"
        )



def resolve_steps_base_dir(project_root: Path) -> Path:
    """Resolve ``.specify/workflows/steps`` refusing symlinked parent dirs."""
    return _pi().resolve_base_dir(project_root, _step_spec())


def _resolve_step_dir(steps_base_dir: Path, step_id: str) -> Path:
    """Return the canonical destination directory for ``step_id``."""
    return _pi().resolve_destination(steps_base_dir, step_id, _step_spec())


def _reject_unsafe_destination(step_dir: Path) -> None:
    """Refuse a symlink (including dangling) or non-directory destination."""
    _pi().reject_unsafe_destination(step_dir, _step_spec())


# ---------------------------------------------------------------------------
# Package shape + safety validation
# ---------------------------------------------------------------------------


def _entry_limit_error() -> StepInstallError:
    return _pi().entry_limit_error(_step_spec())


def _scan_retained_entries(directory: Path, budget: int) -> list[os.DirEntry]:
    return _pi().scan_retained_entries(directory, budget, _step_spec())


def _walk_package_tree(package_dir: Path):
    """Yield ``(path, is_dir)`` for every retained descendant of *package_dir*."""
    return _pi().walk_package_tree(package_dir, _step_spec())


def _parse_step_metadata(step_yml_text: str, step_id: str) -> dict[str, Any]:
    """Parse and validate ``step.yml``, returning the ``step`` mapping."""
    try:
        # ``safe_load`` returns None for BOTH an empty document and an explicit
        # null scalar (``null``, ``~``, ``NULL``), so it cannot tell them apart
        # on its own. ``compose`` yields no node only for a genuinely empty
        # document.
        node = yaml.compose(step_yml_text)
        meta = yaml.safe_load(step_yml_text)
        is_empty_document = node is None or (
            meta is None
            and isinstance(node, yaml.nodes.ScalarNode)
            and node.value == ""
            and node.start_mark.index == node.end_mark.index
        )
    except Exception as exc:
        raise StepInstallError(f"Invalid step.yml: {exc}") from exc

    # Do NOT coerce with ``or {}`` here: that also turns a FALSY non-mapping
    # (top-level ``[]``, ``false``, ``0``, ``''``, or an explicit ``null``)
    # into ``{}`` and silently bypasses this shape check. Only a genuinely
    # empty document defaults to ``{}``.
    if meta is None and is_empty_document:
        meta = {}
    elif not isinstance(meta, dict):
        raise StepInstallError("step.yml must be a YAML mapping")

    step_meta = meta.get("step", {})
    if not isinstance(step_meta, dict):
        raise StepInstallError("step.yml 'step' field must be a mapping")
    type_key = step_meta.get("type_key", "")
    if not type_key:
        raise StepInstallError("step.yml missing 'step.type_key' field")
    if type_key != step_id:
        raise StepInstallError(
            f"step.yml type_key ({type_key!r}) does not match step ID ({step_id!r})"
        )
    return step_meta


def validate_step_package(package_dir: Path, step_id: str) -> dict[str, Any]:
    """Validate a materialized step package directory.

    Returns the validated ``step.yml`` ``step`` mapping. Raises
    :class:`StepInstallError` on any shape, symlink, limit, path, or identity
    violation. Never imports or executes ``__init__.py``.
    """
    package_dir = Path(package_dir)
    _pi().check_package_shape(package_dir, _step_spec(), ("step.yml", "__init__.py"))

    try:
        step_yml_text = (package_dir / "step.yml").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise StepInstallError(f"Invalid step.yml: {exc}") from exc

    return _parse_step_metadata(step_yml_text, step_id)


def resolve_package_root(extracted_root: Path) -> Path:
    """Resolve a root-level or single-nested step package directory."""
    return _pi().resolve_package_root(extracted_root, _step_spec(), "step.yml")


# ---------------------------------------------------------------------------
# Collision / duplicate preflight
# ---------------------------------------------------------------------------


def _reject_builtin_collision(step_id: str) -> None:
    from .. import BUILTIN_STEP_TYPES

    if step_id in BUILTIN_STEP_TYPES:
        raise StepInstallError(
            f"Step type '{step_id}' conflicts with a built-in step type"
        )



def _check_duplicate(
    registry: Any, step_id: str, step_dir: Path, *, force: bool
) -> None:
    _pi().check_duplicate(registry, step_id, step_dir, force=force, spec=_step_spec())


def _locate(project_root: Path, step_id: str) -> PackageLocation:
    """Validate the id and resolve its base directory and destination slot."""
    validate_step_id(step_id)
    steps_base_dir = resolve_steps_base_dir(project_root)
    step_dir = _resolve_step_dir(steps_base_dir, step_id)
    _reject_unsafe_destination(step_dir)
    return _pi().PackageLocation(steps_base_dir, step_dir)


def _open_registry(project_root: Path):
    from .catalog import StepRegistry

    return StepRegistry(project_root)


def _check_destination(
    registry: Any, step_id: str, location: PackageLocation, *, force: bool
) -> None:
    _reject_builtin_collision(step_id)
    _check_duplicate(registry, step_id, location.destination, force=force)


def check_installable(project_root: Path, step_id: str, *, force: bool = False) -> Path:
    """Advisory preflight shared by all sources.

    Validates the id, base directory, built-in collision, and
    duplicate/orphan-destination state without touching the package. The CLI
    uses this to reject before a download; :func:`install_step_package`
    re-runs the same checks as defense-in-depth.
    """
    location = _locate(project_root, step_id)
    _check_destination(_open_registry(project_root), step_id, location, force=force)
    return location.destination


# ---------------------------------------------------------------------------
# Staging + commit
# ---------------------------------------------------------------------------


def _build_entry(
    step_id: str,
    step_meta: Mapping[str, Any],
    *,
    source: str,
    catalog_name: str,
    catalog_metadata: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if source not in _SOURCES:
        raise StepInstallError(
            "Step install source must be one of: catalog, local, url"
        )
    if source == "catalog" and not isinstance(catalog_name, str):
        raise StepInstallError("Catalog step install requires a string catalog name")
    if catalog_metadata is not None and not isinstance(catalog_metadata, Mapping):
        raise StepInstallError("Catalog step metadata must be a mapping")
    catalog_metadata = catalog_metadata or {}

    def _string_value(metadata: Mapping[str, Any], field: str) -> str | None:
        value = metadata.get(field)
        if value is None:
            return None
        if not isinstance(value, str):
            raise StepInstallError(
                f"step metadata '{field}' must be a string when present"
            )
        return value

    type_key = _string_value(step_meta, "type_key")
    if not type_key:
        raise StepInstallError("step.yml missing 'step.type_key' field")
    package_values = {
        field: _string_value(step_meta, field)
        for field in ("name", "version", "description", "author")
    }
    catalog_values = {
        field: _string_value(catalog_metadata, field)
        for field in ("name", "version", "description", "author")
    }
    entry: dict[str, Any] = {
        "name": catalog_values["name"] or package_values["name"] or step_id,
        "version": catalog_values["version"] or package_values["version"] or "0.0.0",
        "description": (
            catalog_values["description"]
            if catalog_values["description"] is not None
            else package_values["description"] or ""
        ),
        "author": (
            catalog_values["author"]
            if catalog_values["author"] is not None
            else package_values["author"] or ""
        ),
        "type_key": type_key,
        "source": source,
    }
    if source == "catalog":
        entry["catalog_name"] = catalog_name
    return entry



def _copy_package_tree(source_dir: Path, target_dir: Path) -> None:
    """Copy *source_dir* into *target_dir*, skipping excludes (never follows symlinks)."""
    _pi().copy_package_tree(
        source_dir,
        target_dir,
        _step_spec(),
        copy_file=lambda *args: _copy_regular_file(*args),
    )


def _copy_regular_file(
    source: str, target: Path, expected_mode: int, remaining_bytes: int
) -> int:
    """Copy an inspected regular file within the remaining package byte budget."""
    return _pi().copy_regular_file(
        source, target, expected_mode, remaining_bytes, _step_spec()
    )


def _replace_install(
    step_dir: Path,
    staged_dir: Path,
    registry: Any,
    step_id: str,
    entry: dict[str, Any],
    *,
    force: bool,
) -> None:
    """Publish the staged package and record its registry entry."""
    _pi().replace_install(
        step_dir, staged_dir, registry, step_id, entry, force=force, spec=_step_spec()
    )


def install_step_package(
    project_root: Path,
    step_id: str,
    package_dir: Path,
    *,
    source: str,
    catalog_name: str = "",
    catalog_metadata: Mapping[str, Any] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Validate, stage, and commit a step package from any source.

    ``source`` is exactly ``"catalog"``, ``"local"``, or ``"url"``. Returns the
    registry entry that was persisted.
    """
    # Every member is looked up when called so the established patch points on
    # this module (``_copy_package_tree``, ``_replace_install``,
    # ``_step_install_transaction``, ``validate_step_package``, ...) still apply.
    shared = _pi()
    rules = shared.PackageRules(
        locate=lambda root, sid: _locate(root, sid),
        open_registry=lambda root: _open_registry(root),
        check_destination=lambda *a, **k: _check_destination(*a, **k),
        validate=lambda path, sid: validate_step_package(path, sid),
        build_entry=lambda step_meta: _build_entry(
            step_id,
            step_meta,
            source=source,
            catalog_name=catalog_name,
            catalog_metadata=catalog_metadata,
        ),
    )
    ops = shared.StagingOps(
        copy=lambda src, dst: _copy_package_tree(src, dst),
        publish=lambda *a, **k: _replace_install(*a, **k),
        transaction=lambda root: _step_install_transaction(root),
    )
    return shared.install_package(
        shared.InstallRequest(project_root, step_id, Path(package_dir), force),
        _step_spec(),
        rules,
        ops,
    )
