"""Scoped filesystem operations; see design/file-helper.md for the contract."""

import codecs
import errno
import os
import secrets
import stat
import sys
import tempfile
from collections import OrderedDict
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from copy import copy
from dataclasses import dataclass, field
from pathlib import Path, PurePath, PureWindowsPath
from typing import TypeVar
from weakref import finalize

from specify_cli._file_handles import (
    _WindowsFileIdentity, _windows_delete, _windows_directory_names, _windows_entry,
    _windows_file_id, _windows_handle, _windows_mode, _windows_overwrite_fd,
    _windows_readlink, _windows_stat, rename_noreplace, windows_read_fd,
)


_PathType = TypeVar("_PathType", bound=PurePath)
_DELETE_DIR_FD_SUPPORTED = (
    {os.open, os.stat, os.readlink, os.unlink, os.rmdir} <= os.supports_dir_fd
    and os.stat in os.supports_follow_symlinks
    and os.scandir in os.supports_fd
)
_DELETE_DIRECTORY_CACHE_SIZE = 8
# Wrapping os.open must not change the underlying platform capability.
_POSIX_OPEN = os.open


def _strip_extended_length_prefix(path: _PathType) -> _PathType:
    """Normalize Windows extended drive/UNC spellings for comparison only."""
    raw = str(path)
    if raw.lower().startswith("\\\\?\\unc\\"):
        return type(path)("\\\\" + raw[len("\\\\?\\UNC\\"):])
    if raw.startswith("\\\\?\\"):
        return type(path)(raw[len("\\\\?\\"):])
    return path


def _windows_extended_path(path: _PathType) -> _PathType:
    raw = str(path)
    if raw.startswith("\\\\?\\"):
        return path
    if raw.startswith("\\\\"):
        return type(path)("\\\\?\\UNC\\" + raw[2:])
    return type(path)("\\\\?\\" + raw)


class FileHelperError(ValueError):
    """An operation violates the scoped filesystem contract."""


class SymlinkDeniedError(FileHelperError):
    """An accessed symlink requires explicit traversal permission."""


class PathEscapeError(FileHelperError):
    """An accessed path is outside the established root."""


class UnsupportedPathError(FileHelperError):
    """An accessed object cannot be used by the requested operation."""


class _SpecialFileError(UnsupportedPathError):
    """An entry is neither a directory, regular file, nor symlink."""


@dataclass(frozen=True)
class _WindowsDirectory:
    path: Path
    handle: int


@dataclass
class _WalkDirectories:
    root: Path
    root_handle: int | _WindowsDirectory
    flags: int
    resources: ExitStack
    opened: dict[Path, _WindowsDirectory] = field(default_factory=dict)
    current: tuple[Path, int] | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if isinstance(self.root_handle, int):
            self.resources.callback(self._release_current)

    def _release_current(self) -> None:
        current, self.current = self.current, None
        if current is not None:
            os.close(current[1])

    def _posix_directory(self, path: Path, root_fd: int) -> int:
        current_path, parent = self.current or (self.root, root_fd)
        if path == current_path:
            return parent
        if path.parent != current_path:
            # Re-anchor jumps, including "..", rather than following a moved
            # directory's physical parent outside the retained root.
            self._release_current()
            current_path, parent = self.root, root_fd
        for part in path.relative_to(current_path).parts:
            child = os.open(part, self.flags, dir_fd=parent)
            previous = self.current
            current_path = current_path / part
            self.current = (current_path, child)
            if previous is not None:
                os.close(previous[1])
            parent = child
        return parent

    def directory(self, path: Path) -> int | _WindowsDirectory:
        path.relative_to(self.root)
        if isinstance(self.root_handle, int):
            return self._posix_directory(path, self.root_handle)
        if path == self.root:
            return self.root_handle
        if path not in self.opened:
            parent = self.directory(path.parent)
            if not isinstance(parent, _WindowsDirectory):
                raise FileHelperError("Expected a native Windows directory")
            try:
                handle = self.resources.enter_context(_windows_handle(
                    Path(path.name), directory=True, parent=parent.handle
                ))
            except OSError as exc:
                if exc.errno == errno.EINVAL and getattr(exc, "winerror", None) is None:
                    raise NotADirectoryError(
                        errno.ENOTDIR, "Expected a directory", str(path)
                    ) from exc
                raise
            self.opened[path] = _WindowsDirectory(path, handle)
        return self.opened[path]


@dataclass(frozen=True)
class _DeletionEntry:
    path: Path
    directory: bool
    children: tuple["_DeletionEntry", ...] = ()


@dataclass
class _DeletionDirectories:
    root: Path
    root_fd: int
    flags: int
    resources: ExitStack
    opened: OrderedDict[Path, int] = field(default_factory=OrderedDict)

    def __post_init__(self) -> None:
        self.resources.callback(self.close)

    def close(self) -> None:
        while self.opened:
            _, fd = self.opened.popitem()
            os.close(fd)

    def discard(self, path: Path) -> None:
        fd = self.opened.pop(path, None)
        if fd is not None:
            os.close(fd)

    def directory(self, path: Path) -> int:
        path.relative_to(self.root)
        ancestor = path
        suffix = []
        while ancestor != self.root and ancestor not in self.opened:
            suffix.append(ancestor.name)
            ancestor = ancestor.parent
        parent = self.root_fd if ancestor == self.root else self.opened[ancestor]
        if ancestor in self.opened:
            self.opened.move_to_end(ancestor)
        for name in reversed(suffix):
            child = os.open(name, self.flags, dir_fd=parent)
            ancestor = ancestor / name
            self.opened[ancestor] = child
            if len(self.opened) > _DELETE_DIRECTORY_CACHE_SIZE:
                _, oldest = self.opened.popitem(last=False)
                os.close(oldest)
            parent = child
        return parent


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
    _windows_root_id: _WindowsFileIdentity | None = field(init=False, repr=False, compare=False)
    _windows_root_handle: int | None = field(init=False, repr=False, compare=False)
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
            windows_root_id: _WindowsFileIdentity | None = None
            windows_root_handle: int | None = None
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
                        windows_root_handle = handle
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
            object.__setattr__(self, "_windows_root_handle", windows_root_handle)
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
                mode = self._deletion_entry_mode(candidate, parent=directory) if (
                    isinstance(directory, _WindowsDirectory)
                ) else self._entry_mode(candidate, dir_fd=directory_fd)
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
                if isinstance(directory, _WindowsDirectory):
                    with _windows_entry(directory.handle, part) as handle:
                        target = Path(_windows_readlink(handle))
                elif directory_fd is None:
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
                raise _SpecialFileError(f"Unsupported filesystem object: {candidate}")
        return current

    def _path(
        self, path: Path | str, *, allow_missing: bool = False, follow_leaf: bool = True,
        root_handle: int | _WindowsDirectory | None = None,
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
                    0 if isinstance(root_handle, _WindowsDirectory) else self._directory_flags(), resources,
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

    @staticmethod
    def _require_directory(path: Path) -> None:
        if not stat.S_ISDIR(path.stat().st_mode):
            raise NotADirectoryError(path)

    def directory_exists(self, path: Path | str) -> bool:
        """Return False for absence only; reject wrong types and forbidden paths."""
        try:
            directory = self._path(path)
        except FileNotFoundError:
            return False
        except _SpecialFileError as exc:
            raise NotADirectoryError(str(exc)) from exc
        self._require_directory(directory)
        return True

    def mkdir(
        self, path: Path | str, *, parents: bool = False, exist_ok: bool = False
    ) -> None:
        """Create a directory, preflighting the entire requested hierarchy."""
        destination = self._path(path, allow_missing=True)
        destination.mkdir(parents=parents, exist_ok=exist_ok)

    def iterdir(
        self, path: Path | str, *, select: Callable[[str], bool] | None = None,
    ) -> tuple[Path, ...]:
        """Enumerate immediate entries, validating only names selected by the caller."""
        requested = Path(path)
        destination = self._path(requested)
        self._require_directory(destination)
        returned_parent = requested if requested.is_absolute() else self.root / requested
        entries = []
        with os.scandir(destination) as iterator:
            names = sorted(entry.name for entry in iterator)
        for name in names:
            if select is not None and not select(name):
                continue
            candidate = destination / name
            mode = self._entry_mode(candidate)
            if stat.S_ISLNK(mode):
                if not self.allow_symlinks:
                    raise SymlinkDeniedError(f"Refusing to enumerate symlink: {candidate}")
                self._path(candidate)
            elif not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise UnsupportedPathError(f"Unsupported filesystem object: {candidate}")
            entries.append(returned_parent / name)
        return tuple(entries)

    def move_noreplace(self, source: Path | str, destination: Path | str) -> None:
        """Atomically move a staged file or directory without clobbering a destination."""
        source_path = self._path(source, follow_leaf=False)
        source_mode = self._entry_mode(source_path)
        if not (stat.S_ISREG(source_mode) or stat.S_ISDIR(source_mode)):
            raise UnsupportedPathError(
                f"Unsupported filesystem object: {source_path}"
            )

        destination_path = self._path(
            destination, allow_missing=True, follow_leaf=False
        )
        try:
            self._entry_mode(destination_path)
        except FileNotFoundError:
            pass
        else:
            raise FileExistsError(
                errno.EEXIST, os.strerror(errno.EEXIST), str(destination_path)
            )
        rename_noreplace(source_path, destination_path)

    @contextmanager
    def temporary_directory(
        self, parent: Path | str, *, prefix: str = "speckit-"
    ) -> Iterator[Path]:
        """Create and clean up a staging directory beneath an existing in-root parent."""
        if any(character in prefix for character in "/\\:\0"):
            raise PathEscapeError(f"Temporary directory prefix must be a name prefix: {prefix!r}")
        requested = Path(parent)
        parent_path = self._path(requested)
        self._require_directory(parent_path)
        staging = Path(tempfile.mkdtemp(prefix=prefix, dir=parent_path))
        returned_parent = requested if requested.is_absolute() else self.root / requested

        def cleanup() -> None:
            try:
                self._entry_mode(staging)
            except FileNotFoundError:
                return
            self.delete(staging, recursive=True)

        try:
            yield returned_parent / staging.name
        except BaseException as body_error:
            try:
                cleanup()
            except BaseException as cleanup_error:
                body_error.add_note(f"Could not clean up staging directory {staging}: {cleanup_error}")
            raise
        else:
            cleanup()

    def read_bytes(self, path: Path | str) -> bytes:
        destination = self._path(path)
        self._require_file(destination)
        with ExitStack() as stack:
            if os.name == "nt":
                parts = destination.relative_to(self._canonical_root).parts
                parent = stack.enter_context(_windows_handle(
                    self._canonical_root, directory=True, traverse=True,
                ))
                for part in parts[:-1]:
                    parent = stack.enter_context(_windows_handle(
                        Path(part), directory=True, parent=parent, traverse=True,
                    ))
                handle = stack.enter_context(_windows_handle(
                    Path(parts[-1]), directory=False, parent=parent,
                ))
                fd = stack.enter_context(windows_read_fd(handle))
            else:
                unsupported = "Safe scoped reads are unsupported on this platform"
                if not getattr(os, "O_NONBLOCK", 0):
                    raise OSError(errno.ENOTSUP, unsupported)
                with self._posix_directory(destination.parent, unsupported_message=unsupported) as parent:
                    fd = os.open(
                        destination.name,
                        os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0),
                        dir_fd=parent,
                    )
                    stack.callback(os.close, fd)
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise UnsupportedPathError(f"Expected a regular file: {destination}")
            with os.fdopen(fd, "rb", closefd=False) as stream:
                return stream.read()

    def read_text(self, path: Path | str, *, encoding: str = "utf-8") -> str:
        return self.read_bytes(path).decode(encoding)

    @contextmanager
    def _posix_directory(self, directory: Path, *, unsupported_message: str) -> Iterator[int]:
        """Walk an already policy-resolved parent with bounded descriptor ownership."""
        parts = directory.relative_to(self._canonical_root).parts
        if not (
            getattr(os, "O_NOFOLLOW", 0)
            and getattr(os, "O_DIRECTORY", 0)
            and _POSIX_OPEN in os.supports_dir_fd
        ):
            raise OSError(errno.ENOTSUP, unsupported_message)
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

    @contextmanager
    def _creation_directory(self, directory: Path) -> Iterator[int | Path]:
        """Anchor an already policy-resolved parent without following new links."""
        if os.name == "nt":
            parts = directory.relative_to(self._canonical_root).parts
            with ExitStack() as stack:
                current = self._canonical_root
                stack.enter_context(_windows_handle(current, directory=True))
                for part in parts:
                    current = current / part
                    stack.enter_context(_windows_handle(current, directory=True))
                yield current
            return

        with self._posix_directory(
            directory, unsupported_message="Anchored file creation is unsupported on this platform",
        ) as parent:
            yield parent

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
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        with ExitStack() as staging:
            fd, stage, parent_fd = self._open_atomic_stage(destination, flags, mode, staging)
            published = False
            try:
                try:
                    with os.fdopen(fd, "wb", closefd=False) as stream:
                        stream.write(content)
                    if parent_fd is not None:
                        os.fchmod(fd, mode)
                finally:
                    os.close(fd)
                if parent_fd is None:
                    stage.chmod(mode)
                if self._path(path, allow_missing=True) != destination:
                    raise FileHelperError(f"Destination changed during write: {path}")
                if parent_fd is None:
                    os.replace(stage, destination)
                else:
                    os.replace(stage, destination, src_dir_fd=parent_fd)
                published = True
            finally:
                if not published:
                    self._unlink_atomic_stage(stage, parent_fd)

    def _open_atomic_stage(
        self, destination: Path, flags: int, mode: int, staging: ExitStack,
    ) -> tuple[int, Path, int | None]:
        mode &= 0o600
        extended_parent = None
        for _ in range(10):
            name = f".{secrets.token_hex(8)}.tmp"
            if name == destination.name.rstrip(" .").casefold():
                continue
            stage = (extended_parent or destination.parent) / name
            try:
                return os.open(stage, flags, mode), stage, None
            except FileExistsError:
                continue
            except OSError as exc:
                # The Windows CRT can report an overlong path as ENOENT.
                length_error = exc.errno == errno.ENAMETOOLONG or (
                    os.name == "nt" and exc.errno == errno.ENOENT
                )
                if not length_error or len(name) <= len(destination.name):
                    raise
                if os.name == "nt":
                    if extended_parent is not None or not destination.parent.is_dir():
                        raise
                    parent_info = destination.parent.stat()
                    # Keep file-only ACL inheritance and avoid requiring directory creation rights.
                    extended_parent = _windows_extended_path(destination.parent)
                    # The extended spelling bypasses Win32 name normalization.
                    if not os.path.samestat(parent_info, extended_parent.stat()):
                        raise FileHelperError(
                            f"Extended staging path does not match destination parent: {destination.parent}"
                        )
                    continue
                if not {os.rename, os.unlink} <= os.supports_dir_fd:
                    raise
            break
        else:
            raise FileExistsError(errno.EEXIST, "Could not allocate a staging file", str(destination))

        # A parent-relative sibling keeps direct inheritance and avoids the
        # absolute path limit without shrinking the name to the leaf budget.
        parent = staging.enter_context(self._posix_directory(
            destination.parent, unsupported_message="Directory-relative staging is unsupported",
        ))
        for _ in range(10):
            name = "." + secrets.token_hex(7)[:13]  # POSIX minimum NAME_MAX is 14.
            if name == destination.name.rstrip(" .").casefold():
                continue
            stage = Path(name)
            try:
                return os.open(stage, flags, mode, dir_fd=parent), stage, parent
            except FileExistsError:
                continue
        raise FileExistsError(errno.EEXIST, "Could not allocate a staging file", str(destination))

    @staticmethod
    def _unlink_atomic_stage(stage: Path, parent: int | None) -> None:
        if parent is not None:
            try:
                os.unlink(stage, dir_fd=parent)
            except FileNotFoundError:
                pass
            return
        try:
            stage.unlink(missing_ok=True)
        except PermissionError:
            if os.name != "nt":
                raise
            mode = stat.S_IMODE(stage.stat().st_mode)
            if mode & stat.S_IWRITE:
                raise
            stage.chmod(mode | stat.S_IWRITE)
            try:
                stage.unlink(missing_ok=True)
            except OSError as exc:
                try:
                    stage.chmod(mode)
                except OSError as restore_error:
                    exc.add_note(f"Could not restore atomic stage permissions: {restore_error}")
                raise

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
        with ExitStack() as stack:
            if os.name == "nt":
                parts = destination.relative_to(self._canonical_root).parts
                current = self._canonical_root
                stack.enter_context(_windows_handle(current, directory=True))
                for part in parts[:-1]:
                    current = current / part
                    stack.enter_context(_windows_handle(current, directory=True))
                yield stack.enter_context(_windows_overwrite_fd(destination))
                return

            unsupported = "Scoped text overwrite is unsupported on this platform"
            if not getattr(os, "O_NONBLOCK", 0):
                raise OSError(errno.ENOTSUP, unsupported)
            with self._posix_directory(destination.parent, unsupported_message=unsupported) as parent:
                flags = (
                    os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK
                    | getattr(os, "O_CLOEXEC", 0)
                )
                fd = os.open(destination.name, flags, 0o666, dir_fd=parent)
                try:
                    yield fd
                finally:
                    os.close(fd)

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
    def _deletion_root(self) -> Iterator[int | _WindowsDirectory]:
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
        if isinstance(self._root_anchor, Path):
            reference = self._windows_root_handle
            identity = self._windows_root_id
            if reference is None or identity is None:
                raise FileHelperError("Missing retained Windows root identity")
            with ExitStack() as resources:
                for ancestor in reversed(self._root_anchor.parents):
                    resources.enter_context(_windows_handle(ancestor, directory=True))
                handle = resources.enter_context(
                    _windows_handle(self._root_anchor, directory=True)
                )
                selected = _windows_file_id(handle, kind=identity.kind)
                retained = _windows_file_id(reference, kind=identity.kind)
                if selected != retained:
                    raise FileHelperError(f"Established root changed during deletion: {self.root}")
                yield _WindowsDirectory(self._canonical_root, handle)
        else:
            self._check_deletion_root(self._canonical_root.stat())
            yield self._root_anchor

    @contextmanager
    def _child_deletion_directory(
        self, parent: int | _WindowsDirectory, name: str, *, readable: bool = False
    ) -> Iterator[int | _WindowsDirectory]:
        if isinstance(parent, _WindowsDirectory):
            with _windows_handle(
                Path(name), directory=True, parent=parent.handle
            ) as handle:
                yield _WindowsDirectory(parent.path / name, handle)
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
    def _deletion_directory(
        self, path: Path, *, root: int | _WindowsDirectory
    ) -> Iterator[int | _WindowsDirectory]:
        parts = path.relative_to(self._canonical_root).parts
        if isinstance(root, int):
            with ExitStack() as resources:
                directories = _WalkDirectories(
                    self._canonical_root, root, self._directory_flags(), resources
                )
                yield directories.directory(path)
            return
        with ExitStack() as resources:
            parent = root
            for part in parts:
                parent = resources.enter_context(self._child_deletion_directory(parent, part))
            yield parent

    @staticmethod
    def _windows_entry_mode(handle: int, path: Path) -> int:
        try:
            return _windows_mode(handle)
        except OSError as exc:
            if exc.errno == errno.ELOOP and getattr(exc, "winerror", None) is None:
                raise UnsupportedPathError(f"Unsupported Windows reparse point: {path}") from exc
            raise

    def _deletion_entry_mode(self, path: Path, *, parent: int | _WindowsDirectory) -> int:
        if isinstance(parent, _WindowsDirectory):
            with _windows_entry(parent.handle, path.name) as handle:
                return self._windows_entry_mode(handle, path)
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
        self, path: Path, *, recursive: bool, parent: int | _WindowsDirectory
    ) -> _DeletionEntry:
        if isinstance(parent, int):
            return self._posix_deletion_plan(path, recursive=recursive, parent=parent)
        directory = self._deletion_kind(path, self._deletion_entry_mode(path, parent=parent))
        children: tuple[_DeletionEntry, ...] = ()
        if directory and recursive:
            with self._child_deletion_directory(parent, path.name, readable=True) as child_directory:
                if not isinstance(child_directory, _WindowsDirectory):
                    raise FileHelperError("Expected a native Windows directory")
                names = sorted(_windows_directory_names(child_directory.handle))
                child_plans = []
                for name in names:
                    child_plans.append(
                        self._deletion_plan(path / name, recursive=True, parent=child_directory)
                    )
                children = tuple(child_plans)
        return _DeletionEntry(path, directory, children)

    def _posix_deletion_plan(
        self, path: Path, *, recursive: bool, parent: int
    ) -> _DeletionEntry:
        pending: list[tuple[Path, list[str] | None]] = [(path, None)]
        completed: dict[Path, _DeletionEntry] = {}
        with ExitStack() as resources:
            directories = _DeletionDirectories(
                path.parent, parent, self._directory_flags(), resources
            )
            while pending:
                entry, children = pending.pop()
                if children is not None:
                    completed[entry] = _DeletionEntry(
                        entry, True, tuple(completed.pop(entry / name) for name in children)
                    )
                    continue
                entry_parent = directories.directory(entry.parent)
                directory = self._deletion_kind(
                    entry, self._deletion_entry_mode(entry, parent=entry_parent)
                )
                if not (directory and recursive):
                    completed[entry] = _DeletionEntry(entry, directory)
                    continue
                with self._child_deletion_directory(
                    entry_parent, entry.name, readable=True
                ) as readable:
                    with os.scandir(readable) as entries:
                        names = sorted(child.name for child in entries)
                pending.append((entry, names))
                for name in reversed(names):
                    pending.append((entry / name, None))
        return completed[path]

    def _delete_plan(self, entry: _DeletionEntry, *, parent: int | _WindowsDirectory) -> None:
        if isinstance(parent, int):
            self._posix_delete_plan(entry, parent=parent)
            return
        with _windows_entry(parent.handle, entry.path.name, deleting=True) as handle:
            directory = self._deletion_kind(
                entry.path, self._windows_entry_mode(handle, entry.path)
            )
            if directory != entry.directory:
                raise FileHelperError(f"Destination changed during deletion: {entry.path}")
            if directory and entry.children:
                child_directory = _WindowsDirectory(entry.path, handle)
                for child in entry.children:
                    self._delete_plan(child, parent=child_directory)
            _windows_delete(handle)

    def _posix_delete_plan(self, entry: _DeletionEntry, *, parent: int) -> None:
        pending = [(entry, False)]
        with ExitStack() as resources:
            # Do not reuse preflight handles: parent replacements must be checked
            # afresh before any removal.
            directories = _DeletionDirectories(
                entry.path.parent, parent, self._directory_flags(), resources
            )
            while pending:
                selected, ready = pending.pop()
                selected_parent = directories.directory(selected.path.parent)
                directory = self._deletion_kind(
                    selected.path,
                    self._deletion_entry_mode(selected.path, parent=selected_parent),
                )
                if directory != selected.directory:
                    raise FileHelperError(f"Destination changed during deletion: {selected.path}")
                if directory and selected.children and not ready:
                    pending.append((selected, True))
                    for child in reversed(selected.children):
                        pending.append((child, False))
                    continue
                if directory:
                    os.rmdir(selected.path.name, dir_fd=selected_parent)
                    directories.discard(selected.path)
                else:
                    os.unlink(selected.path.name, dir_fd=selected_parent)

    def delete(self, path: Path | str, *, recursive: bool = False) -> None:
        """Delete an entry; recursive deletion never follows descendant links."""
        with self._deletion_root() as root:
            destination = self._path(path, follow_leaf=False, root_handle=root)
            if destination == self._canonical_root:
                raise FileHelperError(f"Refusing to delete the established root: {self.root}")
            with self._deletion_directory(destination.parent, root=root) as parent:
                plan = self._deletion_plan(destination, recursive=recursive, parent=parent)
                self._delete_plan(plan, parent=parent)
