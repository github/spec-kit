"""Tests for ``CommandRegistrar._replace_file_text`` (atomic artifact writes)."""

import os
import stat

import pytest

from specify_cli.agents import CommandRegistrar


def test_replace_keeps_long_valid_filename_writable(tmp_path):
    """The temp entry must not be longer than the destination allows: a
    250-byte name is valid and an in-place write accepted it."""
    dest = tmp_path / ("a" * 247 + ".md")
    dest.write_text("old\n", encoding="utf-8")

    CommandRegistrar._replace_file_text(dest, "new\n")

    assert dest.read_text(encoding="utf-8") == "new\n"
    assert sorted(p.name for p in tmp_path.iterdir()) == [dest.name]


def test_replace_creates_long_valid_filename(tmp_path):
    dest = tmp_path / ("b" * 247 + ".md")

    CommandRegistrar._replace_file_text(dest, "new\n")

    assert dest.read_text(encoding="utf-8") == "new\n"


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")
def test_replace_does_not_touch_process_umask(tmp_path, monkeypatch):
    """Reading the umask by setting it to 0 is process-wide and racy; a new
    file must get the creation mode from the kernel instead."""
    old_umask = os.umask(0o027)
    calls = []
    monkeypatch.setattr(os, "umask", lambda mask: calls.append(mask) or 0o027)
    try:
        dest = tmp_path / "new.md"
        CommandRegistrar._replace_file_text(dest, "new\n")
    finally:
        monkeypatch.undo()
        os.umask(old_umask)

    assert calls == []
    assert stat.S_IMODE(dest.stat().st_mode) == 0o640
