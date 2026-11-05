"""Tests for the ``specify preset remove`` command."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.presets import PresetManager


def test_remove_installed_preset(project_dir, pack_dir):
    PresetManager(project_dir).install_from_directory(pack_dir, "0.1.5")

    with patch.object(Path, "cwd", return_value=project_dir):
        result = CliRunner().invoke(app, ["preset", "remove", "test-pack"])

    assert result.exit_code == 0, result.output
    assert not PresetManager(project_dir).registry.is_installed("test-pack")


@pytest.mark.parametrize("operation", ["remove", "switch"])
@pytest.mark.parametrize("user_reference", [False, True])
def test_preset_skill_cleanup_preserves_user_files(tmp_path, monkeypatch, operation, user_reference):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    preset = Path(__file__).resolve().parents[3] / "presets" / "scaffold"
    for args in (
        ["init", "--here", "--integration", "copilot", "--script", "sh", "--ignore-agent-tools"],
        ["preset", "add", "--dev", str(preset)],
    ):
        result = runner.invoke(app, args, catch_exceptions=False)
        assert result.exit_code == 0, result.output
    skill_dir = tmp_path / ".github/skills/speckit-myext-myextcmd"
    reference = skill_dir / "references" / "user.md"
    original = b"\xef\xbb\xbf# User reference\r\nKeep my project notes."
    if user_reference:
        reference.parent.mkdir()
        reference.write_bytes(original)

    args = ["preset", "remove", "my-preset"] if operation == "remove" else ["integration", "switch", "claude"]
    result = runner.invoke(app, args, catch_exceptions=False)

    assert result.exit_code == 0, result.output
    assert not (skill_dir / "SKILL.md").exists()
    if user_reference:
        assert reference.is_file()
        assert reference.read_bytes() == original
    else:
        assert not skill_dir.exists()


@pytest.mark.parametrize("operation", ["remove", "switch"])
@pytest.mark.parametrize("user_reference", [False, True])
def test_preset_skill_cleanup_rollback_preserves_directory_mode(
    tmp_path, monkeypatch, capsys, operation, user_reference,
):
    from specify_cli.integrations._helpers import _read_integration_json
    from specify_cli.integrations._lifecycle import _FileJournal, _transaction
    from specify_cli.integrations.installer import read_records

    project = tmp_path / "project"
    project.mkdir()
    (tmp_path / "home").mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    runner = CliRunner()
    preset = Path(__file__).resolve().parents[3] / "presets" / "scaffold"
    for args in (
        ["init", "--here", "--integration", "copilot", "--script", "sh", "--ignore-agent-tools"],
        ["preset", "add", "--dev", str(preset)],
    ):
        result = runner.invoke(app, args, catch_exceptions=False)
        assert result.exit_code == 0, result.output
    skill_dir = project / ".github/skills/speckit-myext-myextcmd"
    skill_file = skill_dir / "SKILL.md"
    original = skill_file.read_bytes()
    skill_dir.chmod(0o700)
    reference = skill_dir / "references/user.md"
    if user_reference:
        reference.parent.mkdir()
        reference.write_bytes(b"User reference before cleanup")

    snapshot = _FileJournal._snapshot
    snapshotted = []

    def snapshot_without_user_files(self, source, destination):
        snapshotted.append(source)
        assert source != reference and source != reference.parent
        if source == skill_dir and user_reference:
            assert not any(source.iterdir())
        return snapshot(self, source, destination)

    monkeypatch.setattr(_FileJournal, "_snapshot", snapshot_without_user_files)
    args = ["preset", "remove", "my-preset"] if operation == "remove" else ["integration", "switch", "claude"]
    previous_umask = os.umask(0o022)
    try:
        with pytest.raises(RuntimeError, match="failure after cleanup"):
            with _transaction(project, "claude", _read_integration_json(project), read_records(project)):
                result = runner.invoke(app, args, catch_exceptions=False)
                assert result.exit_code == 0, result.output
                assert not skill_file.exists()
                assert skill_dir.exists() == user_reference
                if user_reference:
                    reference.write_bytes(b"User reference edited during transaction")
                raise RuntimeError("failure after cleanup")
    finally:
        os.umask(previous_umask)

    assert skill_file.read_bytes() == original
    if os.name != "nt":
        assert stat.S_IMODE(skill_dir.stat().st_mode) == 0o700
    if user_reference:
        assert skill_dir not in snapshotted
        assert reference.read_bytes() == b"User reference edited during transaction"
    assert "Recovery snapshots retained" not in capsys.readouterr().out
