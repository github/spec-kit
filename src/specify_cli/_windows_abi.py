"""Windows ABI metadata, initialized once through lazy module imports."""

import ctypes
from ctypes import wintypes


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
