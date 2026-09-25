"""Domain install/validation for custom workflow step packages.

This module owns the source-independent behavior shared by every
``specify workflow step add`` source mode (catalog, ``--dev`` local directory,
and ``--from`` archive URL): step-id and base-directory validation, package
shape/symlink/limit validation, staging, atomic commit, and registry
provenance. It is deliberately CLI-independent -- it never prints and never
raises ``typer.Exit``. Callers receive :class:`StepInstallError` and decide how
to surface it.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import stat
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

# Custom step packages contain executable Python, metadata, and optional helper
# files. These ceilings apply uniformly to catalog, local, and archive sources.
_MAX_STEP_PACKAGE_FILES = 512
_MAX_STEP_PACKAGE_BYTES = 50 * 1024 * 1024  # 50 MiB

# Files/dirs never copied into (or counted as part of) an installed step
# package. Mirrors ``bundles/packager.py`` ``EXCLUDE_NAMES``.
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


@contextlib.contextmanager
def _step_install_transaction(project_root: Path):
    """Serialize step directory swaps with their registry updates."""
    from ...shared_infra import _ensure_safe_shared_directory

    lock_dir = Path(project_root) / ".specify"
    try:
        _ensure_safe_shared_directory(
            Path(project_root), lock_dir, context="step install lock directory"
        )
    except ValueError as exc:
        raise StepInstallError(str(exc)) from exc
    lock_file = lock_dir / ".step-install.lock"
    if lock_file.is_symlink():
        raise StepInstallError(f"Refusing to use symlinked step install lock: {lock_file}")

    flags = os.O_RDWR | os.O_CREAT
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(lock_file, flags, 0o600)
    except OSError as exc:
        raise StepInstallError(f"Failed to open step install lock: {exc}") from exc
    try:
        if lock_file.is_symlink():
            raise StepInstallError(
                f"Refusing to use symlinked step install lock: {lock_file}"
            )
        if os.name == "nt":
            import errno
            import msvcrt
            import time

            if os.fstat(fd).st_size == 0:
                os.write(fd, b"\0")
            while True:
                os.lseek(fd, 0, os.SEEK_SET)
                try:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                    break
                except OSError as exc:
                    if exc.errno not in (errno.EACCES, errno.EDEADLK):
                        raise
                    time.sleep(0.05)
        else:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    except StepInstallError:
        raise
    except OSError as exc:
        raise StepInstallError(f"Failed to lock step installation: {exc}") from exc
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


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
    project_root = Path(project_root)
    project_root_resolved = project_root.resolve()
    steps_base_dir_unresolved = project_root / ".specify" / "workflows" / "steps"

    current = project_root
    for part in (".specify", "workflows", "steps"):
        current = current / part
        if current.is_symlink():
            raise StepInstallError(
                f"Refusing to use symlinked step directory '{current}'"
            )
        if current.exists() and not current.is_dir():
            raise StepInstallError(
                f"Step directory path is not a directory: '{current}'"
            )

    steps_base_dir = steps_base_dir_unresolved.resolve()
    try:
        steps_base_dir.relative_to(project_root_resolved)
    except ValueError:
        raise StepInstallError(
            f"Step directory escapes project root: '{steps_base_dir}'"
        ) from None

    return steps_base_dir


def _resolve_step_dir(steps_base_dir: Path, step_id: str) -> Path:
    """Return the canonical destination directory for ``step_id``."""
    step_dir = steps_base_dir / step_id
    try:
        rel_parts = step_dir.relative_to(steps_base_dir).parts
    except ValueError:
        raise StepInstallError(f"Invalid step id '{step_id}'") from None
    if rel_parts != (step_id,):
        raise StepInstallError(f"Invalid step id '{step_id}'")
    return step_dir


def _reject_unsafe_destination(step_dir: Path) -> None:
    """Refuse a symlink (including dangling) or non-directory destination."""
    if step_dir.is_symlink():
        raise StepInstallError(
            f"Refusing to install step through a symlinked path: '{step_dir}'"
        )
    if step_dir.exists() and not step_dir.is_dir():
        raise StepInstallError(
            f"Step install path exists but is not a directory: '{step_dir}'"
        )


# ---------------------------------------------------------------------------
# Package shape + safety validation
# ---------------------------------------------------------------------------


def _walk_package_tree(package_dir: Path):
    """Yield ``(path, is_dir, excluded)`` for every descendant of *package_dir*.

    Descends into excluded directories so a symlink or special file hiding
    inside ``.git``/``__pycache__`` is still rejected, but never follows a
    symlink. Raises :class:`StepInstallError` on any symlink or object that is
    neither a regular file nor a directory.
    """

    def _walk(current: Path, excluded_prefix: bool):
        try:
            entries = sorted(os.scandir(current), key=lambda entry: entry.name)
        except OSError as exc:
            raise StepInstallError(
                f"Failed to read step package directory '{current}': {exc}"
            ) from exc
        for entry in entries:
            try:
                mode = entry.stat(follow_symlinks=False).st_mode
            except OSError as exc:
                raise StepInstallError(
                    f"Failed to inspect step package entry '{entry.path}': {exc}"
                ) from exc
            path = Path(entry.path)
            if stat.S_ISLNK(mode):
                raise StepInstallError(f"Step package contains symlink: {path}")
            excluded = excluded_prefix or entry.name in EXCLUDE_NAMES
            if stat.S_ISDIR(mode):
                yield path, True, excluded
                yield from _walk(path, excluded)
            elif stat.S_ISREG(mode):
                yield path, False, excluded
            else:
                raise StepInstallError(
                    f"Step package contains unsupported file: {path}"
                )

    yield from _walk(package_dir, False)


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

    if package_dir.is_symlink():
        raise StepInstallError(
            f"Refusing to install from a symlinked package directory: '{package_dir}'"
        )
    if not package_dir.is_dir():
        raise StepInstallError(f"Step package directory not found: '{package_dir}'")

    for required in ("step.yml", "__init__.py"):
        required_path = package_dir / required
        if required_path.is_symlink():
            raise StepInstallError(
                f"Step package '{required}' must be a regular file, not a symlink"
            )
        if not required_path.is_file():
            raise StepInstallError(
                f"Step package is missing required file '{required}' at its root"
            )

    retained_files = 0
    retained_bytes = 0
    for path, is_dir, excluded in _walk_package_tree(package_dir):
        if is_dir or excluded:
            continue
        retained_files += 1
        try:
            retained_bytes += path.lstat().st_size
        except OSError as exc:
            raise StepInstallError(
                f"Failed to inspect step package file '{path}': {exc}"
            ) from exc

    if retained_files > _MAX_STEP_PACKAGE_FILES:
        raise StepInstallError(
            f"Step package contains {retained_files} files, exceeding the "
            f"{_MAX_STEP_PACKAGE_FILES}-file limit"
        )
    if retained_bytes > _MAX_STEP_PACKAGE_BYTES:
        raise StepInstallError(
            f"Step package exceeds the {_MAX_STEP_PACKAGE_BYTES}-byte total "
            "size limit"
        )

    try:
        step_yml_text = (package_dir / "step.yml").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise StepInstallError(f"Invalid step.yml: {exc}") from exc

    return _parse_step_metadata(step_yml_text, step_id)


def resolve_package_root(extracted_root: Path) -> Path:
    """Resolve a root-level or single-nested step package directory."""
    extracted_root = Path(extracted_root)
    root_manifest = extracted_root / "step.yml"
    if root_manifest.is_file() and not root_manifest.is_symlink():
        return extracted_root
    try:
        entries = list(extracted_root.iterdir())
    except OSError as exc:
        raise StepInstallError(
            f"Failed to inspect archive contents: {exc}"
        ) from exc
    if len(entries) == 1:
        candidate = entries[0]
        candidate_manifest = candidate / "step.yml"
        if (
            candidate.is_dir()
            and not candidate.is_symlink()
            and candidate_manifest.is_file()
            and not candidate_manifest.is_symlink()
        ):
            return candidate
    raise StepInstallError(
        "archive must contain step.yml at its root or in exactly one top-level "
        "directory"
    )


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
    if force:
        return
    if registry.is_installed(step_id):
        raise StepInstallError(
            f"Step type '{step_id}' is already installed. Remove it first with: "
            f"[cyan]specify workflow step remove {step_id}[/cyan]"
        )
    if step_dir.exists():
        raise StepInstallError(
            f"Step directory already exists at '{step_dir}'. Remove it manually "
            f"or use: [cyan]specify workflow step remove {step_id}[/cyan]"
        )


def check_installable(project_root: Path, step_id: str, *, force: bool = False) -> Path:
    """Advisory preflight shared by all sources.

    Validates the id, base directory, built-in collision, and
    duplicate/orphan-destination state without touching the package. The CLI
    uses this to reject before a download; :func:`install_step_package`
    re-runs the same checks as defense-in-depth.
    """
    from .catalog import StepRegistry

    validate_step_id(step_id)
    steps_base_dir = resolve_steps_base_dir(project_root)
    step_dir = _resolve_step_dir(steps_base_dir, step_id)
    _reject_unsafe_destination(step_dir)
    _reject_builtin_collision(step_id)
    registry = StepRegistry(project_root)
    _check_duplicate(registry, step_id, step_dir, force=force)
    return step_dir


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
    """Recursively copy *source_dir* into *target_dir*, skipping excludes.

    Refuses to follow a symlink encountered mid-copy so a source swapped after
    validation cannot smuggle external content into the staged package.
    """

    def _copy(current: Path, destination: Path) -> None:
        try:
            destination.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StepInstallError(
                f"Failed to stage step package: {exc}"
            ) from exc
        try:
            entries = sorted(os.scandir(current), key=lambda entry: entry.name)
        except OSError as exc:
            raise StepInstallError(
                f"Failed to stage step package: {exc}"
            ) from exc
        for entry in entries:
            if entry.name in EXCLUDE_NAMES:
                continue
            try:
                mode = entry.stat(follow_symlinks=False).st_mode
            except OSError as exc:
                raise StepInstallError(f"Failed to stage step package: {exc}") from exc
            target = destination / entry.name
            if stat.S_ISLNK(mode):
                raise StepInstallError(
                    f"Step package contains symlink: {entry.path}"
                )
            if stat.S_ISDIR(mode):
                _copy(Path(entry.path), target)
            elif stat.S_ISREG(mode):
                _copy_regular_file(entry.path, target, mode)
            else:
                raise StepInstallError(
                    f"Step package contains unsupported file: {entry.path}"
                )

    _copy(source_dir, target_dir)


def _copy_regular_file(source: str, target: Path, expected_mode: int) -> None:
    """Copy an inspected regular file without following a late symlink swap."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(source, flags)
    except OSError as exc:
        raise StepInstallError(f"Failed to stage step package: {exc}") from exc
    try:
        opened = os.fstat(fd)
        source_state = os.stat(source, follow_symlinks=False)
        if (
            not stat.S_ISREG(opened.st_mode)
            or not stat.S_ISREG(source_state.st_mode)
            or opened.st_dev != source_state.st_dev
            or opened.st_ino != source_state.st_ino
            or stat.S_IFMT(source_state.st_mode) != stat.S_IFMT(expected_mode)
        ):
            raise StepInstallError(
                f"Step package file changed while staging: {source}"
            )
        with os.fdopen(fd, "rb", closefd=False) as source_file, target.open("xb") as target_file:
            shutil.copyfileobj(source_file, target_file)
    except OSError as exc:
        raise StepInstallError(f"Failed to stage step package: {exc}") from exc
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


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
    from .catalog import StepValidationError

    if step_dir.exists():
        if not force:
            raise StepInstallError(
                f"Step directory already exists at '{step_dir}'. Remove it manually "
                f"or use: [cyan]specify workflow step remove {step_id}[/cyan]"
            )
        # --force replacement: the replacement is fully staged and validated,
        # so it is safe to remove the previous installation now.
        try:
            shutil.rmtree(step_dir)
        except OSError as exc:
            raise StepInstallError(
                f"Failed to remove the existing step installation at "
                f"'{step_dir}': {exc}. Reinstall from the original source with "
                "--force."
            ) from exc
        try:
            os.replace(staged_dir, step_dir)
        except OSError as exc:
            raise StepInstallError(
                f"Failed to publish the replacement for step type '{step_id}': "
                f"{exc}. The previous installation was removed; reinstall from "
                "the original source with --force."
            ) from exc
        try:
            registry.add(step_id, entry)
        except (StepValidationError, OSError, TypeError, ValueError) as exc:
            raise StepInstallError(
                f"Failed to update the step registry for '{step_id}': {exc}. The "
                "step directory was replaced but is not registered; reinstall "
                "from the original source with --force."
            ) from exc
        return

    try:
        os.replace(staged_dir, step_dir)
    except OSError as exc:
        raise StepInstallError(
            f"Failed to install step '{step_id}': {exc}"
        ) from exc

    try:
        registry.add(step_id, entry)
    except (StepValidationError, OSError, TypeError, ValueError) as exc:
        # Fresh install: roll back the just-published directory so the system
        # is not left with an unregistered step package on disk.
        try:
            shutil.rmtree(step_dir)
        except OSError as cleanup_exc:
            raise StepInstallError(
                f"Failed to update the step registry for '{step_id}': {exc}. "
                f"The unregistered package remains at '{step_dir}' because rollback "
                f"failed: {cleanup_exc}. Remove it manually before reinstalling."
            ) from exc
        raise StepInstallError(str(exc)) from exc


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
    from .catalog import StepRegistry

    package_dir = Path(package_dir)
    if package_dir.is_symlink():
        raise StepInstallError(
            f"Refusing to install from a symlinked package directory: '{package_dir}'"
        )
    if not package_dir.is_dir():
        raise StepInstallError(f"Step package directory not found: '{package_dir}'")

    validate_step_id(step_id)
    steps_base_dir = resolve_steps_base_dir(project_root)
    step_dir = _resolve_step_dir(steps_base_dir, step_id)
    _reject_unsafe_destination(step_dir)

    # Reject a source that resolves to (or contains) the install destination:
    # a --force replacement would otherwise delete the source before it can be
    # copied.
    try:
        source_resolved = package_dir.resolve()
        dest_resolved = step_dir.resolve()
    except OSError as exc:
        raise StepInstallError(f"Failed to resolve step package path: {exc}") from exc
    if source_resolved == dest_resolved or dest_resolved.is_relative_to(
        source_resolved
    ):
        raise StepInstallError(
            f"Step package source resolves to the install destination: "
            f"'{package_dir}'"
        )

    _reject_builtin_collision(step_id)
    registry = StepRegistry(project_root)
    _check_duplicate(registry, step_id, step_dir, force=force)

    # Validate source and all caller-controlled metadata before creating any
    # project directories. The staged metadata is used for the final entry.
    _build_entry(
        step_id,
        validate_step_package(package_dir, step_id),
        source=source,
        catalog_name=catalog_name,
        catalog_metadata=catalog_metadata,
    )

    try:
        steps_base_dir.mkdir(parents=True, exist_ok=True)
        work_dir = Path(
            tempfile.mkdtemp(prefix=_WORK_DIR_PREFIX, dir=steps_base_dir)
        )
    except OSError as exc:
        raise StepInstallError(f"Failed to create staging directory: {exc}") from exc

    staged_dir = work_dir / "staged"
    committed = False
    try:
        _copy_package_tree(package_dir, staged_dir)
        # Re-validate the complete staged copy: the source may have changed
        # while it was copied.
        staged_meta = validate_step_package(staged_dir, step_id)
        entry = _build_entry(
            step_id,
            staged_meta,
            source=source,
            catalog_name=catalog_name,
            catalog_metadata=catalog_metadata,
        )
        # Serialize destination and registry changes. Source downloads/copying
        # stay outside the lock, but all state that can conflict is reloaded and
        # checked again immediately before publication.
        with _step_install_transaction(project_root):
            locked_base_dir = resolve_steps_base_dir(project_root)
            if locked_base_dir != steps_base_dir:
                raise StepInstallError(
                    "Step directory changed while staging; reinstall from the original source"
                )
            step_dir = _resolve_step_dir(locked_base_dir, step_id)
            _reject_unsafe_destination(step_dir)
            _reject_builtin_collision(step_id)
            registry = StepRegistry(project_root)
            _check_duplicate(registry, step_id, step_dir, force=force)
            _replace_install(
                step_dir,
                staged_dir,
                registry,
                step_id,
                entry,
                force=force,
            )
            committed = True
    finally:
        try:
            shutil.rmtree(work_dir)
        except OSError as cleanup_exc:
            # The staged directory is private and cannot be loaded as a step,
            # but callers still need an actionable residual-path diagnostic.
            if work_dir.exists() and not committed and os.sys.exc_info()[0] is None:
                raise StepInstallError(
                    f"Failed to remove staging directory '{work_dir}': {cleanup_exc}"
                ) from cleanup_exc

    return entry


def remove_step_package(project_root: Path, step_id: str) -> tuple[Path | None, bool]:
    """Remove one custom step under the same transaction as installation.

    The returned directory is staged after the registry removal has committed;
    the second value identifies a removed orphan. Callers can delete the staged
    directory best-effort without changing the successful result.
    """
    from .catalog import StepRegistry, StepValidationError

    validate_step_id(step_id)
    with _step_install_transaction(project_root):
        steps_base_dir = resolve_steps_base_dir(project_root)
        step_dir = _resolve_step_dir(steps_base_dir, step_id)
        _reject_unsafe_destination(step_dir)
        registry = StepRegistry(project_root)
        in_registry = registry.is_installed(step_id)
        if not in_registry and not step_dir.exists():
            raise StepInstallError(f"Step type '{step_id}' is not installed")

        staged_dir: Path | None = None
        if step_dir.exists():
            try:
                staged_dir = Path(
                    tempfile.mkdtemp(
                        prefix=f".{step_id}.removing-", dir=steps_base_dir
                    )
                )
                staged_dir.rmdir()
                os.replace(step_dir, staged_dir)
            except OSError as exc:
                raise StepInstallError(
                    f"Failed to stage step directory '{step_dir}' for removal: {exc}"
                ) from exc

        if not in_registry:
            return staged_dir, True
        try:
            registry.remove(step_id)
        except (StepValidationError, OSError, TypeError, ValueError) as exc:
            if staged_dir is not None:
                try:
                    os.replace(staged_dir, step_dir)
                except OSError as restore_exc:
                    raise StepInstallError(
                        f"Failed to update the step registry for '{step_id}': {exc}. "
                        f"The package remains staged at '{staged_dir}' because restore "
                        f"failed: {restore_exc}."
                    ) from exc
            raise StepInstallError(
                f"Failed to update the step registry for '{step_id}': {exc}"
            ) from exc
        return staged_dir, False
