"""Ownership and native Windows evidence for shared handle primitives."""

from contextlib import contextmanager
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace

import pytest

from specify_cli import _file_handles, file_helper
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

    name = str(target.resolve())
    substitute = "\\??\\UNC\\" + name[2:] if name.startswith("\\\\") else "\\??\\" + name
    encoded_substitute = substitute.encode("utf-16-le")
    encoded_name = name.encode("utf-16-le")
    names = encoded_substitute + b"\0\0" + encoded_name + b"\0\0"
    data = struct.pack(
        "<IHHHHHHI", 0xA000000C, 12 + len(names), 0,
        0, len(encoded_substitute), len(encoded_substitute) + 2, len(encoded_name), 0,
    ) + names
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    control = kernel.DeviceIoControl
    control.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
        wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
    ]
    control.restype = wintypes.BOOL
    handle = _winapi.CreateFile(str(path), 0x40000000, 0x7, 0, 3, 0x02200000, 0)
    try:
        buffer = ctypes.create_string_buffer(data)
        returned = wintypes.DWORD()
        if not control(handle, 0x900A4, buffer, len(data), None, 0, ctypes.byref(returned), None):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        _winapi.CloseHandle(handle)


@pytest.mark.skipif(os.name != "nt", reason="Native Windows reparse changes required")
@pytest.mark.parametrize("allow", [False, True])
def test_windows_read_never_reopens_leaf_after_in_place_reparse_change(tmp_path, monkeypatch, allow):
    root = tmp_path / "project"
    root.mkdir()
    selected = root / "file"
    selected.write_bytes(b"inside")
    outside = tmp_path / "outside"
    outside.write_bytes(b"outside")
    changed = False

    @contextmanager
    def change_after_validation(path, **kwargs):
        nonlocal changed
        with _file_handles.windows_handle(path, **kwargs) as handle:
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

    monkeypatch.setattr(file_helper, "windows_handle", change_after_validation)
    try:
        content = FileHelper(root, allow_symlinks=allow).read_bytes(selected)
    except UnsupportedPathError:
        pass
    else:
        assert content == b"inside"
    assert changed


@pytest.mark.skipif(os.name != "nt", reason="Native Windows sharing semantics required")
def test_windows_read_directory_pin_prevents_writable_reparse_handle(tmp_path):
    import _winapi

    def writable_handle():
        return _winapi.CreateFile(str(tmp_path), 0x40000000, 0x7, 0, 3, 0x02200000, 0)

    _winapi.CloseHandle(writable_handle())
    with _file_handles.windows_handle(tmp_path, directory=True, share_write=False):
        with pytest.raises(OSError) as error:
            writable_handle()
        assert error.value.winerror == 32
    _winapi.CloseHandle(writable_handle())
