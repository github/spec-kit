"""Portable contract checks for the private Windows handle primitive."""

import ctypes
from ctypes import wintypes
import errno
from pathlib import Path
from types import SimpleNamespace

import pytest

from specify_cli._file_handles import _windows_handle


@pytest.mark.parametrize("directory", [False, True])
@pytest.mark.parametrize("outcome", ["success", "reparse", "wrong-type", "query-failure", "body-failure", "open-failure"])
def test_windows_handle_flags_validation_and_cleanup(monkeypatch, directory, outcome):
    calls = []

    def create(*args):
        calls.append(("open", args))
        return ctypes.c_void_p(-1).value if outcome == "open-failure" else 123

    def info(handle, kind, buffer, size):
        assert handle == 123 and kind == 9
        attributes = 0x10 if directory else 0
        if outcome == "reparse":
            attributes |= 0x400
        if outcome == "wrong-type":
            attributes ^= 0x10
        buffer._obj.attributes = attributes
        return outcome != "query-failure"

    def close(handle):
        calls.append(("close", handle))
        return True

    # Real ctypes functions accept signature attributes; plain Python functions
    # do too, allowing this contract to run without loading a Windows DLL.
    kernel = SimpleNamespace(
        CreateFileW=create, GetFileInformationByHandleEx=info, CloseHandle=close
    )
    monkeypatch.setattr(ctypes, "WinDLL", lambda *args, **kwargs: kernel, raising=False)
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 5, raising=False)
    monkeypatch.setattr(
        ctypes, "WinError", lambda code: PermissionError(code, "handle denied"), raising=False
    )

    def use():
        with _windows_handle(Path("selected"), directory=directory) as handle:
            assert handle == 123
            assert calls == [calls[0]]
            if outcome == "body-failure":
                raise RuntimeError("body failed")

    if outcome == "success":
        use()
    elif outcome == "body-failure":
        with pytest.raises(RuntimeError, match="body failed"):
            use()
    else:
        with pytest.raises(OSError) as exc:
            use()
        if outcome in ("reparse", "wrong-type"):
            assert exc.value.errno == (errno.ELOOP if outcome == "reparse" else errno.EINVAL)
    args = calls[0][1]
    assert args == (
        "selected", 0x81 if directory else 0x80000000,
        0x3, None, 3, 0x00200000 | 0x02000000, None,
    )
    assert calls[1:] == ([] if outcome == "open-failure" else [("close", 123)])


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
