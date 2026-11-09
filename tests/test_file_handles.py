"""Portable contract checks for the shared Windows handle primitive."""

import ctypes
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
