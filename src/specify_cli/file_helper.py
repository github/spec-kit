"""Scoped filesystem operations; see design/file-helper.md for the contract."""

import codecs
import errno
import os
import stat
import sys
import tempfile
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from copy import copy
from dataclasses import dataclass, field
from pathlib import Path, PurePath, PureWindowsPath
from typing import TypeVar
from weakref import finalize

from specify_cli._file_handles import (
    _windows_file_id, _windows_handle, _windows_overwrite_fd, _windows_stat,
)


_PathType = TypeVar("_PathType", bound=PurePath)
_DELETE_DIR_FD_SUPPORTED = (
    {os.open, os.stat, os.readlink, os.unlink, os.rmdir} <= os.supports_dir_fd
    and os.stat in os.supports_follow_symlinks
    and os.scandir in os.supports_fd
)
_OVERWRITE_DIR_FD_SUPPORTED = os.open in os.supports_dir_fd


def _strip_extended_length_prefix(path: _PathType) -> _PathType:
    """Normalize Windows extended drive/UNC spellings for comparison only."""
    raw = str(path)
    if raw.lower().startswith("\\\\?\\unc\\"):
        return type(path)("\\\\" + raw[len("\\\\?\\UNC\\"):])
    if raw.startswith("\\\\?\\"):
        return type(path)(raw[len("\\\\?\\"):])
    return path


class FileHelperError(ValueError):
    """An operation violates the scoped filesystem contract."""


class SymlinkDeniedError(FileHelperError):
    """An accessed symlink requires explicit traversal permission."""


class PathEscapeError(FileHelperError):
    """An accessed path is outside the established root."""


class UnsupportedPathError(FileHelperError):
    """An accessed object cannot be used by the requested operation."""


@dataclass
class _WalkDirectories:
    root: Path
    root_handle: int | Path
    flags: int
    resources: ExitStack
    opened: dict[Path, int | Path] = field(default_factory=dict)

    def directory(self, path: Path) -> int | Path:
        if path == self.root:
            return self.root_handle
        path.relative_to(self.root)
        if path not in self.opened:
            parent = self.directory(path.parent)
            if isinstance(parent, Path):
                try:
                    self.resources.enter_context(_windows_handle(path, directory=True))
                except OSError as exc:
                    if exc.errno == errno.EINVAL and getattr(exc, "winerror", None) is None:
                        raise NotADirectoryError(
                            errno.ENOTDIR, "Expected a directory", str(path)
                        ) from exc
                    raise
                self.opened[path] = path
            else:
                fd = os.open(path.name, self.flags, dir_fd=parent)
                self.resources.callback(os.close, fd)
                self.opened[path] = fd
        return self.opened[path]


@dataclass(frozen=True)
class _DeletionEntry:
    path: Path
    directory: bool
    children: tuple["_DeletionEntry", ...] = ()


@dataclass(frozen=True)
class FileHelper:
    """Own operations beneath one trusted root with an immutable link policy.

    Relative operation paths are relative to ``root``, not the process cwd.
    The root itself is a trusted alias boundary, resolved once on construction.
    """

    root: Path
    allow_symlinks: bool = False
    _canonical_root: Path = field(init=False, repr=False)
    _root_stat: os.stat_result = field(init=False, repr=False, compare=False)
    _root_anchor: int | Path | None = field(init=False, repr=False, compare=False)
    _root_anchor_error: OSError | None = field(init=False, repr=False, compare=False)
    _windows_root_id: tuple[int, bytes] | None = field(init=False, repr=False, compare=False)
    _root_cleanup: finalize = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        root = Path(self.root).absolute()
        canonical = root.resolve(strict=True)
        root_stat = canonical.stat()
        if not stat.S_ISDIR(root_stat.st_mode):
            raise NotADirectoryError(root)
        object.__setattr__(self, "root", root)
        object.__setattr__(self, "_canonical_root", canonical)
        object.__setattr__(self, "_root_stat", root_stat)
        with ExitStack() as resources:
            anchor: int | Path | None = None
            anchor_error: OSError | None = None
            windows_root_id: tuple[int, bytes] | None = None
            if os.name == "nt":
                with ExitStack() as reference:
                    try:
                        handle = reference.enter_context(
                            _windows_handle(canonical, directory=True, pin=False)
                        )
                        self._check_deletion_root(_windows_stat(handle))
                        windows_root_id = _windows_file_id(handle)
                    except OSError as exc:
                        # Other operations do not require deletion's handle capability.
                        exc.__traceback__ = None
                        anchor_error = exc
                    else:
                        self._check_deletion_root(canonical.stat())
                        resources.enter_context(reference.pop_all())
                        anchor = canonical
            elif (
                _DELETE_DIR_FD_SUPPORTED
                and getattr(os, "O_NOFOLLOW", 0)
                and getattr(os, "O_DIRECTORY", 0)
            ):
                anchor = os.open(canonical, self._directory_flags())
                resources.callback(os.close, anchor)
                self._check_deletion_root(os.fstat(anchor))
            object.__setattr__(self, "_root_anchor", anchor)
            object.__setattr__(self, "_root_anchor_error", anchor_error)
            object.__setattr__(self, "_windows_root_id", windows_root_id)
            object.__setattr__(self, "_root_cleanup", finalize(self, resources.pop_all().close))

    def close(self) -> None:
        """Release retained root handles; closing more than once is harmless."""
        self._root_cleanup()

    def _require_open(self) -> None:
        if not self._root_cleanup.alive:
            raise FileHelperError("FileHelper is closed")

    def __enter__(self) -> "FileHelper":
        self._require_open()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _parts(self, path: PurePath) -> tuple[str, ...]:
        original = path
        if isinstance(path, PureWindowsPath):
            path = _strip_extended_length_prefix(path)
        if not path.is_absolute():
            if original.anchor or path.anchor:
                raise PathEscapeError(f"Rooted-relative, drive-relative, or device path is not permitted: {original}")
            return path.parts
        for root in (self.root, self._canonical_root):
            if isinstance(root, PureWindowsPath):
                root = _strip_extended_length_prefix(root)
            try:
                return path.relative_to(root).parts
            except ValueError:
                continue
        raise PathEscapeError(f"Path is outside root {self.root}: {original}")

    @staticmethod
    def _entry_mode(path: Path, *, dir_fd: int | None = None) -> int:
        entry = (
            path.lstat() if dir_fd is None
            else os.stat(path.name, dir_fd=dir_fd, follow_symlinks=False)
        )
        if (
            getattr(entry, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
            and not stat.S_ISLNK(entry.st_mode)
        ):
            raise UnsupportedPathError(
                f"Unsupported Windows reparse point (including directory junctions): {path}"
            )
        return entry.st_mode

    def _walk(
        self,
        parts: tuple[str, ...],
        *,
        allow_missing: bool = False,
        follow_leaf: bool = True,
        links: tuple[Path, ...] = (),
        directories: _WalkDirectories | None = None,
    ) -> Path:
        current = self._canonical_root
        for index, part in enumerate(parts):
            directory = directories.directory(current) if directories is not None else None
            directory_fd = directory if isinstance(directory, int) else None
            if directories is None and not current.is_dir():
                if not (allow_missing and not current.exists()):
                    raise NotADirectoryError(current)
            if part == "..":
                if current == self._canonical_root:
                    raise PathEscapeError(f"Symlink target escapes root {self.root}")
                current = current.parent
                continue
            candidate = current / part
            try:
                mode = self._entry_mode(candidate, dir_fd=directory_fd)
            except FileNotFoundError:
                if not allow_missing:
                    raise
                current = candidate
                continue
            if stat.S_ISLNK(mode):
                if not self.allow_symlinks:
                    raise SymlinkDeniedError(
                        f"Refusing symlink {candidate}; explicitly allow symlinks "
                        "on this FileHelper to use supported contained targets"
                    )
                if not follow_leaf and index == len(parts) - 1:
                    return candidate
                if candidate in links or len(links) >= 40:
                    raise UnsupportedPathError(f"Symlink cycle or excessive chain: {candidate}")
                if directory_fd is None:
                    target = Path(os.readlink(candidate))
                else:
                    target = Path(os.readlink(part, dir_fd=directory_fd))
                target_parts = self._parts(target)
                if not target.is_absolute():
                    target_parts = current.relative_to(self._canonical_root).parts + target_parts
                # Resolve the link target strictly, even when creating a new child.
                current = self._walk(
                    target_parts, links=links + (candidate,), directories=directories
                )
            elif stat.S_ISDIR(mode) or stat.S_ISREG(mode):
                current = candidate
            else:
                raise UnsupportedPathError(f"Unsupported filesystem object: {candidate}")
        return current

    def _path(
        self, path: Path | str, *, allow_missing: bool = False, follow_leaf: bool = True,
        root_handle: int | Path | None = None,
    ) -> Path:
        self._require_open()
        original = Path(path)
        parts = self._parts(original)
        if ".." in parts:
            raise PathEscapeError(f"Parent traversal is not an operation path: {original}")
        with ExitStack() as resources:
            directories = (
                _WalkDirectories(
                    self._canonical_root, root_handle,
                    0 if isinstance(root_handle, Path) else self._directory_flags(), resources,
                )
                if root_handle is not None else None
            )
            return self._walk(
                parts, allow_missing=allow_missing, follow_leaf=follow_leaf, directories=directories
            )

    @staticmethod
    def _require_file(path: Path) -> None:
        if not stat.S_ISREG(path.stat().st_mode):
            raise UnsupportedPathError(f"Expected a regular file: {path}")

    def mkdir(
        self, path: Path | str, *, parents: bool = False, exist_ok: bool = False
    ) -> None:
        """Create a directory, preflighting the entire requested hierarchy."""
        destination = self._path(path, allow_missing=True)
        destination.mkdir(parents=parents, exist_ok=exist_ok)

    def read_bytes(self, path: Path | str) -> bytes:
        destination = self._path(path)
        self._require_file(destination)
        return destination.read_bytes()

    def read_text(self, path: Path | str, *, encoding: str = "utf-8") -> str:
        return self.read_bytes(path).decode(encoding)

    @contextmanager
    def _creation_directory(self, directory: Path) -> Iterator[int | Path]:
        """Anchor an already policy-resolved parent without following new links."""
        parts = directory.relative_to(self._canonical_root).parts
        if os.name == "nt":
            with ExitStack() as stack:
                current = self._canonical_root
                stack.enter_context(_windows_handle(current, directory=True))
                for part in parts:
                    current = current / part
                    stack.enter_context(_windows_handle(current, directory=True))
                yield current
            return

        if not (
            getattr(os, "O_NOFOLLOW", 0)
            and getattr(os, "O_DIRECTORY", 0)
            and os.open in os.supports_dir_fd
        ):
            raise OSError(errno.ENOTSUP, "Anchored file creation is unsupported on this platform")
        flags = self._directory_flags()
        parent = os.open(self._canonical_root, flags)
        try:
            for part in parts:
                child = os.open(part, flags, dir_fd=parent)
                os.close(parent)
                parent = child
            yield parent
        finally:
            os.close(parent)

    def create_bytes(self, path: Path | str, content: bytes, *, mode: int = 0o644) -> None:
        """Exclusively create a file; never overwrite an existing entry."""
        destination = self._path(path, allow_missing=True, follow_leaf=False)
        try:
            self._entry_mode(destination)
        except FileNotFoundError:
            pass
        else:
            raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), str(destination))
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_NOFOLLOW", 0)
        with self._creation_directory(destination.parent) as directory:
            if isinstance(directory, Path):
                fd = os.open(directory / destination.name, flags, mode)
            else:
                fd = os.open(destination.name, flags, mode, dir_fd=directory)
            try:
                stream = os.fdopen(fd, "wb")
            except BaseException:
                os.close(fd)
                raise
            with stream:
                stream.write(content)

    def create_text(
        self, path: Path | str, content: str, *, encoding: str = "utf-8", mode: int = 0o644
    ) -> None:
        self.create_bytes(path, content.encode(encoding), mode=mode)

    def write_bytes(self, path: Path | str, content: bytes, *, mode: int = 0o644) -> None:
        """Atomically create/replace a file, preserving any allowed leaf link."""
        destination = self._path(path, allow_missing=True)
        if destination.exists():
            self._require_file(destination)
        fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
        temporary_path = Path(temporary)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(content)
            temporary_path.chmod(mode)
            if self._path(path, allow_missing=True) != destination:
                raise FileHelperError(f"Destination changed during write: {path}")
            os.replace(temporary_path, destination)
        finally:
            temporary_path.unlink(missing_ok=True)

    def write_text(
        self, path: Path | str, content: str, *, encoding: str = "utf-8", mode: int = 0o644
    ) -> None:
        self.write_bytes(path, content.encode(encoding), mode=mode)

    def overwrite_text(
        self, path: Path | str, content: str, *, encoding: str = "utf-8"
    ) -> None:
        """Non-atomic text upsert preserving existing inode and native text I/O."""
        destination = self._path(path, allow_missing=True)
        if destination.exists():
            self._require_file(destination)
        codecs.lookup(encoding)
        with self._overwrite_descriptor(destination) as fd:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise UnsupportedPathError(f"Expected a regular file: {destination}")
            os.ftruncate(fd, 0)
            with os.fdopen(fd, "w", encoding=encoding, closefd=False) as stream:
                stream.write(content)

    @contextmanager
    def _overwrite_descriptor(self, destination: Path) -> Iterator[int]:
        """Anchor the resolved hierarchy before opening a non-truncating leaf."""
        parts = destination.relative_to(self._canonical_root).parts
        with ExitStack() as stack:
            if os.name == "nt":
                current = self._canonical_root
                stack.enter_context(_windows_handle(current, directory=True))
                for part in parts[:-1]:
                    current = current / part
                    stack.enter_context(_windows_handle(current, directory=True))
                yield stack.enter_context(_windows_overwrite_fd(destination))
                return

            if not (
                _OVERWRITE_DIR_FD_SUPPORTED
                and getattr(os, "O_NOFOLLOW", 0)
                and getattr(os, "O_DIRECTORY", 0)
                and getattr(os, "O_NONBLOCK", 0)
            ):
                raise OSError(errno.ENOTSUP, "Scoped text overwrite is unsupported on this platform")
            directory_access = getattr(os, "O_SEARCH", getattr(os, "O_PATH", None))
            if directory_access is None:
                # Older Darwin Python builds omit the kernel's O_EXEC/O_SEARCH bit.
                directory_access = 0x40000000 if sys.platform == "darwin" else os.O_RDONLY
            directory_flags = (
                directory_access | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
            )
            parent = os.open(self._canonical_root, directory_flags)
            try:
                for part in parts[:-1]:
                    child = os.open(part, directory_flags, dir_fd=parent)
                    os.close(parent)
                    parent = child
                flags = (
                    os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK
                    | getattr(os, "O_CLOEXEC", 0)
                )
                fd = os.open(parts[-1], flags, 0o666, dir_fd=parent)
                try:
                    yield fd
                finally:
                    os.close(fd)
            finally:
                os.close(parent)

    def symlink(self, target: Path | str, path: Path | str) -> None:
        """Create a link to an existing contained regular file or directory.

        Relative targets use the link's parent, matching ``Path.symlink_to``.
        """
        if not self.allow_symlinks:
            raise SymlinkDeniedError("Symlink creation requires explicit allow_symlinks=True")
        destination = self._path(path, allow_missing=True, follow_leaf=False)
        target = Path(target)
        target_parts = self._parts(target)
        if not target.is_absolute():
            target_parts = destination.parent.relative_to(self._canonical_root).parts + target_parts
        resolved = self._walk(target_parts)
        destination.symlink_to(target, target_is_directory=resolved.is_dir())

    @staticmethod
    def _directory_flags() -> int:
        access = getattr(os, "O_PATH", 0) or getattr(os, "O_SEARCH", 0)
        if not access:
            # Some older Python builds omit Darwin's native search-only flag.
            access = (0x40000000 | os.O_DIRECTORY) if sys.platform == "darwin" else os.O_RDONLY
        return access | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)

    def _check_deletion_root(self, current: os.stat_result) -> None:
        if not os.path.samestat(self._root_stat, current):
            raise FileHelperError(f"Established root changed during deletion: {self.root}")

    @contextmanager
    def _deletion_root(self) -> Iterator[int | Path]:
        """Borrow the root pinned when this helper was established."""
        self._require_open()
        if self._root_anchor is None:
            if self._root_anchor_error is not None:
                error = copy(self._root_anchor_error)
                # OSError's copy protocol omits its native Windows error slot.
                if hasattr(self._root_anchor_error, "winerror"):
                    error.winerror = self._root_anchor_error.winerror
                raise error
            raise OSError(errno.ENOTSUP, "Handle-based deletion is unsupported on this platform")
        self._check_deletion_root(self._canonical_root.stat())
        if isinstance(self._root_anchor, Path):
            with ExitStack() as resources:
                for ancestor in reversed(self._root_anchor.parents):
                    resources.enter_context(_windows_handle(ancestor, directory=True))
                handle = resources.enter_context(
                    _windows_handle(self._root_anchor, directory=True)
                )
                if _windows_file_id(handle) != self._windows_root_id:
                    raise FileHelperError(f"Established root changed during deletion: {self.root}")
                yield self._root_anchor
        else:
            yield self._root_anchor

    @contextmanager
    def _child_deletion_directory(
        self, parent: int | Path, name: str, *, readable: bool = False
    ) -> Iterator[int | Path]:
        if isinstance(parent, Path):
            child = parent / name
            with _windows_handle(child, directory=True):
                yield child
            return
        flags = (
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
            if readable else self._directory_flags()
        )
        child = os.open(name, flags, dir_fd=parent)
        try:
            yield child
        finally:
            os.close(child)

    @contextmanager
    def _deletion_directory(self, path: Path, *, root: int | Path) -> Iterator[int | Path]:
        parts = path.relative_to(self._canonical_root).parts
        with ExitStack() as resources:
            parent = root
            for part in parts:
                parent = resources.enter_context(self._child_deletion_directory(parent, part))
            yield parent

    def _deletion_entry_mode(self, path: Path, *, parent: int | Path) -> int:
        if isinstance(parent, Path):
            return self._entry_mode(parent / path.name)
        return self._entry_mode(path, dir_fd=parent)

    def _deletion_kind(self, path: Path, mode: int) -> bool:
        if stat.S_ISLNK(mode):
            if not self.allow_symlinks:
                raise SymlinkDeniedError(f"Refusing to delete symlink: {path}")
            return False
        if stat.S_ISREG(mode):
            return False
        if not stat.S_ISDIR(mode):
            raise UnsupportedPathError(f"Unsupported filesystem object: {path}")
        return True

    def _deletion_plan(
        self, path: Path, *, recursive: bool, parent: int | Path
    ) -> _DeletionEntry:
        directory = self._deletion_kind(path, self._deletion_entry_mode(path, parent=parent))
        children: tuple[_DeletionEntry, ...] = ()
        if directory and recursive:
            with self._child_deletion_directory(parent, path.name, readable=True) as child_directory:
                with os.scandir(child_directory) as entries:
                    names = sorted(entry.name for entry in entries)
                child_plans = []
                for name in names:
                    child_plans.append(
                        self._deletion_plan(path / name, recursive=True, parent=child_directory)
                    )
                children = tuple(child_plans)
        return _DeletionEntry(path, directory, children)

    def _delete_plan(self, entry: _DeletionEntry, *, parent: int | Path) -> None:
        directory = self._deletion_kind(
            entry.path, self._deletion_entry_mode(entry.path, parent=parent)
        )
        if directory != entry.directory:
            raise FileHelperError(f"Destination changed during deletion: {entry.path}")
        if directory and entry.children:
            with self._child_deletion_directory(parent, entry.path.name) as child_directory:
                for child in entry.children:
                    self._delete_plan(child, parent=child_directory)
        leaf = parent / entry.path.name if isinstance(parent, Path) else entry.path.name
        directory_fd = None if isinstance(parent, Path) else parent
        if directory:
            os.rmdir(leaf, dir_fd=directory_fd)
        else:
            os.unlink(leaf, dir_fd=directory_fd)

    def delete(self, path: Path | str, *, recursive: bool = False) -> None:
        """Delete an entry; recursive deletion never follows descendant links."""
        with self._deletion_root() as root:
            destination = self._path(path, follow_leaf=False, root_handle=root)
            if destination == self._canonical_root:
                raise FileHelperError(f"Refusing to delete the established root: {self.root}")
            with self._deletion_directory(destination.parent, root=root) as parent:
                plan = self._deletion_plan(destination, recursive=recursive, parent=parent)
                self._delete_plan(plan, parent=parent)
