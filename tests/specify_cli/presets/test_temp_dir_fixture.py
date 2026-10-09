"""Fixture cleanup must absorb a transient Windows lock without hiding one.

CI reported two *teardown* errors while the test bodies passed:

    ERROR at teardown of test_priority_override_write_failure_restores_state[False]
    tests\\specify_cli\\presets\\_fixtures.py:18: in temp_dir
        shutil.rmtree(tmpdir)
    E   PermissionError: [WinError 32] The process cannot access the file
        because it is being used by another process: '...\\project'

A probe of the exact scenario on POSIX shows the test process holds **no** open
file or directory handle inside the tree, so the lock is owned outside the test
process (Defender/indexer on the runner releases handles asynchronously). The
cleanup therefore retries a transient lock and still raises when it does not
clear — it must never accept a tree it could not remove.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tests._temp_tree import remove_fixture_tree


def test_cleanup_absorbs_a_transient_lock(tmp_path, monkeypatch):
    """A lock that clears must not fail the teardown.

    The Windows failure is ``PermissionError(32)`` raised by ``rmtree`` for a
    handle another process is still releasing, so the retry has to make real
    progress instead of being a no-op.
    """
    tree = tmp_path / "tree"
    (tree / "project").mkdir(parents=True)
    (tree / "project" / "artifact.md").write_text("body", encoding="utf-8")

    real_rmtree = shutil.rmtree
    calls = []

    def flaky(path, *args, **kwargs):
        calls.append(path)
        if len(calls) == 1:
            # Exactly the error CI reported on the first attempt.
            raise PermissionError(32, "The process cannot access the file")
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(shutil, "rmtree", flaky)
    remove_fixture_tree(tree)

    assert len(calls) >= 2, "cleanup did not retry the locked removal"
    assert not tree.exists()


def test_cleanup_raises_when_the_lock_never_clears(tmp_path, monkeypatch):
    """A permanent lock must surface, never be swallowed."""
    tree = tmp_path / "tree"
    tree.mkdir()
    calls = []

    def stubborn(path, *args, **kwargs):
        calls.append(path)
        raise PermissionError(32, "The process cannot access the file")

    monkeypatch.setattr(shutil, "rmtree", stubborn)

    with pytest.raises(PermissionError):
        remove_fixture_tree(tree)

    assert calls, "cleanup never attempted the removal"
    assert tree.exists()


def test_cleanup_reports_a_tree_it_could_not_remove(tmp_path, monkeypatch):
    """A removal that leaves the tree behind must not look successful."""
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "keep.txt").write_text("x", encoding="utf-8")

    def removes_nothing(path, *args, **kwargs):
        return None  # silently "succeeds" without touching the tree

    monkeypatch.setattr(shutil, "rmtree", removes_nothing)

    with pytest.raises(OSError):
        remove_fixture_tree(tree)

    assert tree.exists()


def test_cleanup_never_removes_a_tree_holding_the_working_directory(
    tmp_path, monkeypatch
):
    """The process must not be left without a working directory.

    Windows cannot remove a directory that is the process CWD, and on POSIX a
    bare ``rmtree`` deletes the CWD out from under the process. The helper
    leaves the tree first, so its caller keeps a usable working directory.
    """
    tree = tmp_path / "tree"
    (tree / "project").mkdir(parents=True)
    monkeypatch.chdir(tree / "project")

    remove_fixture_tree(tree)

    assert not tree.exists()
    cwd = Path.cwd()  # raises FileNotFoundError if the CWD was removed
    assert cwd != tree and tree not in cwd.parents
