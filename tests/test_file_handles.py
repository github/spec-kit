"""Ownership and native Windows evidence for shared handle primitives."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import errno
import gc
import os
from pathlib import Path
import sys
import subprocess
from types import SimpleNamespace
import weakref

import pytest

from specify_cli import _file_handles, file_helper
from specify_cli._file_handles import _windows_handle
from specify_cli.file_helper import FileHelper, UnsupportedPathError


@pytest.mark.skipif(os.name == "nt", reason="POSIX startup must not require Windows ctypes support")
@pytest.mark.parametrize("operation", ["help", "files"])
def test_posix_usage_without_optional_ctypes(tmp_path, operation):
    result = subprocess.run(
        [sys.executable, "-c", """
import sys

class NoCtypes:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "_ctypes":
            raise ModuleNotFoundError("optional _ctypes unavailable", name="_ctypes")

for name in tuple(sys.modules):
    if name == "_ctypes" or name == "ctypes" or name.startswith("ctypes."):
        sys.modules.pop(name)
sys.meta_path.insert(0, NoCtypes())

if sys.argv[1] == "help":
    from specify_cli import main
    sys.argv = ["specify", "--help"]
    main()
else:
    from pathlib import Path
    from specify_cli.file_helper import FileHelper

    root = Path(sys.argv[2])
    for allow in (False, True):
        files = FileHelper(root, allow_symlinks=allow)
        files.mkdir("nested")
        files.create_text("nested/file", "inside")
        assert files.read_text("nested/file") == "inside"
        files.write_text("nested/file", "updated")
        if allow:
            files.symlink("file", "nested/alias")
            assert files.read_text("nested/alias") == "updated"
        files.delete("nested", recursive=True)
    assert "specify_cli._windows_abi" not in sys.modules
    assert "_ctypes" not in sys.modules
""", operation, str(tmp_path)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    if operation == "help":
        assert "Usage" in result.stdout


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


def _set_windows_symlink_reparse(
    path: Path, target: Path, *, junction: bool = False, access: int = 0x40000000,
) -> None:
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
    if junction:
        _winapi.CreateJunction(str(target), str(template))
    else:
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
        handle = _winapi.CreateFile(str(path), access, 0x7, 0, 3, 0x02200000, 0)
        try:
            if not control(handle, 0x900A4, buffer, returned.value, None, 0, ctypes.byref(returned), None):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            _winapi.CloseHandle(handle)
    finally:
        if junction:
            template.rmdir()
        else:
            template.unlink()


@pytest.mark.parametrize("failure", [None, "get", "set"])
@pytest.mark.parametrize("junction", [False, True])
def test_reparse_fixture_copies_native_buffer_and_cleans_up(tmp_path, monkeypatch, failure, junction):
    import ctypes
    from ctypes import wintypes

    target = tmp_path / "outside"
    target.write_bytes(b"outside")
    if not junction:
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
        assert access == (0 if not opened else 0x100 if junction else 0x40000000)
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

    monkeypatch.setitem(sys.modules, "_winapi", SimpleNamespace(
        CreateFile=create, CloseHandle=closed.append,
        CreateJunction=lambda target, path: Path(path).mkdir(),
    ))
    monkeypatch.setattr(ctypes, "WinDLL", lambda *args, **kwargs: SimpleNamespace(DeviceIoControl=Control()), raising=False)
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 5, raising=False)
    monkeypatch.setattr(ctypes, "WinError", lambda code: OSError("injected native failure"), raising=False)
    if failure:
        with pytest.raises(OSError, match="injected native failure"):
            _set_windows_symlink_reparse(
                tmp_path / "file", target, junction=junction, access=0x100 if junction else 0x40000000,
            )
    else:
        _set_windows_symlink_reparse(
            tmp_path / "file", target, junction=junction, access=0x100 if junction else 0x40000000,
        )
    assert closed == opened
    assert not (tmp_path / "reparse-template").is_symlink()
    assert not (tmp_path / "reparse-template").exists()


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
                    _set_windows_symlink_reparse(selected, outside)
                except OSError as exc:
                    if exc.winerror in (50, 1314):
                        pytest.skip(f"Symlink reparse updates unavailable: {exc}")
                    raise
                assert selected.read_bytes() == b"outside"
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
def test_windows_traversal_pin_allows_writes_but_prevents_rename(tmp_path):
    import _winapi

    def writable_handle():
        return _winapi.CreateFile(str(tmp_path), 0x40000000, 0x7, 0, 3, 0x02200000, 0)

    _winapi.CloseHandle(writable_handle())
    with _file_handles._windows_handle(tmp_path, directory=True, traverse=True):
        _winapi.CloseHandle(writable_handle())
        with pytest.raises(OSError) as error:
            tmp_path.rename(tmp_path.with_name(tmp_path.name + "-renamed"))
        assert error.value.winerror == 32
    _winapi.CloseHandle(writable_handle())


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


@pytest.mark.parametrize("options", [{"overwrite": True}, {"create_attributes": 0}])
def test_relative_read_handles_reject_mutating_modes(options):
    with pytest.raises(ValueError, match="Relative Windows handle opens"):
        _file_handles._open_windows_handle(Path("file"), directory=False, parent=51, **options)


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


@pytest.mark.parametrize("directory,traverse", [(False, False), (True, False), (True, True)])
def test_windows_handle_declares_complete_createfile_prototype(tmp_path, monkeypatch, directory, traverse):
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
            (0x80 | (0x20 if traverse else 0x1)) if directory else 0x80000000,
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
    with _windows_handle(tmp_path, directory=directory, traverse=traverse) as handle:
        assert handle == 123
        assert closed == []
    assert closed == [123]


@pytest.mark.parametrize("directory", [False, True])
@pytest.mark.parametrize("failure", [None, "status", "reparse", "type", "info", "empty"])
@pytest.mark.parametrize("child_name", ["caf\u00e9", "face \U0001f600", "surrogate\ud800"])
def test_windows_child_open_is_relative_and_closes_handles(monkeypatch, directory, failure, child_name):
    closed = []
    abi_types = {role: set() for role in (
        "name", "attributes", "status_value", "status",
        "name_pointer", "attributes_pointer", "status_pointer",
    )}

    def create_path(*args):
        pytest.fail("A child must not be opened by absolute pathname")

    def create_child(output, access, attributes, status, allocation, file_attributes,
                     sharing, disposition, options, ea, ea_length):
        assert create_child.restype is ctypes.c_int32
        attributes = attributes._obj
        declarations = (
            type(attributes.ObjectName.contents), type(attributes), type(status._obj.Value),
            type(status._obj), type(attributes.ObjectName),
            create_child.argtypes[2], create_child.argtypes[3],
        )
        for role, declaration in zip(abi_types, declarations):
            abi_types[role].add(weakref.ref(declaration))
        assert attributes.Length == ctypes.sizeof(type(attributes))
        assert attributes.RootDirectory == 51
        assert attributes.Attributes == 0x1040
        assert attributes.SecurityDescriptor is None
        assert attributes.SecurityQualityOfService is None
        name = attributes.ObjectName.contents
        length = len(child_name.encode("utf-16-le", errors="surrogatepass"))
        assert (name.Buffer, name.Length, name.MaximumLength) == (child_name, length, length + 2)
        assert access == (0xA0 if directory else 0x80100000)
        assert sharing == 3 and disposition == 1
        assert options == (0x200001 if directory else 0x200060)
        assert allocation is None and file_attributes == 0 and ea is None and ea_length == 0
        assert ctypes.sizeof(status._obj) == 2 * ctypes.sizeof(ctypes.c_void_p)
        if failure == "status":
            return -1073741790
        if failure != "empty":
            output._obj.value = 77
        return 0

    def info(handle, info_class, buffer, size):
        assert handle == 77 and info_class == 9
        attributes = ctypes.cast(buffer, ctypes.POINTER(wintypes.DWORD))
        attributes[0] = 0x10 if directory else 0
        if failure == "reparse":
            attributes[0] |= 0x400
        if failure == "type":
            attributes[0] ^= 0x10
        return failure != "info"

    def close(handle):
        closed.append(handle)
        return True

    def error(status):
        assert status == -1073741790
        return 5

    def load(name, **kwargs):
        if name == "ntdll":
            return SimpleNamespace(NtCreateFile=create_child, RtlNtStatusToDosError=error)
        assert name == "kernel32" and kwargs == {"use_last_error": True}
        return SimpleNamespace(
            CreateFileW=create_path, GetFileInformationByHandleEx=info, CloseHandle=close,
        )

    monkeypatch.setattr(ctypes, "WinDLL", load, raising=False)
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 5, raising=False)
    monkeypatch.setattr(ctypes, "WinError", lambda code: PermissionError(errno.EACCES, "native denied"), raising=False)
    for iteration in range(32):
        if failure:
            with pytest.raises(OSError):
                with _windows_handle(Path(child_name), directory=directory, traverse=directory, parent=51):
                    pytest.fail("A failing native open must not yield a handle")
        else:
            with _windows_handle(Path(child_name), directory=directory, traverse=directory, parent=51) as handle:
                assert handle == 77 and len(closed) == iteration
    assert closed == ([] if failure in ("status", "empty") else [77] * 32)
    gc.collect()
    assert {role: len(declarations) for role, declarations in abi_types.items()} == dict.fromkeys(abi_types, 1)


@pytest.mark.skipif(os.name != "nt", reason="Native Windows repeated-read lifetime regression")
@pytest.mark.parametrize("allow", [False, True])
def test_repeated_windows_reads_do_not_accumulate_abi_types(tmp_path, allow):
    root = tmp_path / "project"
    selected = root / "nested/file"
    selected.parent.mkdir(parents=True)
    selected.write_bytes(b"inside")
    files = FileHelper(root, allow_symlinks=allow)
    abi_modules = {_file_handles.__name__, f"{_file_handles.__package__}._windows_abi"}

    def live_abi_types():
        return {
            weakref.ref(obj) for obj in gc.get_objects()
            if isinstance(obj, type) and getattr(obj, "__module__", None) in abi_modules
        }

    for _ in range(32):
        assert files.read_bytes("nested/file") == b"inside"
    gc.collect()
    baseline = live_abi_types()
    assert baseline
    for _ in range(256):
        assert files.read_bytes("nested/file") == b"inside"
    gc.collect()
    assert live_abi_types() == baseline


@pytest.mark.parametrize("name", ["", ".", "..", "../file", "dir/file", "dir\\file", "C:outside", "C:\\outside", "\0"])
def test_windows_child_open_rejects_non_component_names(name):
    with pytest.raises(ValueError, match="single relative"):
        _file_handles._open_windows_child(51, name, directory=False, access=0, sharing=3)


def test_windows_child_open_rejects_oversized_unicode_name():
    with pytest.raises(OSError) as error:
        _file_handles._open_windows_child(51, "a" * 32767, directory=False, access=0, sharing=3)
    assert error.value.errno == errno.ENAMETOOLONG


@pytest.mark.skipif(os.name != "nt", reason="Native Windows attribute-only junction changes required")
@pytest.mark.parametrize("allow", [False, True])
@pytest.mark.parametrize("level", ["root", "parent"])
def test_windows_read_anchors_children_after_attribute_only_junction_change(tmp_path, monkeypatch, allow, level):
    root = tmp_path / "project"
    root.mkdir()
    root = root.resolve()
    directory = root / "directory"
    directory.mkdir()
    selected = directory / "file"
    selected.write_bytes(b"inside")
    outside = tmp_path / "outside"
    outside_directory = outside / "directory" if level == "root" else outside
    outside_directory.mkdir(parents=True)
    (outside_directory / "file").write_bytes(b"outside")
    locations = {}
    changed = False

    @contextmanager
    def exchange(path, **kwargs):
        nonlocal changed
        parent = kwargs.get("parent")
        actual = path if parent is None else locations[parent] / path
        with _file_handles._windows_handle(path, **kwargs) as handle:
            locations[handle] = actual
            try:
                if kwargs["directory"] and actual == (root if level == "root" else directory):
                    displaced = directory if level == "root" else selected
                    displaced.rename(tmp_path / "retained")
                    _set_windows_symlink_reparse(actual, outside, junction=True, access=0x100)
                    changed = True
                    # The former full-path open follows this same converted parent.
                    with _windows_handle(selected, directory=False) as old_handle:
                        with _file_handles.windows_read_fd(old_handle) as fd:
                            assert os.read(fd, 7) == b"outside"
                yield handle
            finally:
                locations.pop(handle)

    monkeypatch.setattr(file_helper, "_windows_handle", exchange)
    try:
        content = FileHelper(root, allow_symlinks=allow).read_bytes(selected)
    except (OSError, ValueError):
        pass
    else:
        assert content == b"inside"
    assert changed


@pytest.mark.skipif(os.name != "nt", reason="Native Windows ACL semantics required")
@pytest.mark.parametrize("restricted", ["root", "parent"])
@pytest.mark.parametrize("allow", [False, True])
def test_windows_reads_do_not_require_folder_listing(tmp_path, restricted, allow):
    from specify_cli._file_policy import read_project_options

    root = tmp_path / "project"
    directory = root / ".specify"
    directory.mkdir(parents=True)
    selected = directory / "init-options.json"
    payload = b'{"allow_symlinks": false}'
    selected.write_bytes(payload)
    limited = root if restricted == "root" else directory
    subprocess.run(
        ["icacls", str(limited), "/deny", "*S-1-1-0:(RD)"], check=True, capture_output=True,
    )
    try:
        assert selected.read_bytes() == payload
        with pytest.raises(PermissionError):
            list(limited.iterdir())
        with pytest.raises(PermissionError):
            with _windows_handle(limited, directory=True):
                pytest.fail("The former listing-mode pin must be denied by this ACL")
        assert FileHelper(root, allow_symlinks=allow).read_bytes(selected) == payload
        assert read_project_options(root)["allow_symlinks"] is False
    finally:
        subprocess.run(
            ["icacls", str(limited), "/remove:d", "*S-1-1-0"], check=True, capture_output=True,
        )
