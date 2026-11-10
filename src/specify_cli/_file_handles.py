"""Private platform handles for confined filesystem operations."""

import errno
import os
import secrets
import stat
import tempfile
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
    path: Path, *, directory: bool, overwrite: bool = False,
    create_attributes: int | None = None, pin: bool = True,
) -> int:
    import ctypes
    from ctypes import wintypes

    class AttributeTagInfo(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("tag", wintypes.DWORD)]

    kernel = _windows_api()
    # Pinning needs directory-list access and withholds delete sharing.
    # Metadata-only references retain identity without locking ancestors.
    handle = kernel.CreateFileW(
        str(path),
        (0x40000000 | 0x80) if overwrite else (
            ((0x80 | 0x1) if directory else 0x80000000) if pin else 0x80
        ),
        0x3 if pin else 0x7,
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
            raise OSError(errno.ELOOP, "Refusing a reparse-point filesystem path", str(path))
        if bool(attributes.attributes & 0x10) != directory:
            raise OSError(errno.EINVAL, "Unexpected filesystem object type", str(path))
        return handle
    except BaseException:
        kernel.CloseHandle(handle)
        raise


@contextmanager
def _windows_handle(path: Path, *, directory: bool, pin: bool = True) -> Iterator[int]:
    """Open a non-reparse object, optionally preventing directory replacement."""
    handle = _open_windows_handle(path, directory=directory, pin=pin)
    try:
        yield handle
    finally:
        _windows_api().CloseHandle(handle)


def _windows_file_id(handle: int) -> tuple[int, bytes]:
    """Read the volume and complete file identity from an already opened object."""
    import ctypes
    from ctypes import wintypes

    class FileIdInfo(ctypes.Structure):
        _fields_ = [
            ("volume", ctypes.c_ulonglong),
            ("file_id", ctypes.c_ubyte * 16),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    info = kernel.GetFileInformationByHandleEx
    info.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
    info.restype = wintypes.BOOL
    identity = FileIdInfo()
    if not info(handle, 18, ctypes.byref(identity), ctypes.sizeof(identity)):
        raise ctypes.WinError(ctypes.get_last_error())
    return identity.volume, bytes(identity.file_id)


def _windows_stat(handle: int) -> os.stat_result:
    """Get Python's native metadata without taking ownership of a borrowed handle."""
    import _winapi
    import msvcrt

    process = _winapi.GetCurrentProcess()
    duplicate = _winapi.DuplicateHandle(
        process, handle, process, 0, False, _winapi.DUPLICATE_SAME_ACCESS
    )
    try:
        fd = msvcrt.open_osfhandle(duplicate, os.O_RDONLY | os.O_NOINHERIT)
    except BaseException:
        _winapi.CloseHandle(duplicate)
        raise
    try:
        return os.fstat(fd)
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
