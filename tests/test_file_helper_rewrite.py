"""Public in-place byte rewrite and stat on FileHelper."""

import errno
import os
import stat
import subprocess
import sys
from contextlib import contextmanager

import pytest

from specify_cli.file_helper import (
    FileHelper, SymlinkDeniedError, UnsupportedPathError,
)


REL = "parent/file"
# What open(O_NOFOLLOW | O_DIRECTORY) of a symlink raises: Linux/macOS, FreeBSD, NetBSD.
_NOFOLLOW_REFUSALS = {
    errno.ELOOP, errno.ENOTDIR, errno.EMLINK, getattr(errno, "EFTYPE", errno.ELOOP),
}


def _symlinks_available(tmp_path):
    probe = tmp_path / "probe"
    try:
        probe.symlink_to(tmp_path, target_is_directory=True)
        probe.unlink()
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")


def _seed(tmp_path, content=b"0123456789"):
    path = tmp_path / REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


# stat


def test_stat_matches_the_entry(tmp_path):
    path = _seed(tmp_path)
    with FileHelper(tmp_path) as files:
        info = files.stat(REL)
    native = path.stat()
    assert (info.st_dev, info.st_ino, info.st_size) == (native.st_dev, native.st_ino, 10)
    assert stat.S_ISREG(info.st_mode)


def test_stat_reports_a_directory(tmp_path):
    _seed(tmp_path)
    with FileHelper(tmp_path) as files:
        assert stat.S_ISDIR(files.stat("parent").st_mode)


def test_stat_of_a_missing_entry_raises(tmp_path):
    with FileHelper(tmp_path) as files, pytest.raises(FileNotFoundError):
        files.stat("missing")


def test_stat_refuses_a_symlink_unless_allowed(tmp_path):
    _symlinks_available(tmp_path)
    path = _seed(tmp_path)
    (tmp_path / "link").symlink_to(path)
    with FileHelper(tmp_path) as files, pytest.raises(SymlinkDeniedError):
        files.stat("link")
    with FileHelper(tmp_path, allow_symlinks=True) as files:
        assert files.stat("link").st_ino == path.stat().st_ino


def test_stat_refuses_a_path_outside_the_root(tmp_path):
    with FileHelper(tmp_path) as files, pytest.raises(ValueError):
        files.stat("../outside")


# open_rewrite


def test_open_rewrite_writes_in_place_without_truncating(tmp_path):
    path = _seed(tmp_path)
    inode = path.stat().st_ino
    with FileHelper(tmp_path) as files, files.open_rewrite(REL) as fd:
        assert os.lseek(fd, 0, os.SEEK_CUR) == 0
        assert os.fstat(fd).st_size == 10
        os.write(fd, b"ab\r\n")
    assert path.read_bytes() == b"ab\r\n456789"
    assert path.stat().st_ino == inode


def test_open_rewrite_keeps_the_mode(tmp_path):
    path = _seed(tmp_path)
    path.chmod(0o640)
    before = stat.S_IMODE(path.stat().st_mode)
    with FileHelper(tmp_path) as files, files.open_rewrite(REL) as fd:
        os.ftruncate(fd, 0)
        os.write(fd, b"new")
    assert path.read_bytes() == b"new"
    assert stat.S_IMODE(path.stat().st_mode) == before


@pytest.mark.skipif(os.name == "nt", reason="POSIX set-user-ID and set-group-ID bits")
def test_open_rewrite_leaves_setid_clearing_to_the_os(tmp_path):
    # POSIX lets a write by a process without privilege clear these bits. The
    # helper keeps that behaviour rather than restoring them: its result must
    # match a plain write to an identical file, with permission bits unchanged.
    path = _seed(tmp_path)
    control = tmp_path / "control"
    control.write_bytes(path.read_bytes())
    for target in (path, control):
        target.chmod(0o6750)
    before = stat.S_IMODE(path.stat().st_mode)
    if not before & (stat.S_ISUID | stat.S_ISGID):
        pytest.skip("The filesystem did not keep the set-user-ID or set-group-ID bit")
    assert stat.S_IMODE(control.stat().st_mode) == before

    fd = os.open(control, os.O_WRONLY)
    try:
        os.write(fd, b"new")
        os.ftruncate(fd, 3)
    finally:
        os.close(fd)
    with FileHelper(tmp_path) as files, files.open_rewrite(REL) as fd:
        FileHelper.rewrite_descriptor(fd, b"new")

    after = stat.S_IMODE(path.stat().st_mode)
    assert path.read_bytes() == b"new"
    assert after & 0o777 == before & 0o777
    assert after == stat.S_IMODE(control.stat().st_mode)


def test_open_rewrite_closes_the_descriptor(tmp_path):
    _seed(tmp_path)
    with FileHelper(tmp_path) as files:
        with files.open_rewrite(REL) as fd:
            pass
    with pytest.raises(OSError) as raised:
        os.fstat(fd)
    assert raised.value.errno == errno.EBADF


def test_open_rewrite_never_creates(tmp_path):
    (tmp_path / "parent").mkdir()
    with FileHelper(tmp_path) as files, pytest.raises(FileNotFoundError):
        with files.open_rewrite(REL):
            pass
    assert not (tmp_path / REL).exists()


def test_open_rewrite_does_not_create_a_leaf_removed_after_resolution(tmp_path, monkeypatch):
    path = _seed(tmp_path)
    original = FileHelper._overwrite_descriptor

    @contextmanager
    def remove_first(self, destination, **kwargs):
        path.unlink()
        with original(self, destination, **kwargs) as fd:
            yield fd

    monkeypatch.setattr(FileHelper, "_overwrite_descriptor", remove_first)
    with FileHelper(tmp_path) as files, pytest.raises(FileNotFoundError):
        with files.open_rewrite(REL):
            pass
    assert not path.exists()


def test_open_rewrite_refuses_a_directory(tmp_path):
    _seed(tmp_path)
    with FileHelper(tmp_path) as files, pytest.raises(UnsupportedPathError):
        with files.open_rewrite("parent"):
            pass


@pytest.mark.skipif(os.name == "nt", reason="needs POSIX symlinks")
def test_open_rewrite_refuses_a_parent_swapped_for_a_symlink(tmp_path, monkeypatch):
    path = _seed(tmp_path, b"inside")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "file").write_bytes(b"outside")
    original = FileHelper._overwrite_descriptor

    @contextmanager
    def swap_first(self, destination, **kwargs):
        path.parent.rename(tmp_path / "moved")
        path.parent.symlink_to(outside, target_is_directory=True)
        with original(self, destination, **kwargs) as fd:
            yield fd

    monkeypatch.setattr(FileHelper, "_overwrite_descriptor", swap_first)
    with FileHelper(tmp_path) as files, pytest.raises(OSError) as raised:
        with files.open_rewrite(REL) as fd:
            os.write(fd, b"written")
    assert raised.value.errno in _NOFOLLOW_REFUSALS
    assert (outside / "file").read_bytes() == b"outside"


@pytest.mark.skipif(os.name == "nt", reason="needs POSIX FIFOs")
def test_open_rewrite_refuses_a_fifo_without_blocking(tmp_path):
    (tmp_path / "parent").mkdir()
    os.mkfifo(tmp_path / REL)
    with FileHelper(tmp_path) as files, pytest.raises(UnsupportedPathError):
        with files.open_rewrite(REL):
            pass


def test_open_rewrite_refuses_a_symlinked_leaf_unless_allowed(tmp_path):
    _symlinks_available(tmp_path)
    path = _seed(tmp_path)
    (tmp_path / "link").symlink_to(path)
    with FileHelper(tmp_path) as files, pytest.raises(SymlinkDeniedError):
        with files.open_rewrite("link"):
            pass
    with FileHelper(tmp_path, allow_symlinks=True) as files, files.open_rewrite("link") as fd:
        os.write(fd, b"ab")
    assert (tmp_path / "link").is_symlink()
    assert path.read_bytes() == b"ab23456789"


# Review regressions


@pytest.mark.skipif(os.name == "nt", reason="needs POSIX symlinks")
def test_stat_is_not_redirected_by_a_parent_swapped_after_resolution(tmp_path, monkeypatch):
    path = _seed(tmp_path, b"inside")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "file").write_bytes(b"outside, longer")
    original = FileHelper._posix_directory

    @contextmanager
    def swap_first(self, directory, **kwargs):
        path.parent.rename(tmp_path / "moved")
        path.parent.symlink_to(outside, target_is_directory=True)
        with original(self, directory, **kwargs) as anchored:
            yield anchored

    monkeypatch.setattr(FileHelper, "_posix_directory", swap_first)
    with FileHelper(tmp_path) as files, pytest.raises(OSError) as raised:
        files.stat(REL)
    assert raised.value.errno in _NOFOLLOW_REFUSALS


def test_stat_of_the_root(tmp_path):
    with FileHelper(tmp_path) as files:
        assert files.stat(tmp_path).st_ino == tmp_path.stat().st_ino


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptors")
def test_open_rewrite_yields_a_blocking_descriptor(tmp_path):
    _seed(tmp_path)
    with FileHelper(tmp_path) as files, files.open_rewrite(REL) as fd:
        assert os.get_blocking(fd)


@pytest.mark.skipif(os.name != "nt", reason="needs Windows junctions")
def test_stat_refuses_a_junctioned_parent(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "file").write_bytes(b"outside")
    project = tmp_path / "project"
    project.mkdir()
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(project / "parent"), str(outside)],
        check=True, capture_output=True,
    )
    with FileHelper(project) as files, pytest.raises(UnsupportedPathError):
        files.stat(REL)


@pytest.mark.skipif(os.name == "nt", reason="needs POSIX symlinks")
def test_stat_does_not_follow_a_root_replaced_by_a_symlink(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    with FileHelper(root) as files:
        root.rename(tmp_path / "moved")
        root.symlink_to(other, target_is_directory=True)
        assert stat.S_ISLNK(files.stat(".").st_mode)


@pytest.mark.skipif(os.name == "nt", reason="needs POSIX FIFOs")
def test_open_rewrite_refuses_a_nonregular_leaf_swapped_in_after_preflight(tmp_path, monkeypatch):
    # A FIFO with a reader opens for writing, so only the descriptor check can refuse it.
    path = _seed(tmp_path)
    real_open = os.open
    original = FileHelper._overwrite_descriptor
    leaf: list[int] = []
    readers: list[int] = []

    def open_(name, flags, *args, **kwargs):
        fd = real_open(name, flags, *args, **kwargs)
        if os.fspath(name) == "file":
            leaf.append(fd)
        return fd

    @contextmanager
    def swap_first(self, destination, **kwargs):
        path.unlink()
        os.mkfifo(path)
        readers.append(real_open(path, os.O_RDONLY | os.O_NONBLOCK))
        with original(self, destination, **kwargs) as fd:
            yield fd

    monkeypatch.setattr(os, "open", open_)
    monkeypatch.setattr(FileHelper, "_overwrite_descriptor", swap_first)
    entered = False
    try:
        with FileHelper(tmp_path) as files, pytest.raises(UnsupportedPathError):
            with files.open_rewrite(REL):
                entered = True
    finally:
        for fd in readers:
            os.close(fd)
    monkeypatch.undo()
    assert not entered
    assert len(leaf) == 1
    with pytest.raises(OSError) as raised:
        os.fstat(leaf[0])
    assert raised.value.errno == errno.EBADF


def test_rewrite_descriptor_replaces_and_truncates_from_any_offset(tmp_path):
    target = tmp_path / "file.txt"
    target.write_bytes(b"a much longer original\n")
    inode = target.stat().st_ino
    with FileHelper(tmp_path) as helper, helper.open_rewrite("file.txt") as fd:
        os.lseek(fd, 0, os.SEEK_END)
        FileHelper.rewrite_descriptor(fd, b"short\n")
    assert target.read_bytes() == b"short\n"
    assert target.stat().st_ino == inode


def test_rewrite_descriptor_flushes_after_writing(tmp_path, monkeypatch):
    target = tmp_path / "file.txt"
    target.write_bytes(b"old\n")
    seen = []
    real_fsync = os.fsync

    def fsync(fd):
        seen.append(os.fstat(fd).st_size)
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", fsync)
    with FileHelper(tmp_path) as helper, helper.open_rewrite("file.txt") as fd:
        FileHelper.rewrite_descriptor(fd, b"newer\n")
    assert seen == [len(b"newer\n")]


def test_rewrite_descriptor_raises_when_a_write_makes_no_progress(tmp_path, monkeypatch):
    target = tmp_path / "file.txt"
    target.write_bytes(b"old\n")
    monkeypatch.setattr(os, "write", lambda fd, data: 0)
    with FileHelper(tmp_path) as helper, helper.open_rewrite("file.txt") as fd:
        with pytest.raises(OSError, match="no progress"):
            FileHelper.rewrite_descriptor(fd, b"new\n")


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS F_FULLFSYNC")
@pytest.mark.parametrize("code, raises", [(errno.ENOTSUP, False), (errno.EIO, True)])
def test_rewrite_descriptor_raises_only_real_full_fsync_errors(tmp_path, monkeypatch, code, raises):
    import fcntl

    target = tmp_path / "file.txt"
    target.write_bytes(b"old\n")
    real_fcntl = fcntl.fcntl

    def fail(fd, command, *args):
        if command == fcntl.F_FULLFSYNC:
            raise OSError(code, os.strerror(code))
        return real_fcntl(fd, command, *args)

    monkeypatch.setattr(fcntl, "fcntl", fail)
    with FileHelper(tmp_path) as helper, helper.open_rewrite("file.txt") as fd:
        if raises:
            with pytest.raises(OSError):
                FileHelper.rewrite_descriptor(fd, b"new\n")
        else:
            FileHelper.rewrite_descriptor(fd, b"new\n")
    if not raises:
        assert target.read_bytes() == b"new\n"


@pytest.mark.skipif(os.name == "nt", reason="POSIX append-mode descriptors")
def test_rewrite_descriptor_refuses_an_append_mode_descriptor(tmp_path):
    target = tmp_path / "file.txt"
    target.write_bytes(b"original bytes")
    fd = os.open(target, os.O_WRONLY | os.O_APPEND)
    try:
        with pytest.raises(OSError, match="append-mode"):
            FileHelper.rewrite_descriptor(fd, b"new")
    finally:
        os.close(fd)
    assert target.read_bytes() == b"original bytes"


def _short_writes(monkeypatch, fail_after=None):
    """Make ``os.write`` accept at most 3 bytes a call, optionally failing after some calls."""
    real_write = os.write
    calls = []

    def write(fd, data):
        calls.append(fd)
        if fail_after is not None and len(calls) > fail_after:
            raise OSError(errno.EIO, "I/O error")
        return real_write(fd, bytes(data[:3]))

    monkeypatch.setattr(os, "write", write)
    return calls


def test_rewrite_descriptor_retries_short_writes(tmp_path, monkeypatch):
    target = tmp_path / "file.txt"
    target.write_bytes(b"a much longer original\n")
    with FileHelper(tmp_path) as helper, helper.open_rewrite("file.txt") as fd:
        calls = _short_writes(monkeypatch)
        FileHelper.rewrite_descriptor(fd, b"replacement\n")
        monkeypatch.undo()
    assert len(calls) > 1
    assert target.read_bytes() == b"replacement\n"

