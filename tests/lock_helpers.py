"""Test helpers for observing inter-process lock contention."""

from __future__ import annotations

import os
import threading
import time


def watch_lock_attempt(monkeypatch, thread_name: str) -> threading.Event:
    """Return an event set once ``thread_name`` tries to take a file lock.

    Patches the platform lock primitive (``fcntl.flock`` on POSIX,
    ``msvcrt.locking`` on Windows) so a test can deterministically wait until
    a thread is blocked on a lock held by another thread.
    """
    attempted = threading.Event()
    if os.name == "nt":
        import msvcrt

        real_locking = msvcrt.locking

        def _locking(fd, operation, nbytes):
            observed = (
                threading.current_thread().name == thread_name
                and operation == msvcrt.LK_NBLCK
            )
            try:
                return real_locking(fd, operation, nbytes)
            finally:
                # Windows polls with non-blocking attempts; the first attempt
                # (failed or not) confirms the thread reached the lock.
                if observed:
                    attempted.set()

        monkeypatch.setattr(msvcrt, "locking", _locking)
    else:
        import fcntl

        real_flock = fcntl.flock

        def _flock(fd, operation):
            if (
                threading.current_thread().name == thread_name
                and operation == fcntl.LOCK_EX
            ):
                attempted.set()
            return real_flock(fd, operation)

        monkeypatch.setattr(fcntl, "flock", _flock)
    return attempted


def wait_until_blocked_or_done(
    attempted: threading.Event, done: threading.Event, timeout: float = 10
) -> None:
    """Wait until a thread has reached the lock or has already finished.

    Returning on ``done`` lets a test assert on final state (and fail with a
    meaningful message) when the code under test does not take the lock.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if attempted.is_set() or done.is_set():
            return
        time.sleep(0.01)
    raise AssertionError("thread neither attempted the lock nor finished")
