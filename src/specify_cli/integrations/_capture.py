"""Bounded capture of an integration CLI's stdout and stderr.

``subprocess.run(capture_output=True)`` buffers everything a process writes,
decodes it with the locale encoding, and loses the output on a timeout. Captured
workflow dispatch needs the opposite on all three: a per-stream byte cap, a
fixed UTF-8 decoding, and whatever was read before a timeout or interruption.
"""

from __future__ import annotations

import codecs
import subprocess
import threading
import time
from collections.abc import Sequence
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
    instead of being raised. ``OSError`` from starting the process propagates.
    """
    if not capture_max_bytes_is_valid(max_bytes):
        raise ValueError(
            f"max_bytes must be a positive integer or -1, got {max_bytes!r}."
        )

    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
    )
    sinks = (_Sink(max_bytes), _Sink(max_bytes))
    readers = [
        threading.Thread(target=_drain, args=(pipe, sink), daemon=True)
        for pipe, sink in zip((proc.stdout, proc.stderr), sinks)
    ]
    for reader in readers:
        reader.start()

    deadline = None if timeout is None else time.monotonic() + timeout
    timed_out = interrupted = False
    try:
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        else:
            # The process can exit while a descendant still holds the pipes
            # open; the same deadline bounds the wait for end-of-file.
            timed_out = not _join(readers, deadline)
    except KeyboardInterrupt:
        interrupted = True

    if timed_out or interrupted:
        proc.kill()
        proc.wait()
        _join(readers, time.monotonic() + _DRAIN_GRACE_SECONDS)

    (stdout, stdout_truncated), (stderr, stderr_truncated) = (
        sink.snapshot() for sink in sinks
    )
    stopped = timed_out or interrupted
    if interrupted:
        exit_code = 130
    elif timed_out:
        exit_code = -1
    else:
        exit_code = proc.returncode
    return CapturedProcess(
        exit_code=exit_code,
        stdout=_decode(stdout, complete=not (stopped or stdout_truncated)),
        stderr=_decode(stderr, complete=not (stopped or stderr_truncated)),
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
        timed_out=timed_out,
        interrupted=interrupted,
    )
