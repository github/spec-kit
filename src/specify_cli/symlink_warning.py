"""Advance notice at existing symlink recognition sites, without changing policy."""

from __future__ import annotations

import stat
import warnings
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path


_POLICY_NOTICE = (
    "Symlinks are not specifically supported by Spec Kit. Special symlink "
    "handling is deprecated. Future versions will assume Spec Kit can "
    "operate on project paths without taking special care of symlinks or "
    "their targets. If you use symlinks, you are responsible for the outcome."
)
_defer_when: ContextVar[Callable[[], bool] | None] = ContextVar("symlink_defer_when", default=None)
_pending: ContextVar[bool] = ContextVar("symlink_warning_pending", default=False)


class SymlinkDeprecationWarning(FutureWarning):
    """Symlink-specific handling is being deprecated."""


def _emit_warning() -> None:
    """Use one warning location so default filtering avoids repeated notices."""
    warnings.warn(
        _POLICY_NOTICE,
        SymlinkDeprecationWarning,
        stacklevel=1,
    )


def warn_symlink() -> None:
    """Report an encounter, respecting an adapter's structured-error boundary."""
    defer = _defer_when.get()
    if defer is not None and defer():
        _pending.set(True)
    else:
        _emit_warning()


@contextmanager
def defer_symlink_warnings(when: Callable[[], bool]) -> Iterator[None]:
    """Let an adapter fold a notice into an error, or emit it on completion."""
    defer_token = _defer_when.set(when)
    pending_token = _pending.set(False)
    try:
        yield
    finally:
        pending = _pending.get()
        _pending.reset(pending_token)
        _defer_when.reset(defer_token)
        if pending:
            _emit_warning()


def symlink_error_message(message: str) -> str:
    """Consume a deferred notice without changing a JSON error's shape."""
    if _pending.get():
        _pending.set(False)
        return f"{message}\nSymlinkDeprecationWarning: {_POLICY_NOTICE}"
    return message


def path_is_symlink(path: Path) -> bool:
    """Preserve the existing path probe and warn only on a positive result."""
    result = path.is_symlink()
    if result:
        warn_symlink()
    return result


def mode_is_symlink(mode: int) -> bool:
    """Recognize a link using metadata already obtained by the caller."""
    result = stat.S_ISLNK(mode)
    if result:
        warn_symlink()
    return result
