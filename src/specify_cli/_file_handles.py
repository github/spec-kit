"""Handle-based filesystem primitives shared by confined I/O consumers."""

from collections.abc import Iterator
from contextlib import contextmanager
import errno
import os
from pathlib import Path


@contextmanager
def windows_handle(path: Path, *, directory: bool, share_write: bool = True) -> Iterator[int]:
    """Pin a non-reparse path by withholding Windows delete sharing."""
    import ctypes
    from ctypes import wintypes

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

    # OPEN_REPARSE_POINT checks the entry itself. Directory handles need
    # FILE_LIST_DIRECTORY: attribute-only handles do not prevent renaming.
    handle = create(
        str(path),
        (0x80 | 0x1) if directory else 0x80000000,
        0x1 | (0x2 if share_write else 0),
        None,
        3,
        0x00200000 | 0x02000000,
        None,
    )
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        attributes = AttributeTagInfo()
        if not info(handle, 9, ctypes.byref(attributes), ctypes.sizeof(attributes)):
            raise ctypes.WinError(ctypes.get_last_error())
        if attributes.attributes & 0x400:
            raise OSError(errno.ELOOP, "Refusing a reparse-point path", str(path))
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
