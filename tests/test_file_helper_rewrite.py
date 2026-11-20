"""Public in-place byte rewrite, owner-only creation and stat on FileHelper."""

import errno
import os
import shutil
import stat
import subprocess
import sys
import types
from contextlib import contextmanager

import pytest

from specify_cli import _file_handles
from specify_cli.file_helper import (
    FileHelper, FileHelperError, SymlinkDeniedError, UnsupportedPathError,
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


# access and canonical_root


def test_access_grants_an_accessible_entry(tmp_path):
    _seed(tmp_path)
    with FileHelper(tmp_path) as files:
        assert files.access(REL, os.R_OK | os.W_OK)
        assert files.access("parent", os.X_OK)
        assert files.access(tmp_path, os.W_OK)


@pytest.mark.skipif(
    os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="needs POSIX permissions enforced for the current user",
)
def test_access_refuses_what_the_mode_denies(tmp_path):
    path = _seed(tmp_path)
    path.chmod(0o444)
    try:
        with FileHelper(tmp_path) as files:
            assert files.access(REL, os.R_OK)
            assert not files.access(REL, os.W_OK)
    finally:
        path.chmod(0o644)


@pytest.mark.skipif(os.name != "nt", reason="the read-only attribute is Windows-only")
def test_access_reports_the_windows_read_only_attribute(tmp_path):
    path = _seed(tmp_path)
    path.chmod(stat.S_IREAD)
    try:
        with FileHelper(tmp_path) as files:
            assert not files.access(REL, os.W_OK)
    finally:
        path.chmod(stat.S_IREAD | stat.S_IWRITE)


@pytest.mark.skipif(os.name == "nt", reason="POSIX checks through the parent descriptor")
def test_access_makes_a_plain_faccessat(tmp_path, monkeypatch):
    # Without faccessat2, libc emulates AT_SYMLINK_NOFOLLOW from mode bits.
    _seed(tmp_path)
    calls = []
    real_access = os.access

    def access(path, mode, **kwargs):
        calls.append(kwargs)
        return real_access(path, mode, **kwargs)

    monkeypatch.setattr(os, "access", access)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {access})
    monkeypatch.setattr(os, "supports_follow_symlinks", os.supports_follow_symlinks - {real_access})
    with FileHelper(tmp_path) as files:
        assert files.access(REL, os.R_OK)
    assert len(calls) == 1
    assert "dir_fd" in calls[0] and "follow_symlinks" not in calls[0]


def test_access_of_a_missing_entry_raises(tmp_path):
    with FileHelper(tmp_path) as files, pytest.raises(FileNotFoundError):
        files.access("missing", os.R_OK)


def test_access_refuses_a_symlink_unless_allowed(tmp_path):
    _symlinks_available(tmp_path)
    path = _seed(tmp_path)
    (tmp_path / "link").symlink_to(path)
    with FileHelper(tmp_path) as files, pytest.raises(SymlinkDeniedError):
        files.access("link", os.R_OK)
    with FileHelper(tmp_path, allow_symlinks=True) as files:
        assert files.access("link", os.R_OK)


def test_access_refuses_a_path_outside_the_root(tmp_path):
    with FileHelper(tmp_path) as files, pytest.raises(ValueError):
        files.access("../outside", os.R_OK)


def test_canonical_root_resolves_a_root_alias(tmp_path):
    _symlinks_available(tmp_path)
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with FileHelper(alias) as files:
        assert files.root == alias
        assert files.canonical_root == real.resolve()


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


# create_private_bytes


def test_create_private_bytes_creates_exclusively(tmp_path):
    (tmp_path / "parent").mkdir()
    with FileHelper(tmp_path) as files:
        files.create_private_bytes(REL, b"first")
        with pytest.raises(FileExistsError):
            files.create_private_bytes(REL, b"second")
    assert (tmp_path / REL).read_bytes() == b"first"


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits")
def test_create_private_bytes_is_owner_only(tmp_path):
    (tmp_path / "parent").mkdir()
    with FileHelper(tmp_path) as files:
        files.create_private_bytes(REL, b"content")
    assert stat.S_IMODE((tmp_path / REL).stat().st_mode) & 0o077 == 0


@pytest.mark.skipif(os.name == "nt", reason="POSIX ownership")
def test_create_private_bytes_refuses_a_file_owned_by_another_user(tmp_path, monkeypatch):
    (tmp_path / "parent").mkdir()
    monkeypatch.setattr(os, "geteuid", lambda: os.stat(tmp_path).st_uid + 1)
    with FileHelper(tmp_path) as files, pytest.raises(PermissionError) as raised:
        files.create_private_bytes(REL, b"private")
    assert "owned by uid" in str(raised.value)
    assert not (tmp_path / REL).exists()


def test_create_private_bytes_needs_an_existing_parent(tmp_path):
    with FileHelper(tmp_path) as files, pytest.raises(FileNotFoundError):
        files.create_private_bytes(REL, b"content")
    assert not (tmp_path / "parent").exists()


def test_create_private_bytes_refuses_a_dangling_link(tmp_path):
    _symlinks_available(tmp_path)
    (tmp_path / "parent").mkdir()
    (tmp_path / REL).symlink_to(tmp_path / "target")
    with FileHelper(tmp_path, allow_symlinks=True) as files, pytest.raises(FileExistsError):
        files.create_private_bytes(REL, b"content")
    assert not (tmp_path / "target").exists()


@pytest.mark.skipif(os.name == "nt", reason="needs POSIX symlinks")
def test_create_private_bytes_refuses_a_symlinked_parent(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    (project / "parent").symlink_to(outside)
    with FileHelper(project) as files, pytest.raises(SymlinkDeniedError):
        files.create_private_bytes(REL, b"secret")
    assert not list(outside.iterdir())


@pytest.mark.skipif(os.name == "nt", reason="needs POSIX symlinks")
def test_create_private_bytes_refuses_a_parent_swapped_for_a_symlink(tmp_path, monkeypatch):
    outside = tmp_path / "outside"
    outside.mkdir()
    parent = tmp_path / "parent"
    parent.mkdir()
    original = FileHelper._creation_directory

    @contextmanager
    def swap_first(self, directory):
        parent.rename(tmp_path / "moved")
        parent.symlink_to(outside, target_is_directory=True)
        with original(self, directory) as anchored:
            yield anchored

    monkeypatch.setattr(FileHelper, "_creation_directory", swap_first)
    with FileHelper(tmp_path) as files, pytest.raises(OSError) as raised:
        files.create_private_bytes(REL, b"secret")
    assert raised.value.errno in _NOFOLLOW_REFUSALS
    assert not list(outside.iterdir())


@pytest.mark.skipif(os.name != "nt", reason="needs Windows junctions")
def test_create_private_bytes_refuses_a_junctioned_parent(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(project / "parent"), str(outside)],
        check=True, capture_output=True,
    )
    with FileHelper(project) as files, pytest.raises(UnsupportedPathError):
        files.create_private_bytes(REL, b"secret")
    assert not list(outside.iterdir())


@pytest.mark.skipif(os.name == "nt", reason="POSIX creation path")
@pytest.mark.parametrize("step", ["write", "fsync", "close"])
def test_posix_create_private_bytes_uses_one_descriptor_and_removes_a_partial_file(
    tmp_path, monkeypatch, step
):
    # Reopening the file by name could block on a FIFO swapped in for it.
    (tmp_path / "parent").mkdir()
    real_open, real_step = os.open, getattr(os, step)
    leaf: list[int] = []
    live: set[int] = set()

    def open_(path, flags, *args, **kwargs):
        fd = real_open(path, flags, *args, **kwargs)
        if os.fspath(path) == "file":
            leaf.append(fd)
            live.add(fd)
        return fd

    def fail(fd, *args):
        if fd not in live:
            return real_step(fd, *args)
        if step == "close":
            # Its number may be reused once closed.
            live.discard(fd)
            real_step(fd)
        raise OSError("disk full")

    monkeypatch.setattr(os, "open", open_)
    monkeypatch.setattr(os, step, fail)
    with FileHelper(tmp_path) as files, pytest.raises(OSError, match="disk full"):
        files.create_private_bytes(REL, b"content")
    monkeypatch.undo()
    assert len(leaf) == 1
    assert not (tmp_path / REL).exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX creation path")
def test_posix_create_private_bytes_keeps_a_replacement_it_did_not_create(tmp_path, monkeypatch):
    (tmp_path / "parent").mkdir()
    real_fsync = os.fsync

    def replace_then_fail(fd):
        if stat.S_ISREG(os.fstat(fd).st_mode):
            (tmp_path / REL).unlink()
            (tmp_path / REL).write_bytes(b"someone else's")
            raise OSError("disk full")
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", replace_then_fail)
    with FileHelper(tmp_path) as files, pytest.raises(OSError, match="disk full") as raised:
        files.create_private_bytes(REL, b"content")
    monkeypatch.undo()
    assert (tmp_path / REL).read_bytes() == b"someone else's"
    # The caller is told the name was left, rather than cleanup failing silently.
    assert any(
        "Left file" in note and "not removed" in note for note in raised.value.__notes__
    )


@pytest.mark.skipif(os.name == "nt", reason="POSIX creation path")
def test_posix_create_private_bytes_flushes_the_file_and_its_directory(tmp_path, monkeypatch):
    (tmp_path / "parent").mkdir()
    real_open, real_fsync, real_creation = os.open, os.fsync, FileHelper._creation_directory
    leaf: list[int] = []
    pinned: list[int] = []
    synced: list[tuple[int, bool]] = []

    def open_(path, flags, *args, **kwargs):
        fd = real_open(path, flags, *args, **kwargs)
        if os.fspath(path) == "file":
            leaf.append(fd)
        return fd

    @contextmanager
    def creation_directory(self, directory):
        with real_creation(self, directory) as anchored:
            pinned.append(anchored)
            yield anchored

    def fsync(fd):
        synced.append((fd, stat.S_ISDIR(os.fstat(fd).st_mode)))
        return real_fsync(fd)

    monkeypatch.setattr(os, "open", open_)
    monkeypatch.setattr(os, "fsync", fsync)
    monkeypatch.setattr(FileHelper, "_creation_directory", creation_directory)
    with FileHelper(tmp_path) as files:
        files.create_private_bytes(REL, b"content")
    monkeypatch.undo()
    assert len(leaf) == 1 and (leaf[0], False) in synced
    # The pinned descriptor may be O_PATH, which fsync rejects, so a readable one is used.
    directories = [fd for fd, is_dir in synced if is_dir]
    assert len(directories) == 1 and directories[0] not in pinned
    assert (tmp_path / REL).read_bytes() == b"content"


@pytest.mark.skipif(os.name == "nt", reason="POSIX creation path")
def test_posix_create_private_bytes_succeeds_when_the_directory_cannot_be_flushed(
    tmp_path, monkeypatch
):
    (tmp_path / "parent").mkdir()
    real_fsync = os.fsync

    def fsync(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError(errno.EBADF, "Bad file descriptor")
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", fsync)
    with FileHelper(tmp_path) as files:
        files.create_private_bytes(REL, b"content")
    monkeypatch.undo()
    assert (tmp_path / REL).read_bytes() == b"content"


@pytest.mark.skipif(os.name != "nt", reason="Windows creation path")
def test_windows_create_private_bytes_removes_a_partial_file(tmp_path, monkeypatch):
    (tmp_path / "parent").mkdir()
    real_fsync = os.fsync
    created: list[int] = []
    real_create = _file_handles._windows_create_private_fd

    def create(path):
        fd = real_create(path)
        created.append(fd)
        return fd

    def fsync(fd):
        if fd in created:
            raise OSError("disk full")
        return real_fsync(fd)

    from specify_cli import file_helper

    monkeypatch.setattr(file_helper, "_windows_create_private_fd", create)
    monkeypatch.setattr(os, "fsync", fsync)
    with FileHelper(tmp_path) as files, pytest.raises(OSError, match="disk full"):
        files.create_private_bytes(REL, b"content")
    monkeypatch.undo()
    assert not (tmp_path / REL).exists()
    with FileHelper(tmp_path) as files:
        files.create_private_bytes(REL, b"content")
    assert (tmp_path / REL).read_bytes() == b"content"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows creation path")
def test_windows_create_private_bytes_leaves_no_file_if_no_descriptor_is_made(
    tmp_path, monkeypatch
):
    import msvcrt

    def fail(handle, flags):
        raise OSError("too many open files")

    (tmp_path / "parent").mkdir()
    monkeypatch.setattr(msvcrt, "open_osfhandle", fail)
    with FileHelper(tmp_path) as files, pytest.raises(OSError, match="too many open files"):
        files.create_private_bytes(REL, b"content")
    assert not (tmp_path / REL).exists()
    monkeypatch.undo()
    with FileHelper(tmp_path) as files:
        files.create_private_bytes(REL, b"content")
    assert (tmp_path / REL).read_bytes() == b"content"


def _simulate_windows_create(monkeypatch, calls, *, marked=True, volume_flags=0x8):
    """Fake the Windows calls ``_windows_create_private_fd`` makes, so it runs everywhere."""
    import ctypes

    class Attributes(ctypes.Structure):
        _fields_ = [("nLength", ctypes.c_ulong), ("descriptor", ctypes.c_void_p),
                    ("inherit", ctypes.c_int)]

    class Kernel:
        def CreateFileW(self, path, access, share, attributes, disposition, flags, template):
            calls.append(("CreateFileW", access, share, disposition))
            return 1234

        def GetVolumeInformationByHandleW(self, handle, *args):
            args[4]._obj.value = volume_flags  # lpFileSystemFlags
            return 1

        def SetFileInformationByHandle(self, handle, kind, info, size):
            calls.append(("SetFileInformationByHandle", handle, kind, bytes(info._obj)))
            if marked is None:
                raise ctypes.ArgumentError("bad argument")
            return int(marked)

        def CloseHandle(self, handle):
            calls.append(("CloseHandle", handle))
            return 1

        def LocalFree(self, pointer):
            return None

    class Advapi:
        def ConvertStringSecurityDescriptorToSecurityDescriptorW(self, *args):
            return 1

    def open_osfhandle(handle, flags):
        calls.append(("open_osfhandle", handle))
        raise OSError("too many open files")

    monkeypatch.setattr(
        _file_handles, "_windows_security_api", lambda: (Kernel(), Advapi(), Attributes)
    )
    monkeypatch.setattr(_file_handles, "_windows_owner_only_sddl", lambda: "O:S-1-0D:P")
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 5, raising=False)
    monkeypatch.setattr(ctypes, "WinError", lambda code=None: OSError(code, "denied"), raising=False)
    monkeypatch.setitem(sys.modules, "msvcrt", types.SimpleNamespace(open_osfhandle=open_osfhandle))
    monkeypatch.setattr(os, "O_BINARY", 0x8000, raising=False)


@pytest.mark.parametrize("marked", [True, False, None])
def test_windows_private_fd_removes_its_file_through_the_handle_if_no_descriptor_is_made(
    tmp_path, monkeypatch, marked
):
    # Simulates the Windows calls, so this runs everywhere; the test above
    # makes the real ones.
    calls = []
    _simulate_windows_create(monkeypatch, calls, marked=marked)
    with pytest.raises(OSError, match="too many open files") as raised:
        _file_handles._windows_create_private_fd(tmp_path / "file")
    delete, create_new = 0x00010000, 1
    access, share, disposition = calls[0][1:]
    assert access & delete and share == 0 and disposition == create_new
    # FileDispositionInfo with DeleteFile set, before the handle closes.
    assert calls[1:] == [
        ("open_osfhandle", 1234),
        ("SetFileInformationByHandle", 1234, 4, b"\x01"),
        ("CloseHandle", 1234),
    ]
    # If it cannot be marked, the error names the empty file so it can be deleted.
    noted = any(str(tmp_path / "file") in note for note in getattr(raised.value, "__notes__", []))
    assert noted is not bool(marked)


def test_windows_private_fd_refuses_a_volume_without_persistent_acls(tmp_path, monkeypatch):
    # FAT and exFAT accept the security descriptor but do not keep it.
    calls = []
    _simulate_windows_create(monkeypatch, calls, volume_flags=0)
    with pytest.raises(PermissionError, match="does not keep access-control lists"):
        _file_handles._windows_create_private_fd(tmp_path / "file")
    # Refused before a descriptor exists; the empty file is removed through its handle.
    assert [call[0] for call in calls] == [
        "CreateFileW", "SetFileInformationByHandle", "CloseHandle",
    ]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows access-control lists")
def test_windows_create_private_bytes_sets_an_owner_only_protected_acl(tmp_path):
    (tmp_path / "parent").mkdir()
    with FileHelper(tmp_path) as files:
        files.create_private_bytes(REL, b"content")
    # A step's PowerShell 7 puts its own module paths in PSModulePath, and Windows
    # PowerShell then fails to load Microsoft.PowerShell.Security for Get-Acl.
    # Prefer pwsh, and let either shell rebuild its default module path.
    env = {key: value for key, value in os.environ.items() if key.upper() != "PSMODULEPATH"}
    result = subprocess.run(
        [shutil.which("pwsh") or "powershell", "-NoProfile", "-NonInteractive", "-Command",
         f"(Get-Acl -LiteralPath '{tmp_path / REL}').Sddl"],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0, result.stderr
    sddl = result.stdout.strip()
    sid = _file_handles._windows_current_user_sid()
    assert f"O:{sid}" in sddl
    dacl = sddl.split("D:", 1)[1]
    assert dacl.startswith("P")
    assert dacl.count("(") == 1 and f";;;{sid})" in dacl


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


@pytest.mark.skipif(os.name == "nt", reason="POSIX anchors through parent descriptors")
def test_access_is_not_redirected_by_a_parent_swapped_after_resolution(tmp_path, monkeypatch):
    path = _seed(tmp_path, b"inside")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "file").write_bytes(b"outside")
    original = FileHelper._posix_directory

    @contextmanager
    def swap_first(self, directory, **kwargs):
        path.parent.rename(tmp_path / "moved")
        path.parent.symlink_to(outside, target_is_directory=True)
        with original(self, directory, **kwargs) as anchored:
            yield anchored

    monkeypatch.setattr(FileHelper, "_posix_directory", swap_first)
    with FileHelper(tmp_path) as files, pytest.raises(OSError) as raised:
        files.access(REL, os.R_OK)
    assert raised.value.errno in _NOFOLLOW_REFUSALS


def test_stat_of_the_root(tmp_path):
    with FileHelper(tmp_path) as files:
        assert files.stat(tmp_path).st_ino == tmp_path.stat().st_ino


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptors")
def test_open_rewrite_yields_a_blocking_descriptor(tmp_path):
    _seed(tmp_path)
    with FileHelper(tmp_path) as files, files.open_rewrite(REL) as fd:
        assert os.get_blocking(fd)


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS extended ACLs")
def test_create_private_bytes_refuses_a_directory_with_inheritable_acl_entries(tmp_path):
    parent = tmp_path / "parent"
    parent.mkdir()
    subprocess.run(
        ["chmod", "+a", "everyone allow read,file_inherit", str(parent)],
        check=True, capture_output=True,
    )
    (parent / "plain").write_bytes(b"")
    inherited = subprocess.run(
        ["ls", "-le", str(parent / "plain")], check=True, capture_output=True, text=True,
    ).stdout
    if "everyone" not in inherited:
        pytest.skip("filesystem did not apply the inheritable ACE")
    with FileHelper(tmp_path) as files, pytest.raises(PermissionError, match="inheritable ACL entries allow"):
        files.create_private_bytes(REL, b"secret")
    assert not (tmp_path / REL).exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits")
def test_create_private_bytes_refuses_a_filesystem_that_ignores_the_mode(tmp_path, monkeypatch):
    (tmp_path / "parent").mkdir()
    real_fstat = os.fstat

    def fstat(fd):
        info = real_fstat(fd)
        if stat.S_ISREG(info.st_mode):
            values = list(info)
            values[0] = stat.S_IFREG | 0o777
            return os.stat_result(values)
        return info

    monkeypatch.setattr(os, "fstat", fstat)
    with FileHelper(tmp_path) as files, pytest.raises(PermissionError, match="owner-only"):
        files.create_private_bytes(REL, b"secret")
    monkeypatch.undo()
    assert not (tmp_path / REL).exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX creation path")
def test_posix_create_private_bytes_notes_a_partial_file_it_could_not_remove(
    tmp_path, monkeypatch
):
    (tmp_path / "parent").mkdir()
    real_fsync, real_unlink = os.fsync, os.unlink

    def fsync(fd):
        if stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError(errno.ENOSPC, "No space left")
        return real_fsync(fd)

    def unlink(path, *args, **kwargs):
        if os.fspath(path) == "file":
            raise PermissionError(errno.EACCES, "denied")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(os, "fsync", fsync)
    monkeypatch.setattr(os, "unlink", unlink)
    with FileHelper(tmp_path) as files, pytest.raises(OSError, match="No space left") as raised:
        files.create_private_bytes(REL, b"content")
    monkeypatch.undo()
    assert any("Could not remove partial file" in note for note in raised.value.__notes__)
    assert (tmp_path / REL).exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX creation path")
def test_posix_create_private_bytes_never_removes_a_name_it_could_not_identify(
    tmp_path, monkeypatch
):
    (tmp_path / "parent").mkdir()
    real_fstat = os.fstat
    leaf: list[int] = []
    real_open = os.open

    def open_(path, flags, *args, **kwargs):
        fd = real_open(path, flags, *args, **kwargs)
        if os.fspath(path) == "file":
            leaf.append(fd)
        return fd

    def fstat(fd):
        if fd in leaf:
            raise OSError(errno.EIO, "fstat failed")
        return real_fstat(fd)

    monkeypatch.setattr(os, "open", open_)
    monkeypatch.setattr(os, "fstat", fstat)
    with FileHelper(tmp_path) as files, pytest.raises(OSError, match="fstat failed") as raised:
        files.create_private_bytes(REL, b"content")
    monkeypatch.undo()
    assert (tmp_path / REL).exists()
    assert any("delete it before retrying" in note for note in raised.value.__notes__)


@pytest.mark.skipif(os.name == "nt", reason="POSIX creation path")
def test_posix_create_private_bytes_keeps_the_write_error_when_close_also_fails(
    tmp_path, monkeypatch
):
    (tmp_path / "parent").mkdir()
    real_open, real_write, real_close = os.open, os.write, os.close
    leaf: list[int] = []

    def open_(path, flags, *args, **kwargs):
        fd = real_open(path, flags, *args, **kwargs)
        if os.fspath(path) == "file":
            leaf.append(fd)
        return fd

    def write(fd, data):
        if fd in leaf:
            raise OSError(errno.ENOSPC, "No space left")
        return real_write(fd, data)

    def close(fd):
        real_close(fd)
        if fd in leaf:
            leaf.remove(fd)
            raise OSError(errno.EIO, "Input/output error")

    monkeypatch.setattr(os, "open", open_)
    monkeypatch.setattr(os, "write", write)
    monkeypatch.setattr(os, "close", close)
    with FileHelper(tmp_path) as files, pytest.raises(OSError, match="No space left") as raised:
        files.create_private_bytes(REL, b"content")
    monkeypatch.undo()
    assert any("Could not close" in note for note in raised.value.__notes__)
    assert not (tmp_path / REL).exists()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS extended ACLs")
def test_create_private_bytes_accepts_inherited_deny_only_acl_entries(tmp_path):
    parent = tmp_path / "parent"
    parent.mkdir()
    subprocess.run(
        ["chmod", "+a", "everyone deny delete,file_inherit", str(parent)],
        check=True, capture_output=True,
    )
    try:
        with FileHelper(tmp_path) as files:
            files.create_private_bytes(REL, b"secret")
        assert (tmp_path / REL).read_bytes() == b"secret"
    finally:
        subprocess.run(["chmod", "-RN", str(parent)], check=False, capture_output=True)


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS F_FULLFSYNC")
@pytest.mark.parametrize(("code", "raises"), [(errno.ENOTSUP, False), (errno.EINVAL, False),
                                               (errno.EIO, True)])
def test_create_private_bytes_raises_only_real_full_fsync_errors(tmp_path, monkeypatch, code, raises):
    import fcntl

    (tmp_path / "parent").mkdir()
    real_fcntl = fcntl.fcntl

    def fail(fd, command, *args):
        if command == fcntl.F_FULLFSYNC and stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError(code, os.strerror(code))
        return real_fcntl(fd, command, *args)

    monkeypatch.setattr(fcntl, "fcntl", fail)
    with FileHelper(tmp_path) as files:
        if raises:
            with pytest.raises(OSError) as raised:
                files.create_private_bytes(REL, b"content")
            assert raised.value.errno == code
        else:
            files.create_private_bytes(REL, b"content")
    monkeypatch.undo()
    assert (tmp_path / REL).exists() is not raises


def test_windows_create_private_notes_a_close_failure_after_a_complete_write(
    tmp_path, monkeypatch
):
    # Drives the Windows branch with a real descriptor so it runs everywhere.
    from specify_cli import file_helper

    target = tmp_path / "file"
    real_close = os.close
    opened: list[int] = []

    def create(path):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        opened.append(fd)
        return fd

    def close(fd):
        real_close(fd)
        if fd in opened:
            opened.remove(fd)
            raise OSError(errno.EIO, "Input/output error")

    monkeypatch.setattr(file_helper, "_windows_create_private_fd", create)
    monkeypatch.setattr(os, "close", close)
    with pytest.raises(OSError, match="Input/output error") as raised:
        FileHelper._windows_create_private(target, b"content")
    monkeypatch.undo()
    assert any("may need deleting" in note for note in raised.value.__notes__)
    assert target.read_bytes() == b"content"


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


@pytest.mark.skipif(sys.platform != "win32", reason="NTFS named streams")
def test_windows_create_private_bytes_refuses_a_named_stream(tmp_path):
    # A stream shares its base file's security descriptor, so it cannot be owner-only.
    path = _seed(tmp_path, b"base")
    with FileHelper(tmp_path) as files, pytest.raises(FileHelperError):
        files.create_private_bytes(REL + ":backup", b"secret")
    assert path.read_bytes() == b"base"
    with pytest.raises(FileNotFoundError):
        open(f"{path}:backup", "rb").close()


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


@pytest.mark.skipif(os.name == "nt", reason="POSIX creation path")
@pytest.mark.parametrize("step", ["write", "fsync", "close"])
def test_posix_create_private_bytes_keeps_the_inode_pinned_during_cleanup(
    tmp_path, monkeypatch, step
):
    # Once nothing holds the created inode its number can be reused, and a
    # replacement could then pass the identity check and be removed.
    (tmp_path / "parent").mkdir()
    real_open, real_dup, real_close, real_stat = os.open, os.dup, os.close, os.stat
    real_step = {"write": os.write, "fsync": os.fsync, "close": real_close}[step]
    pinned: set[int] = set()
    leaf: list[int] = []
    pinned_at_check: list[bool] = []

    def open_(name, flags, *args, **kwargs):
        fd = real_open(name, flags, *args, **kwargs)
        if os.fspath(name) == "file":
            leaf.append(fd)
            pinned.add(fd)
        return fd

    def dup(fd):
        copy = real_dup(fd)
        if fd in pinned:
            pinned.add(copy)
        return copy

    def close(fd):
        pinned.discard(fd)
        real_close(fd)
        if step == "close" and leaf and fd == leaf[0]:
            raise OSError("disk full")

    def fail(fd, *args):
        if leaf and fd == leaf[0]:
            raise OSError("disk full")
        return real_step(fd, *args)

    def stat_(name, *args, **kwargs):
        if os.fspath(name) == "file" and kwargs.get("dir_fd") is not None:
            pinned_at_check.append(bool(pinned))
        return real_stat(name, *args, **kwargs)

    monkeypatch.setattr(os, "open", open_)
    monkeypatch.setattr(os, "dup", dup)
    monkeypatch.setattr(os, "stat", stat_)
    monkeypatch.setattr(os, "close", close)
    if step != "close":
        monkeypatch.setattr(os, step, fail)
    with FileHelper(tmp_path) as files, pytest.raises(OSError, match="disk full"):
        files.create_private_bytes(REL, b"content")
    monkeypatch.undo()
    assert pinned_at_check == [True]
    assert not (tmp_path / REL).exists()
