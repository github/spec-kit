"""Unit tests for the mode shared scripts are written with."""

from __future__ import annotations

import os

import pytest

from specify_cli import shared_infra
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
