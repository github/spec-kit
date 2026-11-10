"""Windows non-reparse handles for scoped filesystem operations."""

import errno
import os
import secrets
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


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
    path: Path, *, directory: bool, overwrite: bool = False, create_attributes: int | None = None
) -> int:
    import ctypes
    from ctypes import wintypes

    class AttributeTagInfo(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("tag", wintypes.DWORD)]

    kernel = _windows_api()
    # Attribute-only directory handles do not prevent renaming; include
    # FILE_LIST_DIRECTORY and withhold FILE_SHARE_DELETE for every ancestor.
    handle = kernel.CreateFileW(
        str(path),
        (0x40000000 | 0x80) if overwrite else ((0x80 | 0x1) if directory else 0x80000000),
        0x3,
        None,
        3 if create_attributes is None else 1,  # OPEN_EXISTING or CREATE_NEW.
        0x00200000 | 0x02000000 | (create_attributes or 0),
        None,
    )
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        attributes = AttributeTagInfo()
        if not kernel.GetFileInformationByHandleEx(
            handle, 9, ctypes.byref(attributes), ctypes.sizeof(attributes)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        if attributes.attributes & 0x400:
            raise OSError(errno.ELOOP, "Refusing a reparse-point path", str(path))
        if bool(attributes.attributes & 0x10) != directory:
            raise OSError(errno.EINVAL, "Unexpected file type", str(path))
        return handle
    except BaseException:
        kernel.CloseHandle(handle)
        raise


@contextmanager
def _windows_handle(path: Path, *, directory: bool) -> Iterator[int]:
    """Pin a non-reparse path by withholding Windows delete sharing."""
    handle = _open_windows_handle(path, directory=directory)
    try:
        yield handle
    finally:
        _windows_api().CloseHandle(handle)


@contextmanager
def _windows_overwrite_fd(path: Path) -> Iterator[int]:
    """Open/create without following a new leaf or changing the CRT mask."""
    try:
        handle = _open_windows_handle(path, directory=False, overwrite=True)
    except FileNotFoundError:
        attributes = _windows_creation_attributes(path.parent)
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


def _windows_creation_attributes(parent: Path) -> int:
    """Capture CRT-masked permissions using a private, empty creation probe."""
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
