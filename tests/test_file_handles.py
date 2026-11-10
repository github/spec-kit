"""Portable checks of Windows handle flags, validation, and ownership."""

import ctypes
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from ctypes import wintypes
import errno
from pathlib import Path
from types import SimpleNamespace

import pytest

from specify_cli import _file_handles
from specify_cli import _file_handles as handles
from specify_cli._file_handles import _windows_file_id, _windows_handle, _windows_stat


@pytest.mark.parametrize("directory", [False, True])
@pytest.mark.parametrize("pin", [False, True])
@pytest.mark.parametrize("outcome", ["success", "reparse", "wrong-type", "query-failure", "body-failure", "open-failure"])
def test_windows_handle_flags_validation_and_cleanup(monkeypatch, directory, pin, outcome):
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
        with _windows_handle(Path("selected"), directory=directory, pin=pin) as handle:
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
        "selected", (0x81 if directory else 0x80000000) if pin else 0x80,
        0x3 if pin else 0x7, None, 3, 0x00200000 | 0x02000000, None,
    )
    assert calls[1:] == ([] if outcome == "open-failure" else [("close", 123)])


@pytest.mark.parametrize("failure", [False, True])
def test_windows_file_identity_uses_full_volume_and_file_id(monkeypatch, failure):
    def info(handle, kind, buffer, size):
        assert handle == 0x1FFFFFFFF and kind == 18 and size == 24
        buffer._obj.volume = 0x1FFFFFFFF
        buffer._obj.file_id[:] = bytes(range(16))
        return not failure

    monkeypatch.setattr(
        ctypes, "WinDLL",
        lambda *args, **kwargs: SimpleNamespace(GetFileInformationByHandleEx=info),
        raising=False,
    )
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 5, raising=False)
    monkeypatch.setattr(ctypes, "WinError", lambda code: PermissionError(code, "identity denied"), raising=False)
    if failure:
        with pytest.raises(PermissionError, match="identity denied"):
            _windows_file_id(0x1FFFFFFFF)
    else:
        assert _windows_file_id(0x1FFFFFFFF) == (0x1FFFFFFFF, bytes(range(16)))
    assert info.argtypes == [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
    assert info.restype is wintypes.BOOL


@pytest.mark.parametrize("failure", [None, "duplicate", "convert", "stat"])
def test_windows_stat_preserves_borrowed_handle_and_closes_duplicate(tmp_path, monkeypatch, failure):
    expected = tmp_path.stat()
    closed = []

    def duplicate(source_process, handle, target_process, access, inherit, options):
        assert source_process == target_process == 0x1FFFFFFFF
        assert handle == 0x2FFFFFFFF
        assert access == 0 and inherit is False and options == 2
        if failure == "duplicate":
            raise OSError("duplicate failed")
        return 456

    def convert(handle, flags):
        assert handle == 456 and flags == 128
        if failure == "convert":
            raise OSError("convert failed")
        return 789

    def fstat(fd):
        assert fd == 789
        if failure == "stat":
            raise OSError("stat failed")
        return expected

    monkeypatch.setitem(sys.modules, "_winapi", SimpleNamespace(
        GetCurrentProcess=lambda: 0x1FFFFFFFF,
        DuplicateHandle=duplicate,
        DUPLICATE_SAME_ACCESS=2,
        CloseHandle=lambda handle: closed.append(("handle", handle)),
    ))
    monkeypatch.setitem(sys.modules, "msvcrt", SimpleNamespace(open_osfhandle=convert))
    monkeypatch.setattr(handles, "os", SimpleNamespace(
        O_RDONLY=0, O_NOINHERIT=128, fstat=fstat, close=lambda fd: closed.append(("fd", fd)),
    ))
    if failure:
        with pytest.raises(OSError, match=f"{failure} failed"):
            _windows_stat(0x2FFFFFFFF)
    else:
        assert _windows_stat(0x2FFFFFFFF) is expected
    assert closed == {
        None: [("fd", 789)], "duplicate": [], "convert": [("handle", 456)], "stat": [("fd", 789)],
    }[failure]


@pytest.mark.skipif(os.name != "nt", reason="Native Windows directory-handle metadata")
def test_native_windows_stat_matches_path_metadata_without_closing_reference(tmp_path):
    with _windows_handle(tmp_path, directory=True, pin=False) as handle:
        identity = _windows_file_id(handle)
        assert os.path.samestat(tmp_path.stat(), _windows_stat(handle))
        assert _windows_file_id(handle) == identity


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

    def unexpected_probe():
        raise AssertionError("Existing-file overwrites must not probe creation attributes")

    monkeypatch.setattr(_file_handles, "_windows_creation_attributes", unexpected_probe)
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


def test_concurrent_windows_overwrites_do_not_query_process_mask(kernel, monkeypatch):
    _, calls, closed_handles = kernel
    closed = []
    monkeypatch.setitem(
        sys.modules, "msvcrt", SimpleNamespace(open_osfhandle=lambda handle, flags: 42)
    )
    monkeypatch.setattr(_file_handles.os, "O_BINARY", 0x8000, raising=False)
    monkeypatch.setattr(_file_handles.os, "close", closed.append)

    def overwrite(name):
        with _file_handles._windows_overwrite_fd(Path(name)) as fd:
            assert fd == 42

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(overwrite, ("first", "second")))
    assert {call[0] for call in calls} == {"first", "second"}
    assert len(calls) == 2
    assert all(call[4] == 3 and not call[5] & 0x1 for call in calls)
    assert closed_handles == []
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
