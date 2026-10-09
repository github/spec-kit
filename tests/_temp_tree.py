"""Windows-safe removal of a test fixture tree.

Windows refuses to remove a directory that is the process CWD, and a handle held
by another process (Defender/indexer on a CI runner, releasing asynchronously)
makes ``shutil.rmtree`` fail with ``WinError 32`` even though the test removed
everything it created. POSIX has no such rule, so the failure only ever appears
on Windows.

Deliberately implemented with ``os``/``shutil`` only: a suite may patch
``os.name`` to simulate Windows, and instantiating ``pathlib.Path`` under a
patched ``os.name`` raises ``NotImplementedError`` on this platform.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time

#: Attempts used to absorb a handle that Windows has not released yet.
_ATTEMPTS = 6


def remove_fixture_tree(tmpdir: str | os.PathLike[str]) -> None:
    """Remove *tmpdir*, tolerating Windows directory-handle semantics.

    The process is moved out of the tree first (a Windows CWD cannot be
    removed), then removal is retried briefly because Windows releases handles
    asynchronously. The postcondition is verified after every attempt, and a tree
    that still exists at the end raises, so a genuinely stuck tree is reported
    instead of being silently accepted.
    """
    # ``realpath`` on both sides so a symlinked temp root (macOS ``/var`` →
    # ``/private/var``) does not defeat the containment check.
    target = os.path.realpath(os.fspath(tmpdir))
    try:
        cwd: str | None = os.path.realpath(os.getcwd())
    except OSError:
        # The CWD was already removed under us (POSIX allows that); restore a
        # usable CWD before attempting any further removal.
        cwd = None
    if cwd is None or cwd == target or cwd.startswith(target + os.sep):
        os.chdir(tempfile.gettempdir())

    last_error: OSError | None = None
    for attempt in range(_ATTEMPTS):
        try:
            shutil.rmtree(target)
        except FileNotFoundError as exc:
            # A descendant can vanish mid-walk (Python 3.11 deletion races), so
            # this is not proof that the root is gone: fall through to the
            # postcondition check below instead of returning early.
            last_error = exc
        except OSError as exc:  # PermissionError (WinError 32) on Windows
            last_error = exc
        # Trust the postcondition, not the call: a removal that leaves the tree
        # in place must not be treated as success.
        if not os.path.exists(target):
            return
        time.sleep(0.05 * (attempt + 1))

    if not os.path.exists(target):
        return
    if last_error is None:  # pragma: no cover - defensive
        raise OSError(f"could not remove fixture tree {target}")
    raise last_error
