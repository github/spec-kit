"""Create a file that only the current user can open, on POSIX and Windows.

``FileHelper.create_bytes`` passes its mode to ``os.open``, which on Windows
sets no access-control list, so the file would take the directory's inherited
one. On Windows the file is therefore created owned by the current user, with
an explicit, protected access-control list that grants that user full access
and nobody else any. Both are set by the call that creates the file, which
also shares it with nobody until it is closed, so the content is never
readable under the inherited list, not even briefly.
"""

from __future__ import annotations

import errno
import functools
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

    The content is flushed to disk before this returns. Raises
    ``FileExistsError`` if any entry, including a link, is already there; a
    failure after the file was created removes it, so a partial copy is never
    left to be mistaken for a complete one.
    """
    # FileHelper has no public way to pass a security descriptor, or to flush
    # what it creates; these are the anchored resolution and parent pinning
    # behind ``create_bytes``. Pinned by ``TestCodexFileHelperInternals``.
    destination = helper._path(rel, allow_missing=True, follow_leaf=False)
    with helper._creation_directory(destination.parent) as directory:
        if os.name != "nt":
            _create_posix(directory, destination.name, content)
            return
        path = Path(directory) / destination.name
        fd = _create_windows(path)
        try:
            try:
                stream = os.fdopen(fd, "wb")
            except BaseException:
                os.close(fd)
                raise
            with stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            _remove_partial(helper, rel)
            raise


def _create_posix(directory: int, name: str, content: bytes) -> None:
    """Create ``name`` in the pinned ``directory``, then write and flush it.

    Everything goes through the one descriptor that created the file, so
    nothing swapped in under its name afterwards is opened. Only the file
    this call created is removed when a later step fails. The directory is
    flushed too, so the backup survives a crash that the rewrite after it
    does.
    """
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    fd = os.open(name, flags, 0o600, dir_fd=directory)
    created = None
    try:
        try:
            created = os.fstat(fd)
            view = memoryview(content)
            while view:
                count = os.write(fd, view)
                if count == 0:
                    raise OSError(errno.EIO, "Write made no progress")
                view = view[count:]
            os.fsync(fd)
        finally:
            os.close(fd)
        os.fsync(directory)
    except BaseException:
        try:
            current = os.stat(name, dir_fd=directory, follow_symlinks=False)
            if created is None or (current.st_dev, current.st_ino) == (created.st_dev, created.st_ino):
                os.unlink(name, dir_fd=directory)
        except OSError:
            pass
        raise


def _remove_partial(helper: FileHelper, rel: str) -> None:
    try:
        helper.delete(rel)
    except (OSError, ValueError):  # ValueError covers FileHelperError
        pass


def owner_only_sddl() -> str:
    """The security descriptor, as SDDL, a Windows backup is created with."""
    sid = _current_user_sid()
    return f"O:{sid}D:P(A;;FA;;;{sid})"


def _create_windows(path: Path) -> int:
    """Create ``path`` with the owner-only descriptor and return a CRT descriptor."""
    import ctypes
    import msvcrt
    from ctypes import wintypes

    kernel, advapi, attributes_type = _windows_api()
    descriptor = ctypes.c_void_p()
    if not advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW(
        owner_only_sddl(), _SDDL_REVISION_1, ctypes.byref(descriptor), None,
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        attributes = attributes_type(ctypes.sizeof(attributes_type), descriptor, False)
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
        return msvcrt.open_osfhandle(handle, os.O_WRONLY | os.O_BINARY)
    except BaseException:
        kernel.CloseHandle(handle)
        raise


@functools.lru_cache(maxsize=1)
def _current_user_sid() -> str:
    import ctypes
    from ctypes import wintypes

    kernel, advapi, _ = _windows_api()
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


@functools.lru_cache(maxsize=1)
def _windows_api():
    """kernel32 and advapi32 with the prototypes used here, and SECURITY_ATTRIBUTES."""
    import ctypes
    from ctypes import wintypes

    class SecurityAttributes(ctypes.Structure):
        _fields_ = [
            ("nLength", wintypes.DWORD),
            ("lpSecurityDescriptor", ctypes.c_void_p),
            ("bInheritHandle", wintypes.BOOL),
        ]

    # Private instances, so these prototypes do not change ctypes.windll's.
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.GetCurrentProcess.argtypes = []
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.POINTER(SecurityAttributes), wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p), wintypes.LPVOID,
    ]
    advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = wintypes.BOOL
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
    return kernel, advapi, SecurityAttributes
