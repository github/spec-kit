"""Tests for specify_cli.integrations._file_changes."""

from __future__ import annotations

import os

import pytest

from specify_cli.integrations import _file_changes
from specify_cli.integrations.installer import IntegrationInstallError


@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("failure", ["unlink", "journal"])
def test_unlink_in_directory_propagates_errors(tmp_path, monkeypatch, fallback, failure):
    skill_file = tmp_path / "skill" / "SKILL.md"
    skill_file.parent.mkdir()
    skill_file.write_bytes(b"Generated skill")
    error = PermissionError("unlink denied") if failure == "unlink" else IntegrationInstallError("journal failed")
    unlink = os.unlink

    def unlink_or_fail(path, **kwargs):
        if path == skill_file or path == skill_file.name:
            raise error
        return unlink(path, **kwargs)

    def observe(path, before, removal):
        raise error

    if failure == "unlink":
        monkeypatch.setattr(os, "unlink", unlink_or_fail)
        monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {unlink_or_fail})
    if fallback:
        monkeypatch.setattr(os, "supports_dir_fd", set())
    token = _file_changes.file_change_observer.set(observe if failure == "journal" else None)
    try:
        with pytest.raises(type(error)) as caught:
            _file_changes.unlink_in_directory(skill_file, root=tmp_path)
    finally:
        _file_changes.file_change_observer.reset(token)

    assert caught.value is error
    assert skill_file.read_bytes() == b"Generated skill"


@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("stage", ["open", "unlink", "scan", "rmdir"])
def test_unlink_in_directory_tolerates_expected_errors(tmp_path, monkeypatch, fallback, stage):
    directory = tmp_path / "skill"
    directory.mkdir()
    skill_file = directory / "SKILL.md"
    reference = directory / "user.md"
    if stage == "open":
        directory.rmdir()
    elif stage != "unlink":
        skill_file.write_bytes(b"Generated skill")
    if fallback:
        monkeypatch.setattr(os, "supports_dir_fd", set())
    before = _file_changes.before_file_change
    after = _file_changes.after_file_change

    def before_change(path, **kwargs):
        before(path, **kwargs)
        if stage == "rmdir" and path == directory:
            reference.write_bytes(b"Concurrent user file")

    def after_change(path):
        after(path)
        if stage == "scan" and path == skill_file:
            directory.rmdir()

    monkeypatch.setattr(_file_changes, "before_file_change", before_change)
    monkeypatch.setattr(_file_changes, "after_file_change", after_change)
    _file_changes.unlink_in_directory(skill_file, root=tmp_path)

    assert not skill_file.exists()
    assert directory.exists() == (stage == "rmdir")
    if stage == "rmdir":
        assert reference.read_bytes() == b"Concurrent user file"


@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("replacement", ["link", "loop", "file", "outside", "parent", "boundary"])
def test_unlink_in_directory_skips_unsafe_directory(tmp_path, monkeypatch, fallback, replacement):
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
@pytest.mark.parametrize("swap_at", ["before_unlink", "after_unlink", "before_rmdir", "before_rmdir_self"])
def test_unlink_in_directory_preserves_concurrent_replacements(tmp_path, monkeypatch, fallback, swap_at):
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
        elif path == directory and swap_at == "before_rmdir_self":
            directory.rename(tmp_path / "retained")
            directory.mkdir()
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
    elif swap_at in ("after_unlink", "before_rmdir_self") or not descriptor_io:
        assert directory.is_dir()
