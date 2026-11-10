"""Ownership and native Windows evidence for shared handle primitives."""

from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from specify_cli import _file_handles, file_helper
from specify_cli._file_handles import _windows_handle
from specify_cli.file_helper import FileHelper, UnsupportedPathError


@pytest.mark.parametrize("failure", [None, "duplicate", "convert", "body"])
def test_windows_read_fd_duplicates_and_closes_only_its_owned_handle(tmp_path, monkeypatch, failure):
    selected = tmp_path / "file"
    selected.write_bytes(b"inside")
    original = os.open(selected, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    duplicates = []
    closed_handles = []

    def duplicate(source_process, handle, target_process, access, inherit, options):
        assert (source_process, handle, target_process, access, inherit, options) == (
            7, original, 7, 0, False, 2,
        )
        if failure == "duplicate":
            raise OSError("injected duplicate failure")
        fd = os.dup(handle)
        duplicates.append(fd)
        return fd

    def convert(handle, flags):
        assert handle == duplicates[-1]
        assert flags == 0x8000
        if failure == "convert":
            raise OSError("injected conversion failure")
        return handle

    def close(handle):
        closed_handles.append(handle)
        os.close(handle)

    monkeypatch.setitem(sys.modules, "_winapi", SimpleNamespace(
        GetCurrentProcess=lambda: 7, DuplicateHandle=duplicate,
        DUPLICATE_SAME_ACCESS=2, CloseHandle=close,
    ))
    monkeypatch.setitem(sys.modules, "msvcrt", SimpleNamespace(open_osfhandle=convert))
    monkeypatch.setattr(_file_handles, "os", SimpleNamespace(
        O_RDONLY=0, O_BINARY=0x8000, close=os.close,
    ))
    try:
        if failure:
            with pytest.raises(OSError, match="injected"):
                with _file_handles.windows_read_fd(original):
                    raise OSError("injected body failure")
        else:
            with _file_handles.windows_read_fd(original) as fd:
                assert os.read(fd, 6) == b"inside"
                assert not os.get_inheritable(fd)
        assert closed_handles == (duplicates if failure == "convert" else [])
        assert os.fstat(original).st_size == 6
        for fd in duplicates:
            with pytest.raises(OSError):
                os.fstat(fd)
    finally:
        os.close(original)


def _set_windows_symlink_reparse(path: Path, target: Path) -> None:
    import ctypes
    from ctypes import wintypes
    import _winapi

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    control = kernel.DeviceIoControl
    control.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
        wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
    ]
    control.restype = wintypes.BOOL
    template = target.with_name("reparse-template")
    template.symlink_to(target)
    try:
        buffer = ctypes.create_string_buffer(16 * 1024)
        returned = wintypes.DWORD()
        source = _winapi.CreateFile(str(template), 0, 0x7, 0, 3, 0x02200000, 0)
        try:
            if not control(source, 0x900A8, None, 0, buffer, len(buffer), ctypes.byref(returned), None):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            _winapi.CloseHandle(source)
        handle = _winapi.CreateFile(str(path), 0x40000000, 0x7, 0, 3, 0x02200000, 0)
        try:
            if not control(handle, 0x900A4, buffer, returned.value, None, 0, ctypes.byref(returned), None):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            _winapi.CloseHandle(handle)
    finally:
        template.unlink()


@pytest.mark.parametrize("failure", [None, "get", "set"])
def test_reparse_fixture_copies_native_buffer_and_cleans_up(tmp_path, monkeypatch, failure):
    import ctypes
    from ctypes import wintypes

    target = tmp_path / "outside"
    target.write_bytes(b"outside")
    probe = tmp_path / "probe"
    try:
        probe.symlink_to(target)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")
    probe.unlink()
    opened = []
    closed = []
    payload = b"OS-generated reparse buffer"

    def create(path, access, sharing, security, disposition, flags, template):
        assert (sharing, security, disposition, flags, template) == (7, 0, 3, 0x02200000, 0)
        assert access == (0 if not opened else 0x40000000)
        opened.append(len(opened) + 1)
        return opened[-1]

    class Control:
        def __call__(self, handle, code, source, source_size, destination, size, returned, overlapped):
            if code == 0x900A8:
                assert handle == 1 and source is None and source_size == 0
                if failure == "get":
                    return False
                ctypes.memmove(destination, payload, len(payload))
                ctypes.cast(returned, ctypes.POINTER(wintypes.DWORD))[0] = len(payload)
            else:
                assert code == 0x900A4 and handle == 2
                assert ctypes.string_at(source, source_size) == payload
                if failure == "set":
                    return False
            return True

    monkeypatch.setitem(sys.modules, "_winapi", SimpleNamespace(CreateFile=create, CloseHandle=closed.append))
    monkeypatch.setattr(ctypes, "WinDLL", lambda *args, **kwargs: SimpleNamespace(DeviceIoControl=Control()), raising=False)
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 5, raising=False)
    monkeypatch.setattr(ctypes, "WinError", lambda code: OSError("injected native failure"), raising=False)
    if failure:
        with pytest.raises(OSError, match="injected native failure"):
            _set_windows_symlink_reparse(tmp_path / "file", target)
    else:
        _set_windows_symlink_reparse(tmp_path / "file", target)
    assert closed == opened
    assert not (tmp_path / "reparse-template").is_symlink()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows reparse changes required")
@pytest.mark.parametrize("allow", [False, True])
def test_windows_read_never_reopens_leaf_after_in_place_reparse_change(tmp_path, monkeypatch, allow):
    root = tmp_path / "project"
    root.mkdir()
    selected = root / "file"
    selected.write_bytes(b"")
    outside = tmp_path / "outside"
    outside.write_bytes(b"outside")
    changed = False

    @contextmanager
    def change_after_validation(path, **kwargs):
        nonlocal changed
        with _file_handles._windows_handle(path, **kwargs) as handle:
            if not kwargs["directory"]:
                try:
                    _set_windows_symlink_reparse(path, outside)
                except OSError as exc:
                    if exc.winerror in (50, 1314):
                        pytest.skip(f"Symlink reparse updates unavailable: {exc}")
                    raise
                assert path.read_bytes() == b"outside"
                changed = True
            yield handle

    monkeypatch.setattr(file_helper, "_windows_handle", change_after_validation)
    try:
        content = FileHelper(root, allow_symlinks=allow).read_bytes(selected)
    except UnsupportedPathError:
        pass
    else:
        assert content == b""
    assert changed


@pytest.mark.skipif(os.name != "nt", reason="Native Windows sharing semantics required")
def test_windows_read_directory_pin_prevents_writable_reparse_handle(tmp_path):
    import _winapi

    def writable_handle():
        return _winapi.CreateFile(str(tmp_path), 0x40000000, 0x7, 0, 3, 0x02200000, 0)

    _winapi.CloseHandle(writable_handle())
    with _file_handles._windows_handle(tmp_path, directory=True, share_write=False):
        with pytest.raises(OSError) as error:
            writable_handle()
        assert error.value.winerror == 32
    _winapi.CloseHandle(writable_handle())
@pytest.mark.parametrize("directory", [False, True])
def test_windows_handle_declares_complete_createfile_prototype(tmp_path, monkeypatch, directory):
    closed = []

    def create(*args):
        assert create.argtypes == [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        assert create.restype is wintypes.HANDLE
        assert args == (
            str(tmp_path),
            (0x80 | 0x1) if directory else 0x80000000,
            0x3,
            None,
            3,
            0x00200000 | 0x02000000,
            None,
        )
        return 123

    def info(handle, info_class, buffer, size):
        assert handle == 123 and info_class == 9
        assert size == 2 * ctypes.sizeof(wintypes.DWORD)
        attributes = ctypes.cast(buffer, ctypes.POINTER(wintypes.DWORD))
        attributes[0] = 0x10 if directory else 0
        return True

    def close(handle):
        closed.append(handle)
        return True

    def load_kernel(name, *, use_last_error):
        assert name == "kernel32" and use_last_error
        return SimpleNamespace(
            CreateFileW=create, GetFileInformationByHandleEx=info, CloseHandle=close
        )

    monkeypatch.setattr(ctypes, "WinDLL", load_kernel, raising=False)
    with _windows_handle(tmp_path, directory=directory) as handle:
        assert handle == 123
        assert closed == []
    assert closed == [123]
