"""Observe integration-owned writes only while a lifecycle transaction is active."""

from __future__ import annotations

import errno
import os
import stat
from collections.abc import Callable
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from pathlib import Path

file_change_observer: ContextVar[Callable[[Path, bool, bool], None] | None] = ContextVar(
    "integration_file_change_observer", default=None
)


def before_file_change(path: Path, *, removal: bool = False) -> None:
    observer = file_change_observer.get()
    if observer is not None:
        observer(path, True, removal)


def after_file_change(path: Path) -> None:
    observer = file_change_observer.get()
    if observer is not None:
        observer(path, False, False)


@contextmanager
def changing_file(path: Path, *, removal: bool = False):
    """Journal a host mutation without claiming the file for uninstall."""
    before_file_change(path, removal=removal)
    yield
    after_file_change(path)


def write_text(path: Path, content: str, *, encoding: str = "utf-8", errors: str | None = None) -> int:
    with changing_file(path):
        return path.write_text(content, encoding=encoding, errors=errors)


def write_bytes(path: Path, content: bytes) -> int:
    with changing_file(path):
        return path.write_bytes(content)


def unlink(path: Path, *, missing_ok: bool = False) -> None:
    with changing_file(path, removal=True):
        path.unlink(missing_ok=missing_ok)


def unlink_in_directory(path: Path, *, root: Path) -> None:
    """Remove a generated file and its empty parent beneath a trusted root."""
    directory = path.absolute().parent
    root = root.absolute()
    try:
        relative = directory.relative_to(root)
    except ValueError:
        return
    if not relative.parts or ".." in relative.parts:
        return
    if (
        getattr(os, "O_DIRECTORY", 0)
        and getattr(os, "O_NOFOLLOW", 0)
        and {os.open, os.unlink, os.rmdir, os.stat} <= os.supports_dir_fd
        and os.listdir in os.supports_fd
    ):
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        with ExitStack() as stack:
            try:
                parent_fd = os.open(root, flags & ~os.O_NOFOLLOW)
                stack.callback(os.close, parent_fd)
                for part in relative.parts[:-1]:
                    parent_fd = os.open(part, flags, dir_fd=parent_fd)
                    stack.callback(os.close, parent_fd)
                directory_fd = os.open(directory.name, flags, dir_fd=parent_fd)
                stack.callback(os.close, directory_fd)
            except OSError as exc:
                if exc.errno not in (errno.ENOENT, errno.ELOOP, errno.ENOTDIR):
                    raise
                return
            with changing_file(path, removal=True):
                try:
                    os.unlink(path.name, dir_fd=directory_fd)
                except FileNotFoundError:
                    pass

            def same_directory() -> bool:
                return os.path.samestat(
                    os.fstat(directory_fd),
                    os.stat(directory.name, dir_fd=parent_fd, follow_symlinks=False),
                )

            try:
                empty = not os.listdir(directory_fd) and same_directory()
            except (FileNotFoundError, NotADirectoryError):
                return
            if empty:
                before_file_change(path.parent, removal=True)
                try:
                    if not same_directory():
                        return
                    os.rmdir(directory.name, dir_fd=parent_fd)
                except OSError as exc:
                    if exc.errno not in (errno.ENOTEMPTY, errno.EEXIST, errno.ENOENT, errno.ENOTDIR):
                        raise
                    return
                after_file_change(path.parent)
        return

    # Without dir_fd (notably Windows), re-check before each path-based
    # deletion. This narrows, but cannot eliminate, concurrent swap races.
    def safe_directory() -> os.stat_result | None:
        parent = root
        for part in relative.parts:
            parent = parent / part
            try:
                info = parent.lstat()
            except OSError as exc:
                if exc.errno not in (errno.ENOENT, errno.ELOOP, errno.ENOTDIR):
                    raise
                return None
            if not stat.S_ISDIR(info.st_mode) or (
                getattr(info, "st_file_attributes", 0)
                & stat.FILE_ATTRIBUTE_REPARSE_POINT
            ):
                return None
        return info

    original = safe_directory()
    if original is None:
        return
    with changing_file(path, removal=True):
        if safe_directory() is None:
            return
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    try:
        empty = not any(directory.iterdir())
    except OSError as exc:
        if exc.errno not in (errno.ENOENT, errno.ELOOP, errno.ENOTDIR):
            raise
        return
    if empty:
        before_file_change(path.parent, removal=True)
        current = safe_directory()
        if current is None or not os.path.samestat(original, current):
            return
        try:
            directory.rmdir()
        except OSError as exc:
            if exc.errno not in (errno.ENOTEMPTY, errno.EEXIST, errno.ENOENT, errno.ENOTDIR):
                raise
            return
        after_file_change(path.parent)
