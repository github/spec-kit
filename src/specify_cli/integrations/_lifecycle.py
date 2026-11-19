"""External-adapter preparation and rollback shared by public lifecycle commands."""

from __future__ import annotations

import errno
import hashlib
import inspect
import os
import shutil
import stat
import sys
import tempfile
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from collections.abc import Callable
from functools import partial, wraps
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
from ._file_changes import directory_creation_observer, file_change_observer

_init_directory: ContextVar[tuple[Path, bool, list[Path]] | None] = ContextVar(
    "external_integration_init_directory", default=None
)
_success_messages: ContextVar[list[str] | None] = ContextVar(
    "external_integration_success_messages", default=None
)
_MAX_BACKUP_BYTES = 128 * 1024 * 1024
_MAX_BACKUP_ENTRIES = 4096
_HAS_XATTRS = all(hasattr(os, name) for name in ("listxattr", "getxattr", "setxattr", "removexattr"))
_XATTRS_UNSUPPORTED = {errno.ENOTSUP, getattr(errno, "EOPNOTSUPP", errno.ENOTSUP)}
# The Linux POSIX access ACL, which the file's owner may set like a user
# attribute and ``shutil.copy2()`` copies with the others.
_ACCESS_ACL = "system.posix_acl_access"
# Most read-only descriptors held on snapshotted files so rollback can trust
# their identity; ``_pin_limit()`` lowers it to a quarter of the open-file limit.
_MAX_PINNED_FILES = 1024
# Flags the filesystem itself changes when a file's bytes are rewritten:
# UF_COMPRESSED on macOS, and the UF_ARCHIVE bit FreeBSD and DragonFly set
# on a write (ZFS, msdosfs).
if sys.platform == "darwin":
    _UNCOMPARED_FLAGS = getattr(stat, "UF_COMPRESSED", 0x20)
elif sys.platform.startswith(("freebsd", "dragonfly")):
    _UNCOMPARED_FLAGS = 0x800
else:
    _UNCOMPARED_FLAGS = 0


def _restorable_xattrs(target: Path | int, journal: Any = None) -> dict[str, bytes]:
    """Read the extended attributes of a path or descriptor that rollback restores.

    These are the ``user.*`` attributes and the POSIX access ACL, all of which
    the file's owner may set. The kernel and security modules manage the
    others (``security.*``, the rest of ``system.*``), which a file write can
    change and an unprivileged rollback cannot set back. An attribute removed
    between listing and reading it is skipped. ``journal``, when given, is
    charged for the bytes kept.
    """
    follow = {} if isinstance(target, int) else {"follow_symlinks": False}
    attributes = {}
    for name in os.listxattr(target, **follow):
        if not name.startswith("user.") and name != _ACCESS_ACL:
            continue
        try:
            attributes[name] = os.getxattr(target, name, **follow)
        except OSError as exc:
            if exc.errno != errno.ENODATA:
                raise
    if journal is not None:
        size = sum(len(name) + len(value) for name, value in attributes.items())
        if size > _MAX_BACKUP_BYTES - journal.backup_bytes:
            raise installer.IntegrationInstallError("Integration rollback snapshot budget exceeded (bytes)")
        journal.backup_bytes += size
    return attributes


def _pin_limit() -> int:
    """How many snapshotted files a transaction may pin, leaving most descriptors free."""
    try:
        import resource

        soft, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
        if soft == resource.RLIM_INFINITY:
            return _MAX_PINNED_FILES
    except (ImportError, OSError, ValueError):
        soft = 256
    return max(0, min(_MAX_PINNED_FILES, soft // 4))


def lifecycle_owns_rollback() -> bool:
    """Leave failure cleanup to the active transaction's mutation journal."""
    return file_change_observer.get() is not None


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


def _entry_state(path: Path) -> tuple[int, ...]:
    entry = path.lstat()
    return (
        entry.st_mode, entry.st_dev, entry.st_ino, entry.st_size,
        entry.st_mtime_ns, entry.st_ctime_ns,
    )

def _matches_directory_before_write(current: Any, expected: Any, parents: tuple[str, ...]) -> bool:
    """Allow only new empty directories on the destination's parent chain."""
    if current == expected:
        return True
    if (
        not parents or current is None or expected is None
        or current[0] != "directory" or expected[0] != "directory"
    ):
        return False
    current_entries = dict(current[1])
    expected_entries = dict(expected[1])
    name = parents[0]
    if name in current_entries and _matches_directory_before_write(
        current_entries[name], expected_entries.get(name, ("directory", ())), parents[1:],
    ):
        if name in expected_entries:
            current_entries[name] = expected_entries[name]
        else:
            del current_entries[name]
    return current_entries == expected_entries


def _initial_entries(paths: list[Path]) -> dict[Path, tuple[int, ...]]:
    """Census names and metadata without reading or copying file contents."""
    entries = {}

    def fail_walk(error: OSError) -> None:
        raise error

    for path in paths:
        try:
            entries[path] = _entry_state(path)
        except FileNotFoundError:
            continue
        if stat.S_ISDIR(entries[path][0]):
            for directory, folders, files in os.walk(path, onerror=fail_walk, followlinks=False):
                for name in folders + files:
                    child = Path(directory) / name
                    entries[child] = _entry_state(child)
    return entries


class _FileJournal:
    """Restore observed owned writes, never every file under an output root."""

    def __init__(
        self, root: Path, paths: list[Path], backup: Path, initial: dict[Path, tuple[int, ...]],
        home_scopes: tuple[Path, ...] = (),
    ):
        self.root = root
        self.paths = paths
        self.backup = backup
        self.initial = initial
        self.home_scopes = home_scopes
        self.changes: dict[Path, tuple[Path | None, Any]] = {}
        self.pending: set[Path] = set()
        self.backup_bytes = 0
        self.backup_entries = 0
        self.directory_states: dict[Path, bool] = {}
        self.created_directories: list[tuple[Path, tuple[int, int]]] = []
        # The (st_dev, st_ino) of each snapshotted regular file, so rollback
        # can tell the same file, rewritten in place, from a replacement.
        self.snapshotted_files: dict[Path, tuple[int, int]] = {}
        # Outside Windows, a read-only descriptor on each such file, held
        # until the transaction ends so its inode cannot be freed and reused
        # by a replacement. Windows gets none: an open file there cannot be
        # replaced or removed, which would fail the operation itself, so it
        # keeps the device and file-ID check alone.
        self.pinned_files: dict[Path, int] = {}
        self.pin_limit = 0 if os.name == "nt" else _pin_limit()
        # The (st_dev, st_ino) of files that could not be pinned (past
        # ``pin_limit``). Rollback recreates them, and reports one that still
        # has that identity, as it was probably rewritten in place.
        self.unverified_files: dict[Path, tuple[int, int]] = {}
        # Each such file's restorable extended attributes, read when it was
        # snapshotted; None when they could not be read or the os module has
        # no extended-attribute API (CPython has one on Linux only).
        self.snapshotted_xattrs: dict[Path, dict[str, bytes] | None] = {}
        # Each such file's BSD file flags (macOS and the BSDs), or None.
        self.snapshotted_flags: dict[Path, int | None] = {}
        # Files whose bytes rollback restored without all of their metadata.
        self.incomplete_restores: list[Path] = []
        for path in paths:
            self._remember_parents(path)

    def _remember_parents(self, path: Path) -> None:
        boundary = self.root if path.is_relative_to(self.root) else Path.home().absolute()
        for parent in path.parents:
            if parent == boundary:
                break
            if parent in self.directory_states:
                continue
            for scope in self.paths:
                if parent == scope or scope in parent.parents:
                    original = self.initial.get(parent)
                    self.directory_states[parent] = original is not None and stat.S_ISDIR(original[0])
                    break
            else:
                self.directory_states[parent] = parent.is_dir()

    def _snapshot(self, source: Path, destination: Path) -> None:
        """Copy ``source`` to ``destination``; a pinned regular file's first snapshot is read through its pin.

        A file already journalled has been snapshotted, and the operation may
        have replaced it since, so a later snapshot of a directory holding it
        reads it from its path: its pin may hold an inode no longer there.
        """
        self.backup_entries += 1
        if self.backup_entries > _MAX_BACKUP_ENTRIES:
            raise installer.IntegrationInstallError("Integration rollback snapshot budget exceeded (entries)")
        mode = source.lstat().st_mode
        if stat.S_ISLNK(mode):
            destination.symlink_to(os.readlink(source))
        elif stat.S_ISDIR(mode):
            destination.mkdir()
            for child in source.iterdir():
                self._snapshot(child, destination / child.name)
            shutil.copystat(source, destination, follow_symlinks=False)
        elif stat.S_ISREG(mode):
            pinned = self.pinned_files.get(source) if source not in self.changes else None
            size = os.fstat(pinned).st_size if pinned is not None else source.stat().st_size
            if size > _MAX_BACKUP_BYTES - self.backup_bytes:
                raise installer.IntegrationInstallError("Integration rollback snapshot budget exceeded (bytes)")
            if pinned is not None:
                # A duplicate, so reading leaves the pin's own offset alone.
                incoming = os.fdopen(os.dup(pinned), "rb")
                incoming.seek(0)
            else:
                incoming = source.open("rb")
            with incoming, destination.open("wb") as outgoing:
                while content := incoming.read(min(65536, _MAX_BACKUP_BYTES - self.backup_bytes + 1)):
                    self.backup_bytes += len(content)
                    if self.backup_bytes > _MAX_BACKUP_BYTES:
                        raise installer.IntegrationInstallError("Integration rollback snapshot budget exceeded (bytes)")
                    outgoing.write(content)
            shutil.copystat(source, destination, follow_symlinks=False)
        else:
            raise installer.IntegrationInstallError(f"Unsupported integration output: {source}")

    def _remember_original(self, path: Path, entry: os.stat_result, attributes: dict[str, bytes] | None) -> None:
        """Record what rollback needs to restore ``path`` in place later."""
        if os.name != "nt" and path not in self.pinned_files:
            self.unverified_files[path] = (entry.st_dev, entry.st_ino)
            return
        self.snapshotted_files[path] = (entry.st_dev, entry.st_ino)
        self.snapshotted_xattrs[path] = attributes
        self.snapshotted_flags[path] = getattr(entry, "st_flags", None)

    def _pin(self, path: Path, entry: os.stat_result) -> bool:
        """Hold a read-only descriptor on ``path`` if it is still ``entry``.

        Taken before the file is snapshotted, so the inode is held from then
        on and a replacement cannot be mistaken for the original.
        """
        if len(self.pinned_files) >= self.pin_limit:
            return False
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        try:
            descriptor = os.open(path, flags)
        except OSError:
            return False
        try:
            same = os.path.samestat(entry, os.fstat(descriptor))
        except OSError:
            same = False
        if not same:
            os.close(descriptor)
            return False
        self.pinned_files[path] = descriptor
        return True

    def _unpin(self, path: Path) -> None:
        descriptor = self.pinned_files.pop(path, None)
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass

    def is_original(self, path: Path, current: os.stat_result) -> bool:
        """Whether ``current``, found at ``path``, is the snapshotted file itself.

        Same device and inode and, outside Windows, a pin that still has a
        name: while pinned the inode cannot be reused, and a pinned inode
        unlinked everywhere is not the file now at ``path``.
        """
        identity = self.snapshotted_files.get(path)
        if not stat.S_ISREG(current.st_mode) or (current.st_dev, current.st_ino) != identity:
            return False
        if os.name == "nt":
            return True
        descriptor = self.pinned_files.get(path)
        return descriptor is not None and os.fstat(descriptor).st_nlink > 0

    def release(self) -> None:
        """Close the descriptors pinning snapshotted files."""
        descriptors = list(self.pinned_files.values())
        self.pinned_files.clear()
        for descriptor in descriptors:
            try:
                os.close(descriptor)
            except OSError:
                pass

    def _read_xattrs(self, path: Path) -> dict[str, bytes] | None:
        """Read a file's restorable extended attributes, or None if they cannot be read.

        Kept in memory rather than relying on the copy ``shutil.copystat()``
        puts on the snapshot, which it silently skips where the temporary
        filesystem has no user attributes.
        """
        if not _HAS_XATTRS:
            return None
        try:
            return _restorable_xattrs(path, self)
        except OSError as exc:
            if exc.errno in _XATTRS_UNSUPPORTED:
                return {}
            return None

    def directory_created(self, path: Path) -> None:
        entry = path.lstat()
        self.created_directories.append((Path(os.path.abspath(path)), (entry.st_dev, entry.st_ino)))

    def safe_path(self, path: Path, *, allow_leaf_symlink: bool = True) -> Path:
        path = path.absolute()
        boundary = self.root
        if not path.is_relative_to(boundary):
            if not any(path.is_relative_to(scope) for scope in self.home_scopes):
                raise installer.IntegrationInstallError(f"Integration output escapes trusted scopes: {path}")
            boundary = Path.home().absolute()
        relative = path.relative_to(boundary).as_posix()
        installer.safe_project_path(boundary, relative, allow_leaf_symlink=allow_leaf_symlink)
        return path

    def observe(self, path: Path, before: bool, removal: bool = False) -> None:
        path = self.safe_path(path, allow_leaf_symlink=not before or removal)
        for parent in path.parents:
            if parent not in self.changes:
                continue
            if parent in self.pending:
                return
            saved, identity = self.changes[parent]
            if identity is not None and identity[0] == "directory":
                if before:
                    if not _matches_directory_before_write(
                        _file_identity(parent), identity, path.relative_to(parent).parts[:-1],
                    ):
                        raise installer.IntegrationInstallError(
                            f"Integration output changed during the operation; refusing to overwrite {path}"
                        )
                    self.pending.add(path)
                else:
                    self.changes[parent] = (saved, _file_identity(parent))
                    self.pending.discard(path)
                return
        self._remember_parents(path)
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
                    entry = path.lstat()
                    # A file the operation is removing is recreated, never
                    # restored in place, so it is not pinned either.
                    restorable = stat.S_ISREG(entry.st_mode) and not removal
                    if restorable and os.name != "nt":
                        self._pin(path, entry)
                    try:
                        self._snapshot(path, saved)
                        if restorable:
                            attributes = self._read_xattrs(path)
                            if os.path.samestat(entry, path.lstat()):
                                self._remember_original(path, entry, attributes)
                            else:
                                self._unpin(path)
                    except BaseException:
                        self._unpin(path)
                        raise
            else:
                if not any(path == scope or scope in path.parents for scope in self.paths):
                    raise installer.IntegrationInstallError(
                        f"Integration output {path} must use manifest.record_file() "
                        "or the host file-writing helpers outside its declared output root"
                    )
                original = self.initial.get(path)
                if original is not None:
                    if _entry_state(path) == original:
                        return
                    raise installer.IntegrationInstallError(
                        f"Integration output {path} changed without before-write observation; "
                        "cannot restore its original bytes. Use manifest.record_file() "
                        "or IntegrationBase.write_file_and_record() before overwriting existing files."
                    )
            self.changes[path] = (saved, _file_identity(path))
        if not before:
            saved, _ = self.changes[path]
            self.changes[path] = (saved, _file_identity(path))
            self.pending.discard(path)
        else:
            self.pending.add(path)


def _prune_new_parents(root: Path, journal: _FileJournal, path: Path) -> None:
    """Remove the empty directories the operation created above ``path``."""
    parent = path.parent
    boundary = root if path.is_relative_to(root) else Path.home().absolute()
    while parent != boundary and not journal.directory_states.get(parent, True):
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def _restore_file_in_place(
    path: Path, saved: Path, is_original: Callable[[os.stat_result], bool] | None,
    attributes: dict[str, bytes] | None, file_flags: int | None = None,
) -> str:
    """Write a snapshot back into the file it was taken from.

    Unlinking and recreating the file would give it the restoring user as
    owner and the directory's default permissions (on Windows, its inherited
    access-control list), so a file the operation rewrote in place gets its
    bytes, extended attributes, times and mode back through the same file.

    ``is_original`` tells whether a stat result is the snapshotted file;
    None means the file cannot be restored in place. Returns
    ``"untouched"``, having changed nothing, when ``path`` is no longer that
    regular file (removed, or replaced by another file, a symlink
    or a directory) or cannot be opened for writing; the caller then
    recreates it. Returns ``"incomplete"`` when the bytes were restored but
    some metadata could not be, safely or at all (another user's file, say),
    and ``"restored"`` otherwise. ``file_flags`` are the file's BSD flags when
    snapshotted; Python has no descriptor form of ``chflags()``, so changed
    flags are reported, not set back. A failed byte write raises.
    """
    if is_original is None:
        return "untouched"
    try:
        entry = path.lstat()
    except FileNotFoundError:
        return "untouched"
    if not is_original(entry):
        return "untouched"
    # No O_TRUNC: nothing is written until the opened file is known to be the
    # snapshotted one. Windows has no O_NOFOLLOW, so the identity check after
    # opening is what stops a symlink swapped in after lstat() being written.
    # O_NONBLOCK keeps a FIFO swapped in from blocking the open.
    flags = (
        os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_BINARY", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return "untouched"
    with os.fdopen(descriptor, "wb") as outgoing:
        opened = os.fstat(outgoing.fileno())
        if not is_original(opened):
            return "untouched"
        # Before reading the snapshot, which can move its access time.
        original = saved.stat()
        outgoing.truncate(0)
        with saved.open("rb") as incoming:
            shutil.copyfileobj(incoming, outgoing)
        outgoing.flush()
        complete = _restore_metadata(outgoing.fileno(), path, original, attributes)
        if file_flags is not None:
            current = getattr(os.fstat(outgoing.fileno()), "st_flags", file_flags)
            if (current ^ file_flags) & ~_UNCOMPARED_FLAGS:
                complete = False
        # A path unlinked or replaced during the copy no longer names the
        # restored file; report that, and leave whatever is there alone.
        try:
            if not os.path.samestat(os.fstat(outgoing.fileno()), path.lstat()):
                complete = False
        except OSError:
            complete = False
        return "restored" if complete else "incomplete"


def _restore_metadata(
    descriptor: int, path: Path, original: os.stat_result, attributes: dict[str, bytes] | None,
) -> bool:
    """Restore a snapshot's extended attributes, times and mode onto the open, verified file.

    Every change goes through ``descriptor``, so a path swapped for a symlink
    since the open cannot redirect it to another file. Windows offers no
    descriptor form of ``os.utime`` (nor of ``os.chmod`` before Python
    3.13), but a file Python opens there cannot be renamed, replaced or
    deleted until it is closed, so ``path`` still names the verified file
    while ``descriptor`` is open. Anywhere else without a descriptor form,
    the metadata is left and the restore reported incomplete. Values that
    already match are not set again, so a file the restoring user may write
    but not otherwise modify is only refused what it actually needs.
    """
    complete = True
    if _HAS_XATTRS:
        # Before the mode: a read-only mode refuses user attributes, and an
        # access ACL sets the group mode bits.
        if attributes is None:
            complete = False
        else:
            complete = _restore_xattrs(descriptor, attributes)
    current = os.fstat(descriptor)
    times = (original.st_atime_ns, original.st_mtime_ns)
    if (current.st_atime_ns, current.st_mtime_ns) != times:
        try:
            if os.utime in os.supports_fd:
                os.utime(descriptor, ns=times)
            elif os.name == "nt":
                os.utime(path, ns=times)
            else:
                complete = False
        except OSError:
            complete = False
    mode = stat.S_IMODE(original.st_mode)
    if stat.S_IMODE(current.st_mode) != mode:
        try:
            if hasattr(os, "fchmod"):
                os.fchmod(descriptor, mode)
            elif os.name == "nt":
                os.chmod(path, mode)
            else:
                complete = False
        except OSError:
            complete = False
    return complete


def _restore_xattrs(descriptor: int, attributes: dict[str, bytes]) -> bool:
    """Set a file's restorable attributes back, each one independently."""
    try:
        live = _restorable_xattrs(descriptor)
    except OSError as exc:
        return exc.errno in _XATTRS_UNSUPPORTED and not attributes
    complete = True
    changes = [(name, None) for name in live.keys() - attributes.keys()]
    changes += [(name, value) for name, value in attributes.items() if live.get(name) != value]
    # The access ACL last: it sets the mode bits, and a read-only one would
    # refuse the user attributes still to come.
    changes.sort(key=lambda change: change[0] == _ACCESS_ACL)
    for name, value in changes:
        try:
            if value is None:
                os.removexattr(descriptor, name)
            else:
                os.setxattr(descriptor, name, value)
        except OSError:
            complete = False
    return complete


def _still_has_identity(path: Path, identity: tuple[int, int] | None) -> bool:
    if identity is None:
        return False
    try:
        entry = path.lstat()
    except OSError:
        return False
    return (entry.st_dev, entry.st_ino) == identity


def _restore_snapshots(root: Path, journal: _FileJournal) -> list[Path]:
    conflicts = []
    for path, (saved, written_identity) in reversed(tuple(journal.changes.items())):
        journal.safe_path(path)
        current_identity = _file_identity(path)
        if path in journal.pending or any(path in pending.parents for pending in journal.pending):
            original_identity = _file_identity(saved) if saved is not None else None
            if saved is None and path not in journal.pending and current_identity == written_identity:
                # A new directory whose pending child never landed is
                # unchanged since it was recorded; remove it below.
                pass
            elif current_identity != original_identity:
                conflicts.append(path)
                continue
            else:
                if saved is None and path in journal.pending:
                    # A new file whose write never landed still leaves the
                    # directories created for it.
                    _prune_new_parents(root, journal, path)
                continue
        if path not in journal.pending and current_identity != written_identity:
            conflicts.append(path)
            continue
        if saved is not None:
            is_original = partial(journal.is_original, path) if path in journal.snapshotted_files else None
            restored = _restore_file_in_place(
                path, saved, is_original, journal.snapshotted_xattrs.get(path),
                journal.snapshotted_flags.get(path),
            )
            if (
                restored == "incomplete"
                or _still_has_identity(path, journal.unverified_files.get(path))
                or (restored == "untouched" and _still_has_identity(path, journal.snapshotted_files.get(path)))
            ):
                # A file still at its old inode that is not restored in place
                # (unverified, or refusing to be opened for writing) was
                # probably rewritten in place; recreating it below loses its
                # owner, links and any metadata its snapshot could not hold.
                journal.incomplete_restores.append(path)
            if restored != "untouched":
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
            _prune_new_parents(root, journal, path)
    _prune_new_directories(journal)
    return conflicts


def _prune_new_directories(journal: _FileJournal) -> None:
    """Remove empty directories the operation created without writing into them.

    ``setup()`` can create its output directory before its first observed
    write, so a failure in between leaves directories no journal entry
    covers. Only directories the operation reported creating, through
    ``make_directories()``, are removed, newest first and only while empty;
    a directory that appeared from elsewhere is left alone, and files are
    never touched here.
    """
    home = Path.home().absolute()
    for path, identity in reversed(journal.created_directories):
        try:
            entry = path.lstat()
            if not stat.S_ISDIR(entry.st_mode) or (entry.st_dev, entry.st_ino) != identity:
                continue
            # A new parent of a home scope, such as ~/.hermes, lies outside
            # every scope safe_path() accepts.
            home_parent = path != home and path.is_relative_to(home) and any(
                path in scope.parents for scope in journal.home_scopes
            )
            if not home_parent:
                journal.safe_path(path)
            path.rmdir()
        except (OSError, installer.IntegrationInstallError):
            continue


_SPECIFY_SCOPE = (
    ".specify/integrations", ".specify/templates", ".specify/scripts",
    ".specify/.gitignore", ".specify/presets", ".specify/extensions",
    ".specify/extensions.yml", ".specify/workflows/speckit",
)


@contextmanager
def _transaction(
    root: Path, target: str | None,
    expected_state: dict[str, Any] | None, expected_records: dict[str, dict[str, Any]],
    *, creation_root: Path | None = None,
):
    """Journal operation-owned writes under an inter-process integration lock."""
    from ..shared_infra import _exclusive_project_lock
    from .manifest import IntegrationManifest

    folders = set(_SPECIFY_SCOPE)
    manifest_leaves: set[str] = set()
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
                installer.safe_project_path(root, relative, allow_leaf_symlink=True)
                manifest_leaves.add(relative)
    for integration in INTEGRATION_REGISTRY.values():
        if type(integration).__module__.startswith(installer._MODULE_PREFIX):
            folders.add(integration.config["folder"].rstrip("/"))
    target_integration = INTEGRATION_REGISTRY.get(target)
    target_folder = (target_integration.config or {}).get("folder") if target_integration else None
    if target_folder:
        folders.add(target_folder.rstrip("/"))
    paths = [
        installer.safe_project_path(
            root, folder, allow_leaf_symlink=folder in manifest_leaves and folder not in folders
        )
        for folder in sorted(folders | manifest_leaves)
    ]
    home_scopes = []
    for key in {*installed_integration_keys(state or {}), target} & BUILTIN_INTEGRATION_KEYS:
        integration = INTEGRATION_REGISTRY[key]
        directory = (integration.registrar_config or {}).get("dir", "")
        if directory.startswith("~/"):
            scope = installer.safe_project_path(Path.home().absolute(), directory[2:])
            home_scopes.append(scope)
    paths.extend(home_scopes)
    paths = [path for path in paths if not any(other != path and other in path.parents for other in paths)]
    root_existed = root.exists()
    lock_root = installer._trust_store(root).parent.parent
    lock_id = hashlib.sha256(os.path.normcase(str(root.resolve())).encode()).hexdigest()
    outcome = {"retained": False}
    try:
        # Keep the stable project-keyed lock outside an uninitialized target.
        with _exclusive_project_lock(lock_root, f".integration-install-{lock_id}.lock", context="integration"):
            if creation_root is None:
                root.mkdir(parents=True, exist_ok=True)
            else:
                from .._file_policy import prepare_init_root

                prepare_init_root(creation_root)
            current_state, state_error = try_read_integration_json(root)
            if state_error or current_state != expected_state or installer.read_records(root) != expected_records:
                raise installer.IntegrationInstallError(
                    "Integration state changed while preparing the operation; retry with the current project state"
                )
            with _journalled(root, paths, home_scopes, outcome):
                with installer.event_recovery_transaction():
                    yield
    finally:
        if not outcome["retained"] and not root_existed:
            try:
                root.rmdir()
            except FileNotFoundError:
                pass
            except OSError as exc:
                if exc.errno not in (errno.ENOTEMPTY, errno.EEXIST):
                    raise


@contextmanager
def _journalled(
    root: Path, paths: list[Path], home_scopes: list[Path], outcome: dict[str, bool],
    initial: dict[Path, tuple[int, ...]] | None = None,
):
    """Restore every observed write if the body raises.

    Sets ``outcome["retained"]`` when recovery snapshots are kept because
    restoring them found conflicts, restored a file's contents without all of
    its metadata (mode, times, extended attributes or BSD flags), or failed.
    A file the body rewrote in place is restored in place; a file it replaced
    or removed, one rollback cannot safely identify, and a directory are
    recreated from their snapshots. ``initial`` is the census of ``paths``,
    taken here when not given.
    """
    if initial is None:
        initial = _initial_entries(paths)
    backup = Path(tempfile.mkdtemp(prefix="speckit-integration-rollback-"))
    journal = None
    try:
        journal = _FileJournal(root, paths, backup, initial, tuple(home_scopes))
        token = file_change_observer.set(journal.observe)
        directory_token = directory_creation_observer.set(journal.directory_created)
        try:
            yield
        except BaseException as operation_error:
            # Keep the snapshots unless restoring them completes cleanly.
            outcome["retained"] = True
            try:
                # Restoration itself must not add writes to the journal.
                file_change_observer.reset(token)
                token = None
                directory_creation_observer.reset(directory_token)
                directory_token = None
                conflicts = _restore_snapshots(root, journal)
                incomplete = journal.incomplete_restores
                outcome["retained"] = bool(conflicts or incomplete)
                if conflicts:
                    console.print(
                        "[yellow]Warning:[/yellow] Preserved concurrent edits or incomplete writes to "
                        f"{escape(str(conflicts))}. Recovery snapshots retained at {escape(str(backup))}"
                    )
                if incomplete:
                    console.print(
                        "[yellow]Warning:[/yellow] Could not fully restore "
                        f"{escape(str(incomplete))}: their contents, ownership, links, permissions, "
                        "timestamps, extended attributes or file flags may differ from the originals. "
                        f"Recovery snapshots retained at {escape(str(backup))}"
                    )
            except (OSError, installer.IntegrationInstallError) as restore_error:
                outcome["retained"] = True
                if isinstance(operation_error, typer.Exit) and operation_error.__context__ is not None:
                    # A command that reports its own failure exits; name the cause.
                    operation_error = operation_error.__context__
                raise installer.IntegrationInstallError(
                    f"Integration operation failed ({operation_error}); rollback failed "
                    f"({restore_error}). Recovery snapshots retained at {backup}; "
                    f"write snapshot indexes correspond to {[str(path) for path in journal.changes]}"
                ) from operation_error
            raise
        finally:
            if token is not None:
                file_change_observer.reset(token)
            if directory_token is not None:
                directory_creation_observer.reset(directory_token)
    finally:
        if journal is not None:
            journal.release()
        if not outcome["retained"]:
            # Snapshots keep their source's modes, so make a read-only one
            # writable; a removal failure must not fail a committed operation.
            # Only retry removals, and only chmod real entries inside the
            # snapshot: os.chmod follows a snapshotted symlink to its live
            # target, and the backup root's parent is the system temp dir.
            def inside_backup(path) -> bool:
                path = Path(path)
                return path == backup or backup in path.parents

            def writable_and_retry(function, path, _exc_info):
                try:
                    if inside_backup(path) and not os.path.islink(path):
                        os.chmod(path, stat.S_IRWXU)
                    parent = os.path.dirname(path)
                    if inside_backup(parent):
                        os.chmod(parent, stat.S_IRWXU)
                    if function in (os.unlink, os.remove, os.rmdir):
                        function(path)
                except OSError:
                    pass

            shutil.rmtree(backup, onerror=writable_and_retry)
            # A directory rmtree could not open was made readable above; a
            # second pass removes what the first had to leave.
            if os.path.lexists(backup):
                shutil.rmtree(backup, onerror=writable_and_retry)


@contextmanager
def builtin_journal(root: Path, key: str, manifest_files, discover_folders=lambda: ()) -> Any:
    """Journal a built-in upgrade or init up to its manifest and state commit.

    ``setup()`` writes generated files, in place where they already exist,
    before the new manifest is saved, so a failure in between would leave
    files no manifest describes, which later runs then treat as the user's.
    Inside an external lifecycle transaction this does nothing, as that
    journal already covers the operation. It takes no project lock and reads
    no other integration's state. If the journal cannot cover the operation
    (a symlinked or unsafe scope, an unreadable directory), it runs
    unjournalled, as it did before, rather than failing. ``manifest_files``
    are the integration's currently recorded files. ``discover_folders``
    returns its ``upgrade_output_folders()``, which its config cannot name;
    it is called outside an external transaction only, and if it fails the
    operation runs unjournalled.
    """
    if lifecycle_owns_rollback():
        yield
        return
    try:
        integration = INTEGRATION_REGISTRY.get(key)
        folders = set(_SPECIFY_SCOPE)
        folder = (integration.config or {}).get("folder") if integration else None
        if folder:
            folders.add(folder.rstrip("/"))
        folders.update(extra.rstrip("/") for extra in discover_folders())
        # Merge targets an integration leaves untracked (Copilot's
        # .vscode/settings.json) must pass the same eligibility check.
        exclusions = integration.stale_cleanup_exclusions() if integration else set()
        leaves = (set(manifest_files) | exclusions) - folders
        paths = [
            installer.safe_project_path(root, entry, allow_leaf_symlink=entry in leaves)
            for entry in sorted(folders | leaves)
        ]
        home_scopes = []
        directory = (integration.registrar_config or {}).get("dir", "") if integration else ""
        if directory.startswith("~/"):
            home_scopes.append(installer.safe_project_path(Path.home().absolute(), directory[2:]))
        paths.extend(home_scopes)
        paths = [path for path in paths if not any(other != path and other in path.parents for other in paths)]
        initial = _initial_entries(paths)
        # The journal refuses a write to or beneath anything but a regular
        # file or directory, which an unjournalled upgrade would have made.
        # Manifests record paths under the resolved root, so a root reached
        # through a symlink or junction would make every observed write look
        # like an escape; leave such a project unjournalled.
        covered = root.absolute() == root.resolve() and all(
            stat.S_ISREG(state[0]) or stat.S_ISDIR(state[0]) for state in initial.values()
        )
    except (installer.IntegrationInstallError, OSError, ValueError, RuntimeError):
        covered = False
    if not covered:
        yield
        return
    with _journalled(root, paths, home_scopes, {"retained": False}, initial):
        yield


def external_lifecycle(operation: str):
    """Add package preparation to existing handlers without duplicating setup."""
    def decorate(handler):
        signature = inspect.signature(handler)

        @wraps(handler)
        @installer.registry_synchronized
        def invoke(*args, **kwargs):
            values = signature.bind_partial(*args, **kwargs).arguments
            loaded = False
            if operation == "init":
                project_name = values.get("project_name")
                here = values.get("here", False) or project_name == "."
                if (here and project_name not in (None, ".")) or (not here and not project_name):
                    return handler(*args, **kwargs)
                creation_root = Path.cwd() if here else Path(project_name).absolute()
                root = creation_root
                key = values.get("integration")
            else:
                from .. import _require_specify_project

                root = _require_specify_project()
                key = values.get("target" if operation == "switch" else "key")
            recovery_token = None
            recovery_binding = None
            try:
                if operation == "init":
                    from .._file_policy import preflight_init_root

                    root = preflight_init_root(creation_root)
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
                    recovery_binding = installer.recovery_metadata(root, key, records[key])
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
                            (creation_root, root.exists(), list(root.iterdir()) if root.is_dir() else [])
                        )
                        stack.callback(_init_directory.reset, token)
                    transaction = (
                        _transaction(root, key, state, records, creation_root=creation_root)
                        if operation == "init"
                        else _transaction(root, key, state, records)
                    )
                    with transaction:
                        if recovery_token is not None and recovery_binding is None:
                            from .manifest import IntegrationManifest

                            path = root / ".specify/integrations" / f"{key}.manifest.json"
                            if path.exists():
                                manifest = IntegrationManifest.load(key, root)
                                IntegrationManifest(key, root, version=manifest.version).save()
                            console.print(
                                "[yellow]Warning:[/yellow] No local recovery ownership record; "
                                "preserving old generated files from cleanup. They may require manual cleanup. "
                                "A trusted replacement can overwrite files at its declared destination."
                            )
                        elif recovery_token is not None and recovery_binding is not None:
                            from .manifest import IntegrationManifest

                            path = root / ".specify/integrations" / f"{key}.manifest.json"
                            if path.exists():
                                manifest = IntegrationManifest.load(key, root)
                                modes = recovery_binding.get("ownership_modes", {})
                                preserved = []
                                for relative in manifest.files:
                                    mode = modes.get(relative, "shared")
                                    manifest.set_ownership(relative, mode)
                                    if mode != "whole":
                                        preserved.append(relative)
                                manifest.save()
                                if preserved:
                                    console.print(
                                        "[yellow]Warning:[/yellow] Preserving shared, partial, or unproven "
                                        f"file ownership: {escape(str(preserved))}. Manual event cleanup may be needed."
                                    )
                        try:
                            result = handler(*args, **kwargs)
                        except typer.Exit as exc:
                            if exc.exit_code != 0 or (candidate and operation == "upgrade"):
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
                            # The uninstall command cleans up its own key. A stale
                            # record's contributions must go here, while its adapter
                            # is still loaded.
                            if operation == "uninstall" and removed != key:
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
