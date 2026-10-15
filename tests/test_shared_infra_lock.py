"""Tests for the shared inter-process project lock."""

from __future__ import annotations

import os
import threading

import pytest

from specify_cli.shared_infra import _exclusive_project_lock
from tests.lock_helpers import watch_lock_attempt

LOCK_NAME = ".test-resource.lock"


def _symlink_or_skip(link, target, *, target_is_directory=False):
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks are unavailable: {exc}")


def test_lock_creates_lock_file_under_specify(tmp_path):
    with _exclusive_project_lock(tmp_path, LOCK_NAME, context="test"):
        assert (tmp_path / ".specify" / LOCK_NAME).is_file()


def test_lock_blocks_second_holder_until_released(tmp_path, monkeypatch):
    first_inside = threading.Event()
    release_first = threading.Event()
    second_inside = threading.Event()
    second_attempted = watch_lock_attempt(monkeypatch, "lock-second")
    errors: list[BaseException] = []

    def _hold(inside, release=None):
        try:
            with _exclusive_project_lock(tmp_path, LOCK_NAME, context="test"):
                inside.set()
                if release is not None and not release.wait(10):
                    raise AssertionError("first holder was never released")
        except BaseException as exc:  # noqa: BLE001 - surfaced below
            errors.append(exc)

    first = threading.Thread(
        target=_hold, args=(first_inside, release_first), name="lock-first", daemon=True
    )
    second = threading.Thread(
        target=_hold, args=(second_inside,), name="lock-second", daemon=True
    )
    first.start()
    assert first_inside.wait(10)
    second.start()
    assert second_attempted.wait(10), "second holder never attempted the lock"
    assert not second_inside.is_set()

    release_first.set()
    first.join(10)
    second.join(10)

    assert not errors
    assert second_inside.is_set()


def test_lock_is_released_when_body_raises(tmp_path):
    with pytest.raises(RuntimeError):
        with _exclusive_project_lock(tmp_path, LOCK_NAME, context="test"):
            raise RuntimeError("boom")

    reacquired = threading.Event()

    def _reacquire():
        with _exclusive_project_lock(tmp_path, LOCK_NAME, context="test"):
            reacquired.set()

    thread = threading.Thread(target=_reacquire, daemon=True)
    thread.start()
    thread.join(10)
    assert reacquired.is_set()


def test_lock_rejects_symlinked_lock_file(tmp_path):
    (tmp_path / ".specify").mkdir()
    target = tmp_path / "outside.lock"
    target.write_text("", encoding="utf-8")
    _symlink_or_skip(tmp_path / ".specify" / LOCK_NAME, target)

    with pytest.raises(OSError, match="Refusing to use symlinked test lock"):
        with _exclusive_project_lock(tmp_path, LOCK_NAME, context="test"):
            pass


def test_lock_rejects_symlinked_specify_directory(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    _symlink_or_skip(project / ".specify", outside, target_is_directory=True)

    with pytest.raises(OSError, match="symlinked test lock directory"):
        with _exclusive_project_lock(project, LOCK_NAME, context="test"):
            pass
    assert not (outside / LOCK_NAME).exists()


def test_lock_reports_unopenable_lock_file_as_oserror(tmp_path):
    (tmp_path / ".specify" / LOCK_NAME).mkdir(parents=True)

    with pytest.raises(OSError):
        with _exclusive_project_lock(tmp_path, LOCK_NAME, context="test"):
            pass


@pytest.mark.skipif(os.name == "nt", reason="POSIX file mode semantics")
def test_lock_file_is_private(tmp_path):
    with _exclusive_project_lock(tmp_path, LOCK_NAME, context="test"):
        pass
    mode = (tmp_path / ".specify" / LOCK_NAME).stat().st_mode & 0o777
    assert mode & 0o077 == 0
