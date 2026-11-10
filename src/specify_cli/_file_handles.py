"""Private platform handles for confined filesystem operations."""

import errno
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def _windows_handle(path: Path, *, directory: bool, pin: bool = True) -> Iterator[int]:
    """Open a non-reparse object, optionally preventing directory replacement."""
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

    # OPEN_REPARSE_POINT inspects the link itself; BACKUP_SEMANTICS permits
    # directory handles. Holding every ancestor without FILE_SHARE_DELETE
    # prevents a junction/symlink swap during path-based create/replace.
    # Pinning needs FILE_LIST_DIRECTORY as well as FILE_READ_ATTRIBUTES.
    # An attribute-only reference preserves identity without locking ancestors.
    handle = create(
        str(path),
        ((0x80 | 0x1) if directory else 0x80000000) if pin else 0x80,
        0x3 if pin else 0x7,
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
            raise OSError(errno.ELOOP, "Refusing a reparse-point filesystem path", str(path))
        if bool(attributes.attributes & 0x10) != directory:
            raise OSError(errno.EINVAL, "Unexpected filesystem object type", str(path))
        yield handle
    finally:
        close(handle)


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
