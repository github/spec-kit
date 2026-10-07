"""Observe integration-owned writes only while a lifecycle transaction is active."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
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
