"""Portable checks of Windows handle flags, validation, and ownership."""

import ctypes
import os
import sys
from ctypes import wintypes
from pathlib import Path
from types import SimpleNamespace

import pytest

from specify_cli import _file_handles


@pytest.fixture
def kernel(monkeypatch):
    calls = []
    closed = []
    state = SimpleNamespace(attributes=0, query_ok=True, handle=123, mask=0)

    def umask(value):
        previous, state.mask = state.mask, value
        return previous

    def create(*args):
        calls.append(args)
        return state.handle

    def query(handle, info_class, output, size):
        assert handle == 123 and info_class == 9
        output._obj.attributes = state.attributes
        return state.query_ok

    api = SimpleNamespace(
        CreateFileW=create,
        GetFileInformationByHandleEx=query,
        CloseHandle=closed.append,
    )
    monkeypatch.setattr(_file_handles, "_windows_api", lambda: api)
    monkeypatch.setattr(_file_handles, "os", SimpleNamespace(**{**vars(os), "umask": umask}))
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 5, raising=False)
    monkeypatch.setattr(ctypes, "WinError", lambda code: OSError(code, "native error"), raising=False)
    return state, calls, closed


@pytest.mark.parametrize("directory", [False, True])
def test_read_handle_retains_existing_access_and_sharing(kernel, directory):
    state, calls, closed = kernel
    state.attributes = 0x10 if directory else 0
    with _file_handles._windows_handle(Path("path"), directory=directory) as handle:
        assert handle == 123
        assert closed == []
        assert calls == [
            ("path", 0x81 if directory else 0x80000000, 0x3, None, 3, 0x02200000, None)
        ]
    assert closed == [123]


@pytest.mark.parametrize("mask", [0, 0o200, 0o400, 0o600])
@pytest.mark.parametrize("query_ok", [False, True])
def test_windows_creation_flags_honor_and_restore_crt_mask(kernel, monkeypatch, mask, query_ok):
    state, calls, closed = kernel
    state.query_ok = query_ok
    current_mask = mask

    def umask(value):
        nonlocal current_mask
        previous, current_mask = current_mask, value
        return previous

    monkeypatch.setattr(_file_handles, "os", SimpleNamespace(umask=umask))
    if query_ok:
        handle = _file_handles._open_windows_handle(Path("path"), directory=False, overwrite=True)
        assert handle == 123
    else:
        with pytest.raises(OSError):
            _file_handles._open_windows_handle(Path("path"), directory=False, overwrite=True)
    assert current_mask == mask
    assert bool(calls[0][5] & 0x1) == bool(mask & 0o200)
    assert closed == ([] if query_ok else [123])


@pytest.mark.parametrize("failure", ["reparse", "directory", "query", "open"])
def test_windows_overwrite_handle_checks_before_transfer(kernel, failure):
    state, calls, closed = kernel
    if failure == "reparse":
        state.attributes = 0x400
    elif failure == "directory":
        state.attributes = 0x10
    elif failure == "query":
        state.query_ok = False
    else:
        state.handle = wintypes.HANDLE(-1).value
    with pytest.raises(OSError):
        _file_handles._open_windows_handle(Path("path"), directory=False, overwrite=True)
    assert calls == [("path", 0x40000080, 0x3, None, 4, 0x02200000, None)]
    assert closed == ([] if failure == "open" else [123])


@pytest.mark.parametrize("failure", [None, "convert", "body"])
def test_overwrite_descriptor_ownership_and_binary_mode(kernel, monkeypatch, failure):
    state, calls, closed_handles = kernel
    closed_fds = []

    def convert(handle, flags):
        assert handle == state.handle
        assert flags == os.O_WRONLY | 0x8000
        if failure == "convert":
            raise OSError("conversion failed")
        return 42

    monkeypatch.setitem(sys.modules, "msvcrt", SimpleNamespace(open_osfhandle=convert))
    monkeypatch.setattr(
        _file_handles, "os",
        SimpleNamespace(
            O_WRONLY=os.O_WRONLY, O_BINARY=0x8000,
            close=closed_fds.append, umask=lambda value: 0,
        ),
    )

    def run():
        with _file_handles._windows_overwrite_fd(Path("path")) as fd:
            assert fd == 42
            assert closed_handles == closed_fds == []
            if failure == "body":
                raise OSError("body failed")

    if failure:
        with pytest.raises(OSError, match="failed"):
            run()
    else:
        run()
    assert calls[0][4] == 4  # OPEN_ALWAYS, never CREATE_ALWAYS.
    assert closed_handles == ([123] if failure == "convert" else [])
    assert closed_fds == ([] if failure == "convert" else [42])
