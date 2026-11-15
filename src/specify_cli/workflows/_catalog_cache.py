"""Confined filesystem I/O shared by workflow and step catalog caches."""

from __future__ import annotations

import errno
import json
import os
import stat
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from specify_cli._file_handles import _windows_handle


@contextmanager
def _cache_directory(
    root: Path, directory: Path, *, create: bool
) -> Iterator[int | Path]:
    relative = directory.relative_to(root)
    if ".." in relative.parts:
        raise OSError(errno.EINVAL, "Catalog cache escapes project root")
    root = root.resolve()
    if os.name == "nt":
        with ExitStack() as stack:
            current = root
            stack.enter_context(_windows_handle(current, directory=True))
            for part in relative.parts:
                current = current / part
                try:
                    stack.enter_context(_windows_handle(current, directory=True))
                except FileNotFoundError:
                    if not create:
                        raise
                    try:
                        current.mkdir()
                    except FileExistsError:
                        pass
                    stack.enter_context(_windows_handle(current, directory=True))
            yield current
        return

    if not (
        getattr(os, "O_NOFOLLOW", 0)
        and getattr(os, "O_DIRECTORY", 0)
        and {os.open, os.mkdir, os.rename, os.unlink} <= os.supports_dir_fd
    ):
        raise OSError(
            errno.ENOTSUP, "Safe catalog cache I/O is unsupported on this platform"
        )
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    parent = os.open(root, flags)
    try:
        for part in relative.parts:
            try:
                child = os.open(part, flags, dir_fd=parent)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(part, dir_fd=parent)
                except FileExistsError:
                    pass
                child = os.open(part, flags, dir_fd=parent)
            os.close(parent)
            parent = child
        yield parent
    finally:
        os.close(parent)


def read_cache_json(
    root: Path,
    path: Path,
    *,
    object_pairs_hook: Callable[[list[tuple[str, Any]]], dict[str, Any]] | None = None,
) -> Any:
    """Read a regular cache leaf without following links or swapped ancestors."""
    with _cache_directory(root, path.parent, create=False) as directory_fd:
        if isinstance(directory_fd, Path):
            path = directory_fd / path.name
            with (
                _windows_handle(path, directory=False),
                open(path, encoding="utf-8") as stream,
            ):
                return json.load(stream, object_pairs_hook=object_pairs_hook)
        flags = (
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
        )
        fd = os.open(path.name, flags, dir_fd=directory_fd)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise OSError(
                    errno.EINVAL, "Catalog cache leaf is not a regular file", str(path)
                )
            stream = os.fdopen(fd, encoding="utf-8")
        except BaseException:
            os.close(fd)
            raise
        with stream:
            return json.load(stream, object_pairs_hook=object_pairs_hook)


def write_cache_json(
    root: Path, path: Path, payload: dict[str, Any], *, indent: int | None = None
) -> None:
    """Atomically replace a cache leaf, never truncating its previous inode."""
    content = json.dumps(payload, indent=indent)
    with _cache_directory(root, path.parent, create=True) as directory:
        directory_fd = None if isinstance(directory, Path) else directory
        temporary = f".{path.name}.{uuid4().hex}.tmp"
        staged = directory / temporary if isinstance(directory, Path) else temporary
        destination = (
            directory / path.name if isinstance(directory, Path) else path.name
        )
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(staged, flags, 0o600, dir_fd=directory_fd)
        try:
            try:
                stream = os.fdopen(fd, "w", encoding="utf-8")
            except BaseException:
                os.close(fd)
                raise
            with stream:
                stream.write(content)
            # replace operates on directory entries, not the destination's
            # referent, even if a symlink is installed just before this call.
            os.replace(
                staged, destination, src_dir_fd=directory_fd, dst_dir_fd=directory_fd
            )
        finally:
            try:
                os.unlink(staged, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
