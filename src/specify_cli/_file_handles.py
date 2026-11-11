"""Private platform handles for confined filesystem operations."""

from collections.abc import Iterator
from contextlib import contextmanager
import errno
import os
import secrets
import stat
import struct
import tempfile
from pathlib import Path, PureWindowsPath
from typing import Literal, NamedTuple


_IdentityKind = Literal["fileid128", "legacy64"]


class _WindowsFileIdentity(NamedTuple):
    kind: _IdentityKind
    volume: int
    file_id: bytes


def _open_windows_child(
    parent: int, name: str, *, directory: bool | None, access: int,
    sharing: int, allow_reparse: bool = False,
) -> int:
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
        0x40 | (0 if allow_reparse else 0x1000), None, None,
    )
    handle = wintypes.HANDLE()
    status = abi._IoStatusBlock()
    options = 0x00200000 | 0x20  # FILE_OPEN_REPARSE_POINT | FILE_SYNCHRONOUS_IO_NONALERT.
    if directory is not None:
        options |= 0x1 if directory else 0x40
    result = create(
        ctypes.byref(handle), access | 0x100000,  # SYNCHRONIZE is required for synchronous I/O.
        ctypes.byref(attributes), ctypes.byref(status), None, 0,
        sharing, 1, options, None, 0,
    )
    if result < 0:
        raise ctypes.WinError(dos_error(result))
    if not handle.value:
        raise OSError(errno.EBADF, "Native child open returned no handle", name)
    return handle.value


@contextmanager
def _windows_entry(parent: int, name: str, *, deleting: bool = False) -> Iterator[int]:
    """Open the leaf itself relative to its directory, including allowed links."""
    handle = _open_windows_child(
        parent, name, directory=None, access=0x80 | (0x10000 if deleting else 0),
        sharing=0x7, allow_reparse=True,
    )
    try:
        yield handle
    finally:
        _windows_api().CloseHandle(handle)


def _windows_mode(handle: int) -> int:
    import ctypes

    class Attributes(ctypes.Structure):
        _fields_ = [("attributes", ctypes.c_uint32), ("tag", ctypes.c_uint32)]

    info = Attributes()
    if not _windows_api().GetFileInformationByHandleEx(
        handle, 9, ctypes.byref(info), ctypes.sizeof(info)
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    if info.attributes & 0x400:
        if info.tag != 0xA000000C:
            raise OSError(errno.ELOOP, "Unsupported Windows reparse point")
        return stat.S_IFLNK
    return stat.S_IFDIR if info.attributes & 0x10 else stat.S_IFREG


def _windows_readlink(handle: int) -> str:
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    control = kernel.DeviceIoControl
    control.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
        wintypes.LPVOID, wintypes.DWORD, wintypes.LPDWORD, wintypes.LPVOID,
    ]
    control.restype = wintypes.BOOL
    buffer = ctypes.create_string_buffer(16384)
    length = wintypes.DWORD()
    if not control(
        handle, 0x900A8, None, 0, buffer, len(buffer), ctypes.byref(length), None
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    data = buffer.raw[:length.value]
    if len(data) < 20:
        raise OSError(errno.EIO, "Incomplete Windows symlink data")
    tag, size, _, offset, count, _, _, flags = struct.unpack_from("<IHHHHHHI", data)
    end = 20 + offset + count
    if (
        tag != 0xA000000C or offset % 2 or not count or count % 2 or flags & ~1
        or 8 + size > len(data) or end > 8 + size
    ):
        raise OSError(errno.EIO, "Invalid Windows symlink data")
    target = data[20 + offset:end].decode("utf-16-le", errors="surrogatepass")
    if "\0" in target:
        raise OSError(errno.EIO, "Invalid Windows symlink target")
    if not flags & 1 and target.startswith("\\??\\"):
        target = "\\\\?\\" + target[4:]
    return target


def _windows_directory_names(handle: int) -> list[str]:
    import ctypes

    buffer = ctypes.create_string_buffer(131072)
    names = []
    kind = 15  # FileFullDirectoryRestartInfo, then FileFullDirectoryInfo.
    while True:
        if not _windows_api().GetFileInformationByHandleEx(handle, kind, buffer, len(buffer)):
            error = ctypes.get_last_error()
            if error == 18:  # ERROR_NO_MORE_FILES.
                return names
            raise ctypes.WinError(error)
        kind = 14
        data = buffer.raw
        offset = 0
        while True:
            if offset + 68 > len(data):
                raise OSError(errno.EIO, "Incomplete Windows directory entry")
            next_entry = struct.unpack_from("<I", data, offset)[0]
            size = struct.unpack_from("<I", data, offset + 60)[0]
            end = offset + 68 + size
            if not size or size % 2 or end > len(data):
                raise OSError(errno.EIO, "Invalid Windows directory entry")
            name = data[offset + 68:end].decode("utf-16-le", errors="surrogatepass")
            if name not in (".", ".."):
                if PureWindowsPath(name).parts != (name,) or PureWindowsPath(name).anchor or "\0" in name:
                    raise OSError(errno.EIO, "Invalid Windows directory component")
                names.append(name)
            if not next_entry:
                break
            if next_entry % 8 or next_entry < 68 + size:
                raise OSError(errno.EIO, "Invalid Windows directory entry offset")
            offset += next_entry


def _windows_delete(handle: int) -> None:
    """Mark the opened object for removal, never reopen its pathname."""
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    dispose = kernel.SetFileInformationByHandle
    dispose.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
    dispose.restype = wintypes.BOOL
    delete = ctypes.c_int32(True)
    if not dispose(handle, 4, ctypes.byref(delete), ctypes.sizeof(delete)):
        raise ctypes.WinError(ctypes.get_last_error())


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
    pin: bool = True,
) -> int:
    if parent is not None and (overwrite or create_attributes is not None):
        raise ValueError("Relative Windows handle opens do not support creation or overwrite")
    import ctypes
    from ctypes import wintypes

    class AttributeTagInfo(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("tag", wintypes.DWORD)]

    kernel = _windows_api()
    access = (0x80 | (0x20 if traverse else 0x1)) if directory else 0x80000000
    if not pin:
        access = 0x80
    if overwrite:
        access = 0x40000000 | 0x80
    sharing = 0x3 if pin else 0x7
    if parent is None:
        # FILE_TRAVERSE participates in sharing checks without requiring enumeration.
        handle = kernel.CreateFileW(
            str(path), access, sharing, None,
            3 if create_attributes is None else 1,  # OPEN_EXISTING or CREATE_NEW.
            0x00200000 | 0x02000000 | (create_attributes or 0), None,
        )
        if handle == wintypes.HANDLE(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
    else:
        handle = _open_windows_child(
            parent, str(path), directory=directory, access=access, sharing=sharing
        )
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
    pin: bool = True,
) -> Iterator[int]:
    """Open a non-reparse object, optionally relative to a retained parent."""
    if not pin:
        handle = _open_windows_handle(
            path, directory=directory, parent=parent, traverse=traverse, pin=False
        )
    elif parent is None and not traverse:
        handle = _open_windows_handle(path, directory=directory)
    else:
        handle = _open_windows_handle(path, directory=directory, parent=parent, traverse=traverse)
    try:
        yield handle
    finally:
        _windows_api().CloseHandle(handle)


def _windows_filesystem(handle: int) -> str:
    """Query the opened volume, including network filesystems, without a pathname."""
    import ctypes
    from ctypes import wintypes
    from . import _windows_abi as abi

    class FilesystemAttributes(ctypes.Structure):
        _fields_ = [
            ("attributes", ctypes.c_uint32),
            ("maximum_component", ctypes.c_int32),
            ("name_length", ctypes.c_uint32),
            ("name", ctypes.c_uint16 * 261),
        ]

    native = ctypes.WinDLL("ntdll")
    query = native.NtQueryVolumeInformationFile
    query.argtypes = [
        wintypes.HANDLE, abi._IoStatusBlockPointer, wintypes.LPVOID,
        ctypes.c_uint32, ctypes.c_int,
    ]
    query.restype = ctypes.c_int32
    dos_error = native.RtlNtStatusToDosError
    dos_error.argtypes = [ctypes.c_int32]
    dos_error.restype = ctypes.c_uint32
    attributes = FilesystemAttributes()
    status = abi._IoStatusBlock()
    result = query(
        handle, ctypes.byref(status), ctypes.byref(attributes),
        ctypes.sizeof(attributes), 5,  # FileFsAttributeInformation.
    )
    if result != 0:
        raise ctypes.WinError(dos_error(result))
    length = attributes.name_length
    if not length or length % 2 or length > ctypes.sizeof(attributes.name):
        raise OSError(errno.EINVAL, "Invalid filesystem name from volume query")
    return bytes(attributes.name)[:length].decode("utf-16-le")


def _windows_legacy_file_id(handle: int) -> _WindowsFileIdentity:
    """Query a live legacy identity only on filesystems with usable 64-bit IDs."""
    import ctypes
    from ctypes import wintypes

    filesystem = _windows_filesystem(handle).upper()
    # ReFS needs 128 bits; unknown drivers may report non-identifying indexes.
    if filesystem not in {"FAT", "FAT32", "EXFAT", "NTFS"}:
        raise OSError(errno.ENOTSUP, f"No reliable legacy file identity for {filesystem}")

    class FileInformation(ctypes.Structure):
        _fields_ = [
            ("attributes", ctypes.c_uint32),
            ("times", ctypes.c_uint32 * 6),
            ("volume", ctypes.c_uint32),
            ("size_high", ctypes.c_uint32),
            ("size_low", ctypes.c_uint32),
            ("links", ctypes.c_uint32),
            ("index_high", ctypes.c_uint32),
            ("index_low", ctypes.c_uint32),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    query = kernel.GetFileInformationByHandle
    query.argtypes = [wintypes.HANDLE, wintypes.LPVOID]
    query.restype = wintypes.BOOL
    information = FileInformation()
    if not query(handle, ctypes.byref(information)):
        raise ctypes.WinError(ctypes.get_last_error())
    index = (information.index_high << 32) | information.index_low
    if not index:
        raise OSError(errno.ENOTSUP, "No usable legacy file identity")
    return _WindowsFileIdentity("legacy64", information.volume, index.to_bytes(8, "little"))


def _windows_file_id(
    handle: int, *, kind: _IdentityKind | None = None
) -> _WindowsFileIdentity:
    """Select a supported identity once, or query the already selected scheme."""
    if kind == "legacy64":
        return _windows_legacy_file_id(handle)
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
        error = ctypes.get_last_error()
        if kind is None and error in (1, 50, 87):
            return _windows_legacy_file_id(handle)
        raise ctypes.WinError(error)
    value = bytes(identity.file_id)
    if not any(value):
        if kind is None:
            return _windows_legacy_file_id(handle)
        raise OSError(errno.ENOTSUP, "No usable extended file identity")
    return _WindowsFileIdentity("fileid128", identity.volume, value)


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
