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
@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("ancestor", [False, True])
def test_preset_skill_cleanup_preserves_swapped_link_target(
    tmp_path, monkeypatch, operation, fallback, ancestor,
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
    runner = CliRunner()
    preset = Path(__file__).resolve().parents[3] / "presets" / "scaffold"
    for args in (
        ["init", "--here", "--integration", "copilot", "--script", "sh", "--ignore-agent-tools"],
        ["preset", "add", "--dev", str(preset)],
    ):
        result = runner.invoke(app, args, catch_exceptions=False)
        assert result.exit_code == 0, result.output
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
        monkeypatch.setattr(os, "supports_dir_fd", set())
    args = ["preset", "remove", "my-preset"] if operation == "remove" else ["integration", "switch", "claude"]
    result = runner.invoke(app, args, catch_exceptions=False)

    assert swapped
    assert outside_file.is_file(), result.output
    assert outside_file.read_bytes() == original
    assert swapped_dir.is_symlink()
    assert result.exit_code == 0, result.output


@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("replacement", ["link", "loop", "file", "outside", "parent", "boundary"])
def test_preset_skill_cleanup_skips_unsafe_directory(tmp_path, monkeypatch, fallback, replacement):
    from specify_cli.integrations import _file_changes

    directory = tmp_path / "skill"
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_file = outside / "SKILL.md"
    outside_file.write_bytes(b"Outside skill")
    root = tmp_path
    if replacement in ("outside", "parent", "boundary"):
        directory.mkdir()
        (directory / "SKILL.md").write_bytes(b"Retained skill")
        root = tmp_path / "root"
        root.mkdir()
        if replacement == "parent":
            directory = root / ".." / directory.name
        elif replacement == "boundary":
            root = directory
    elif replacement == "file":
        directory.write_bytes(b"Replacement file")
    else:
        try:
            directory.symlink_to(directory if replacement == "loop" else outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("Directory links are unavailable")
    if fallback:
        monkeypatch.setattr(os, "supports_dir_fd", set())
    observed = []
    token = _file_changes.file_change_observer.set(lambda *args: observed.append(args))
    try:
        _file_changes.unlink_in_directory(directory / "SKILL.md", root=root)
    finally:
        _file_changes.file_change_observer.reset(token)

    assert observed == []
    assert outside_file.read_bytes() == b"Outside skill"
    if replacement in ("outside", "parent", "boundary"):
        assert (directory / "SKILL.md").read_bytes() == b"Retained skill"
    elif replacement == "file":
        assert directory.is_file()
    else:
        assert directory.is_symlink()


@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("swap_at", ["before_unlink", "after_unlink", "before_rmdir"])
def test_preset_skill_cleanup_preserves_concurrent_replacements(tmp_path, monkeypatch, fallback, swap_at):
    from specify_cli.integrations import _file_changes

    directory = tmp_path / "skills" / "skill"
    directory.mkdir(parents=True)
    skill_file = directory / "SKILL.md"
    skill_file.write_bytes(b"Generated skill")
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_file = outside / "SKILL.md"
    outside_file.write_bytes(b"Outside skill")
    outside_skill = outside / directory.name
    outside_skill.mkdir()
    probe = tmp_path / "link"
    try:
        probe.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Directory links are unavailable")
    probe.unlink()
    if fallback:
        monkeypatch.setattr(os, "supports_dir_fd", set())
    descriptor_io = (
        getattr(os, "O_DIRECTORY", 0)
        and getattr(os, "O_NOFOLLOW", 0)
        and {os.open, os.unlink, os.rmdir, os.stat} <= os.supports_dir_fd
        and os.listdir in os.supports_fd
    )
    before = _file_changes.before_file_change
    after = _file_changes.after_file_change
    swapped = False

    def before_change(path, **kwargs):
        nonlocal swapped
        before(path, **kwargs)
        if path == skill_file and swap_at == "before_unlink":
            directory.rename(tmp_path / "retained")
            directory.symlink_to(outside, target_is_directory=True)
            swapped = True
        elif path == directory and swap_at == "before_rmdir":
            directory.parent.rename(tmp_path / "retained")
            directory.parent.symlink_to(outside if descriptor_io else tmp_path / "retained", target_is_directory=True)
            swapped = True

    def after_change(path):
        nonlocal swapped
        after(path)
        if path == skill_file and swap_at == "after_unlink":
            directory.rename(tmp_path / "retained")
            directory.mkdir()
            swapped = True

    monkeypatch.setattr(_file_changes, "before_file_change", before_change)
    monkeypatch.setattr(_file_changes, "after_file_change", after_change)
    _file_changes.unlink_in_directory(skill_file, root=tmp_path)

    assert swapped
    assert outside_file.read_bytes() == b"Outside skill"
    assert outside_skill.is_dir()
    if swap_at == "before_unlink":
        assert directory.is_symlink()
        if descriptor_io:
            assert not (tmp_path / "retained" / "SKILL.md").exists()
    elif swap_at == "after_unlink" or not descriptor_io:
        assert directory.is_dir()


@pytest.mark.parametrize("operation", ["remove", "switch"])
@pytest.mark.parametrize(
    "user_reference,layout",
    [(False, "project"), (True, "project"), (False, "linked-parent")],
    ids=["empty", "user-files", "linked-parent"],
)
@pytest.mark.parametrize("fallback", [False, True])
def test_preset_skill_cleanup_preserves_user_files(
    tmp_path, monkeypatch, operation, user_reference, layout, fallback,
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
    runner = CliRunner()
    preset = Path(__file__).resolve().parents[3] / "presets" / "scaffold"
    for args in (
        ["init", "--here", "--integration", "copilot", "--script", "sh", "--ignore-agent-tools"],
        ["preset", "add", "--dev", str(preset)],
    ):
        result = runner.invoke(app, args, catch_exceptions=False)
        assert result.exit_code == 0, result.output
    # getcwd() resolves parent links; retain the user's lexical project path.
    monkeypatch.setattr(Path, "cwd", lambda: project)
    skill_dir = project / ".github/skills/speckit-myext-myextcmd"
    reference = skill_dir / "references" / "user.md"
    original = b"\xef\xbb\xbf# User reference\r\nKeep my project notes."
    if user_reference:
        reference.parent.mkdir()
        reference.write_bytes(original)
    if fallback:
        monkeypatch.setattr(os, "supports_dir_fd", set())

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
@pytest.mark.parametrize("fallback", [False, True])
def test_preset_skill_cleanup_uses_global_boundary(project_dir, tmp_path, monkeypatch, operation, fallback):
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    skills_root = home / ".hermes/skills"
    skill_dir = skills_root / "speckit-custom"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nmetadata:\n  source: preset:global-preset\n---\nGenerated skill\n")
    if fallback:
        monkeypatch.setattr(os, "supports_dir_fd", set())
    manager = PresetManager(project_dir)
    if operation == "switch":
        manager._delete_agent_preset_skills("hermes", [skill_dir.name], "global-preset")
    else:
        manager._unregister_skills_in_dir([skill_dir.name], skills_root, "hermes", pack_id="global-preset")

    assert not (skill_dir / "SKILL.md").exists()
    assert not skill_dir.exists()


@pytest.mark.parametrize("operation", ["remove", "switch"])
@pytest.mark.parametrize("user_reference", [False, True])
@pytest.mark.parametrize("fallback", [False, True])
def test_preset_skill_cleanup_rollback_preserves_directory_mode(
    tmp_path, monkeypatch, capsys, operation, user_reference, fallback,
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
    if fallback:
        monkeypatch.setattr(os, "supports_dir_fd", set())

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
