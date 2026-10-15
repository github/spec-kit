"""Bounded capture of an integration CLI's stdout and stderr.

``subprocess.run(capture_output=True)`` buffers everything a process writes,
decodes it with the locale encoding, and loses the output on a timeout. Captured
workflow dispatch needs the opposite on all three: a per-stream byte cap, a
fixed UTF-8 decoding, and whatever was read before a timeout or interruption.
"""

from __future__ import annotations

import codecs
import os
import signal
import subprocess
import threading
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

DEFAULT_CAPTURE_MAX_BYTES = 1024 * 1024
UNLIMITED_CAPTURE = -1

_READ_CHUNK_BYTES = 64 * 1024
# After a kill, a descendant that inherited the pipes can keep them open; wait
# this long for end-of-file before returning what has been read so far.
_DRAIN_GRACE_SECONDS = 2.0


def capture_max_bytes_is_valid(value: Any) -> bool:
    """Return whether *value* is a positive int or ``-1`` (unlimited).

    bool is a subclass of int, but ``capture_max_bytes: true`` is a config
    error rather than a one-byte limit, so it is rejected explicitly.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    return value > 0 or value == UNLIMITED_CAPTURE


@dataclass(frozen=True)
class CapturedProcess:
    """Outcome of one captured process.

    ``stdout_truncated``/``stderr_truncated`` report size-based truncation
    only. Output can also be incomplete because the process was stopped;
    ``timed_out`` and ``interrupted`` report that separately.
    """

    exit_code: int
    stdout: str
    stderr: str
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    timed_out: bool = False
    interrupted: bool = False

    def as_dispatch_result(self) -> dict[str, Any]:
        """Return the ``dispatch_command`` result dict for this process."""
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "stdout_truncated": self.stdout_truncated,
            "stderr_truncated": self.stderr_truncated,
            "timed_out": self.timed_out,
            "interrupted": self.interrupted,
        }


class _Sink:
    """Retain at most *limit* bytes of a stream; count the rest as truncated."""

    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._data = bytearray()
        self._truncated = False
        self._lock = threading.Lock()

    def feed(self, chunk: bytes) -> None:
        with self._lock:
            if self._limit != UNLIMITED_CAPTURE:
                room = self._limit - len(self._data)
                if len(chunk) > room:
                    self._truncated = True
                    chunk = chunk[:room]
            self._data += chunk

    def snapshot(self) -> tuple[bytes, bool]:
        with self._lock:
            return bytes(self._data), self._truncated


def _drain(pipe: Any, sink: _Sink) -> None:
    """Read *pipe* to end-of-file, including past the sink's limit.

    Reading continues after the cap so the process never blocks writing to a
    full pipe; the sink discards what it does not retain.
    """
    try:
        while chunk := pipe.read1(_READ_CHUNK_BYTES):
            sink.feed(chunk)
    except (OSError, ValueError):
        pass
    finally:
        try:
            pipe.close()
        except OSError:
            pass


def _join(readers: Sequence[threading.Thread], deadline: float | None) -> bool:
    """Join *readers* until *deadline*; return whether all reached end-of-file."""
    for reader in readers:
        if deadline is None:
            reader.join()
        else:
            reader.join(max(0.0, deadline - time.monotonic()))
    return not any(reader.is_alive() for reader in readers)


# Windows process creation flag; not exported by ``subprocess``.
_CREATE_SUSPENDED = 0x00000004


class _ProcessTree:
    """Run a process so that it and its process group or job can be killed.

    Killing only the CLI would leave the tools it started running, still
    changing the project and holding the pipes open after the step has
    failed. On POSIX the CLI leads a new session and its process group is
    killed; on Windows it runs inside a job object that is terminated. The
    boundary is that group or job, not every descendant: a process that
    moves to another session or process group (POSIX) or breaks away from
    the job (Windows), as a daemonising helper can, survives the kill.
    A separate session also keeps the terminal's Ctrl+C from reaching the CLI
    directly: the interrupt is handled here, by killing the group or job.
    """

    def __init__(self, args: Sequence[str], cwd: str | None) -> None:
        isolation: dict[str, Any] = (
            {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | _CREATE_SUSPENDED}
            if os.name == "nt"
            else {"start_new_session": True}
        )
        self.proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            **isolation,
        )
        self._job: Any = None
        if os.name == "nt":
            try:
                self._job = _start_in_job(self.proc)
            except BaseException:
                # Fail closed: a CLI whose descendants could not be killed
                # never runs.
                self.proc.kill()
                self.proc.wait()
                for pipe in (self.proc.stdout, self.proc.stderr):
                    if pipe is not None:
                        pipe.close()
                raise

        self._lock = threading.Lock()
        # Set when another thread kills the tree through interrupt().
        self.interrupted = False

    def _send_kill(self) -> None:
        if self._job is not None:
            _windows().TerminateJobObject(self._job, 1)
        elif os.name != "nt":
            try:
                os.killpg(self.proc.pid, signal.SIGKILL)
            except OSError:
                pass
        try:
            self.proc.kill()
        except OSError:
            pass

    def interrupt(self) -> None:
        """Kill the process group or job from another thread.

        The thread running the capture sees the process exit and reports
        the capture as interrupted.
        """
        with self._lock:
            self.interrupted = True
            self._send_kill()

    def kill(self) -> None:
        """Kill the process group or job, then reap the process."""
        with self._lock:
            self._send_kill()
        self.proc.wait()

    def close(self) -> None:
        with self._lock:
            if self._job is not None:
                _windows().CloseHandle(self._job)
                self._job = None


# Captures running in any thread, so an interrupt of the main thread can
# reach the ones running in worker threads; see cancel_captures().
_active_lock = threading.Lock()
_active: set[_ProcessTree] = set()
_cancelling = 0


def _register(tree: _ProcessTree) -> None:
    with _active_lock:
        _active.add(tree)
        cancelling = _cancelling > 0
    if cancelling:
        tree.interrupt()


def _unregister(tree: _ProcessTree) -> None:
    with _active_lock:
        _active.discard(tree)


@contextmanager
def cancel_captures() -> Iterator[None]:
    """Kill every running capture, and any that starts, until the block ends.

    Ctrl+C raises ``KeyboardInterrupt`` in the main thread only, and a
    captured CLI runs in its own session or job, so it does not receive the
    terminal's Ctrl+C either. When the main thread is interrupted while
    worker threads run captures, wait for those workers inside this block:
    their captures are killed and report ``interrupted``, and a capture that
    starts meanwhile is killed as soon as it is registered.
    """
    global _cancelling
    with _active_lock:
        _cancelling += 1
        trees = list(_active)
    try:
        for tree in trees:
            tree.interrupt()
        yield
    finally:
        with _active_lock:
            _cancelling -= 1


@contextmanager
def _deferred_interrupt() -> Iterator[list[int]]:
    """Record Ctrl+C instead of raising it until cleanup is in place.

    A ``KeyboardInterrupt`` raised after ``Popen`` returned but before the
    code that kills the process on interruption would leave the CLI running
    in its own session (POSIX) or suspended outside its job (Windows).
    Within this block a SIGINT is appended to the yielded list; the caller
    treats a non-empty list as an interruption. Only the main thread
    receives SIGINT, and only Python's default handler is replaced, so a
    custom or ignoring handler keeps its behaviour.
    """
    pending: list[int] = []
    if (
        threading.current_thread() is not threading.main_thread()
        or signal.getsignal(signal.SIGINT) is not signal.default_int_handler
    ):
        yield pending
        return
    previous = signal.signal(
        signal.SIGINT, lambda signum, frame: pending.append(signum)
    )
    try:
        yield pending
    finally:
        signal.signal(signal.SIGINT, previous)


_kernel32: Any = None


def _windows() -> Any:
    """Return kernel32 with the signatures the job-object helpers use."""
    global _kernel32
    if _kernel32 is None:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ((wintypes.LPVOID, wintypes.LPCWSTR), wintypes.HANDLE),
            "AssignProcessToJobObject": (
                (wintypes.HANDLE, wintypes.HANDLE),
                wintypes.BOOL,
            ),
            "TerminateJobObject": ((wintypes.HANDLE, wintypes.UINT), wintypes.BOOL),
            "CreateToolhelp32Snapshot": (
                (wintypes.DWORD, wintypes.DWORD),
                wintypes.HANDLE,
            ),
            "Thread32First": ((wintypes.HANDLE, ctypes.c_void_p), wintypes.BOOL),
            "Thread32Next": ((wintypes.HANDLE, ctypes.c_void_p), wintypes.BOOL),
            "OpenThread": (
                (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD),
                wintypes.HANDLE,
            ),
            "ResumeThread": ((wintypes.HANDLE,), wintypes.DWORD),
            "CloseHandle": ((wintypes.HANDLE,), wintypes.BOOL),
        }
        for name, (argtypes, restype) in signatures.items():
            function = getattr(kernel32, name)
            function.argtypes = argtypes
            function.restype = restype
        _kernel32 = kernel32
    return _kernel32


def _start_in_job(proc: subprocess.Popen) -> Any:
    """Put the suspended *proc* in a new job object, then resume it.

    *proc* was created suspended, so it cannot start a descendant before it
    is in the job; every process it starts afterwards joins the job too.
    Returns the job handle. Raises OSError if any step fails.
    """
    import ctypes

    kernel32 = _windows()
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not kernel32.AssignProcessToJobObject(job, int(proc._handle)):
            raise ctypes.WinError(ctypes.get_last_error())
        _resume_threads(proc.pid)
    except BaseException:
        # The CLI may already be running if the failure or interruption came
        # after a thread was resumed: kill everything in the job before the
        # handle goes, because closing it does not.
        kernel32.TerminateJobObject(job, 1)
        kernel32.CloseHandle(job)
        raise
    return job


def _resume_threads(pid: int) -> None:
    """Resume the threads of the suspended process *pid*.

    ``subprocess`` closes the main thread's handle, so the thread is found
    through a thread snapshot.
    """
    import ctypes
    from ctypes import wintypes

    class THREADENTRY32(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ThreadID", wintypes.DWORD),
            ("th32OwnerProcessID", wintypes.DWORD),
            ("tpBasePri", wintypes.LONG),
            ("tpDeltaPri", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
        ]

    th32cs_snapthread = 0x00000004
    thread_suspend_resume = 0x0002
    resume_failed = 0xFFFFFFFF
    invalid_handle = wintypes.HANDLE(-1).value

    kernel32 = _windows()
    snapshot = kernel32.CreateToolhelp32Snapshot(th32cs_snapthread, 0)
    if not snapshot or snapshot == invalid_handle:
        raise ctypes.WinError(ctypes.get_last_error())
    resumed = 0
    try:
        entry = THREADENTRY32()
        entry.dwSize = ctypes.sizeof(THREADENTRY32)
        more = kernel32.Thread32First(snapshot, ctypes.byref(entry))
        while more:
            if entry.th32OwnerProcessID == pid:
                thread = kernel32.OpenThread(
                    thread_suspend_resume, False, entry.th32ThreadID
                )
                if not thread:
                    raise ctypes.WinError(ctypes.get_last_error())
                try:
                    if kernel32.ResumeThread(thread) == resume_failed:
                        raise ctypes.WinError(ctypes.get_last_error())
                finally:
                    kernel32.CloseHandle(thread)
                resumed += 1
            more = kernel32.Thread32Next(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    if not resumed:
        raise OSError(f"Could not find the threads of process {pid} to resume.")


def _decode(data: bytes, *, complete: bool) -> str:
    """Decode captured bytes as UTF-8, replacing invalid sequences with U+FFFD.

    When the capture is not *complete* (cut at the byte limit, or the process
    was stopped), a trailing partial multibyte sequence is dropped rather than
    replaced, so a cut never invents a replacement character. Line endings are
    normalised to ``\\n`` as ``subprocess`` text mode does.
    """
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    text = decoder.decode(data, final=complete)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def run_captured(
    args: Sequence[str],
    *,
    cwd: str | None = None,
    timeout: float | None = None,
    max_bytes: int = DEFAULT_CAPTURE_MAX_BYTES,
) -> CapturedProcess:
    """Run *args* and capture stdout and stderr, each capped at *max_bytes*.

    *max_bytes* counts raw bytes before decoding; ``-1`` disables the cap. A
    timeout or ``KeyboardInterrupt`` kills the process and is reported on the
    result (exit code ``-1`` or ``130``) together with the output read so far,
    instead of being raised, after the process's group (POSIX) or job
    (Windows) is killed; a descendant that left it is not killed. ``OSError``
    from starting the process propagates.
    """
    if not capture_max_bytes_is_valid(max_bytes):
        raise ValueError(
            f"max_bytes must be a positive integer or -1, got {max_bytes!r}."
        )

    tree: _ProcessTree | None = None
    sinks = (_Sink(max_bytes), _Sink(max_bytes))
    readers: list[threading.Thread] = []
    deadline = None if timeout is None else time.monotonic() + timeout
    timed_out = interrupted = False
    try:
        try:
            with _deferred_interrupt() as pending_interrupt:
                tree = _ProcessTree(args, cwd)
                _register(tree)
                for pipe, sink in zip((tree.proc.stdout, tree.proc.stderr), sinks):
                    reader = threading.Thread(
                        target=_drain, args=(pipe, sink), daemon=True
                    )
                    reader.start()
                    readers.append(reader)
            # From here a Ctrl+C raises KeyboardInterrupt inside this try.
            if pending_interrupt:
                raise KeyboardInterrupt
            try:
                tree.proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
            else:
                # The process can exit while a descendant still holds the
                # pipes open; the same deadline bounds the wait for
                # end-of-file.
                timed_out = not _join(readers, deadline)
        except KeyboardInterrupt:
            interrupted = True
            if tree is None:
                # Setup was interrupted, and the constructor has already
                # killed the process it started.
                return CapturedProcess(
                    exit_code=130, stdout="", stderr="", interrupted=True
                )
        except BaseException:
            if tree is not None:
                tree.kill()
            raise
        if tree.interrupted:
            # Killed through cancel_captures() while this thread waited.
            interrupted, timed_out = True, False

        if timed_out or interrupted:
            # Killing the group or job closes the write ends of the pipes its
            # processes hold, so the readers reach end-of-file. Only a
            # descendant that left the group or job could keep them open; the
            # grace period bounds that wait.
            tree.kill()
            _join(readers, time.monotonic() + _DRAIN_GRACE_SECONDS)
            # A pipe whose reader never started is closed here instead.
            for pipe in (tree.proc.stdout, tree.proc.stderr)[len(readers) :]:
                pipe.close()
    finally:
        if tree is not None:
            _unregister(tree)
            tree.close()

    (stdout, stdout_truncated), (stderr, stderr_truncated) = (
        sink.snapshot() for sink in sinks
    )
    stopped = timed_out or interrupted
    if interrupted:
        exit_code = 130
    elif timed_out:
        exit_code = -1
    else:
        exit_code = tree.proc.returncode
    return CapturedProcess(
        exit_code=exit_code,
        stdout=_decode(stdout, complete=not (stopped or stdout_truncated)),
        stderr=_decode(stderr, complete=not (stopped or stderr_truncated)),
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
        timed_out=timed_out,
        interrupted=interrupted,
    )
