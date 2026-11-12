"""Tests for mirrored integration CLI behavior in test_lifecycle.py."""

from __future__ import annotations

import json  # noqa: F401
import os  # noqa: F401
import shutil  # noqa: F401
from pathlib import Path  # noqa: F401

import pytest  # noqa: F401

from specify_cli import app  # noqa: F401
from tests.conftest import strip_ansi  # noqa: F401
from tests.specify_cli.integrations._helpers import (
    _copy_project_template,  # noqa: F401
    _init_project,  # noqa: F401
    _integration_list_row_cells,  # noqa: F401
    _move_kilocode_install_to_legacy_layout,  # noqa: F401
    _run_in_project,  # noqa: F401
    _symlink_or_skip,
    _write_invalid_manifest,  # noqa: F401
    runner,  # noqa: F401
)

class TestIntegrationLifecycle:
    def test_install_modify_uninstall_preserves_modified(self, tmp_path):
        """Full lifecycle: install → modify file → uninstall → verify modified file kept."""
        project = tmp_path / "lifecycle"
        project.mkdir()
        (project / ".specify").mkdir()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)

            # Install
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
            assert result.exit_code == 0
            assert "installed successfully" in result.output

            # Claude uses skills directory
            plan_file = project / ".claude" / "skills" / "speckit-plan" / "SKILL.md"
            assert plan_file.exists()

            # Modify one file
            plan_file.write_text("# user customization\n", encoding="utf-8")

            # Uninstall
            result = runner.invoke(app, ["integration", "uninstall"], catch_exceptions=False)
            assert result.exit_code == 0
            assert "preserved" in result.output

            # Modified file kept
            assert plan_file.exists()
            assert plan_file.read_text(encoding="utf-8") == "# user customization\n"
        finally:
            os.chdir(old_cwd)


@pytest.mark.parametrize("change", ["none", "changed-file", "new-file", "deleted-directory", "nonempty-sibling"])
def test_directory_identity_ignores_only_new_empty_destination_parents(tmp_path, change):
    from specify_cli.integrations._lifecycle import _file_identity, _matches_directory_before_write

    package = tmp_path / "package"
    package.mkdir()
    (package / "original.txt").write_text("original")
    (package / "original-empty").mkdir()
    expected = _file_identity(package)
    (package / ".cache/nested").mkdir(parents=True)
    if change == "changed-file":
        (package / "original.txt").write_text("concurrent edit")
    elif change == "new-file":
        (package / "user.txt").write_text("concurrent user file")
    elif change == "deleted-directory":
        (package / "original-empty").rmdir()
    elif change == "nonempty-sibling":
        (package / ".cache/user.txt").write_text("concurrent user cache file")
    assert _matches_directory_before_write(
        _file_identity(package), expected, (".cache", "nested"),
    ) == (change == "none")


def test_journal_snapshot_cleanup_leaves_symlink_targets_and_temp_dir_alone(tmp_path, monkeypatch):
    """Removing a read-only snapshot never chmods a live symlink target or its temp parent."""
    from specify_cli.integrations import _lifecycle

    if os.name == "nt":
        pytest.skip("POSIX permissions")
    target = tmp_path / "live-target"
    target.write_text("live\n", encoding="utf-8")
    target.chmod(0o444)
    temp_parent = tmp_path / "temp"
    temp_parent.mkdir()
    temp_mode = temp_parent.stat().st_mode & 0o7777
    monkeypatch.setattr(_lifecycle.tempfile, "tempdir", str(temp_parent))
    chmodded = []
    real_chmod = os.chmod

    def chmod(path, mode, *args, **kwargs):
        chmodded.append(Path(path))
        return real_chmod(path, mode, *args, **kwargs)

    monkeypatch.setattr(_lifecycle.os, "chmod", chmod)

    root = tmp_path / "project"
    (root / ".specify" / "scripts").mkdir(parents=True)
    with _lifecycle._journalled(root, [root / ".specify" / "scripts"], [], {"retained": False}):
        backup = next(temp_parent.iterdir())
        snapshot = backup / "writes"
        snapshot.mkdir()
        _symlink_or_skip(snapshot / "link", target)
        snapshot.chmod(0o555)
        backup.chmod(0o555)

    assert not any(temp_parent.iterdir())
    assert target.stat().st_mode & 0o7777 == 0o444
    assert temp_parent.stat().st_mode & 0o7777 == temp_mode
    assert target not in chmodded and temp_parent not in chmodded


def test_journal_snapshot_cleanup_survives_a_directory_open_failure(tmp_path, monkeypatch):
    """rmtree reporting a failed os.open must not fail a committed upgrade."""
    from specify_cli.integrations import _lifecycle

    real_rmtree = shutil.rmtree

    def rmtree(path, onerror=None, **kwargs):
        onerror(os.open, str(path), None)
        return real_rmtree(path, **kwargs)

    monkeypatch.setattr(_lifecycle.shutil, "rmtree", rmtree)
    # A writable temp parent, so the callback reaches the retry it must skip.
    temp_parent = tmp_path / "temp"
    temp_parent.mkdir()
    monkeypatch.setattr(_lifecycle.tempfile, "tempdir", str(temp_parent))
    temp_mode = temp_parent.stat().st_mode & 0o7777
    root = tmp_path / "project"
    (root / ".specify").mkdir(parents=True)
    with _lifecycle._journalled(root, [root / ".specify"], [], {"retained": False}):
        pass

    assert not any(temp_parent.iterdir())
    assert temp_parent.stat().st_mode & 0o7777 == temp_mode


def test_journal_snapshot_cleanup_removes_an_unreadable_snapshot_directory(tmp_path, monkeypatch):
    """A snapshot directory that copied a mode rmtree cannot open is still removed."""
    from specify_cli.integrations import _lifecycle

    if os.name == "nt":
        pytest.skip("POSIX permissions")
    temp_parent = tmp_path / "temp"
    temp_parent.mkdir()
    monkeypatch.setattr(_lifecycle.tempfile, "tempdir", str(temp_parent))
    root = tmp_path / "project"
    (root / ".specify").mkdir(parents=True)
    with _lifecycle._journalled(root, [root / ".specify"], [], {"retained": False}):
        locked = next(temp_parent.iterdir()) / "writes" / "0"
        locked.mkdir(parents=True)
        (locked / "file").write_text("x\n", encoding="utf-8")
        locked.chmod(0o000)

    assert not any(temp_parent.iterdir())


def test_builtin_journal_runs_unjournalled_through_a_symlinked_project_root(tmp_path, monkeypatch):
    """A root reached through an alias falls back to the unjournalled upgrade."""
    from specify_cli.integrations import _lifecycle

    project = _init_project(tmp_path, "claude")
    alias = tmp_path / "alias"
    _symlink_or_skip(alias, project, directory=True)
    entered = []
    real_journalled = _lifecycle._journalled

    def journalled(*args, **kwargs):
        entered.append(args[0])
        return real_journalled(*args, **kwargs)

    monkeypatch.setattr(_lifecycle, "_journalled", journalled)

    with _lifecycle.builtin_journal(alias, "claude", []):
        pass
    with _lifecycle.builtin_journal(project, "claude", []):
        pass

    assert entered == [project]


def test_builtin_journal_removes_directories_a_failed_init_created(tmp_path):
    """Rolling back a first init into a plain directory leaves no new directories."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    project = tmp_path / "plain"
    project.mkdir()
    (project / "README.md").write_text("user file\n", encoding="utf-8")

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            for relative in (".specify/integrations/claude.manifest.json", ".claude/skills/x/SKILL.md"):
                target = project / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                write_text(target, "generated\n")
            raise OSError("disk full")

    assert sorted(path.name for path in project.iterdir()) == ["README.md"]
