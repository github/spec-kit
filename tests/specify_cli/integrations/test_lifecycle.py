"""Tests for mirrored integration CLI behavior in test_lifecycle.py."""

from __future__ import annotations

import json  # noqa: F401
import os  # noqa: F401
import shutil  # noqa: F401
import stat
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


def test_builtin_journal_removes_a_new_directory_whose_pending_write_never_landed(tmp_path):
    """A failure between before- and after-write of a file in a new directory leaves no directory."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import after_file_change, before_file_change

    project = tmp_path / "plain"
    project.mkdir()
    (project / "README.md").write_text("user file\n", encoding="utf-8")
    new_directory = project / ".claude" / "skills" / "speckit-x"

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            before_file_change(new_directory)
            new_directory.mkdir(parents=True)
            after_file_change(new_directory)
            before_file_change(new_directory / "SKILL.md")
            raise OSError("disk full")

    assert sorted(path.name for path in project.iterdir()) == ["README.md"]


def test_builtin_journal_recreates_a_file_the_operation_replaced(tmp_path):
    """A file swapped for a new one is restored as a file, never written through the new one."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import after_file_change, before_file_change

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    witness = tmp_path / "witness"
    os.link(target, witness)
    replacement = tmp_path / "replacement"
    replacement.write_text("generated\n", encoding="utf-8")
    other = tmp_path / "other-link"
    os.link(replacement, other)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            before_file_change(target)
            os.replace(replacement, target)
            after_file_change(target)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert not os.path.samefile(target, other)
    assert other.read_text(encoding="utf-8") == "generated\n"
    assert witness.read_text(encoding="utf-8") == "original\n"


def test_builtin_journal_recreates_and_reports_a_file_it_cannot_open_in_place(tmp_path, monkeypatch, capsys):
    """A file rollback cannot open for writing is recreated from its snapshot, reported, and its snapshot kept."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    from specify_cli.file_helper import FileHelper

    real_open_rewrite = FileHelper.open_rewrite

    def refuse_target(self, path):
        # Patched here, not at os.open: Windows opens through CreateFileW.
        if Path(self.root) / path == target:
            raise PermissionError("read-only")
        return real_open_rewrite(self, path)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            monkeypatch.setattr(FileHelper, "open_rewrite", refuse_target)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert _INCOMPLETE_WARNING in " ".join(capsys.readouterr().out.split())
    assert len(backups) == 1 and backups[0].is_dir()
    shutil.rmtree(backups[0])


def test_builtin_journal_leaves_a_file_intact_when_its_snapshot_cannot_be_read(tmp_path, monkeypatch):
    """An unreadable snapshot must not empty the live file or its hard links."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    link = tmp_path / "link"
    os.link(target, link)
    from specify_cli.file_helper import FileHelper

    real_open_read = FileHelper.open_read

    def refuse_snapshot(self, path):
        if any(parent in backups for parent in (Path(self.root), *Path(self.root).parents)):
            raise PermissionError("unreadable snapshot")
        return real_open_read(self, path)

    with pytest.raises(Exception, match="rollback failed"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            monkeypatch.setattr(FileHelper, "open_read", refuse_snapshot)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "generated\n"
    assert link.read_text(encoding="utf-8") == "generated\n"
    for backup in backups:
        shutil.rmtree(backup)


_INCOMPLETE_WARNING = "timestamps, extended attributes or file flags"


def _record_rollback_backups(monkeypatch):
    from specify_cli.integrations import _lifecycle

    original_mkdtemp = _lifecycle.tempfile.mkdtemp
    backups = []

    def record_backup(*args, **kwargs):
        path = original_mkdtemp(*args, **kwargs)
        if kwargs.get("prefix") == "speckit-integration-rollback-":
            backups.append(Path(path))
        return path

    monkeypatch.setattr(_lifecycle.tempfile, "mkdtemp", record_backup)
    return backups


def test_builtin_journal_never_writes_a_different_file_open_returned(tmp_path, monkeypatch, capsys):
    """A descriptor that is not the snapshotted file is neither truncated nor written."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    decoy = tmp_path / "decoy"
    decoy.write_text("decoy\n", encoding="utf-8")
    from contextlib import contextmanager

    from specify_cli.file_helper import FileHelper

    real_open_rewrite = FileHelper.open_rewrite
    opened = []

    @contextmanager
    def open_decoy(self, path):
        # Patched here, not at os.open: Windows opens through CreateFileW.
        if Path(self.root) / path != target:
            with real_open_rewrite(self, path) as descriptor:
                yield descriptor
            return
        opened.append(path)
        descriptor = os.open(decoy, os.O_WRONLY | getattr(os, "O_BINARY", 0))
        try:
            yield descriptor
        finally:
            os.close(descriptor)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            monkeypatch.setattr(FileHelper, "open_rewrite", open_decoy)
            raise OSError("disk full")

    assert opened
    assert decoy.read_text(encoding="utf-8") == "decoy\n"
    # A descriptor on another file means the path cannot be trusted, so it is
    # kept as a conflict, with its snapshot, rather than recreated.
    assert target.read_text(encoding="utf-8") == "generated\n"
    assert not os.path.samefile(target, decoy)
    assert "Preserved concurrent edits" in " ".join(capsys.readouterr().out.split())
    assert len(backups) == 1 and backups[0].is_dir()
    for backup in backups:
        shutil.rmtree(backup)


def test_builtin_journal_keeps_restoring_after_a_metadata_refusal(tmp_path, monkeypatch, capsys):
    """A file whose times cannot be set still gets its bytes, and later entries are restored."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import make_directories, write_text

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    first = project / ".specify" / "templates" / "spec.md"
    first.parent.mkdir(parents=True)
    first.write_text("first original\n", encoding="utf-8")
    created = project / ".specify" / "templates" / "new"
    refused = project / ".specify" / "templates" / "plan.md"
    refused.write_text("refused original\n", encoding="utf-8")
    refused_inode = refused.stat().st_ino
    from specify_cli.file_helper import FileHelper

    real_utime = FileHelper.utime
    real_futime = _lifecycle.futime

    def refuse_refused(self, path, **kwargs):
        if Path(self.root) / path == refused:
            raise PermissionError("not the owner")
        return real_utime(self, path, **kwargs)

    def refuse_refused_descriptor(descriptor, **kwargs):
        if os.fstat(descriptor).st_ino == refused_inode:
            raise PermissionError("not the owner")
        return real_futime(descriptor, **kwargs)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(first, "first generated\n")
            make_directories(created)
            write_text(created / "file.md", "new\n")
            # Restored first, as rollback runs newest first.
            write_text(refused, "refused generated\n")
            monkeypatch.setattr(FileHelper, "utime", refuse_refused)
            monkeypatch.setattr(_lifecycle, "futime", refuse_refused_descriptor)
            raise OSError("disk full")

    assert refused.read_text(encoding="utf-8") == "refused original\n"
    assert refused.stat().st_ino == refused_inode
    assert first.read_text(encoding="utf-8") == "first original\n"
    assert not created.exists()
    assert _INCOMPLETE_WARNING in " ".join(capsys.readouterr().out.split())
    assert len(backups) == 1 and backups[0].is_dir()
    shutil.rmtree(backups[0])


@pytest.mark.skipif(os.name == "nt", reason="POSIX modes and symlinks")
def test_builtin_journal_never_restores_metadata_through_a_path_swapped_for_a_symlink(
    tmp_path, monkeypatch, capsys,
):
    """Times set by path after the copy cannot be redirected by a path swapped for a symlink."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    target.chmod(0o600)
    os.utime(target, ns=(1_000_000_000, 1_000_000_000))
    witness = tmp_path / "witness"
    os.link(target, witness)
    victim = tmp_path / "victim"
    victim.write_text("victim\n", encoding="utf-8")
    victim.chmod(0o644)
    victim_before = victim.stat()
    real_copy = _lifecycle._copy_descriptor

    def copy_then_swap(source, destination):
        # Once the bytes are back, swap the path for a symlink, so any
        # metadata restored by path from here on lands on the victim.
        real_copy(source, destination)
        target.unlink()
        target.symlink_to(victim)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            monkeypatch.setattr(_lifecycle, "_copy_descriptor", copy_then_swap)
            raise OSError("disk full")

    victim_after = victim.stat()
    assert stat.S_IMODE(victim_after.st_mode) == 0o644
    assert victim_after.st_mtime_ns == victim_before.st_mtime_ns
    assert victim.read_text(encoding="utf-8") == "victim\n"
    assert witness.read_text(encoding="utf-8") == "original\n"
    # The times were not restored by path through the swapped-in symlink.
    assert witness.stat().st_mtime_ns != 1_000_000_000
    assert _INCOMPLETE_WARNING in " ".join(capsys.readouterr().out.split())
    assert len(backups) == 1 and backups[0].is_dir()
    shutil.rmtree(backups[0])


@pytest.mark.skipif(os.name != "nt", reason="Windows sharing semantics")
def test_windows_open_file_cannot_be_replaced_while_rollback_holds_it(tmp_path):
    """Rollback sets times by path on Windows only while its verified handle pins that path."""
    parent = tmp_path / "parent"
    parent.mkdir()
    target = parent / "plan.md"
    target.write_text("original\n", encoding="utf-8")
    replacement = tmp_path / "replacement"
    replacement.write_text("replacement\n", encoding="utf-8")
    descriptor = os.open(target, os.O_WRONLY | getattr(os, "O_BINARY", 0))
    try:
        with pytest.raises(PermissionError):
            os.replace(replacement, target)
        with pytest.raises(PermissionError):
            os.remove(target)
        with pytest.raises(PermissionError):
            os.rename(parent, tmp_path / "moved")
        os.utime(target, ns=(1_000_000_000, 2_000_000_000))
        os.chmod(target, stat.S_IREAD | stat.S_IWRITE)
    finally:
        os.close(descriptor)
    assert target.stat().st_mtime_ns == 2_000_000_000
    assert target.read_text(encoding="utf-8") == "original\n"


def _user_xattrs(path):
    return {
        name: os.getxattr(path, name)
        for name in os.listxattr(path)
        if name.startswith("user.")
    }


@pytest.mark.skipif(not hasattr(os, "setxattr"), reason="no extended-attribute API in the os module")
def test_builtin_journal_restores_extended_attributes_in_place(tmp_path):
    """Attributes a journalled copy2() put onto an existing file are put back."""
    import errno

    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import after_file_change, before_file_change

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    try:
        os.setxattr(target, "user.origin", b"original")
    except OSError as exc:
        if exc.errno in (errno.ENOTSUP, errno.EOPNOTSUPP):
            pytest.skip("filesystem has no user extended attributes")
        raise
    os.setxattr(target, "user.kept", b"kept")
    witness = tmp_path / "witness"
    os.link(target, witness)
    source = tmp_path / "source"
    source.write_text("generated\n", encoding="utf-8")
    os.setxattr(source, "user.origin", b"generated")
    os.setxattr(source, "user.added", b"added")

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            before_file_change(target)
            shutil.copy2(source, target)
            after_file_change(target)
            assert _user_xattrs(target)["user.added"] == b"added"
            raise OSError("disk full")

    assert os.path.samefile(target, witness)
    assert target.read_text(encoding="utf-8") == "original\n"
    assert _user_xattrs(target) == {"user.origin": b"original", "user.kept": b"kept"}


@pytest.mark.skipif(not hasattr(os, "setxattr"), reason="no extended-attribute API in the os module")
def test_builtin_journal_restores_other_attributes_after_one_is_refused(tmp_path, monkeypatch, capsys):
    """One refused attribute is reported without leaving the others changed."""
    import errno

    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import after_file_change, before_file_change

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    try:
        os.setxattr(target, "user.a", b"original")
    except OSError as exc:
        if exc.errno in (errno.ENOTSUP, errno.EOPNOTSUPP):
            pytest.skip("filesystem has no user extended attributes")
        raise
    os.setxattr(target, "user.z", b"original")
    source = tmp_path / "source"
    source.write_text("generated\n", encoding="utf-8")
    for name in ("user.a", "user.z", "user.added"):
        os.setxattr(source, name, b"generated")
    real_setxattr = os.setxattr

    def refuse_a(target, name, *args, **kwargs):
        if name == "user.a":
            raise PermissionError("refused")
        return real_setxattr(target, name, *args, **kwargs)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            before_file_change(target)
            shutil.copy2(source, target)
            after_file_change(target)
            monkeypatch.setattr(_lifecycle.os, "setxattr", refuse_a)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert _user_xattrs(target) == {"user.a": b"generated", "user.z": b"original"}
    assert _INCOMPLETE_WARNING in " ".join(capsys.readouterr().out.split())
    assert len(backups) == 1 and backups[0].is_dir()
    shutil.rmtree(backups[0])


def test_builtin_journal_never_writes_through_a_replacement_that_reuses_the_inode(tmp_path):
    """An unlinked original cannot lend its inode to a replacement while rollback relies on it."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import after_file_change, before_file_change

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    other = tmp_path / "other-link"

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            before_file_change(target)
            # No other link keeps the original alive, so without a pin its
            # inode is free for the replacement created straight after.
            target.unlink()
            target.write_text("generated\n", encoding="utf-8")
            os.link(target, other)
            after_file_change(target)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert not os.path.samefile(target, other)
    assert other.read_text(encoding="utf-8") == "generated\n"


_PINS_FILES = os.name != "nt"

@pytest.mark.skipif(not _PINS_FILES, reason="Windows files are never pinned")
def test_builtin_journal_recreates_and_reports_a_file_it_could_not_pin(tmp_path, monkeypatch, capsys):
    """A file without a pin is recreated from its snapshot, not written in place, and reported."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    backups = _record_rollback_backups(monkeypatch)
    monkeypatch.setattr(_lifecycle, "_MAX_PINNED_FILES", 0)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    witness = tmp_path / "witness"
    os.link(target, witness)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert not os.path.samefile(target, witness)
    assert witness.read_text(encoding="utf-8") == "generated\n"
    assert _INCOMPLETE_WARNING in " ".join(capsys.readouterr().out.split())
    assert len(backups) == 1 and backups[0].is_dir()
    shutil.rmtree(backups[0])


@pytest.mark.skipif(not _PINS_FILES or not os.path.isdir("/dev/fd"), reason="no pins, or no /dev/fd to count them")
@pytest.mark.parametrize("fails", [True, False])
def test_builtin_journal_releases_its_pins(tmp_path, fails):
    """The descriptors pinning snapshotted files close whether the operation fails or commits."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    project = tmp_path / "plain"
    targets = [project / ".specify" / "templates" / f"{name}.md" for name in ("plan", "spec")]
    targets[0].parent.mkdir(parents=True)
    for target in targets:
        target.write_text("original\n", encoding="utf-8")
    before = len(os.listdir("/dev/fd"))

    try:
        with _lifecycle.builtin_journal(project, "claude", {}):
            for target in targets:
                write_text(target, "generated\n")
            assert len(os.listdir("/dev/fd")) >= before + len(targets)
            if fails:
                raise OSError("disk full")
    except OSError:
        assert fails

    assert len(os.listdir("/dev/fd")) == before
    expected = "original\n" if fails else "generated\n"
    assert all(target.read_text(encoding="utf-8") == expected for target in targets)


@pytest.mark.skipif(
    not hasattr(os, "chflags") or not hasattr(stat, "UF_NODUMP"), reason="no BSD file flags",
)
@pytest.mark.parametrize(
    "source_flags", [0, stat.UF_NODUMP if hasattr(stat, "UF_NODUMP") else 0], ids=["cleared", "kept"],
)
def test_builtin_journal_reports_file_flags_it_cannot_restore(tmp_path, monkeypatch, capsys, source_flags):
    """BSD flags a journalled copy2() cleared are reported, with the snapshots kept."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import after_file_change, before_file_change

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    try:
        os.chflags(target, stat.UF_NODUMP)
    except OSError:
        pytest.skip("filesystem refuses UF_NODUMP")
    witness = tmp_path / "witness"
    os.link(target, witness)
    source = tmp_path / "source"
    source.write_text("generated\n", encoding="utf-8")
    os.chflags(source, source_flags)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            before_file_change(target)
            shutil.copy2(source, target)
            after_file_change(target)
            assert target.stat().st_flags & stat.UF_NODUMP == source_flags
            raise OSError("disk full")

    assert os.path.samefile(target, witness)
    assert target.read_text(encoding="utf-8") == "original\n"
    warned = _INCOMPLETE_WARNING in " ".join(capsys.readouterr().out.split())
    if source_flags:
        assert not warned
        assert backups and not backups[0].exists()
    else:
        assert warned
        assert len(backups) == 1 and backups[0].is_dir()
        shutil.rmtree(backups[0])


_ACCESS_ACL = "system.posix_acl_access"


def _access_acl(uid: int, owner: int = 6) -> bytes:
    """A POSIX access ACL granting ``uid`` read access, with mask and mode bits ``owner``-r--r--."""
    import struct

    undefined = 0xFFFFFFFF
    entries = [(0x01, owner, undefined), (0x02, 4, uid), (0x04, 4, undefined), (0x10, 4, undefined),
               (0x20, 4, undefined)]
    return struct.pack("<I", 2) + b"".join(struct.pack("<HHI", *entry) for entry in entries)


@pytest.mark.skipif(not hasattr(os, "setxattr"), reason="no extended-attribute API in the os module")
@pytest.mark.parametrize("original_acl", [None, _access_acl(1001)], ids=["no-acl", "acl"])
def test_builtin_journal_restores_the_access_acl_in_place(tmp_path, original_acl):
    """A POSIX access ACL a journalled copy2() brought in is removed or set back."""
    import errno

    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import after_file_change, before_file_change

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    target.chmod(0o644)
    source = tmp_path / "source"
    source.write_text("generated\n", encoding="utf-8")
    source.chmod(0o644)
    try:
        os.setxattr(source, _ACCESS_ACL, _access_acl(1002))
    except OSError as exc:
        if exc.errno in (errno.ENOTSUP, errno.EOPNOTSUPP):
            pytest.skip("filesystem has no POSIX ACLs")
        raise
    if original_acl is not None:
        os.setxattr(target, _ACCESS_ACL, original_acl)
    before = os.getxattr(target, _ACCESS_ACL) if original_acl is not None else None
    witness = tmp_path / "witness"
    os.link(target, witness)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            before_file_change(target)
            shutil.copy2(source, target)
            after_file_change(target)
            assert os.getxattr(target, _ACCESS_ACL) == os.getxattr(source, _ACCESS_ACL)
            raise OSError("disk full")

    assert os.path.samefile(target, witness)
    assert target.read_text(encoding="utf-8") == "original\n"
    assert stat.S_IMODE(target.stat().st_mode) == 0o644
    if before is None:
        assert _ACCESS_ACL not in os.listxattr(target)
    else:
        assert os.getxattr(target, _ACCESS_ACL) == before


def test_builtin_journal_recreates_a_file_the_operation_removed_and_rewrote(tmp_path):
    """A file observed as removed is recreated on rollback, never written through what replaced it."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import unlink, write_text

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    other = tmp_path / "other-link"

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            unlink(target)
            write_text(target, "generated\n")
            os.link(target, other)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert not os.path.samefile(target, other)
    assert other.read_text(encoding="utf-8") == "generated\n"


@pytest.mark.skipif(not hasattr(os, "setxattr"), reason="no extended-attribute API in the os module")
def test_builtin_journal_restores_user_attributes_before_a_read_only_access_acl(tmp_path, monkeypatch):
    """The access ACL goes back after the user attributes, so its mode bits cannot refuse them."""
    import errno

    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import after_file_change, before_file_change

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    try:
        os.setxattr(target, "user.origin", b"original")
        os.setxattr(target, _ACCESS_ACL, _access_acl(1001, owner=4))
    except OSError as exc:
        if exc.errno in (errno.ENOTSUP, errno.EOPNOTSUPP):
            pytest.skip("filesystem has no user extended attributes or POSIX ACLs")
        raise
    before = os.getxattr(target, _ACCESS_ACL)
    assert stat.S_IMODE(target.stat().st_mode) == 0o444
    source = tmp_path / "source"
    source.write_text("generated\n", encoding="utf-8")
    source.chmod(0o644)
    os.setxattr(source, "user.origin", b"generated")
    real_restorable_xattrs = _lifecycle._restorable_xattrs

    def acl_first(*args, **kwargs):
        # ext4 lists user attributes first; other filesystems need not. Only
        # the journal's own reads are reordered: patching os.listxattr would
        # reorder shutil.copystat() too, and Python before 3.13 raises when it
        # copies a read-only ACL before the user attributes.
        attributes = real_restorable_xattrs(*args, **kwargs)
        return dict(sorted(attributes.items(), key=lambda item: item[0] != _ACCESS_ACL))

    monkeypatch.setattr(_lifecycle, "_restorable_xattrs", acl_first)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            before_file_change(target)
            target.chmod(0o644)
            shutil.copy2(source, target)
            after_file_change(target)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert _user_xattrs(target) == {"user.origin": b"original"}
    assert stat.S_IMODE(target.stat().st_mode) == 0o444
    assert os.getxattr(target, _ACCESS_ACL) == before


def test_builtin_journal_restores_in_place_after_copying_an_older_template(tmp_path):
    """A copy2() from an older source, which can move a file's birth time back, still restores in place."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import after_file_change, before_file_change

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    witness = tmp_path / "witness"
    os.link(target, witness)
    source = tmp_path / "source"
    source.write_text("generated\n", encoding="utf-8")
    os.utime(source, ns=(1_000_000_000, 1_000_000_000))

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            before_file_change(target)
            shutil.copy2(source, target)
            after_file_change(target)
            raise OSError("disk full")

    assert os.path.samefile(target, witness)
    assert target.read_text(encoding="utf-8") == "original\n"


@pytest.mark.skipif(not _PINS_FILES, reason="Windows files are never pinned")
def test_builtin_journal_recreates_an_unpinned_replaced_file_without_a_warning(tmp_path, monkeypatch, capsys):
    """Past the pin limit, a file the operation replaced is recreated as a complete restore."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import after_file_change, before_file_change

    backups = _record_rollback_backups(monkeypatch)
    monkeypatch.setattr(_lifecycle, "_MAX_PINNED_FILES", 0)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    replacement = tmp_path / "replacement"
    replacement.write_text("generated\n", encoding="utf-8")

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            before_file_change(target)
            os.replace(replacement, target)
            after_file_change(target)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert _INCOMPLETE_WARNING not in " ".join(capsys.readouterr().out.split())
    assert backups and not backups[0].exists()


def test_builtin_journal_restores_the_original_modification_time(tmp_path, monkeypatch, capsys):
    """A rewritten file comes back with its saved modification time and no incomplete-restore warning."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    saved_mtime = 1_500_000_000_000_000_000
    os.utime(target, ns=(saved_mtime, saved_mtime))
    witness = tmp_path / "witness"
    os.link(target, witness)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            assert target.stat().st_mtime_ns != saved_mtime
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert target.stat().st_mtime_ns == saved_mtime
    assert os.path.samefile(target, witness)
    assert _INCOMPLETE_WARNING not in " ".join(capsys.readouterr().out.split())
    assert backups and not backups[0].exists()


@pytest.mark.skipif(not _PINS_FILES, reason="Windows files are never pinned")
def test_builtin_journal_pins_a_file_before_snapshotting_it(tmp_path, monkeypatch):
    """The original is pinned before it is snapshotted, so one replaced meanwhile is never taken for it."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    replacement = tmp_path / "replacement"
    replacement.write_text("replacement\n", encoding="utf-8")
    other = tmp_path / "other-link"
    os.link(replacement, other)
    real_snapshot = _lifecycle._FileJournal._snapshot
    pins = []

    def swap_during_snapshot(self, source, destination):
        real_snapshot(self, source, destination)
        if source == target:
            pins.append(source in self.pinned_files)
            os.replace(replacement, target)

    monkeypatch.setattr(_lifecycle._FileJournal, "_snapshot", swap_during_snapshot)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            raise OSError("disk full")

    assert pins == [True]
    assert target.read_text(encoding="utf-8") == "original\n"
    assert not os.path.samefile(target, other)
    # The operation's own write went through the replacement; rollback left it as that write made it.
    assert other.read_text(encoding="utf-8") == "generated\n"


@pytest.mark.skipif(not _PINS_FILES, reason="rollback pins files only outside Windows")
def test_builtin_journal_snapshots_a_replaced_file_from_its_path_when_its_parent_is_removed(tmp_path, capsys):
    """A parent snapshotted after its journalled child was rewritten and replaced holds the replacement, not the pinned file."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import changing_file, write_text

    project = tmp_path / "plain"
    directory = project / ".specify" / "templates"
    target = directory / "plan.md"
    directory.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    replacement = tmp_path / "replacement"

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            replacement.write_text("replacement\n", encoding="utf-8")
            with changing_file(target):
                os.replace(replacement, target)
            with changing_file(directory, removal=True):
                shutil.rmtree(directory)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert "Preserved concurrent edits" not in capsys.readouterr().out


@pytest.mark.skipif(not _PINS_FILES, reason="Windows files cannot be replaced while open")
def test_builtin_journal_keeps_the_snapshot_when_the_path_is_replaced_during_restore(tmp_path, monkeypatch, capsys):
    """A path swapped for another file while its bytes are restored is reported, kept, and not overwritten."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    replacement = tmp_path / "replacement"
    replacement.write_text("concurrent\n", encoding="utf-8")
    real_restore_metadata = _lifecycle._restore_metadata

    def swap_after_copy(*args, **kwargs):
        result = real_restore_metadata(*args, **kwargs)
        os.replace(replacement, target)
        return result

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            monkeypatch.setattr(_lifecycle, "_restore_metadata", swap_after_copy)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "concurrent\n"
    warning = " ".join(capsys.readouterr().out.split())
    assert _INCOMPLETE_WARNING in warning
    # The path still holds the concurrent file, so the warning must not claim its contents came back.
    assert "Could not fully restore" in warning and "their contents" in warning
    assert len(backups) == 1 and backups[0].is_dir()
    shutil.rmtree(backups[0])


@pytest.mark.parametrize("edit", ["append", "same-size"])
def test_builtin_journal_refuses_a_file_edited_in_place_while_it_is_snapshotted(tmp_path, monkeypatch, edit):
    """A snapshot taken while the file changed in place may hold mixed bytes, so the write is refused."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text
    from specify_cli.integrations.installer import IntegrationInstallError

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    # Bytes, so the same-size edit matches on Windows too, where text mode
    # would write a carriage return.
    target.write_bytes(b"original\n")
    os.utime(target, ns=(1_000_000_000, 1_000_000_000))
    real_snapshot = _lifecycle._FileJournal._snapshot

    def edit_during_snapshot(self, source, destination):
        real_snapshot(self, source, destination)
        if source == target:
            with target.open("ab" if edit == "append" else "r+b") as stream:
                stream.write(b"user edit\n" if edit == "append" else b"ORIGINAL\n")
            if edit == "same-size":
                os.utime(target, ns=(1_000_000_000, 2_000_000_000))

    monkeypatch.setattr(_lifecycle._FileJournal, "_snapshot", edit_during_snapshot)

    with pytest.raises(IntegrationInstallError, match="changed during the operation"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")

    edited = b"original\nuser edit\n" if edit == "append" else b"ORIGINAL\n"
    assert target.read_bytes() == edited


@pytest.mark.skipif(not _PINS_FILES, reason="Windows files cannot be replaced while open")
def test_builtin_journal_keeps_a_file_replaced_before_its_in_place_restore_opens_it(tmp_path, monkeypatch, capsys):
    """A path replaced after the content check is a conflict, never an untouched file to recreate."""
    from specify_cli.file_helper import FileHelper
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    replacement = tmp_path / "replacement"
    replacement.write_text("concurrent\n", encoding="utf-8")
    real_open_rewrite = FileHelper.open_rewrite

    def replace_then_open(self, path):
        if Path(self.root) / path == target and replacement.exists():
            os.replace(replacement, target)
        return real_open_rewrite(self, path)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            monkeypatch.setattr(FileHelper, "open_rewrite", replace_then_open)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "concurrent\n"
    assert "Preserved concurrent edits" in " ".join(capsys.readouterr().out.split())
    assert len(backups) == 1 and backups[0].is_dir()
    shutil.rmtree(backups[0])


def test_builtin_journal_keeps_a_file_replaced_before_it_is_recreated(tmp_path, monkeypatch, capsys):
    """A path replaced between the content check and the fallback recreate is kept as a conflict."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import after_file_change, before_file_change

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    generated = tmp_path / "generated"
    generated.write_text("generated\n", encoding="utf-8")
    concurrent = tmp_path / "concurrent"
    concurrent.write_text("concurrent\n", encoding="utf-8")
    real_restore = _lifecycle._restore_file_in_place

    def restore_then_replace(path, *args, **kwargs):
        result = real_restore(path, *args, **kwargs)
        if path == target:
            os.replace(concurrent, target)
        return result

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            before_file_change(target)
            # The operation replaces the file, so rollback recreates it.
            os.replace(generated, target)
            after_file_change(target)
            monkeypatch.setattr(_lifecycle, "_restore_file_in_place", restore_then_replace)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "concurrent\n"
    assert "Preserved concurrent edits" in " ".join(capsys.readouterr().out.split())
    assert len(backups) == 1 and backups[0].is_dir()
    shutil.rmtree(backups[0])


@pytest.mark.parametrize("edit", [
    "mtime",
    pytest.param("mode", marks=pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits")),
])
def test_builtin_journal_keeps_a_metadata_edit_made_after_the_operation_wrote(tmp_path, monkeypatch, capsys, edit):
    """A mode or time changed after the operation's write is kept as a conflict, not silently undone."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    target.chmod(0o644)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            if edit == "mode":
                target.chmod(0o600)
            else:
                os.utime(target, ns=(1_000_000_000, 1_000_000_000))
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "generated\n"
    if edit == "mode":
        assert stat.S_IMODE(target.stat().st_mode) == 0o600
    else:
        assert target.stat().st_mtime_ns == 1_000_000_000
    assert "Preserved concurrent edits" in " ".join(capsys.readouterr().out.split())
    assert len(backups) == 1 and backups[0].is_dir()
    shutil.rmtree(backups[0])


@pytest.mark.skipif(not hasattr(os, "setxattr"), reason="no extended-attribute API in the os module")
def test_builtin_journal_keeps_an_attribute_edit_made_after_the_operation_wrote(tmp_path, monkeypatch, capsys):
    """A user attribute set after the operation's write is kept as a conflict."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    try:
        os.setxattr(target, "user.probe", b"1")
        os.removexattr(target, "user.probe")
    except OSError as exc:
        pytest.skip(f"user attributes unsupported here: {exc}")

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            os.setxattr(target, "user.label", b"mine")
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "generated\n"
    assert os.getxattr(target, "user.label") == b"mine"
    assert "Preserved concurrent edits" in " ".join(capsys.readouterr().out.split())
    shutil.rmtree(backups[0])


def _fake_xattrs(monkeypatch, target, attributes):
    """Report ``attributes`` on ``target`` and none elsewhere, with or without an os xattr API."""
    from specify_cli.integrations import _lifecycle

    original = target.stat()

    def restorable(path, journal=None):
        # The target by path, or through a descriptor still on its original
        # inode, as a pinned snapshot reads it.
        if isinstance(path, Path) and path == target:
            return dict(attributes)
        if isinstance(path, int) and os.path.samestat(os.fstat(path), original):
            return dict(attributes)
        return {}

    monkeypatch.setattr(_lifecycle, "_HAS_XATTRS", True)
    monkeypatch.setattr(_lifecycle, "_restorable_xattrs", restorable)
    # Setting them on the snapshot copy is a no-op: its filesystem keeps none.
    monkeypatch.setattr(os, "setxattr", lambda *args, **kwargs: None, raising=False)
    monkeypatch.setattr(os, "removexattr", lambda *args, **kwargs: None, raising=False)


def test_builtin_journal_persists_captured_attributes_beside_the_snapshot(tmp_path, monkeypatch):
    """Captured attributes are written to a sidecar, so a retained snapshot keeps them after the process exits."""
    import base64

    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    _fake_xattrs(monkeypatch, target, {"user.label": b"\x00mine", "system.posix_acl_access": b"acl"})

    with _lifecycle.builtin_journal(project, "claude", {}):
        write_text(target, "generated\n")
        sidecars = list((backups[0] / "writes").glob("*.xattrs.json"))
        assert len(sidecars) == 1
        record = json.loads(sidecars[0].read_text(encoding="utf-8"))
        if os.name != "nt":
            assert stat.S_IMODE(sidecars[0].stat().st_mode) == 0o600

    assert record["path"] == str(target)
    assert {name: base64.b64decode(value) for name, value in record["attributes"].items()} == {
        "user.label": b"\x00mine", "system.posix_acl_access": b"acl",
    }


def test_builtin_journal_refuses_the_write_when_attributes_cannot_be_persisted(tmp_path, monkeypatch):
    """A sidecar that cannot be written fails the operation before it writes the file."""
    from specify_cli.file_helper import FileHelper
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    _fake_xattrs(monkeypatch, target, {"user.label": b"mine"})

    def refuse(self, path, content):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(FileHelper, "create_private_bytes", refuse)
    with pytest.raises(OSError, match="No space left"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")

    assert target.read_text(encoding="utf-8") == "original\n"


def test_builtin_journal_sets_times_after_the_write_handle_closes(tmp_path, monkeypatch, capsys):
    """A last-write time moved by closing the write handle (as Windows can) is set back afterwards."""
    from contextlib import contextmanager

    from specify_cli.file_helper import FileHelper
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    os.utime(target, ns=(1_000_000_000, 1_000_000_000))
    real_open_rewrite = FileHelper.open_rewrite

    @contextmanager
    def move_time_on_close(self, path):
        with real_open_rewrite(self, path) as descriptor:
            yield descriptor
            if Path(self.root) / path == target:
                # What closing a written handle can do on Windows.
                os.utime(target, ns=(3_000_000_000, 3_000_000_000))

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            monkeypatch.setattr(FileHelper, "open_rewrite", move_time_on_close)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert target.stat().st_mtime_ns == 1_000_000_000
    assert _INCOMPLETE_WARNING not in " ".join(capsys.readouterr().out.split())


@pytest.mark.skipif(not _PINS_FILES, reason="Windows sets times by path while its handle pins the file")
def test_builtin_journal_never_sets_times_on_a_file_renamed_over_the_path(tmp_path, monkeypatch):
    """Times go through the verified descriptor, so a regular file renamed over the path keeps its own."""
    from specify_cli.file_helper import FileHelper
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    os.utime(target, ns=(1_000_000_000, 1_000_000_000))
    other = tmp_path / "other"
    other.write_text("other\n", encoding="utf-8")
    os.utime(other, ns=(5_000_000_000, 5_000_000_000))
    witness = tmp_path / "witness"
    os.link(other, witness)
    real_utime = FileHelper.utime
    real_futime = _lifecycle.futime

    def rename_then(set_times):
        def swap(*args, **kwargs):
            if other.exists():
                os.replace(other, target)
            return set_times(*args, **kwargs)
        return swap

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            monkeypatch.setattr(FileHelper, "utime", rename_then(real_utime))
            monkeypatch.setattr(_lifecycle, "futime", rename_then(real_futime))
            raise OSError("disk full")

    assert witness.stat().st_mtime_ns == 5_000_000_000


@pytest.mark.skipif(
    not hasattr(os, "chflags") or not hasattr(stat, "UF_HIDDEN"), reason="no BSD file flags",
)
def test_builtin_journal_recreates_a_replaced_pinned_file_with_its_flags(tmp_path, capsys):
    """A pinned file's snapshot carries its BSD flags, so recreating a replaced file keeps them."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import after_file_change, before_file_change

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    try:
        os.chflags(target, stat.UF_HIDDEN)
    except OSError as exc:
        pytest.skip(f"cannot set file flags here: {exc}")
    replacement = tmp_path / "replacement"
    replacement.write_text("generated\n", encoding="utf-8")

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            before_file_change(target)
            os.replace(replacement, target)
            after_file_change(target)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert target.stat().st_flags & stat.UF_HIDDEN


@pytest.mark.skipif(not _PINS_FILES, reason="Windows files are never pinned")
def test_builtin_journal_gives_up_a_pin_when_the_snapshot_runs_out_of_descriptors(tmp_path, monkeypatch, capsys):
    """A copy that hits the open-file limit is retried without the pin, and no more files are pinned."""
    import errno

    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    targets = [project / ".specify" / "templates" / f"{name}.md" for name in ("plan", "spec")]
    targets[0].parent.mkdir(parents=True)
    for target in targets:
        target.write_text("original\n", encoding="utf-8")
    real_snapshot_pinned = _lifecycle._FileJournal._snapshot_pinned
    attempts = []

    def exhausted(self, pinned, destination):
        attempts.append(destination)
        if len(attempts) == 1:
            destination.write_bytes(b"partial")
            raise OSError(errno.EMFILE, "Too many open files")
        return real_snapshot_pinned(self, pinned, destination)

    monkeypatch.setattr(_lifecycle._FileJournal, "_snapshot_pinned", exhausted)
    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            for target in targets:
                write_text(target, "generated\n")
            raise OSError("disk full")

    # Only the first snapshot was attempted through a pin; the second file was never pinned.
    assert len(attempts) == 1
    assert all(target.read_text(encoding="utf-8") == "original\n" for target in targets)
    warning = " ".join(capsys.readouterr().out.split())
    assert _INCOMPLETE_WARNING in warning
    # The warning names each affected path's snapshot.
    assert "writes/0 is" in warning
    shutil.rmtree(backups[0])


def test_restorable_xattrs_stops_reading_once_the_budget_is_spent(monkeypatch):
    """The snapshot budget is charged per attribute, so the rest are never read into memory."""
    import types

    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations.installer import IntegrationInstallError

    names = [f"user.a{index}" for index in range(10)]
    read = []

    def getxattr(target, name, **kwargs):
        read.append(name)
        return b"x" * 1024

    monkeypatch.setattr(_lifecycle.os, "listxattr", lambda target, **kwargs: names, raising=False)
    monkeypatch.setattr(_lifecycle.os, "getxattr", getxattr, raising=False)
    journal = types.SimpleNamespace(backup_bytes=_lifecycle._MAX_BACKUP_BYTES - 2048)
    with pytest.raises(IntegrationInstallError, match="budget exceeded"):
        _lifecycle._restorable_xattrs(3, journal)
    assert len(read) == 2


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits")
def test_builtin_journal_keeps_a_mode_changed_between_repeated_after_notifications(tmp_path, monkeypatch, capsys):
    """A second after-notification with no write in between keeps the metadata the write left."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import after_file_change, before_file_change

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    target.chmod(0o600)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            before_file_change(target)
            target.write_text("generated\n", encoding="utf-8")
            after_file_change(target)
            target.chmod(0o644)  # someone else's change
            after_file_change(target)  # as record_existing() sends after write_file_and_record()
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "generated\n"
    assert stat.S_IMODE(target.stat().st_mode) == 0o644
    assert "Preserved concurrent edits" in " ".join(capsys.readouterr().out.split())
    shutil.rmtree(backups[0])


@pytest.mark.skipif(
    not hasattr(os, "chflags") or not hasattr(stat, "UF_NODUMP"), reason="no BSD file flags",
)
def test_builtin_journal_keeps_a_file_flag_set_after_the_operation_wrote(tmp_path, monkeypatch, capsys):
    """A BSD flag set after the operation's write is kept as a conflict, not undone."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            os.chflags(target, target.stat().st_flags | stat.UF_NODUMP)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "generated\n"
    assert target.stat().st_flags & stat.UF_NODUMP
    assert "Preserved concurrent edits" in " ".join(capsys.readouterr().out.split())
    os.chflags(target, target.stat().st_flags & ~stat.UF_NODUMP)
    shutil.rmtree(backups[0])


def test_builtin_journal_keeps_an_in_place_edit_made_just_before_the_restore_opens(
    tmp_path, monkeypatch, capsys
):
    """An edit that keeps the inode, landing between the state check and the open, is not truncated."""
    from contextlib import contextmanager

    from specify_cli.file_helper import FileHelper
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    real_open_rewrite = FileHelper.open_rewrite
    edited = []

    @contextmanager
    def edit_then_open(self, path):
        if Path(self.root) / path == target and not edited:
            with target.open("r+b") as stream:  # same inode
                # Over "generated" only, leaving the line ending Windows text mode wrote.
                stream.write(b"EDITED!!!")
            os.utime(target, ns=(3_000_000_000, 3_000_000_000))
            edited.append(path)
        with real_open_rewrite(self, path) as descriptor:
            yield descriptor

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            monkeypatch.setattr(FileHelper, "open_rewrite", edit_then_open)
            raise OSError("disk full")

    assert edited
    assert target.read_text(encoding="utf-8") == "EDITED!!!\n"
    assert "Preserved concurrent edits" in " ".join(capsys.readouterr().out.split())
    for backup in backups:
        shutil.rmtree(backup)


@pytest.mark.parametrize("refused", [False, True], ids=["restored", "refused"])
def test_builtin_journal_sets_captured_attributes_on_a_recreated_file(tmp_path, monkeypatch, capsys, refused):
    """A replaced file recreated from a snapshot gets its captured attributes, or is reported incomplete."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import after_file_change, before_file_change

    backups = _record_rollback_backups(monkeypatch)
    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    replacement = tmp_path / "replacement"
    replacement.write_text("generated\n", encoding="utf-8")
    # The snapshot's filesystem keeps none of them, so only the capture has them.
    _fake_xattrs(monkeypatch, target, {"user.label": b"mine"})
    set_attributes = []

    def setxattr(descriptor, name, value, *args, **kwargs):
        if refused:
            raise OSError(1, "Operation not permitted")
        # Only what is set on the file at the target, not on its snapshot copy.
        if os.path.samestat(os.fstat(descriptor), target.stat()):
            set_attributes.append((name, value))

    monkeypatch.setattr(os, "setxattr", setxattr, raising=False)
    monkeypatch.setattr(os, "removexattr", lambda *args, **kwargs: None, raising=False)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            before_file_change(target)
            os.replace(replacement, target)
            after_file_change(target)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "original\n"
    output = " ".join(capsys.readouterr().out.split())
    if refused:
        assert _INCOMPLETE_WARNING in output
        assert len(backups) == 1 and backups[0].is_dir()
        assert list((backups[0] / "writes").glob("*.xattrs.json"))
        shutil.rmtree(backups[0])
    else:
        assert set_attributes == [("user.label", b"mine")]
        assert _INCOMPLETE_WARNING not in output


@pytest.mark.parametrize("soft, expected", [
    (400, 100),
    (1_000_000, 1024),
    (3, 0),
])
def test_pin_limit_is_a_quarter_of_the_open_file_limit_up_to_the_cap(monkeypatch, soft, expected):
    resource = pytest.importorskip("resource")
    from specify_cli.integrations import _lifecycle

    monkeypatch.setattr(resource, "getrlimit", lambda which: (soft, resource.RLIM_INFINITY))
    assert _lifecycle._pin_limit() == expected


def test_pin_limit_caps_an_unlimited_open_file_limit(monkeypatch):
    resource = pytest.importorskip("resource")
    from specify_cli.integrations import _lifecycle

    monkeypatch.setattr(resource, "getrlimit", lambda which: (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
    assert _lifecycle._pin_limit() == _lifecycle._MAX_PINNED_FILES


@pytest.mark.parametrize("failure", ["getrlimit", "import"])
def test_pin_limit_assumes_256_descriptors_when_the_limit_is_unknown(monkeypatch, failure):
    import sys

    from specify_cli.integrations import _lifecycle

    if failure == "import":
        monkeypatch.setitem(sys.modules, "resource", None)
    else:
        resource = pytest.importorskip("resource")

        def fail(which):
            raise OSError("unavailable")

        monkeypatch.setattr(resource, "getrlimit", fail)
    assert _lifecycle._pin_limit() == 64


def test_builtin_journal_restores_an_empty_attribute_set_on_a_recreated_file(tmp_path, monkeypatch, capsys):
    """A file recreated from its snapshot loses attributes it inherited when the original had none."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import after_file_change, before_file_change

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    original = target.stat()
    inherited = {"system.posix_acl_access": b"default-acl"}
    removed = []

    def restorable(subject, journal=None):
        # The original file has no attributes; any other file in its
        # directory inherits the default ACL's access ACL.
        entry = os.fstat(subject) if isinstance(subject, int) else os.lstat(subject)
        if os.path.samestat(entry, original) or not stat.S_ISREG(entry.st_mode):
            return {}
        if isinstance(subject, int) and "system.posix_acl_access" in removed:
            return {}
        return dict(inherited)

    monkeypatch.setattr(_lifecycle, "_HAS_XATTRS", True)
    monkeypatch.setattr(_lifecycle, "_restorable_xattrs", restorable)
    monkeypatch.setattr(_lifecycle.os, "setxattr", lambda *args, **kwargs: None, raising=False)
    monkeypatch.setattr(
        _lifecycle.os, "removexattr", lambda target, name, **kwargs: removed.append(name), raising=False,
    )
    replacement = target.with_name("replacement.md")
    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            before_file_change(target)
            replacement.write_text("generated\n", encoding="utf-8")
            os.replace(replacement, target)
            after_file_change(target)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert removed == ["system.posix_acl_access"]
    assert "Recovery snapshots retained" not in capsys.readouterr().out


@pytest.mark.skipif(not _PINS_FILES, reason="Windows files are never pinned")
def test_builtin_journal_charges_a_pinned_snapshot_s_attributes_as_they_are_read(tmp_path, monkeypatch):
    """A pinned file's attributes stop being read once the snapshot budget is spent."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text
    from specify_cli.integrations.installer import IntegrationInstallError

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    names = [f"user.a{index}" for index in range(10)]
    read = []

    def listxattr(subject, **kwargs):
        return names if isinstance(subject, int) or Path(subject) == target else []

    def getxattr(subject, name, **kwargs):
        read.append(name)
        return b"x" * 1024

    monkeypatch.setattr(_lifecycle, "_HAS_XATTRS", True)
    monkeypatch.setattr(_lifecycle, "_MAX_BACKUP_BYTES", 4096)
    monkeypatch.setattr(_lifecycle.os, "listxattr", listxattr, raising=False)
    monkeypatch.setattr(_lifecycle.os, "getxattr", getxattr, raising=False)
    monkeypatch.setattr(_lifecycle.os, "setxattr", lambda *args, **kwargs: None, raising=False)
    monkeypatch.setattr(_lifecycle.os, "removexattr", lambda *args, **kwargs: None, raising=False)
    snapshotted = []
    real_snapshot_pinned = _lifecycle._FileJournal._snapshot_pinned

    def through_pin(self, pinned, destination):
        snapshotted.append(destination)
        return real_snapshot_pinned(self, pinned, destination)

    monkeypatch.setattr(_lifecycle._FileJournal, "_snapshot_pinned", through_pin)
    with pytest.raises(IntegrationInstallError, match="budget exceeded"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")

    assert len(snapshotted) == 1
    # 4096 bytes less the file's own fit three 1 KiB values; the fourth is refused.
    assert len(read) == 4
    assert target.read_text(encoding="utf-8") == "original\n"


def test_builtin_journal_restores_in_place_when_a_handle_stat_reports_another_ctime(tmp_path, monkeypatch, capsys):
    """A descriptor's ``st_ctime`` differing from a path stat's (Windows) is not taken for an edit."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    real_fstat = os.fstat

    def handle_fstat(descriptor):
        # On Windows a handle's stat reports the metadata-change time as
        # st_ctime, while a path stat reports the creation time.
        entry = real_fstat(descriptor)
        if not stat.S_ISREG(entry.st_mode):
            return entry
        fields = list(entry)
        fields[9] += 1
        positional = {"st_mode", "st_ino", "st_dev", "st_nlink", "st_uid", "st_gid", "st_size"}
        extra = {
            name: getattr(entry, name) for name in dir(entry)
            if name.startswith("st_") and name not in positional
        }
        extra.update({"st_ctime_ns": entry.st_ctime_ns + 1_000_000_000, "st_ctime": entry.st_ctime + 1})
        return os.stat_result(fields[:10], extra)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            identity = (target.stat().st_dev, target.stat().st_ino)
            monkeypatch.setattr(_lifecycle.os, "fstat", handle_fstat)
            raise OSError("disk full")

    monkeypatch.undo()
    assert target.read_text(encoding="utf-8") == "original\n"
    assert (target.stat().st_dev, target.stat().st_ino) == identity
    assert "Recovery snapshots retained" not in capsys.readouterr().out
