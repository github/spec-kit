"""Observe integration-owned writes only while a lifecycle transaction is active."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

file_change_observer: ContextVar[Callable[[Path, bool, bool], None] | None] = ContextVar(
    "integration_file_change_observer", default=None
)
directory_change_observer: ContextVar[Callable[[Path, bool, bool], None] | None] = ContextVar(
    "integration_directory_change_observer", default=None
)


def before_file_change(path: Path, *, removal: bool = False) -> None:
    observer = file_change_observer.get()
    if observer is not None:
        observer(path, True, removal)


def after_file_change(path: Path) -> None:
    observer = file_change_observer.get()
    if observer is not None:
        observer(path, False, False)

def observe_file_change(path: Path, before: bool, removal: bool = False) -> None:
    """Forward a scoped helper's actual mutation entry to the lifecycle journal."""
    if before:
        before_file_change(path, removal=removal)
    else:
        after_file_change(path)

def observe_directory_change(path: Path, before: bool, removal: bool = False) -> None:
    """Observe newly created directories without claiming their contents."""
    observer = directory_change_observer.get()
    if observer is not None:
        observer(path, before, removal)


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
