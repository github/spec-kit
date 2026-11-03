"""Tests for the ``specify preset remove`` command."""

from __future__ import annotations

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
