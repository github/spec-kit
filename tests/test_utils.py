"""Unit tests for specify_cli._utils – ensure_writable_tree(), copy_file_preserving_exec()."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from specify_cli._utils import copy_file_preserving_exec, ensure_writable_tree

_SKIP_WINDOWS = pytest.mark.skipif(
    os.name == "nt", reason="POSIX mode bits are not stable on Windows"
)


# -- Positive tests -----------------------------------------------------------


@_SKIP_WINDOWS
def test_ensure_writable_tree_adds_owner_write_to_readonly_dirs(tmp_path: Path) -> None:
    """Read-only directories should gain owner write+execute bits."""
    child = tmp_path / "a"
    child.mkdir()
    child.chmod(0o555)

    ensure_writable_tree(tmp_path)

    mode = stat.S_IMODE(child.stat().st_mode)
    assert mode & 0o300 == 0o300, f"Expected owner w+x bits set, got {oct(mode)}"


@_SKIP_WINDOWS
def test_ensure_writable_tree_preserves_existing_permissions(tmp_path: Path) -> None:
    """Directories that are already writable should keep their existing bits."""
    child = tmp_path / "a"
    child.mkdir()
    child.chmod(0o755)

    ensure_writable_tree(tmp_path)

    mode = stat.S_IMODE(child.stat().st_mode)
    assert mode == 0o755, f"Expected 0o755 unchanged, got {oct(mode)}"


@_SKIP_WINDOWS
def test_ensure_writable_tree_handles_nested_readonly_dirs(tmp_path: Path) -> None:
    """All levels of a deeply nested read-only tree should become writable."""
    # Build bottom-up so we can still mkdir before locking
    a = tmp_path / "a"
    b = a / "b"
    c = b / "c"
    c.mkdir(parents=True)

    # Lock from the bottom up
    for d in (c, b, a):
        d.chmod(0o555)

    ensure_writable_tree(tmp_path)

    for d in (a, b, c):
        mode = stat.S_IMODE(d.stat().st_mode)
        assert mode & 0o300 == 0o300, f"{d} missing owner w+x: {oct(mode)}"


@_SKIP_WINDOWS
def test_ensure_writable_tree_does_not_touch_files(tmp_path: Path) -> None:
    """File permissions must be left untouched – only directories are fixed."""
    f = tmp_path / "readonly.txt"
    f.write_text("hello")
    f.chmod(0o444)

    ensure_writable_tree(tmp_path)

    mode = stat.S_IMODE(f.stat().st_mode)
    assert mode == 0o444, f"File mode should be unchanged, got {oct(mode)}"


# -- Negative / edge-case tests ----------------------------------------------


def test_ensure_writable_tree_noop_on_windows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """On Windows (os.name == 'nt'), the function should return immediately."""
    monkeypatch.setattr(os, "name", "nt")

    child = tmp_path / "a"
    child.mkdir()

    # Capture the mode before the call (may not be meaningful on real Windows,
    # but this test runs on any OS with os.name faked).
    before = child.stat().st_mode

    ensure_writable_tree(tmp_path)

    after = child.stat().st_mode
    assert before == after, "Permissions should not change when os.name == 'nt'"


@_SKIP_WINDOWS
def test_ensure_writable_tree_swallows_oserror(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """OSError on individual chmod calls must be silently swallowed."""
    child = tmp_path / "a"
    child.mkdir()

    original_chmod = Path.chmod

    def exploding_chmod(self: Path, mode: int) -> None:
        if self == child:
            raise OSError("synthetic permission error")
        original_chmod(self, mode)

    monkeypatch.setattr(Path, "chmod", exploding_chmod)

    # Must not raise
    ensure_writable_tree(tmp_path)


@_SKIP_WINDOWS
def test_ensure_writable_tree_empty_directory(tmp_path: Path) -> None:
    """An empty directory should itself gain write bits without error."""
    tmp_path.chmod(0o555)

    ensure_writable_tree(tmp_path)

    mode = stat.S_IMODE(tmp_path.stat().st_mode)
    assert mode & 0o300 == 0o300, f"Root dir missing owner w+x: {oct(mode)}"


# -- copy_file_preserving_exec tests ------------------------------------------


@_SKIP_WINDOWS
def test_copy_file_preserving_exec_executable_source(tmp_path: Path) -> None:
    """Execute bits present on the source must appear on the destination."""
    src = tmp_path / "script.sh"
    src.write_text("#!/bin/sh\necho hi\n")
    src.chmod(0o755)

    dst = tmp_path / "out" / "script.sh"
    dst.parent.mkdir()
    copy_file_preserving_exec(str(src), str(dst))

    mode = stat.S_IMODE(dst.stat().st_mode)
    assert mode & 0o111, f"Execute bits missing on destination: {oct(mode)}"
    assert mode & 0o200, f"Owner write bit missing on destination: {oct(mode)}"


@_SKIP_WINDOWS
def test_copy_file_preserving_exec_non_executable_source(tmp_path: Path) -> None:
    """Execute bits absent on the source must not appear on the destination."""
    src = tmp_path / "data.json"
    src.write_text('{"key": "value"}')
    src.chmod(0o644)

    dst = tmp_path / "out" / "data.json"
    dst.parent.mkdir()
    copy_file_preserving_exec(str(src), str(dst))

    mode = stat.S_IMODE(dst.stat().st_mode)
    assert not (mode & 0o111), f"Unexpected execute bits on destination: {oct(mode)}"
    assert mode & 0o200, f"Owner write bit missing on destination: {oct(mode)}"


@_SKIP_WINDOWS
def test_copy_file_preserving_exec_readonly_source_is_writable(tmp_path: Path) -> None:
    """Source read-only bits must not propagate to the destination."""
    src = tmp_path / "locked.txt"
    src.write_text("content")
    src.chmod(0o444)

    dst = tmp_path / "out" / "locked.txt"
    dst.parent.mkdir()
    copy_file_preserving_exec(str(src), str(dst))

    mode = stat.S_IMODE(dst.stat().st_mode)
    assert mode & 0o200, f"Destination is not owner-writable: {oct(mode)}"


@_SKIP_WINDOWS
def test_copy_file_preserving_exec_copies_content(tmp_path: Path) -> None:
    """File content must be faithfully copied."""
    payload = "hello world\n"
    src = tmp_path / "src.txt"
    src.write_text(payload)

    dst = tmp_path / "dst.txt"
    copy_file_preserving_exec(str(src), str(dst))

    assert dst.read_text() == payload
