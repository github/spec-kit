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
    real_open = os.open

    def refuse_target(path, flags, *args, **kwargs):
        if Path(path) == target and flags & os.O_WRONLY:
            raise PermissionError("read-only")
        return real_open(path, flags, *args, **kwargs)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            monkeypatch.setattr(_lifecycle.os, "open", refuse_target)
            raise OSError("disk full")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert _INCOMPLETE_WARNING in " ".join(capsys.readouterr().out.split())
    assert len(backups) == 1 and backups[0].is_dir()
    shutil.rmtree(backups[0])


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


def test_builtin_journal_never_writes_a_different_file_open_returned(tmp_path, monkeypatch):
    """A descriptor that is not the snapshotted file is neither truncated nor written."""
    from specify_cli.integrations import _lifecycle
    from specify_cli.integrations._file_changes import write_text

    project = tmp_path / "plain"
    target = project / ".specify" / "templates" / "plan.md"
    target.parent.mkdir(parents=True)
    target.write_text("original\n", encoding="utf-8")
    decoy = tmp_path / "decoy"
    decoy.write_text("decoy\n", encoding="utf-8")
    real_open = os.open
    opened = []

    def open_decoy(path, flags, *args, **kwargs):
        if Path(path) == target and flags & os.O_WRONLY:
            opened.append(path)
            return real_open(decoy, flags, *args, **kwargs)
        return real_open(path, flags, *args, **kwargs)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            monkeypatch.setattr(_lifecycle.os, "open", open_decoy)
            raise OSError("disk full")

    assert opened
    assert decoy.read_text(encoding="utf-8") == "decoy\n"
    assert target.read_text(encoding="utf-8") == "original\n"
    assert not os.path.samefile(target, decoy)


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
    real_utime = os.utime

    def refuse_refused(target, *args, **kwargs):
        if isinstance(target, int) and os.fstat(target).st_ino == refused_inode:
            raise PermissionError("not the owner")
        if not isinstance(target, int) and Path(target) == refused:
            raise PermissionError("not the owner")
        return real_utime(target, *args, **kwargs)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(first, "first generated\n")
            make_directories(created)
            write_text(created / "file.md", "new\n")
            # Restored first, as rollback runs newest first.
            write_text(refused, "refused generated\n")
            monkeypatch.setattr(_lifecycle.os, "utime", refuse_refused)
            if real_utime in os.supports_fd:
                # So rollback takes the descriptor call and meets the refusal.
                monkeypatch.setattr(_lifecycle.os, "supports_fd", os.supports_fd | {refuse_refused})
            raise OSError("disk full")

    assert refused.read_text(encoding="utf-8") == "refused original\n"
    assert refused.stat().st_ino == refused_inode
    assert first.read_text(encoding="utf-8") == "first original\n"
    assert not created.exists()
    assert _INCOMPLETE_WARNING in " ".join(capsys.readouterr().out.split())
    assert len(backups) == 1 and backups[0].is_dir()
    shutil.rmtree(backups[0])


@pytest.mark.skipif(os.name == "nt", reason="POSIX modes and symlinks")
def test_builtin_journal_never_restores_metadata_by_path_without_descriptor_support(
    tmp_path, monkeypatch, capsys,
):
    """Without descriptor-based times, a path swapped for a symlink cannot redirect them."""
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
    real_copyfileobj = shutil.copyfileobj

    def copy_then_swap(source, destination, *args, **kwargs):
        # Once the bytes are back, swap the path for a symlink, so any
        # metadata restored by path from here on lands on the victim.
        real_copyfileobj(source, destination, *args, **kwargs)
        target.unlink()
        target.symlink_to(victim)

    with pytest.raises(OSError, match="disk full"):
        with _lifecycle.builtin_journal(project, "claude", {}):
            write_text(target, "generated\n")
            monkeypatch.setattr(_lifecycle.os, "supports_fd", os.supports_fd - {os.utime})
            monkeypatch.setattr(_lifecycle.shutil, "copyfileobj", copy_then_swap)
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
