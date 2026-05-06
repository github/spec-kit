"""Helpers for bounded downloads and archive extraction."""

from __future__ import annotations

import hashlib
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import TypeVar


ErrorT = TypeVar("ErrorT", bound=Exception)

MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
MAX_ZIP_ENTRIES = 512
MAX_ZIP_MEMBER_BYTES = 10 * 1024 * 1024
MAX_ZIP_TOTAL_BYTES = 50 * 1024 * 1024
READ_CHUNK_SIZE = 1024 * 1024
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _raise(error_type: type[ErrorT], message: str) -> None:
    raise error_type(message)


def read_response_limited(
    response,
    *,
    max_bytes: int = MAX_DOWNLOAD_BYTES,
    error_type: type[ErrorT] = ValueError,
    label: str = "download",
) -> bytes:
    """Read at most *max_bytes* from a response object."""
    data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        _raise(error_type, f"{label} exceeds maximum size of {max_bytes} bytes")
    return data


def normalize_sha256(value: object, *, error_type: type[ErrorT] = ValueError) -> str | None:
    """Normalize an optional sha256/sha256:<hex> checksum value."""
    if value is None:
        return None
    if not isinstance(value, str):
        _raise(error_type, "sha256 checksum must be a string")

    checksum = value.strip()
    if checksum.startswith("sha256:"):
        checksum = checksum[len("sha256:") :]
    if not SHA256_RE.fullmatch(checksum):
        _raise(error_type, "sha256 checksum must be 64 hexadecimal characters")
    return checksum.lower()


def verify_sha256(
    data: bytes,
    expected: object,
    *,
    error_type: type[ErrorT] = ValueError,
    label: str = "download",
) -> None:
    """Verify *data* against an optional sha256 checksum."""
    checksum = normalize_sha256(expected, error_type=error_type)
    if checksum is None:
        return

    actual = hashlib.sha256(data).hexdigest()
    if actual != checksum:
        _raise(
            error_type,
            f"{label} checksum mismatch: expected sha256:{checksum}, got sha256:{actual}",
        )


def _safe_zip_name(name: str, *, error_type: type[ErrorT]) -> str:
    """Return a normalized ZIP member name or raise on traversal."""
    if "\x00" in name:
        _raise(error_type, f"Unsafe path in ZIP archive: {name!r}")

    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    has_windows_drive = re.match(r"^[A-Za-z]:", normalized) is not None
    if (
        not path.parts
        or path.is_absolute()
        or has_windows_drive
        or any(part == ".." for part in path.parts)
    ):
        _raise(
            error_type,
            f"Unsafe path in ZIP archive: {name} (potential path traversal)",
        )
    return normalized


def safe_extract_zip(
    zip_path: Path,
    target_dir: Path,
    *,
    error_type: type[ErrorT] = ValueError,
    max_entries: int = MAX_ZIP_ENTRIES,
    max_member_bytes: int = MAX_ZIP_MEMBER_BYTES,
    max_total_bytes: int = MAX_ZIP_TOTAL_BYTES,
) -> None:
    """Extract a ZIP archive after path, symlink, and size validation."""
    target_root = target_dir.resolve()

    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.infolist()
        if len(members) > max_entries:
            _raise(
                error_type,
                f"ZIP archive contains too many entries ({len(members)} > {max_entries})",
            )

        normalized_members: list[tuple[zipfile.ZipInfo, str]] = []
        total_size = 0
        for member in members:
            normalized_name = _safe_zip_name(member.filename, error_type=error_type)

            mode = member.external_attr >> 16
            if stat.S_ISLNK(mode):
                _raise(error_type, f"Unsafe symlink in ZIP archive: {member.filename}")

            member_path = (target_dir / normalized_name).resolve()
            try:
                member_path.relative_to(target_root)
            except ValueError:
                _raise(
                    error_type,
                    f"Unsafe path in ZIP archive: {member.filename} "
                    "(potential path traversal)",
                )

            if not member.is_dir():
                if member.file_size > max_member_bytes:
                    _raise(
                        error_type,
                        f"ZIP member {member.filename} exceeds maximum size "
                        f"of {max_member_bytes} bytes",
                    )
                total_size += member.file_size
                if total_size > max_total_bytes:
                    _raise(
                        error_type,
                        f"ZIP archive exceeds maximum uncompressed size "
                        f"of {max_total_bytes} bytes",
                    )

            normalized_members.append((member, normalized_name))

        for member, normalized_name in normalized_members:
            member_path = target_dir / normalized_name
            if member.is_dir():
                member_path.mkdir(parents=True, exist_ok=True)
                continue

            member_path.parent.mkdir(parents=True, exist_ok=True)
            written = 0
            with zf.open(member, "r") as source, member_path.open("wb") as dest:
                while True:
                    chunk = source.read(READ_CHUNK_SIZE)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > max_member_bytes:
                        _raise(
                            error_type,
                            f"ZIP member {member.filename} exceeds maximum size "
                            f"of {max_member_bytes} bytes",
                        )
                    dest.write(chunk)
