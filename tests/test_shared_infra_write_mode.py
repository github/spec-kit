"""Unit tests for the mode the shared text writer leaves on a file."""

from __future__ import annotations

import os
import stat

import pytest

from specify_cli.shared_infra import SymlinkedSharedPathError, _write_shared_text

pytestmark = pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")


def _mode(path):
    return stat.S_IMODE(path.stat().st_mode)


@pytest.fixture
def umask():
    """Set the process umask for one test and restore it afterwards."""
    previous = os.umask(0o022)

    def set_umask(value):
        os.umask(value)

    yield set_umask
    os.umask(previous)


@pytest.mark.parametrize(
    ("mask", "preserve_mode", "expected"),
    [(0o077, True, 0o600), (0o022, True, 0o644), (0o077, False, 0o644)],
    ids=["umask-077", "umask-022", "without-preserve-mode"],
)
def test_new_file_mode_follows_umask_only_with_preserve_mode(
    tmp_path, umask, mask, preserve_mode, expected
):
    """``preserve_mode`` leaves a new file's mode to the umask; without it
    the writer keeps its fixed 0644. An existing file keeps its bits."""
    new_file = tmp_path / "new.md"
    existing = tmp_path / "existing.md"
    existing.write_text("old\n", encoding="utf-8")
    existing.chmod(0o640)
    umask(mask)

    for dest in (new_file, existing):
        _write_shared_text(tmp_path, dest, "new\n", preserve_mode=preserve_mode)

    assert new_file.read_text(encoding="utf-8") == "new\n"
    assert _mode(new_file) == expected
    assert existing.read_text(encoding="utf-8") == "new\n"
    assert _mode(existing) == (0o640 if preserve_mode else 0o644)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["existing.md", "new.md"]


@pytest.mark.parametrize("mask", [0o022, 0o077])
def test_new_file_takes_the_mode_of_the_file_it_stands_in_for(tmp_path, umask, mask):
    """``new_file_mode`` is exact for a new file, whatever the umask, and
    never overrides the bits of a file that is already there."""
    new_file = tmp_path / "new.md"
    existing = tmp_path / "existing.md"
    existing.write_text("old\n", encoding="utf-8")
    existing.chmod(0o640)
    umask(mask)

    for dest in (new_file, existing):
        _write_shared_text(
            tmp_path, dest, "new\n", preserve_mode=True, new_file_mode=0o600
        )

    assert _mode(new_file) == 0o600
    assert _mode(existing) == 0o640
    assert existing.read_text(encoding="utf-8") == "new\n"


def test_preserve_mode_does_not_read_or_write_through_a_link(tmp_path):
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    outside.chmod(0o600)
    project = tmp_path / "project"
    project.mkdir()
    (project / "linked.md").symlink_to(outside)

    with pytest.raises(SymlinkedSharedPathError):
        _write_shared_text(project, project / "linked.md", "new\n", preserve_mode=True)

    assert outside.read_text(encoding="utf-8") == "outside\n"
    assert _mode(outside) == 0o600
