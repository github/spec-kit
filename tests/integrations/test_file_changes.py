"""Tests for the shared atomic writer in integrations/_file_changes.py."""

import os
import sys

import pytest

from specify_cli.integrations._file_changes import atomic_write_bytes

posix_only = pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")


def _mode(path):
    return path.stat().st_mode & 0o777


@posix_only
def test_mode_is_narrowed_by_the_umask_unless_exact(tmp_path):
    previous = os.umask(0o022)
    try:
        narrowed = tmp_path / "narrowed"
        atomic_write_bytes(narrowed, b"x", 0o775)
        exact = tmp_path / "exact"
        atomic_write_bytes(exact, b"x", 0o775, exact=True)
    finally:
        os.umask(previous)
    assert _mode(narrowed) == 0o755
    assert _mode(exact) == 0o775


@posix_only
def test_content_is_never_on_disk_under_a_wider_mode(tmp_path, monkeypatch):
    seen = []
    original = os.replace

    def spy(src, dst):
        seen.append(os.stat(src).st_mode & 0o777)
        return original(src, dst)

    monkeypatch.setattr(os, "replace", spy)
    previous = os.umask(0)  # a umask that would otherwise give 0666
    try:
        atomic_write_bytes(tmp_path / "private", b"secret", 0o600)
    finally:
        os.umask(previous)
    assert seen == [0o600]


def test_replaces_an_existing_file(tmp_path):
    target = tmp_path / "f"
    target.write_bytes(b"old")
    atomic_write_bytes(target, b"new", 0o644)
    assert target.read_bytes() == b"new"


def test_long_file_names_do_not_overflow_the_temporary_name(tmp_path):
    target = tmp_path / ("a" * 250)
    atomic_write_bytes(target, b"x", 0o644, exact=True)
    assert target.read_bytes() == b"x"
    assert [p.name for p in tmp_path.iterdir() if p.is_file()] == [target.name]


def test_before_replace_can_abort_and_leaves_no_temporary_file(tmp_path):
    target = tmp_path / "f"
    target.write_bytes(b"old")

    def refuse():
        raise ValueError("destination changed")

    with pytest.raises(ValueError, match="destination changed"):
        atomic_write_bytes(target, b"new", 0o644, before_replace=refuse)
    assert target.read_bytes() == b"old"
    assert [p.name for p in tmp_path.iterdir() if p.is_file()] == ["f"]
