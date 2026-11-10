"""Portable checks of Windows handle flags, validation, and ownership."""

import ctypes
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from ctypes import wintypes
from pathlib import Path
from types import SimpleNamespace

import pytest

from specify_cli import _file_handles


@pytest.fixture
def runtime_probe(monkeypatch):
    root = Path("runtime")
    events = []

    @contextmanager
    def temporary_directory(*, prefix):
        assert prefix == "specify-mode-"
        events.append("temporary")
        try:
            yield str(root)
        finally:
            events.append("cleanup")

    @contextmanager
    def pin(path, *, directory):
        assert path == root and directory
        events.append("pin")
        try:
            yield 1
        finally:
            events.append("unpin")

    monkeypatch.setattr(
        _file_handles, "tempfile",
        SimpleNamespace(TemporaryDirectory=temporary_directory), raising=False,
    )
    monkeypatch.setattr(_file_handles, "_windows_handle", pin)
    return root, events


@pytest.fixture
def kernel(monkeypatch):
    calls = []
    closed = []
    state = SimpleNamespace(attributes=0, query_ok=True, handle=123, handles=None)

    def umask(value):
        raise AssertionError("Handle operations must not change the process mask")

    def create(*args):
        calls.append(args)
        return state.handles.pop(0) if state.handles is not None else state.handle

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
def test_existing_windows_overwrite_does_not_query_creation_mask(kernel, monkeypatch, mask, query_ok):
    state, calls, closed = kernel
    state.query_ok = query_ok
    def umask(value):
        raise AssertionError(f"Existing-file open must not query or change mask {mask:o}")

    monkeypatch.setattr(_file_handles, "os", SimpleNamespace(umask=umask))
    if query_ok:
        handle = _file_handles._open_windows_handle(Path("path"), directory=False, overwrite=True)
        assert handle == 123
    else:
        with pytest.raises(OSError):
            _file_handles._open_windows_handle(Path("path"), directory=False, overwrite=True)
    assert calls == [("path", 0x40000080, 0x3, None, 3, 0x02200000, None)]
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
    assert calls == [("path", 0x40000080, 0x3, None, 3, 0x02200000, None)]
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
            close=closed_fds.append,
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
    assert calls[0][4] == 3  # OPEN_EXISTING, never CREATE_ALWAYS.
    assert closed_handles == ([123] if failure == "convert" else [])
    assert closed_fds == ([] if failure == "convert" else [42])


@pytest.mark.parametrize("mask", [0, 0o200, 0o400, 0o600])
@pytest.mark.parametrize("body_failure", [False, True])
def test_windows_creation_probe_uses_crt_mask_without_changing_it(
    monkeypatch, runtime_probe, mask, body_failure
):
    runtime, events = runtime_probe
    created = []
    closed_fds = []
    chmods = []
    removed = []

    def create(path, flags, mode):
        created.append((path, flags, mode))
        return 42

    def umask(value):
        raise AssertionError("Creation must let the CRT apply the mask")

    def inspect(fd):
        assert fd == 42
        if body_failure:
            raise OSError("query failed")
        return SimpleNamespace(st_mode=0o666 & ~mask)

    monkeypatch.setattr(_file_handles, "os", SimpleNamespace(**{
        **vars(os), "O_BINARY": 0x8000, "open": create,
        "close": closed_fds.append, "umask": umask, "fstat": inspect,
        "chmod": lambda path, mode: chmods.append((path, mode)), "unlink": removed.append,
    }))
    monkeypatch.setattr(_file_handles.secrets, "token_hex", lambda size: "a" * (size * 2))
    probe = runtime / f".specify-mode-{'a' * 32}.tmp"
    if body_failure:
        with pytest.raises(OSError, match="query failed"):
            _file_handles._windows_creation_attributes()
    else:
        assert _file_handles._windows_creation_attributes() == (
            0x1 if mask & 0o200 else 0
        )
    assert created == [(probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL | 0x8000, 0o666)]
    assert chmods == [(probe, 0o600)]
    assert removed == [probe]
    assert closed_fds == [42]
    assert events == ["temporary", "pin", "unpin", "cleanup"]


@pytest.mark.parametrize("attributes", [0, 0x1])
@pytest.mark.parametrize("body_failure", [False, True])
def test_missing_windows_leaf_uses_native_no_follow_creation(
    kernel, monkeypatch, attributes, body_failure
):
    state, calls, closed_handles = kernel
    state.handles = [wintypes.HANDLE(-1).value, 123]
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 2)
    closed_fds = []
    probes = []

    def probe():
        probes.append(True)
        return attributes

    monkeypatch.setattr(_file_handles, "_windows_creation_attributes", probe)
    monkeypatch.setattr(_file_handles.os, "O_BINARY", 0x8000, raising=False)
    monkeypatch.setattr(_file_handles.os, "close", closed_fds.append)
    monkeypatch.setitem(
        sys.modules, "msvcrt", SimpleNamespace(open_osfhandle=lambda handle, flags: 42)
    )

    def write():
        with _file_handles._windows_overwrite_fd(Path("parent/new")) as fd:
            assert fd == 42
            if body_failure:
                raise OSError("write failed")

    if body_failure:
        with pytest.raises(OSError, match="write failed"):
            write()
    else:
        write()
    assert probes == [True]
    assert calls[0][4] == 3
    assert calls[1][4:6] == (1, 0x02200000 | attributes)
    assert closed_handles == []
    assert closed_fds == [42]


@pytest.mark.parametrize("error", [FileExistsError, PermissionError, FileNotFoundError])
def test_windows_native_creation_errors_propagate_without_retry(kernel, monkeypatch, error):
    _, _, closed_handles = kernel
    attempted = []

    def open_handle(path, **kwargs):
        attempted.append(kwargs)
        if len(attempted) == 1:
            raise FileNotFoundError("missing")
        raise error("creation failed")

    monkeypatch.setattr(_file_handles, "_open_windows_handle", open_handle)
    monkeypatch.setattr(_file_handles, "_windows_creation_attributes", lambda: 0)
    with pytest.raises(error, match="creation failed"):
        with _file_handles._windows_overwrite_fd(Path("new")):
            pytest.fail("A failed creation yielded a descriptor")
    assert attempted == [
        {"directory": False, "overwrite": True},
        {"directory": False, "overwrite": True, "create_attributes": 0},
    ]
    assert closed_handles == []


def test_interleaved_windows_overwrites_do_not_change_process_mask(kernel, monkeypatch):
    _, calls, _ = kernel
    started = threading.Barrier(2)
    first_changed = threading.Event()
    second_changed = threading.Event()
    first_restored = threading.Event()
    local = threading.local()
    lock = threading.Lock()
    current_mask = 0
    mask_calls = []
    closed = []

    def umask(value):
        nonlocal current_mask
        initial = local.mask_calls == 0
        local.mask_calls += 1
        if initial and local.role == "second":
            assert first_changed.wait(5)
        with lock:
            previous, current_mask = current_mask, value
            mask_calls.append((local.role, value))
        if initial and local.role == "first":
            first_changed.set()
            assert second_changed.wait(5)
        elif initial:
            second_changed.set()
            assert first_restored.wait(5)
        elif local.role == "first":
            first_restored.set()
        return previous

    monkeypatch.setitem(
        sys.modules, "msvcrt", SimpleNamespace(open_osfhandle=lambda handle, flags: 42)
    )
    monkeypatch.setattr(
        _file_handles, "os",
        SimpleNamespace(O_WRONLY=os.O_WRONLY, O_BINARY=0x8000, close=closed.append, umask=umask),
    )

    def overwrite(role):
        local.role = role
        local.mask_calls = 0
        started.wait(5)
        with _file_handles._windows_overwrite_fd(Path(role)) as fd:
            assert fd == 42

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(overwrite, role) for role in ("first", "second")]
        for future in futures:
            future.result(timeout=10)
    assert current_mask == 0
    assert mask_calls == []
    assert all(not call[5] & 0x1 for call in calls)
    assert closed == [42, 42]


def test_missing_windows_leaf_does_not_require_project_delete_rights(
    kernel, runtime_probe, monkeypatch
):
    state, calls, closed_handles = kernel
    state.handles = [wintypes.HANDLE(-1).value, 123]
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 2)
    runtime, events = runtime_probe
    created = []
    deleted = []
    closed = []

    def create(path, flags, mode):
        created.append(Path(path))
        return 100

    def unlink(path):
        path = Path(path)
        if path.parent == Path("project"):
            raise PermissionError("Project grants creation but not deletion")
        deleted.append(path)

    monkeypatch.setattr(_file_handles, "os", SimpleNamespace(**{
        **vars(os), "O_BINARY": 0x8000, "open": create,
        "fstat": lambda fd: SimpleNamespace(st_mode=0o666),
        "chmod": lambda path, mode: None, "unlink": unlink, "close": closed.append,
    }))
    monkeypatch.setitem(
        sys.modules, "msvcrt", SimpleNamespace(open_osfhandle=lambda handle, flags: 42)
    )
    with _file_handles._windows_overwrite_fd(Path("project/new")) as fd:
        assert fd == 42
    assert len(created) == 1 and created[0].parent == runtime
    assert deleted == created
    assert events == ["temporary", "pin", "unpin", "cleanup"]
    assert closed == [100, 42]
    assert closed_handles == []
    assert calls[1][4] == 1
