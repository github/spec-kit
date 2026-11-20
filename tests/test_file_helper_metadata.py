"""Public read descriptor, times and mode on FileHelper."""

import os
import stat
from contextlib import contextmanager

import pytest

from specify_cli.file_helper import FileHelper, SymlinkDeniedError, UnsupportedPathError


REL = "parent/file"


def _seed(tmp_path, content=b"0123456789"):
    path = tmp_path / REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _link_or_skip(link, target):
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")


def test_open_read_yields_a_blocking_descriptor_on_the_file(tmp_path):
    path = _seed(tmp_path)
    with FileHelper(tmp_path) as files, files.open_read(REL) as fd:
        assert os.path.samestat(os.fstat(fd), path.stat())
        if os.name != "nt":
            assert os.get_blocking(fd)
        assert os.read(fd, 100) == b"0123456789"
    with pytest.raises(OSError):
        os.fstat(fd)


def test_open_read_refuses_a_directory_and_a_missing_file(tmp_path):
    (tmp_path / "parent").mkdir()
    with FileHelper(tmp_path) as files:
        with pytest.raises(UnsupportedPathError):
            with files.open_read("parent"):
                pass
        with pytest.raises(FileNotFoundError):
            with files.open_read(REL):
                pass


def test_open_read_refuses_a_leaf_link(tmp_path):
    _seed(tmp_path)
    _link_or_skip(tmp_path / "parent" / "link", tmp_path / REL)
    with FileHelper(tmp_path) as files, pytest.raises(SymlinkDeniedError):
        with files.open_read("parent/link"):
            pass


@pytest.mark.skipif(os.name == "nt", reason="POSIX anchors through parent descriptors")
def test_open_read_is_not_redirected_by_a_leaf_swapped_for_a_link(tmp_path, monkeypatch):
    _seed(tmp_path, b"inside")
    outside = tmp_path / "outside"
    outside.write_bytes(b"outside")
    original = FileHelper._posix_directory

    @contextmanager
    def swap_first(self, directory, **kwargs):
        (tmp_path / REL).unlink()
        (tmp_path / REL).symlink_to(outside)
        with original(self, directory, **kwargs) as anchored:
            yield anchored

    monkeypatch.setattr(FileHelper, "_posix_directory", swap_first)
    with FileHelper(tmp_path) as files, pytest.raises(OSError):
        with files.open_read(REL):
            pass


def test_utime_sets_both_times(tmp_path):
    path = _seed(tmp_path)
    with FileHelper(tmp_path) as files:
        files.utime(REL, ns=(1_000_000_000, 2_000_000_000))
    info = path.stat()
    assert (info.st_atime_ns, info.st_mtime_ns) == (1_000_000_000, 2_000_000_000)


def test_utime_and_chmod_refuse_a_leaf_link(tmp_path):
    target = _seed(tmp_path)
    _link_or_skip(tmp_path / "parent" / "link", target)
    before = target.stat()
    with FileHelper(tmp_path) as files:
        with pytest.raises(SymlinkDeniedError):
            files.utime("parent/link", ns=(1_000_000_000, 1_000_000_000))
        with pytest.raises(SymlinkDeniedError):
            files.chmod("parent/link", 0o600)
    assert target.stat().st_mtime_ns == before.st_mtime_ns
    assert target.stat().st_mode == before.st_mode


@pytest.mark.skipif(os.name == "nt", reason="POSIX anchors through parent descriptors")
@pytest.mark.parametrize("operation", ["utime", "chmod"])
def test_metadata_is_not_redirected_by_a_leaf_swapped_for_a_link(tmp_path, monkeypatch, operation):
    _seed(tmp_path)
    outside = tmp_path / "outside"
    outside.write_bytes(b"outside")
    outside.chmod(0o644)
    before = outside.stat()
    original = FileHelper._posix_directory

    @contextmanager
    def swap_first(self, directory, **kwargs):
        (tmp_path / REL).unlink()
        (tmp_path / REL).symlink_to(outside)
        with original(self, directory, **kwargs) as anchored:
            yield anchored

    monkeypatch.setattr(FileHelper, "_posix_directory", swap_first)
    with FileHelper(tmp_path) as files:
        try:
            if operation == "utime":
                files.utime(REL, ns=(1_000_000_000, 1_000_000_000))
            else:
                files.chmod(REL, 0o600)
        except (OSError, SymlinkDeniedError):
            pass
    after = outside.stat()
    assert after.st_mtime_ns == before.st_mtime_ns
    assert stat.S_IMODE(after.st_mode) == 0o644


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits")
@pytest.mark.parametrize("no_follow_chmod", [True, False])
def test_chmod_sets_the_mode(tmp_path, monkeypatch, no_follow_chmod):
    path = _seed(tmp_path)
    path.chmod(0o644)
    if not no_follow_chmod:
        # Linux has no no-follow fchmodat; the helper checks the leaf first.
        monkeypatch.setattr(os, "supports_follow_symlinks", os.supports_follow_symlinks - {os.chmod})
    with FileHelper(tmp_path) as files:
        files.chmod(REL, 0o600)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


@pytest.mark.skipif(os.name != "nt", reason="Windows read-only attribute")
def test_windows_chmod_toggles_read_only(tmp_path):
    path = _seed(tmp_path)
    with FileHelper(tmp_path) as files:
        files.chmod(REL, stat.S_IREAD)
        assert not path.stat().st_mode & stat.S_IWRITE
        files.chmod(REL, stat.S_IREAD | stat.S_IWRITE)
    assert path.stat().st_mode & stat.S_IWRITE
