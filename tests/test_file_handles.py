"""Portable contract checks for the private Windows handle primitive."""

import ctypes
from ctypes import wintypes
from types import SimpleNamespace

import pytest

from specify_cli._file_handles import _windows_handle


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
