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


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")
def test_replace_writes_private_content_only_into_private_temp(tmp_path, monkeypatch):
    """Replacing a 0600 file under a 022 umask must not expose the new
    content through a 0644 temp file before the final chmod."""
    dest = tmp_path / "private.md"
    dest.write_text("old\n", encoding="utf-8")
    dest.chmod(0o600)
    modes_at_write = []
    real_fdopen = os.fdopen

    def recording_fdopen(fd, *args, **kwargs):
        modes_at_write.append(stat.S_IMODE(os.fstat(fd).st_mode))
        return real_fdopen(fd, *args, **kwargs)

    old_umask = os.umask(0o022)
    try:
        monkeypatch.setattr(os, "fdopen", recording_fdopen)
        CommandRegistrar._replace_file_text(dest, "secret\n")
    finally:
        monkeypatch.undo()
        os.umask(old_umask)

    assert modes_at_write == [0o600]
    assert dest.read_text(encoding="utf-8") == "secret\n"
    assert stat.S_IMODE(dest.stat().st_mode) == 0o600
