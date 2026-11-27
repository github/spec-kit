"""RunState._atomic_write_json tolerates a transient Windows sharing violation."""

import errno
import json
import os
import time

import pytest

from specify_cli.workflows import engine
from specify_cli.workflows.engine import RunState

WINDOWS_DELAYS = (0.1, 0.2, 0.4, 0.8)


@pytest.fixture
def windows_retries(monkeypatch):
    """Apply the Windows retry schedule on any platform and record the waits."""
    monkeypatch.setattr(engine, "_REPLACE_RETRY_DELAYS", WINDOWS_DELAYS, raising=False)
    sleeps = []
    monkeypatch.setattr(time, "sleep", sleeps.append)
    return sleeps


def _flaky_replace(monkeypatch, failures, error=errno.EACCES):
    """Make ``os.replace`` raise ``OSError(error)`` for the first *failures* calls."""
    real_replace = os.replace
    calls = []

    def replace(src, dst):
        calls.append((src, dst))
        if len(calls) <= failures:
            # OSError(errno.EACCES, ...) constructs a PermissionError, as
            # Windows raises for a sharing violation.
            raise OSError(error, os.strerror(error))
        return real_replace(src, dst)

    monkeypatch.setattr(engine.os, "replace", replace)
    return calls


def _leftover_temp_files(directory):
    return [p for p in directory.iterdir() if p.name.endswith(".tmp")]


def _target(tmp_path):
    target = tmp_path / "state.json"
    target.write_text("{}", encoding="utf-8")
    return target


def test_retry_schedule_applies_on_windows_only():
    expected = WINDOWS_DELAYS if os.name == "nt" else ()
    assert engine._REPLACE_RETRY_DELAYS == expected


def test_transient_permission_error_is_retried(tmp_path, monkeypatch, windows_retries):
    target = _target(tmp_path)
    calls = _flaky_replace(monkeypatch, failures=2)

    RunState._atomic_write_json(target, {"status": "running"})

    assert json.loads(target.read_text(encoding="utf-8")) == {"status": "running"}
    assert len(calls) == 3
    assert windows_retries == [0.1, 0.2]
    assert _leftover_temp_files(tmp_path) == []


def test_persistent_permission_error_is_raised(tmp_path, monkeypatch, windows_retries):
    target = _target(tmp_path)
    calls = _flaky_replace(monkeypatch, failures=10**6)

    with pytest.raises(PermissionError) as raised:
        RunState._atomic_write_json(target, {"status": "running"})

    assert raised.value.errno == errno.EACCES
    assert len(calls) == 5
    assert windows_retries == [0.1, 0.2, 0.4, 0.8]
    assert json.loads(target.read_text(encoding="utf-8")) == {}
    assert _leftover_temp_files(tmp_path) == []


def test_other_os_error_is_not_retried(tmp_path, monkeypatch, windows_retries):
    target = _target(tmp_path)
    calls = _flaky_replace(monkeypatch, failures=1, error=errno.ENOSPC)

    with pytest.raises(OSError) as raised:
        RunState._atomic_write_json(target, {"status": "running"})

    assert not isinstance(raised.value, PermissionError)
    assert len(calls) == 1
    assert windows_retries == []
    assert _leftover_temp_files(tmp_path) == []
