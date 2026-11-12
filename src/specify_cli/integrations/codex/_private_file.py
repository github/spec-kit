"""Create a file that only the current user can open, on POSIX and Windows.

``FileHelper.create_bytes`` passes its mode to ``os.open``, which on Windows
sets no access-control list, so the file would take the directory's inherited
one. On Windows the file is therefore created with an explicit, protected
access-control list that grants the current user full access and nobody else
any. It is set by the call that creates the file, so the content is never
readable under the inherited list, not even briefly.
"""

from __future__ import annotations

import errno
import os
from pathlib import Path

from ...file_helper import FileHelper

_GENERIC_WRITE = 0x40000000
_CREATE_NEW = 1
_FILE_ATTRIBUTE_NORMAL = 0x80
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_TOKEN_QUERY = 0x8
_TOKEN_USER = 1
_ERROR_INSUFFICIENT_BUFFER = 122
_SDDL_REVISION_1 = 1


def create_private(helper: FileHelper, rel: str, content: bytes) -> None:
    """Exclusively create ``rel`` under ``helper``'s root, readable by its owner only.

    Raises ``FileExistsError`` if any entry, including a link, is already there.
    """
    if os.name != "nt":
        helper.create_bytes(rel, content, mode=0o600)
        return
    # FileHelper has no public way to pass a security descriptor; these are the
    # anchored resolution and parent pinning behind ``create_bytes``. Pinned by
    # ``TestCodexFileHelperInternals``.
    destination = helper._path(rel, allow_missing=True, follow_leaf=False)
    with helper._creation_directory(destination.parent) as directory:
        _create_windows(Path(directory) / destination.name, content)


def owner_only_sddl() -> str:
    """The SDDL of the access-control list a Windows backup is created with."""
    return f"D:P(A;;FA;;;{_current_user_sid()})"


def _create_windows(path: Path, content: bytes) -> None:
    import ctypes
    import msvcrt
    from ctypes import wintypes

    class SecurityAttributes(ctypes.Structure):
        _fields_ = [
            ("nLength", wintypes.DWORD),
            ("lpSecurityDescriptor", ctypes.c_void_p),
            ("bInheritHandle", wintypes.BOOL),
        ]

    kernel = _kernel32()
    advapi = _advapi32()
    convert = advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p), wintypes.LPVOID,
    ]
    convert.restype = wintypes.BOOL
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.POINTER(SecurityAttributes), wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE

    descriptor = ctypes.c_void_p()
    if not convert(owner_only_sddl(), _SDDL_REVISION_1, ctypes.byref(descriptor), None):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        attributes = SecurityAttributes(ctypes.sizeof(SecurityAttributes), descriptor, False)
        # No sharing: nobody else can open the file until it is written and closed.
        handle = kernel.CreateFileW(
            str(path), _GENERIC_WRITE, 0, ctypes.byref(attributes), _CREATE_NEW,
            _FILE_ATTRIBUTE_NORMAL | _FILE_FLAG_OPEN_REPARSE_POINT, None,
        )
        if handle is None or handle == wintypes.HANDLE(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel.LocalFree(descriptor)
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_WRONLY | os.O_BINARY)
    except BaseException:
        kernel.CloseHandle(handle)
        raise
    with os.fdopen(fd, "wb") as stream:
        stream.write(content)


def _current_user_sid() -> str:
    import ctypes
    from ctypes import wintypes

    kernel = _kernel32()
    advapi = _advapi32()
    kernel.GetCurrentProcess.argtypes = []
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    advapi.OpenProcessToken.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE),
    ]
    advapi.OpenProcessToken.restype = wintypes.BOOL
    advapi.GetTokenInformation.argtypes = [
        wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    advapi.GetTokenInformation.restype = wintypes.BOOL
    advapi.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR)]
    advapi.ConvertSidToStringSidW.restype = wintypes.BOOL

    token = wintypes.HANDLE()
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), _TOKEN_QUERY, ctypes.byref(token)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        size = wintypes.DWORD()
        if not advapi.GetTokenInformation(token, _TOKEN_USER, None, 0, ctypes.byref(size)):
            code = ctypes.get_last_error()
            if code != _ERROR_INSUFFICIENT_BUFFER:
                raise ctypes.WinError(code)
        buffer = ctypes.create_string_buffer(size.value)
        if not advapi.GetTokenInformation(
            token, _TOKEN_USER, buffer, size, ctypes.byref(size),
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        # TOKEN_USER starts with SID_AND_ATTRIBUTES, whose first field is the SID.
        sid = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0]
        text = wintypes.LPWSTR()
        if not advapi.ConvertSidToStringSidW(sid, ctypes.byref(text)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            value = text.value
        finally:
            kernel.LocalFree(ctypes.cast(text, ctypes.c_void_p))
    finally:
        kernel.CloseHandle(token)
    if not value or not value.startswith("S-"):
        raise OSError(errno.EINVAL, "Could not read the current user's security identifier")
    return value


def _kernel32():
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    return kernel


def _advapi32():
    import ctypes

    return ctypes.WinDLL("advapi32", use_last_error=True)
