"""Private platform handles for confined filesystem operations."""

from collections.abc import Iterator
from contextlib import contextmanager
import errno
import os
import secrets
import stat
import tempfile
from pathlib import Path, PureWindowsPath


def _open_windows_child(parent: int, name: str, *, directory: bool, access: int, sharing: int) -> int:
    """Open one component relative to an already validated directory handle."""
    if PureWindowsPath(name).parts != (name,) or PureWindowsPath(name).anchor or name == ".." or "\0" in name:
        raise ValueError(f"Expected a single relative Windows path component: {name!r}")
    encoded_length = len(name.encode("utf-16-le", errors="surrogatepass"))
    if encoded_length > 65532:
        raise OSError(errno.ENAMETOOLONG, "Windows path component is too long", name)

    import ctypes
    from ctypes import wintypes
    from . import _windows_abi as abi

    native = ctypes.WinDLL("ntdll")
    create = native.NtCreateFile
    create.argtypes = [
        ctypes.POINTER(wintypes.HANDLE), ctypes.c_uint32,
        abi._ObjectAttributesPointer, abi._IoStatusBlockPointer,
        wintypes.LPVOID, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
        ctypes.c_uint32, wintypes.LPVOID, ctypes.c_uint32,
    ]
    create.restype = ctypes.c_int32
    dos_error = native.RtlNtStatusToDosError
    dos_error.argtypes = [ctypes.c_int32]
    dos_error.restype = ctypes.c_uint32
    buffer = ctypes.create_unicode_buffer(name)
    unicode_name = abi._UnicodeString(
        encoded_length, encoded_length + 2, ctypes.cast(buffer, wintypes.LPWSTR)
    )
    # OBJ_DONT_REPARSE and FILE_OPEN_REPARSE_POINT keep resolution on this handle.
    attributes = abi._ObjectAttributes(
        ctypes.sizeof(abi._ObjectAttributes), parent, ctypes.pointer(unicode_name),
        0x40 | 0x1000, None, None,
    )
    handle = wintypes.HANDLE()
    status = abi._IoStatusBlock()
    options = 0x00200000 | (0x1 if directory else 0x40 | 0x20)
    result = create(
        ctypes.byref(handle), access | (0 if directory else 0x100000),
        ctypes.byref(attributes), ctypes.byref(status), None, 0,
        sharing, 1, options, None, 0,
    )
    if result < 0:
        raise ctypes.WinError(dos_error(result))
    if not handle.value:
        raise OSError(errno.EBADF, "Native child open returned no handle", name)
    return handle.value


def _windows_api():
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.GetFileInformationByHandleEx.argtypes = [
        wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD
    ]
    kernel.GetFileInformationByHandleEx.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    return kernel


def _open_windows_handle(
    path: Path, *, directory: bool, overwrite: bool = False,
    create_attributes: int | None = None, parent: int | None = None, traverse: bool = False,
) -> int:
    if parent is not None and (overwrite or create_attributes is not None):
        raise ValueError("Relative Windows handle opens do not support creation or overwrite")
    import ctypes
    from ctypes import wintypes

    class AttributeTagInfo(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("tag", wintypes.DWORD)]

    kernel = _windows_api()
    access = (0x80 | (0x20 if traverse else 0x1)) if directory else 0x80000000
    if overwrite:
        access = 0x40000000 | 0x80
    if parent is None:
        # FILE_TRAVERSE participates in sharing checks without requiring enumeration.
        handle = kernel.CreateFileW(
            str(path), access, 0x3, None,
            3 if create_attributes is None else 1,  # OPEN_EXISTING or CREATE_NEW.
            0x00200000 | 0x02000000 | (create_attributes or 0), None,
        )
        if handle == wintypes.HANDLE(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
    else:
        handle = _open_windows_child(parent, str(path), directory=directory, access=access, sharing=0x3)
    try:
        attributes = AttributeTagInfo()
        if not kernel.GetFileInformationByHandleEx(
            handle, 9, ctypes.byref(attributes), ctypes.sizeof(attributes)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        if attributes.attributes & 0x400:
            raise OSError(errno.ELOOP, "Refusing a reparse-point filesystem path", str(path))
        if bool(attributes.attributes & 0x10) != directory:
            raise OSError(errno.EINVAL, "Unexpected filesystem object type", str(path))
        return handle
    except BaseException:
        kernel.CloseHandle(handle)
        raise


@contextmanager
def _windows_handle(
    path: Path, *, directory: bool, parent: int | None = None, traverse: bool = False,
) -> Iterator[int]:
    """Pin a non-reparse path by withholding Windows delete sharing."""
    if parent is None and not traverse:
        handle = _open_windows_handle(path, directory=directory)
    else:
        handle = _open_windows_handle(path, directory=directory, parent=parent, traverse=traverse)
    try:
        yield handle
    finally:
        _windows_api().CloseHandle(handle)


@contextmanager
def windows_read_fd(handle: int) -> Iterator[int]:
    """Read the validated object through an independently owned duplicate."""
    import _winapi
    import msvcrt

    process = _winapi.GetCurrentProcess()
    duplicate = _winapi.DuplicateHandle(
        process, handle, process, 0, False, _winapi.DUPLICATE_SAME_ACCESS
    )
    try:
        fd = msvcrt.open_osfhandle(duplicate, os.O_RDONLY | os.O_BINARY)
    except BaseException:
        _winapi.CloseHandle(duplicate)
        raise
    try:
        yield fd
    finally:
        os.close(fd)


@contextmanager
def _windows_overwrite_fd(path: Path) -> Iterator[int]:
    """Open/create without following a new leaf or changing the CRT mask."""
    try:
        handle = _open_windows_handle(path, directory=False, overwrite=True)
    except FileNotFoundError:
        attributes = _windows_creation_attributes()
        handle = _open_windows_handle(
            path, directory=False, overwrite=True, create_attributes=attributes
        )
    try:
        import msvcrt

        fd = msvcrt.open_osfhandle(handle, os.O_WRONLY | os.O_BINARY)
    except BaseException:
        _windows_api().CloseHandle(handle)
        raise
    try:
        yield fd
    finally:
        os.close(fd)


def _windows_creation_attributes() -> int:
    """Capture CRT-masked permissions in independent runtime-owned storage."""
    with tempfile.TemporaryDirectory(prefix="specify-mode-") as directory:
        parent = Path(directory)
        with _windows_handle(parent, directory=True):
            probe = parent / f".specify-mode-{secrets.token_hex(16)}.tmp"
            fd = os.open(probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_BINARY, 0o666)
            try:
                readonly = not os.fstat(fd).st_mode & stat.S_IWRITE
            finally:
                try:
                    os.chmod(probe, 0o600)
                finally:
                    os.close(fd)
                    os.unlink(probe)
    return 0x1 if readonly else 0
