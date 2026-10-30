"""Scoped filesystem operations; see design/file-helper.md for the contract."""

from dataclasses import dataclass, field
from collections.abc import Callable
import codecs
import errno
import os
from pathlib import Path, PurePath, PureWindowsPath
import stat
import tempfile
from typing import TypeVar


_PathType = TypeVar("_PathType", bound=PurePath)
MutationObserver = Callable[[Path, bool, bool], None]


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


@dataclass(frozen=True)
class FileHelper:
    """Own operations beneath one trusted root with an immutable link policy.

    Relative operation paths are relative to ``root``, not the process cwd.
    The root itself is a trusted alias boundary, resolved once on construction.
    """

    root: Path
    allow_symlinks: bool = False
    _canonical_root: Path = field(init=False, repr=False)

    def __post_init__(self) -> None:
        root = Path(self.root).absolute()
        canonical = root.resolve(strict=True)
        if not canonical.is_dir():
            raise NotADirectoryError(root)
        object.__setattr__(self, "root", root)
        object.__setattr__(self, "_canonical_root", canonical)

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
    def _entry_mode(path: Path) -> int:
        entry = path.lstat()
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
    ) -> Path:
        current = self._canonical_root
        for index, part in enumerate(parts):
            if not current.is_dir():
                if not (allow_missing and not current.exists()):
                    raise NotADirectoryError(current)
            if part == "..":
                if current == self._canonical_root:
                    raise PathEscapeError(f"Symlink target escapes root {self.root}")
                current = current.parent
                continue
            candidate = current / part
            try:
                mode = self._entry_mode(candidate)
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
                target = Path(os.readlink(candidate))
                target_parts = self._parts(target)
                if not target.is_absolute():
                    target_parts = current.relative_to(self._canonical_root).parts + target_parts
                # Resolve the link target strictly, even when creating a new child.
                current = self._walk(target_parts, links=links + (candidate,))
            elif stat.S_ISDIR(mode) or stat.S_ISREG(mode):
                current = candidate
            else:
                raise UnsupportedPathError(f"Unsupported filesystem object: {candidate}")
        return current

    def _path(
        self, path: Path | str, *, allow_missing: bool = False, follow_leaf: bool = True
    ) -> Path:
        original = Path(path)
        parts = self._parts(original)
        if ".." in parts:
            raise PathEscapeError(f"Parent traversal is not an operation path: {original}")
        return self._walk(
            parts, allow_missing=allow_missing, follow_leaf=follow_leaf
        )

    @staticmethod
    def _require_file(path: Path) -> None:
        if not stat.S_ISREG(path.stat().st_mode):
            raise UnsupportedPathError(f"Expected a regular file: {path}")

    def mkdir(
        self, path: Path | str, *, parents: bool = False, exist_ok: bool = False,
        observer: MutationObserver | None = None,
    ) -> None:
        """Create a directory, preflighting the entire requested hierarchy."""
        destination = self._path(path, allow_missing=True)
        if observer is None or destination.exists() or (not parents and not destination.parent.exists()):
            destination.mkdir(parents=parents, exist_ok=exist_ok)
            return
        missing = [destination]
        if parents:
            current = destination.parent
            while not current.exists():
                missing.append(current)
                current = current.parent
        for directory in reversed(missing):
            if self._path(path, allow_missing=True) != destination:
                raise FileHelperError(f"Destination changed during mkdir: {path}")
            observer(directory, True, False)
            directory.mkdir(exist_ok=exist_ok if directory == destination else True)
            observer(directory, False, False)

    def read_bytes(self, path: Path | str, *, size: int | None = None) -> bytes:
        destination = self._path(path)
        self._require_file(destination)
        if size is None:
            return destination.read_bytes()
        with destination.open("rb") as stream:
            return stream.read(size)

    def read_text(self, path: Path | str, *, encoding: str = "utf-8") -> str:
        return self.read_bytes(path).decode(encoding)

    def listdir(self, path: Path | str) -> list[str]:
        """Read directory entry names without resolving or inspecting children."""
        return os.listdir(self._path(path))

    def chmod(
        self, path: Path | str, mode: int, *, observer: MutationObserver | None = None,
    ) -> None:
        """Update a regular file's mode, preserving allowed links."""
        destination = self._path(path)
        self._require_file(destination)
        if observer is not None:
            observer(destination, True, False)
        destination.chmod(mode)
        if observer is not None:
            observer(destination, False, False)

    def stat(
        self, path: Path | str, *, follow_symlinks: bool = True, missing_ok: bool = False
    ) -> os.stat_result | None:
        """Inspect an entry under policy; missing link targets always fail."""
        destination = self._path(path, allow_missing=True, follow_leaf=follow_symlinks)
        try:
            entry = destination.stat(follow_symlinks=follow_symlinks)
        except FileNotFoundError:
            if missing_ok:
                return None
            raise
        self._entry_mode(destination)
        return entry

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
        fd = os.open(destination, flags, mode)
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)

    def create_text(
        self, path: Path | str, content: str, *, encoding: str = "utf-8", mode: int = 0o644
    ) -> None:
        self.create_bytes(path, content.encode(encoding), mode=mode)

    def write_bytes(
        self, path: Path | str, content: bytes, *, mode: int = 0o644,
        observer: MutationObserver | None = None,
    ) -> None:
        """Atomically create/replace a file, preserving any allowed leaf link."""
        destination = self._path(path, allow_missing=True)
        if destination.exists():
            self._require_file(destination)
        if observer is not None:
            observer(destination, True, False)
        fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
        temporary_path = Path(temporary)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(content)
            temporary_path.chmod(mode)
            if self._path(path, allow_missing=True) != destination:
                raise FileHelperError(f"Destination changed during write: {path}")
            os.replace(temporary_path, destination)
            if observer is not None:
                observer(destination, False, False)
        finally:
            temporary_path.unlink(missing_ok=True)

    def write_text(
        self, path: Path | str, content: str, *, encoding: str = "utf-8", mode: int = 0o644,
        observer: MutationObserver | None = None,
    ) -> None:
        self.write_bytes(path, content.encode(encoding), mode=mode, observer=observer)

    def overwrite_text(
        self, path: Path | str, content: str, *, encoding: str = "utf-8"
    ) -> None:
        """Non-atomic text upsert preserving existing inode and native text I/O."""
        destination = self._path(path, allow_missing=True)
        if destination.exists():
            self._require_file(destination)
        codecs.lookup(encoding)
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        flags |= getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(destination, flags, 0o666)
        with os.fdopen(fd, "w", encoding=encoding) as stream:
            stream.write(content)

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

    def _deletion_plan(self, path: Path, *, recursive: bool) -> list[tuple[Path, bool]]:
        mode = self._entry_mode(path)
        if stat.S_ISLNK(mode):
            if not self.allow_symlinks:
                raise SymlinkDeniedError(f"Refusing to delete symlink: {path}")
            return [(path, False)]
        if stat.S_ISREG(mode):
            return [(path, False)]
        if not stat.S_ISDIR(mode):
            raise UnsupportedPathError(f"Unsupported filesystem object: {path}")
        plan: list[tuple[Path, bool]] = []
        if recursive:
            with os.scandir(path) as entries:
                children = sorted((Path(entry.path) for entry in entries))
            for child in children:
                plan.extend(self._deletion_plan(child, recursive=True))
        plan.append((path, True))
        return plan

    def delete(
        self, path: Path | str, *, recursive: bool = False,
        observer: MutationObserver | None = None,
    ) -> None:
        """Delete an entry; recursive deletion never follows descendant links."""
        destination = self._path(path, follow_leaf=False)
        if destination == self._canonical_root:
            raise FileHelperError(f"Refusing to delete the established root: {self.root}")
        plan = self._deletion_plan(destination, recursive=recursive)
        for entry, directory in plan:
            # Recheck accessed parents/leaf before each mutation, not just preflight.
            checked = self._path(entry, follow_leaf=False)
            if checked != entry:
                raise FileHelperError(f"Destination changed during deletion: {entry}")
            if observer is not None:
                observer(entry, True, True)
            if directory:
                entry.rmdir()
            else:
                entry.unlink()
            if observer is not None:
                observer(entry, False, False)
