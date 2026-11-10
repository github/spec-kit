"""Private platform handles for confined filesystem operations."""

from collections.abc import Iterator
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import errno
import os
from pathlib import Path, PureWindowsPath


# Older Python versions retain POINTER types globally; reuse these ABI classes.
class _UnicodeString(ctypes.Structure):
    _fields_ = [
        ("Length", ctypes.c_uint16),
        ("MaximumLength", ctypes.c_uint16),
        ("Buffer", wintypes.LPWSTR),
    ]


_UnicodeStringPointer = ctypes.POINTER(_UnicodeString)


class _ObjectAttributes(ctypes.Structure):
    _fields_ = [
        ("Length", ctypes.c_uint32),
        ("RootDirectory", wintypes.HANDLE),
        ("ObjectName", _UnicodeStringPointer),
        ("Attributes", ctypes.c_uint32),
        ("SecurityDescriptor", wintypes.LPVOID),
        ("SecurityQualityOfService", wintypes.LPVOID),
    ]


_ObjectAttributesPointer = ctypes.POINTER(_ObjectAttributes)


class _StatusValue(ctypes.Union):
    _fields_ = [("Status", ctypes.c_int32), ("Pointer", wintypes.LPVOID)]


class _IoStatusBlock(ctypes.Structure):
    _fields_ = [("Value", _StatusValue), ("Information", ctypes.c_size_t)]


_IoStatusBlockPointer = ctypes.POINTER(_IoStatusBlock)


def _open_windows_child(parent: int, name: str, *, directory: bool, access: int, sharing: int) -> int:
    """Open one component relative to an already validated directory handle."""
    if PureWindowsPath(name).parts != (name,) or PureWindowsPath(name).anchor or name == ".." or "\0" in name:
        raise ValueError(f"Expected a single relative Windows path component: {name!r}")
    encoded_length = len(name.encode("utf-16-le", errors="surrogatepass"))
    if encoded_length > 65532:
        raise OSError(errno.ENAMETOOLONG, "Windows path component is too long", name)

    native = ctypes.WinDLL("ntdll")
    create = native.NtCreateFile
    create.argtypes = [
        ctypes.POINTER(wintypes.HANDLE), ctypes.c_uint32,
        _ObjectAttributesPointer, _IoStatusBlockPointer,
        wintypes.LPVOID, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
        ctypes.c_uint32, wintypes.LPVOID, ctypes.c_uint32,
    ]
    create.restype = ctypes.c_int32
    dos_error = native.RtlNtStatusToDosError
    dos_error.argtypes = [ctypes.c_int32]
    dos_error.restype = ctypes.c_uint32
    buffer = ctypes.create_unicode_buffer(name)
    unicode_name = _UnicodeString(
        encoded_length, encoded_length + 2, ctypes.cast(buffer, wintypes.LPWSTR)
    )
    # OBJ_DONT_REPARSE and FILE_OPEN_REPARSE_POINT keep resolution on this handle.
    attributes = _ObjectAttributes(
        ctypes.sizeof(_ObjectAttributes), parent, ctypes.pointer(unicode_name),
        0x40 | 0x1000, None, None,
    )
    handle = wintypes.HANDLE()
    status = _IoStatusBlock()
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


@contextmanager
def _windows_handle(
    path: Path, *, directory: bool,
    parent: int | None = None, traverse: bool = False,
) -> Iterator[int]:
    """Pin a non-reparse path by withholding Windows delete sharing."""
    class AttributeTagInfo(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("tag", wintypes.DWORD)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create.restype = wintypes.HANDLE
    info = kernel.GetFileInformationByHandleEx
    info.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
    info.restype = wintypes.BOOL
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL

    access = (0x80 | (0x20 if traverse else 0x1)) if directory else 0x80000000
    sharing = 0x3
    if parent is None:
        # FILE_TRAVERSE also participates in sharing checks, unlike attributes alone.
        handle = create(
            str(path), access, sharing, None, 3, 0x00200000 | 0x02000000, None,
        )
        if handle == wintypes.HANDLE(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
    else:
        handle = _open_windows_child(parent, str(path), directory=directory, access=access, sharing=sharing)
    try:
        attributes = AttributeTagInfo()
        if not info(handle, 9, ctypes.byref(attributes), ctypes.sizeof(attributes)):
            raise ctypes.WinError(ctypes.get_last_error())
        if attributes.attributes & 0x400:
            raise OSError(errno.ELOOP, "Refusing a reparse-point filesystem path", str(path))
        if bool(attributes.attributes & 0x10) != directory:
            raise OSError(errno.EINVAL, "Unexpected filesystem object type", str(path))
        yield handle
    finally:
        close(handle)


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
