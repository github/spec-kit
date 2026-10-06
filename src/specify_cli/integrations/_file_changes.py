"""Observe integration-owned writes only while a lifecycle transaction is active."""

from __future__ import annotations

from collections.abc import Callable
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
