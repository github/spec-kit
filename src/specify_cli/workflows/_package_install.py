"""Shared install mechanics for project-installed workflow packages.

Step packages and function packages are both directories of executable Python
plus a manifest, installed under ``.specify/workflows/<kind>s/<id>/`` and
recorded in a registry. This module owns what is identical for both: path and
symlink safety, package-tree walking and copying, the staged install flow, the
project lock, and replacement/rollback.

What differs per package kind is described by three small value objects:

* :class:`PackageSpec` -- static identity (naming, error type, size limits).
* :class:`PackageRules` -- the kind's semantics (where it lives, how a manifest
  is validated, which collisions are rejected, what registry entry is stored).
* :class:`StagingOps` -- the filesystem mechanics; :meth:`StagingOps.standard`
  supplies the shared implementations and callers override single members only
  when they must (the step installer does so to keep its established patch
  points).

:func:`install_package` combines them with an :class:`InstallRequest`. The module
is CLI-independent: it never prints and never raises ``typer.Exit``; failures
use ``spec.error``.
"""

from __future__ import annotations

import contextlib
import functools
import os
import shutil
import stat
import sys
import tempfile
import warnings
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ContextManager

# Files/dirs never inspected, copied into, or counted as part of an installed
# package; excluded directories are pruned without being entered. Mirrors
# ``bundles/packager.py`` ``EXCLUDE_NAMES``.
EXCLUDE_NAMES: frozenset[str] = frozenset({".git", "__pycache__", ".DS_Store"})

_COPY_CHUNK_BYTES = 64 * 1024


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PackageLimits:
    """Ceilings applied uniformly to catalog, local, and archive sources."""

    max_files: int
    max_bytes: int
    max_depth: int


@dataclass(frozen=True)
class PackageSpec:
    """Static identity of a package kind.

    ``noun`` is the capitalized kind name (``"Step"``, ``"Function"``) used to
    build user-facing messages; ``kind_label`` names an installed item
    (``"Step type"``, ``"Function package"``). Directory, lock and staging
    names are derived from ``noun`` so they cannot drift apart.
    """

    noun: str
    kind_label: str
    error: type[Exception]
    limits: PackageLimits
    registry_errors: tuple[type[Exception], ...] = (OSError, TypeError, ValueError)
    excludes: frozenset[str] = EXCLUDE_NAMES

    @property
    def lower(self) -> str:
        return self.noun.lower()

    @property
    def directory(self) -> str:
        return f"{self.lower}s"

    @property
    def remove_command(self) -> str:
        return f"specify workflow {self.lower} remove"

    @property
    def work_prefix(self) -> str:
        return f".speckit-{self.lower}-install-"

    @property
    def lock_name(self) -> str:
        return f".{self.lower}-install.lock"


@dataclass(frozen=True)
class PackageLocation:
    """Where a package is installed: the kind's base directory and its slot."""

    base_dir: Path
    destination: Path


@dataclass(frozen=True)
class InstallRequest:
    """What is being installed."""

    project_root: Path
    package_id: str
    package_dir: Path
    force: bool = False


@dataclass(frozen=True)
class PackageRules:
    """Package-kind semantics supplied to :func:`install_package`.

    ``check_destination`` rejects by id and destination state (built-ins,
    duplicates); ``check_contents`` rejects by manifest content (for example
    claimed names) and is optional.
    """

    locate: Callable[[Path, str], PackageLocation]
    open_registry: Callable[[Path], Any]
    check_destination: Callable[..., None]  # (registry, id, location, *, force)
    validate: Callable[[Path, str], Any]  # (package_dir, id) -> parsed manifest
    build_entry: Callable[[Any], dict[str, Any]]  # parsed manifest -> registry entry
    check_contents: Callable[..., None] | None = None  # (registry, id, manifest, *, force)


@dataclass(frozen=True)
class StagingOps:
    """Filesystem mechanics of an install."""

    copy: Callable[[Path, Path], None]
    publish: Callable[..., None]  # (destination, staged, registry, id, entry, *, force)
    transaction: Callable[[Path], ContextManager[None]]

    @classmethod
    def standard(cls, spec: PackageSpec) -> StagingOps:
        return cls(
            copy=functools.partial(copy_package_tree, spec=spec),
            publish=functools.partial(replace_install, spec=spec),
            transaction=functools.partial(install_transaction, spec=spec),
        )


@dataclass(frozen=True)
class RemoveRequest:
    """What is being removed."""

    project_root: Path
    package_id: str


@dataclass(frozen=True)
class RemoveHooks:
    """Package-kind steps of a removal; ``transaction`` defaults to the shared lock."""

    open_registry: Callable[[Path], Any]
    transaction: Callable[[Path], ContextManager[None]] | None = None


@dataclass(frozen=True)
class RemovalOutcome:
    """Result of a removal; ``orphaned`` means the directory had no registry entry."""

    destination: Path
    orphaned: bool


# ---------------------------------------------------------------------------
# Lock, directories and destination safety
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def install_transaction(project_root: Path, spec: PackageSpec) -> Iterator[None]:
    """Serialize package directory and registry mutations (install and remove)."""
    from ..shared_infra import _exclusive_project_lock

    # Only acquisition failures are reported as lock errors; exceptions raised
    # by the caller's critical section propagate unchanged. The message is
    # operation-neutral because both install and remove share this lock; callers
    # that add their own context should report ``exc.__cause__`` instead.
    with contextlib.ExitStack() as stack:
        try:
            stack.enter_context(
                _exclusive_project_lock(
                    Path(project_root), spec.lock_name, context=spec.lower
                )
            )
        except OSError as exc:
            raise spec.error(f"Failed to acquire the {spec.lower} lock: {exc}") from exc
        yield


def resolve_base_dir(project_root: Path, spec: PackageSpec) -> Path:
    """Resolve ``.specify/workflows/<kind>s`` refusing symlinked parent dirs."""
    project_root = Path(project_root)
    project_root_resolved = project_root.resolve()
    base_unresolved = project_root / ".specify" / "workflows" / spec.directory

    current = project_root
    for part in (".specify", "workflows", spec.directory):
        current = current / part
        if current.is_symlink():
            raise spec.error(
                f"Refusing to use symlinked {spec.lower} directory '{current}'"
            )
        if current.exists() and not current.is_dir():
            raise spec.error(
                f"{spec.noun} directory path is not a directory: '{current}'"
            )

    base_dir = base_unresolved.resolve()
    try:
        base_dir.relative_to(project_root_resolved)
    except ValueError:
        raise spec.error(
            f"{spec.noun} directory escapes project root: '{base_dir}'"
        ) from None
    return base_dir


def resolve_destination(base_dir: Path, package_id: str, spec: PackageSpec) -> Path:
    """Return the canonical destination directory for ``package_id``."""
    destination = base_dir / package_id
    try:
        rel_parts = destination.relative_to(base_dir).parts
    except ValueError:
        raise spec.error(f"Invalid {spec.lower} id '{package_id}'") from None
    if rel_parts != (package_id,):
        raise spec.error(f"Invalid {spec.lower} id '{package_id}'")
    return destination


def reject_unsafe_destination(destination: Path, spec: PackageSpec) -> None:
    """Refuse a symlink (including dangling) or non-directory destination."""
    if destination.is_symlink():
        raise spec.error(
            f"Refusing to install {spec.lower} through a symlinked path: "
            f"'{destination}'"
        )
    if destination.exists() and not destination.is_dir():
        raise spec.error(
            f"{spec.noun} install path exists but is not a directory: '{destination}'"
        )


def reject_source_overlap(package_dir: Path, destination: Path, spec: PackageSpec) -> None:
    """Reject a source that resolves to (or contains) the install destination.

    A ``--force`` replacement would otherwise delete the source before it can
    be copied.
    """
    try:
        source_resolved = package_dir.resolve()
        dest_resolved = destination.resolve()
    except OSError as exc:
        raise spec.error(
            f"Failed to resolve {spec.lower} package path: {exc}"
        ) from exc
    if source_resolved == dest_resolved or dest_resolved.is_relative_to(
        source_resolved
    ):
        raise spec.error(
            f"{spec.noun} package source resolves to the install destination: "
            f"'{package_dir}'"
        )


# ---------------------------------------------------------------------------
# Package shape + safety validation
# ---------------------------------------------------------------------------


def entry_limit_error(spec: PackageSpec) -> Exception:
    return spec.error(
        f"{spec.noun} package contains too many entries, exceeding the "
        f"{spec.limits.max_files}-entry limit (files and directories combined)"
    )


def scan_retained_entries(
    directory: Path, budget: int, spec: PackageSpec
) -> list[os.DirEntry]:
    """Return *directory*'s retained children, sorted by name.

    Streams the listing and drops ``EXCLUDE_NAMES`` without inspecting them.
    Raises the entry-limit error as soon as more than *budget* retained
    entries are seen, so an oversized directory is never fully materialized
    or sorted. ``OSError`` propagates to the caller.
    """
    entries: list[os.DirEntry] = []
    with os.scandir(directory) as iterator:
        for entry in iterator:
            if entry.name in spec.excludes:
                continue
            if len(entries) >= budget:
                raise entry_limit_error(spec)
            entries.append(entry)
    entries.sort(key=lambda entry: entry.name)
    return entries


def walk_package_tree(package_dir: Path, spec: PackageSpec):
    """Yield ``(path, is_dir)`` for every retained descendant of *package_dir*.

    Excluded names are pruned without being entered or inspected, matching
    ``bundles/packager.py``; their contents are never staged, so they are not
    part of the package. Every retained entry discovered counts against the
    entry limit before its directory listing is sorted, which bounds traversal
    work by the entry ceiling. Never follows a symlink. Raises ``spec.error`` on
    any symlink, object that is neither a regular file nor a directory,
    nesting deeper than the depth limit, or too many entries. Iterative so deep
    trees cannot exhaust the Python recursion limit.
    """
    limits = spec.limits
    discovered = 0

    def _children(current: Path, depth: int):
        nonlocal discovered
        try:
            entries = scan_retained_entries(
                current, limits.max_files - discovered, spec
            )
        except OSError as exc:
            raise spec.error(
                f"Failed to read {spec.lower} package directory '{current}': {exc}"
            ) from exc
        discovered += len(entries)
        return [(entry, depth) for entry in reversed(entries)]

    stack = _children(package_dir, 1)
    while stack:
        entry, depth = stack.pop()
        try:
            mode = entry.stat(follow_symlinks=False).st_mode
        except OSError as exc:
            raise spec.error(
                f"Failed to inspect {spec.lower} package entry '{entry.path}': {exc}"
            ) from exc
        path = Path(entry.path)
        if stat.S_ISLNK(mode):
            raise spec.error(f"{spec.noun} package contains symlink: {path}")
        if stat.S_ISDIR(mode):
            if depth > limits.max_depth:
                raise spec.error(
                    f"{spec.noun} package exceeds the {limits.max_depth}-level "
                    "directory depth limit"
                )
            yield path, True
            stack.extend(_children(path, depth + 1))
        elif stat.S_ISREG(mode):
            yield path, False
        else:
            raise spec.error(f"{spec.noun} package contains unsupported file: {path}")


def check_package_shape(
    package_dir: Path, spec: PackageSpec, required_files: tuple[str, ...]
) -> None:
    """Validate a materialized package directory's shape, symlinks and limits.

    Raises ``spec.error`` on any shape, symlink, limit or path violation. Never
    imports or executes package code; manifest content is the caller's concern.
    """
    package_dir = Path(package_dir)

    if package_dir.is_symlink():
        raise spec.error(
            f"Refusing to install from a symlinked package directory: '{package_dir}'"
        )
    if not package_dir.is_dir():
        raise spec.error(f"{spec.noun} package directory not found: '{package_dir}'")

    for required in required_files:
        required_path = package_dir / required
        if required_path.is_symlink():
            raise spec.error(
                f"{spec.noun} package '{required}' must be a regular file, not a symlink"
            )
        if not required_path.is_file():
            raise spec.error(
                f"{spec.noun} package is missing required file '{required}' at its root"
            )

    # The walk enforces the entry ceiling itself; only bytes are summed here.
    retained_bytes = 0
    for path, is_dir in walk_package_tree(package_dir, spec):
        if is_dir:
            continue
        try:
            retained_bytes += path.lstat().st_size
        except OSError as exc:
            raise spec.error(
                f"Failed to inspect {spec.lower} package file '{path}': {exc}"
            ) from exc
        if retained_bytes > spec.limits.max_bytes:
            raise spec.error(
                f"{spec.noun} package exceeds the {spec.limits.max_bytes}-byte total "
                "size limit"
            )


def resolve_package_root(
    extracted_root: Path, spec: PackageSpec, manifest_name: str
) -> Path:
    """Resolve a root-level or single-nested package directory."""
    extracted_root = Path(extracted_root)
    root_manifest = extracted_root / manifest_name
    if root_manifest.is_file() and not root_manifest.is_symlink():
        return extracted_root
    try:
        entries = list(extracted_root.iterdir())
    except OSError as exc:
        raise spec.error(f"Failed to inspect archive contents: {exc}") from exc
    if len(entries) == 1:
        candidate = entries[0]
        candidate_manifest = candidate / manifest_name
        if (
            candidate.is_dir()
            and not candidate.is_symlink()
            and candidate_manifest.is_file()
            and not candidate_manifest.is_symlink()
        ):
            return candidate
    raise spec.error(
        f"archive must contain {manifest_name} at its root or in exactly one "
        "top-level directory"
    )


# ---------------------------------------------------------------------------
# Collision / duplicate preflight
# ---------------------------------------------------------------------------


def check_duplicate(
    registry: Any,
    package_id: str,
    destination: Path,
    *,
    force: bool,
    spec: PackageSpec,
) -> None:
    """Reject case-insensitive aliases and, without ``force``, existing installs."""
    folded_id = package_id.casefold()
    try:
        registered_ids = registry.list()
    except (AttributeError, TypeError):
        registered_ids = ()
    for registered_id in registered_ids:
        if (
            isinstance(registered_id, str)
            and registered_id != package_id
            and registered_id.casefold() == folded_id
        ):
            raise spec.error(
                f"{spec.noun} ID '{package_id}' collides case-insensitively with "
                f"registered {spec.lower} ID '{registered_id}'; use the exact "
                "registered ID with --force"
            )

    try:
        destination_exists = destination.exists()
        for existing_path in destination.parent.iterdir():
            existing_name = existing_path.name
            if existing_name == package_id:
                continue
            aliases_destination = (
                destination_exists and existing_path.samefile(destination)
            )
            if existing_name.casefold() != folded_id and not aliases_destination:
                continue
            raise spec.error(
                f"{spec.noun} ID '{package_id}' collides case-insensitively or "
                f"resolves to the same filesystem path as existing {spec.lower} "
                f"directory '{existing_name}'"
            )
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise spec.error(
            f"Failed to inspect existing {spec.lower} directories: {exc}"
        ) from exc

    if force:
        return
    if registry.is_installed(package_id):
        raise spec.error(
            f"{spec.kind_label} '{package_id}' is already installed. Remove it "
            f"first with: {spec.remove_command} {package_id}"
        )
    if destination.exists():
        raise spec.error(
            f"{spec.noun} directory already exists at '{destination}'. Remove it "
            f"manually or use: {spec.remove_command} {package_id}"
        )


# ---------------------------------------------------------------------------
# Staging + commit
# ---------------------------------------------------------------------------


def copy_package_tree(
    source_dir: Path,
    target_dir: Path,
    spec: PackageSpec,
    *,
    copy_file: Callable[[str, Path, int, int], int] | None = None,
) -> None:
    """Copy *source_dir* into *target_dir*, skipping excludes.

    Refuses to follow a symlink encountered mid-copy so a source swapped after
    validation cannot smuggle external content into the staged package, and
    re-enforces the depth, entry, and byte budgets. Entries count against the
    entry budget as each listing is streamed, before it is sorted, so an
    oversized source directory is rejected without being fully read. Iterative
    so a deep tree cannot exhaust the Python recursion limit.

    ``copy_file(source, target, expected_mode, remaining_bytes)`` copies one
    inspected regular file and returns the bytes written.
    """
    limits = spec.limits
    if copy_file is None:
        copy_file = functools.partial(copy_regular_file, spec=spec)

    remaining_bytes = limits.max_bytes
    discovered_entries = 0
    pending = [(source_dir, target_dir, 0)]
    while pending:
        current, destination, depth = pending.pop()
        if depth > limits.max_depth:
            raise spec.error(
                f"{spec.noun} package exceeds the {limits.max_depth}-level "
                "directory depth limit"
            )
        try:
            destination.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise spec.error(f"Failed to stage {spec.lower} package: {exc}") from exc
        try:
            entries = scan_retained_entries(
                current, limits.max_files - discovered_entries, spec
            )
        except OSError as exc:
            raise spec.error(f"Failed to stage {spec.lower} package: {exc}") from exc
        discovered_entries += len(entries)
        for entry in entries:
            try:
                mode = entry.stat(follow_symlinks=False).st_mode
            except OSError as exc:
                raise spec.error(
                    f"Failed to stage {spec.lower} package: {exc}"
                ) from exc
            target = destination / entry.name
            if stat.S_ISLNK(mode):
                raise spec.error(f"{spec.noun} package contains symlink: {entry.path}")
            if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise spec.error(
                    f"{spec.noun} package contains unsupported file: {entry.path}"
                )
            if stat.S_ISDIR(mode):
                pending.append((Path(entry.path), target, depth + 1))
            else:
                remaining_bytes -= copy_file(entry.path, target, mode, remaining_bytes)


def copy_regular_file(
    source: str,
    target: Path,
    expected_mode: int,
    remaining_bytes: int,
    spec: PackageSpec,
) -> int:
    """Copy an inspected regular file within the remaining package byte budget."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(source, flags)
    except OSError as exc:
        raise spec.error(f"Failed to stage {spec.lower} package: {exc}") from exc
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
            raise spec.error(
                f"{spec.noun} package file changed while staging: {source}"
            )
        copied_bytes = 0
        with os.fdopen(fd, "rb", closefd=False) as source_file, target.open(
            "xb"
        ) as target_file:
            while True:
                chunk = source_file.read(
                    min(_COPY_CHUNK_BYTES, remaining_bytes - copied_bytes + 1)
                )
                if not chunk:
                    break
                if copied_bytes + len(chunk) > remaining_bytes:
                    raise spec.error(
                        f"{spec.noun} package exceeds the {spec.limits.max_bytes}-byte "
                        "total size limit while staging"
                    )
                target_file.write(chunk)
                copied_bytes += len(chunk)
        return copied_bytes
    except OSError as exc:
        raise spec.error(f"Failed to stage {spec.lower} package: {exc}") from exc
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


def replace_install(
    destination: Path,
    staged_dir: Path,
    registry: Any,
    package_id: str,
    entry: dict[str, Any],
    *,
    force: bool,
    spec: PackageSpec,
) -> None:
    """Publish the staged package and record its registry entry."""
    if destination.exists():
        if not force:
            raise spec.error(
                f"{spec.noun} directory already exists at '{destination}'. Remove it "
                f"manually or use: {spec.remove_command} {package_id}"
            )
        # --force replacement: the replacement is fully staged and validated,
        # so it is safe to remove the previous installation now.
        try:
            shutil.rmtree(destination)
        except OSError as exc:
            raise spec.error(
                f"Failed to remove the existing {spec.lower} installation at "
                f"'{destination}': {exc}. Reinstall from the original source with "
                "--force."
            ) from exc
        try:
            os.replace(staged_dir, destination)
        except OSError as exc:
            raise spec.error(
                f"Failed to publish the replacement for {spec.kind_label.lower()} "
                f"'{package_id}': {exc}. The previous installation was removed; "
                "reinstall from the original source with --force."
            ) from exc
        try:
            registry.add(package_id, entry)
        except spec.registry_errors as exc:
            raise spec.error(
                f"Failed to update the {spec.lower} registry for '{package_id}': "
                f"{exc}. The package was replaced but the registry metadata was not "
                "updated; reinstall from the original source with --force."
            ) from exc
        return

    try:
        os.replace(staged_dir, destination)
    except OSError as exc:
        raise spec.error(
            f"Failed to install {spec.lower} '{package_id}': {exc}"
        ) from exc

    try:
        registry.add(package_id, entry)
    except spec.registry_errors as exc:
        # Fresh install: roll back the just-published directory so the system
        # is not left with an unregistered package on disk.
        try:
            shutil.rmtree(destination)
        except OSError as cleanup_exc:
            raise spec.error(
                f"Failed to update the {spec.lower} registry for '{package_id}': "
                f"{exc}. The unregistered package remains at '{destination}' because "
                f"rollback failed: {cleanup_exc}. Remove it manually before "
                "reinstalling."
            ) from exc
        raise spec.error(str(exc)) from exc


def install_package(
    request: InstallRequest,
    spec: PackageSpec,
    rules: PackageRules,
    ops: StagingOps | None = None,
) -> dict[str, Any]:
    """Validate, stage, and commit a package; return the persisted registry entry.

    The order is the contract: reject unsafe or conflicting targets, validate
    the source before creating any project directory, copy it into a private
    work directory, re-validate the complete staged copy (the source may have
    changed while it was copied), then take the project lock and re-run every
    conflict check against freshly read state immediately before publishing.
    """
    ops = ops or StagingOps.standard(spec)
    root, package_id, force = request.project_root, request.package_id, request.force

    package_dir = Path(request.package_dir)
    if package_dir.is_symlink():
        raise spec.error(
            f"Refusing to install from a symlinked package directory: '{package_dir}'"
        )
    if not package_dir.is_dir():
        raise spec.error(f"{spec.noun} package directory not found: '{package_dir}'")

    location = rules.locate(root, package_id)
    reject_source_overlap(package_dir, location.destination, spec)
    registry = rules.open_registry(root)
    rules.check_destination(registry, package_id, location, force=force)

    # Validate source and all caller-controlled metadata before creating any
    # project directories. The staged metadata is used for the final entry.
    manifest = rules.validate(package_dir, package_id)
    rules.build_entry(manifest)
    if rules.check_contents is not None:
        rules.check_contents(registry, package_id, manifest, force=force)

    try:
        location.base_dir.mkdir(parents=True, exist_ok=True)
        work_dir = Path(
            tempfile.mkdtemp(prefix=spec.work_prefix, dir=location.base_dir)
        )
    except OSError as exc:
        raise spec.error(f"Failed to create staging directory: {exc}") from exc

    staged_dir = work_dir / "staged"
    committed = False
    try:
        ops.copy(package_dir, staged_dir)
        staged_manifest = rules.validate(staged_dir, package_id)
        entry = rules.build_entry(staged_manifest)
        # Serialize destination and registry changes. Source downloads/copying
        # stay outside the lock, but all state that can conflict is reloaded and
        # checked again immediately before publication.
        with ops.transaction(root):
            locked = rules.locate(root, package_id)
            if locked.base_dir != location.base_dir:
                raise spec.error(
                    f"{spec.noun} directory changed while staging; reinstall from "
                    "the original source"
                )
            registry = rules.open_registry(root)
            rules.check_destination(registry, package_id, locked, force=force)
            if rules.check_contents is not None:
                rules.check_contents(registry, package_id, staged_manifest, force=force)
            ops.publish(
                locked.destination, staged_dir, registry, package_id, entry, force=force
            )
            committed = True
    finally:
        primary_error = sys.exc_info()[1]
        try:
            shutil.rmtree(work_dir)
        except OSError as cleanup_exc:
            if work_dir.exists():
                message = (
                    f"Could not remove {spec.lower} staging directory '{work_dir}': "
                    f"{cleanup_exc}"
                )
                if primary_error is not None:
                    primary_error.add_note(message)
                elif committed:
                    warnings.warn(message, UserWarning, stacklevel=2)
                else:
                    raise spec.error(message) from cleanup_exc

    return entry


def remove_package(
    request: RemoveRequest, spec: PackageSpec, hooks: RemoveHooks
) -> RemovalOutcome:
    """Remove a package directory and its registry entry under the project lock.

    The registry and directory are resolved after the lock is acquired, so a
    concurrent install cannot be lost or resurrected by a stale snapshot. The
    registry entry is removed first and restored verbatim if deleting the
    directory fails, so a later install is not blocked by an orphaned directory.
    Failures raise ``spec.error``; advisory detail that should be shown
    alongside it is attached as exception notes.
    """
    root, package_id = request.project_root, request.package_id
    transaction = hooks.transaction or functools.partial(install_transaction, spec=spec)
    with contextlib.ExitStack() as stack:
        try:
            stack.enter_context(transaction(root))
        except spec.error as exc:
            # Report the underlying acquisition error so the message is not
            # prefixed twice by the helper's own lock-failure text.
            raise spec.error(
                f"Failed to lock {spec.lower} removal '{package_id}': "
                f"{exc.__cause__ or exc}"
            ) from exc
        return remove_package_locked(request, spec, hooks)


def remove_package_locked(
    request: RemoveRequest, spec: PackageSpec, hooks: RemoveHooks
) -> RemovalOutcome:
    """The removal itself; the caller must already hold the project lock.

    Exposed for callers that run inside their own locked section (for example
    a bundle refresh that snapshots and restores around the removal).
    """
    root, package_id = request.project_root, request.package_id
    registry = hooks.open_registry(root)
    in_registry = registry.is_installed(package_id)

    base_dir = resolve_base_dir(root, spec)
    destination = (base_dir / package_id).resolve()
    # Defense-in-depth: even though the id was validated, ensure the resolved
    # directory is a single child of the base directory and not the base itself.
    try:
        rel_parts = destination.relative_to(base_dir).parts
    except ValueError:
        raise spec.error(f"Invalid {spec.lower} id '{package_id}'") from None
    if rel_parts != (package_id,):
        raise spec.error(f"Invalid {spec.lower} id '{package_id}'")

    dir_exists = destination.exists()
    if not in_registry and not dir_exists:
        raise spec.error(f"{spec.kind_label} '{package_id}' is not installed")

    def _delete_failure(exc: OSError) -> Exception:
        return spec.error(
            f"Failed to remove {spec.lower} directory {destination}: {exc}"
        )

    if not in_registry:
        # The registry was likely reset due to corruption. No registry write is
        # needed; just delete the orphaned directory.
        try:
            shutil.rmtree(destination)
        except OSError as exc:
            failure = _delete_failure(exc)
            failure.add_note(_orphan_note(package_id))
            raise failure from exc
        return RemovalOutcome(destination, orphaned=True)

    metadata = registry.get(package_id)
    try:
        registry.remove(package_id)
    except registry.ERROR as exc:
        raise spec.error(str(exc)) from exc
    if dir_exists:
        try:
            shutil.rmtree(destination)
        except OSError as exc:
            failure = _delete_failure(exc)
            try:
                if metadata is not None:
                    registry.restore(package_id, metadata)
            except Exception as restore_exc:  # noqa: BLE001
                failure.add_note(
                    f"Failed to restore registry entry for '{package_id}' after "
                    f"directory removal failure: {restore_exc}"
                )
            raise failure from exc
    return RemovalOutcome(destination, orphaned=False)


def _orphan_note(package_id: str) -> str:
    return (
        f"'{package_id}' has no registry entry (registry may have been reset). "
        "Removing the orphaned directory."
    )


def orphan_warning(package_id: str) -> str:
    """Advisory shown when a removal deleted a directory that had no registry entry."""
    return _orphan_note(package_id)
