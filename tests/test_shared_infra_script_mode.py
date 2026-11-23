"""Unit tests for shared infrastructure writes and script modes."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from specify_cli import shared_infra
from specify_cli.integrations._file_changes import file_change_observer
from specify_cli.shared_infra import _shared_script_mode

SHEBANG = b"#!/usr/bin/env bash\necho hi\n"


def _source(tmp_path, name, mode):
    path = tmp_path / name
    path.write_bytes(SHEBANG)
    path.chmod(mode)
    return path


@pytest.mark.skipif(os.name == "nt", reason="POSIX execute bits are not meaningful on Windows")
@pytest.mark.parametrize(
    ("source_mode", "expected"),
    [(0o644, 0o755), (0o640, 0o750), (0o600, 0o700), (0o200, 0o300)],
)
def test_shell_script_gets_execute_bit_for_each_class_that_reads(tmp_path, source_mode, expected):
    source = _source(tmp_path, "setup-plan.sh", source_mode)
    assert _shared_script_mode(source, SHEBANG) == expected


@pytest.mark.skipif(os.name == "nt", reason="POSIX execute bits are not meaningful on Windows")
@pytest.mark.parametrize("source_mode", [0o755, 0o744, 0o754, 0o700, 0o710])
def test_already_executable_script_keeps_its_mode(tmp_path, source_mode):
    source = _source(tmp_path, "setup-plan.sh", source_mode)
    assert _shared_script_mode(source, SHEBANG) == source_mode


@pytest.mark.skipif(os.name == "nt", reason="POSIX execute bits are not meaningful on Windows")
@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("common.sh", b"echo sourced, no shebang\n"),
        ("common.sh", b""),
        ("setup-plan.ps1", SHEBANG),
        ("setup_plan.py", SHEBANG),
        ("sh", SHEBANG),
    ],
)
def test_other_files_keep_the_packaged_mode(tmp_path, name, content):
    source = _source(tmp_path, name, 0o644)
    assert _shared_script_mode(source, content) == 0o644


def test_windows_keeps_the_packaged_mode(tmp_path, monkeypatch):
    source = _source(tmp_path, "setup-plan.sh", 0o644)
    packaged = source.stat().st_mode & 0o777
    monkeypatch.setattr(shared_infra.os, "name", "nt")
    assert _shared_script_mode(source, SHEBANG) == packaged


@pytest.mark.skipif(os.name == "nt", reason="Exercises POSIX mode and filename limits")
def test_shared_script_atomic_overwrite_with_relative_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = Path("project")
    project.mkdir()
    destination = project / ("s" * 252 + ".sh")
    destination.write_bytes(b"old")
    observations = []
    replace = os.replace

    def observe(path, before, removal):
        assert path == destination
        assert not removal
        observations.append((before, path.read_bytes()))

    def check_publish(source, target):
        assert Path(target).resolve() == destination.resolve()
        assert Path(source).read_bytes() == SHEBANG
        assert destination.read_bytes() == b"old"
        assert stat.S_IMODE(Path(source).stat().st_mode) == 0o750
        replace(source, target)

    monkeypatch.setattr(os, "replace", check_publish)
    token = file_change_observer.set(observe)
    try:
        shared_infra._write_shared_bytes(project, destination, SHEBANG, mode=0o750)
    finally:
        file_change_observer.reset(token)

    assert observations == [(True, b"old"), (False, SHEBANG)]
    assert stat.S_IMODE(destination.stat().st_mode) == 0o750
    assert list(project.iterdir()) == [destination]


def test_failed_shared_text_publish_preserves_original_and_removes_stage(tmp_path, monkeypatch):
    destination = tmp_path / "template.md"
    destination.write_bytes(b"old")
    content = "caf\u00e9\n"
    observations = []

    def refuse_publish(source, target):
        assert Path(source).read_bytes() == content.encode("utf-8")
        raise PermissionError("injected publish failure")

    monkeypatch.setattr(os, "replace", refuse_publish)
    token = file_change_observer.set(lambda *change: observations.append(change))
    try:
        with pytest.raises(PermissionError, match="injected publish failure"):
            shared_infra._write_shared_text(tmp_path, destination, content)
    finally:
        file_change_observer.reset(token)

    assert observations == [(destination, True, False)]
    assert destination.read_bytes() == b"old"
    assert list(tmp_path.iterdir()) == [destination]


@pytest.mark.skipif(os.name == "nt", reason="Requires creating a symlink")
def test_shared_write_denies_link_introduced_after_snapshot(tmp_path, monkeypatch):
    target = tmp_path / "custom.md"
    target.write_bytes(b"custom")
    destination = tmp_path / "template.md"
    observations = []
    open_file = os.open

    def observe(path, before, removal):
        observations.append((path, before, removal))
        if before:
            path.symlink_to(target.name)

    def reject_staging(path, flags, *args, **kwargs):
        assert not flags & os.O_CREAT, "A denied path must not create a staging file"
        return open_file(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", reject_staging)
    token = file_change_observer.set(observe)
    try:
        with pytest.raises(shared_infra.SymlinkedSharedPathError):
            shared_infra._write_shared_text(tmp_path, destination, "replacement")
    finally:
        file_change_observer.reset(token)

    assert observations == [(destination, True, False)]
    assert destination.is_symlink()
    assert target.read_bytes() == b"custom"
    assert set(tmp_path.iterdir()) == {destination, target}
