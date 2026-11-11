"""Preset skill cleanup checks shared by the `preset remove` and `integration switch` suites."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.presets import PresetManager

PRESET_REMOVE = ["preset", "remove", "my-preset"]
INTEGRATION_SWITCH = ["integration", "switch", "claude"]


def _install_scaffold_preset() -> CliRunner:
    """Initialize Copilot skills in the current directory and add the bundled scaffold preset."""
    runner = CliRunner()
    preset = Path(__file__).resolve().parents[3] / "presets" / "scaffold"
    for args in (
        ["init", "--here", "--integration", "copilot", "--script", "sh", "--ignore-agent-tools"],
        ["preset", "add", "--dev", str(preset)],
    ):
        result = runner.invoke(app, args, catch_exceptions=False)
        assert result.exit_code == 0, result.output
    return runner


def check_cleanup_preserves_swapped_link_target(
    tmp_path, monkeypatch, command, fallback, ancestor,
):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    probe = tmp_path / "link"
    try:
        probe.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Directory links are unavailable")
    probe.unlink()
    monkeypatch.chdir(project)
    runner = _install_scaffold_preset()
    skill_dir = project / ".github/skills/speckit-myext-myextcmd"
    original = (skill_dir / "SKILL.md").read_bytes()
    swapped_dir = skill_dir.parent if ancestor else skill_dir
    outside_skill = outside / skill_dir.name if ancestor else outside
    outside_skill.mkdir(exist_ok=True)
    outside_file = outside_skill / "SKILL.md"
    outside_file.write_bytes(original)
    validate = PresetManager._validate_skill_subdir
    swapped = False

    def validate_then_swap(self, directory, **kwargs):
        nonlocal swapped
        valid = validate(self, directory, **kwargs)
        if valid and directory == skill_dir and not kwargs["create"] and not swapped:
            swapped_dir.rename(project / "retained-skills")
            swapped_dir.symlink_to(outside, target_is_directory=True)
            swapped = True
        return valid

    monkeypatch.setattr(PresetManager, "_validate_skill_subdir", validate_then_swap)
    if fallback:
        # Disable descriptor-relative cleanup without disabling safe project reads.
        monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd - {os.rmdir})
    result = runner.invoke(app, command, catch_exceptions=False)

    assert swapped
    assert outside_file.is_file(), result.output
    assert outside_file.read_bytes() == original
    assert swapped_dir.is_symlink()
    assert result.exit_code == 0, result.output


def check_cleanup_preserves_user_files(
    tmp_path, monkeypatch, command, user_reference, layout, fallback,
):
    project = tmp_path
    if layout == "linked-parent":
        (tmp_path / "real" / "project").mkdir(parents=True)
        try:
            (tmp_path / "link").symlink_to(tmp_path / "real", target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("Directory links are unavailable")
        project = tmp_path / "link" / "project"
    monkeypatch.chdir(project)
    runner = _install_scaffold_preset()
    # getcwd() resolves parent links; retain the user's lexical project path.
    monkeypatch.setattr(Path, "cwd", lambda: project)
    skill_dir = project / ".github/skills/speckit-myext-myextcmd"
    reference = skill_dir / "references" / "user.md"
    original = b"\xef\xbb\xbf# User reference\r\nKeep my project notes."
    if user_reference:
        reference.parent.mkdir()
        reference.write_bytes(original)
    if fallback:
        monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd - {os.rmdir})

    result = runner.invoke(app, command, catch_exceptions=False)

    assert result.exit_code == 0, result.output
    assert not (skill_dir / "SKILL.md").exists()
    if user_reference:
        assert reference.is_file()
        assert reference.read_bytes() == original
    else:
        assert not skill_dir.exists()


def check_cleanup_rollback_preserves_directory_mode(
    tmp_path, monkeypatch, capsys, command, user_reference, fallback,
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
    runner = _install_scaffold_preset()
    skill_dir = project / ".github/skills/speckit-myext-myextcmd"
    skill_file = skill_dir / "SKILL.md"
    original = skill_file.read_bytes()
    skill_dir.chmod(0o700)
    reference = skill_dir / "references/user.md"
    if user_reference:
        reference.parent.mkdir()
        reference.write_bytes(b"User reference before cleanup")
    if fallback:
        monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd - {os.rmdir})

    snapshot = _FileJournal._snapshot
    snapshotted = []

    def snapshot_without_user_files(self, source, destination):
        snapshotted.append(source)
        assert source != reference and source != reference.parent
        if source == skill_dir and user_reference:
            assert not any(source.iterdir())
        return snapshot(self, source, destination)

    monkeypatch.setattr(_FileJournal, "_snapshot", snapshot_without_user_files)
    previous_umask = os.umask(0o022)
    try:
        with pytest.raises(RuntimeError, match="failure after cleanup"):
            with _transaction(project, "claude", _read_integration_json(project), read_records(project)):
                result = runner.invoke(app, command, catch_exceptions=False)
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
