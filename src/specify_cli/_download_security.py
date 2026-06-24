"""Helpers for bounded downloads and archive extraction."""

from __future__ import annotations

import hashlib
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import NoReturn, TypeVar
from urllib.parse import urlparse


ErrorT = TypeVar("ErrorT", bound=Exception)

MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
MAX_ZIP_ENTRIES = 512
MAX_ZIP_MEMBER_BYTES = 10 * 1024 * 1024
MAX_ZIP_TOTAL_BYTES = 50 * 1024 * 1024
READ_CHUNK_SIZE = 1024 * 1024

# Tighter ceilings for responses that are read fully into memory and parsed as
# JSON. The 50 MiB MAX_DOWNLOAD_BYTES default is sized for archive/payload
# downloads; JSON responses are far smaller, so capping them close to their real
# size shrinks the memory-DoS surface and keeps the "too large" error reachable
# (rather than only triggering on tens of MiB). Pass the matching constant
# explicitly at each JSON call site so the intended bound is pinned there.
#   * METADATA - fixed-shape single-object responses (an OAuth token, one
#     release's metadata): a few KiB in practice, 1 MiB is already generous.
#   * CATALOG - listings that grow with the number of published items. The
#     largest bundled catalog is ~130 KiB today, so 8 MiB leaves ~60x headroom
#     for growth while staying well under the download ceiling.
MAX_JSON_METADATA_BYTES = 1 * 1024 * 1024
MAX_JSON_CATALOG_BYTES = 8 * 1024 * 1024
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def is_https_or_localhost_http(url: str) -> bool:
    """Return True if *url* is HTTPS, or HTTP limited to loopback hosts.

    Shared scheme-safety predicate used by the auth HTTP redirect handler and
    by the direct URL validations in the CLI download flows, so the rule (and
    any future tightening of it) lives in one place.

    A hostname is always required: a URL without one (e.g. ``https:///x``)
    has no real target and is rejected regardless of scheme.

    The loopback allowance is a deliberate *exact-string* match on
    ``localhost`` / ``127.0.0.1`` / ``::1``, not an IP-range check: other
    loopback addresses (e.g. ``127.0.0.2``) are intentionally not covered.
    ``urlparse`` already lower-cases the hostname, so the comparison is
    case-insensitive.
    """
    parsed = urlparse(url)
    if not parsed.hostname:
        return False
    is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
    return parsed.scheme == "https" or (parsed.scheme == "http" and is_localhost)


def _raise(error_type: type[ErrorT], message: str) -> NoReturn:
    raise error_type(message)


def _raise_from(error_type: type[ErrorT], message: str, exc: Exception) -> NoReturn:
    raise error_type(message) from exc


def read_response_limited(
    response,
    *,
    max_bytes: int = MAX_DOWNLOAD_BYTES,
    error_type: type[ErrorT] = ValueError,
    label: str = "download",
) -> bytes:
    """Read at most *max_bytes* from a response object.

    ``response.read(n)`` is only guaranteed to return *up to* ``n`` bytes and may
    return fewer even when more data is pending (e.g. chunked transfer encoding),
    so a single ``read(max_bytes + 1)`` cannot enforce the bound on its own. Read
    in a loop until EOF or until one byte past the limit has been accumulated.

    *max_bytes* is keyword-only. It defaults to the module-wide
    ``MAX_DOWNLOAD_BYTES`` (50 MiB) ceiling for archive/payload downloads;
    callers with a tighter budget (e.g. small JSON responses) should pass an
    explicit value so the intended bound is pinned at the call site rather than
    tracking changes to the shared default.
    """
    chunks: list[bytes] = []
    total = 0
    limit = max_bytes + 1
    while total < limit:
        chunk = response.read(min(READ_CHUNK_SIZE, limit - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
    if total > max_bytes:
        _raise(error_type, f"{label} exceeds maximum size of {max_bytes} bytes")
    return b"".join(chunks)


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


def read_zip_member_limited(
    zf: zipfile.ZipFile,
    name: str,
    *,
    max_bytes: int = MAX_ZIP_MEMBER_BYTES,
    error_type: type[ErrorT] = ValueError,
    label: str | None = None,
) -> bytes:
    """Read a single ZIP member into memory under a hard size cap.

    Reading a member with ``zf.open(name).read()`` is unbounded: a crafted
    archive can declare a tiny ``file_size`` yet decompress to many gigabytes (a
    "zip bomb"), exhausting memory before the caller ever inspects the data.
    This rejects members whose *declared* size already exceeds *max_bytes* and,
    to defend against headers that lie, also reads in bounded chunks and stops
    one byte past the limit.

    Use this for any inline manifest/metadata read that happens *before*
    :func:`safe_extract_zip` (which already enforces the same per-member bound
    during extraction); a raw ``zf.open(...).read()`` bypasses that protection.
    """
    member_label = label or name
    try:
        info = zf.getinfo(name)
    except KeyError as exc:
        _raise_from(error_type, f"ZIP member not found: {name}", exc)
    if info.file_size > max_bytes:
        _raise(
            error_type,
            f"ZIP member {member_label} exceeds maximum size of {max_bytes} bytes",
        )

    chunks: list[bytes] = []
    total = 0
    limit = max_bytes + 1
    try:
        with zf.open(name, "r") as source:
            while total < limit:
                chunk = source.read(min(READ_CHUNK_SIZE, limit - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        _raise_from(error_type, f"Failed to read ZIP member {member_label}: {exc}", exc)
    if total > max_bytes:
        _raise(
            error_type,
            f"ZIP member {member_label} exceeds maximum size of {max_bytes} bytes",
        )
    return b"".join(chunks)


def _safe_zip_name(name: str, *, error_type: type[ErrorT]) -> str:
    """Return a normalized ZIP member name or raise on traversal."""
    if "\x00" in name:
        _raise(error_type, f"Unsafe path in ZIP archive: {name!r}")

    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    raw_parts = normalized.split("/")
    # Strip a single trailing empty segment, i.e. the one-slash directory
    # marker that legitimate ZIPs use ("mydir/", "mydir/subdir/"). Anything
    # else that produces an empty segment - consecutive slashes ("a//b") or a
    # second trailing slash - is left in place and rejected below as malformed.
    if raw_parts and raw_parts[-1] == "":
        raw_parts = raw_parts[:-1]
    has_windows_drive = re.match(r"^[A-Za-z]:", normalized) is not None
    if (
        not raw_parts
        or path.is_absolute()
        or has_windows_drive
        or any(part in {"", ".", ".."} for part in raw_parts)
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
    try:
        target_root = target_dir.resolve()
    except OSError as exc:
        _raise_from(error_type, f"Invalid ZIP extraction target: {target_dir}", exc)

    try:
        zf = zipfile.ZipFile(zip_path, "r")
    except (OSError, zipfile.BadZipFile) as exc:
        _raise_from(error_type, f"Invalid ZIP archive: {zip_path}", exc)

    with zf:
        try:
            members = zf.infolist()
        except zipfile.BadZipFile as exc:
            _raise_from(error_type, f"Invalid ZIP archive: {zip_path}", exc)
        if len(members) > max_entries:
            _raise(
                error_type,
                f"ZIP archive contains too many entries ({len(members)} > {max_entries})",
            )

        normalized_members: list[tuple[zipfile.ZipInfo, str, bool]] = []
        total_size = 0
        for member in members:
            normalized_name = _safe_zip_name(member.filename, error_type=error_type)
            is_dir = member.is_dir() or normalized_name.endswith("/")

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

            if not is_dir:
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

            normalized_members.append((member, normalized_name, is_dir))

        # The loop above bounds the *declared* total via member.file_size, but a
        # crafted archive can understate those headers. Mirror the per-member
        # guard below with a cumulative count of the bytes actually written so
        # the total-size bound holds even when the headers lie.
        total_written = 0
        for member, normalized_name, is_dir in normalized_members:
            member_path = target_dir / normalized_name
            if is_dir:
                try:
                    member_path.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    _raise_from(
                        error_type,
                        f"Failed to create ZIP directory {member.filename}: {exc}",
                        exc,
                    )
                continue

            try:
                member_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                _raise_from(
                    error_type,
                    f"Failed to create parent directory for ZIP member {member.filename}: {exc}",
                    exc,
                )
            written = 0
            # Raised outside the try below: if error_type subclasses OSError or
            # RuntimeError, raising inside would re-wrap the limit error as
            # "Failed to extract" and lose the size-bound message.
            limit_error: str | None = None
            try:
                with zf.open(member, "r") as source, member_path.open("wb") as dest:
                    while True:
                        chunk = source.read(READ_CHUNK_SIZE)
                        if not chunk:
                            break
                        written += len(chunk)
                        if written > max_member_bytes:
                            limit_error = (
                                f"ZIP member {member.filename} exceeds maximum size "
                                f"of {max_member_bytes} bytes"
                            )
                            break
                        total_written += len(chunk)
                        if total_written > max_total_bytes:
                            limit_error = (
                                f"ZIP archive exceeds maximum uncompressed size "
                                f"of {max_total_bytes} bytes"
                            )
                            break
                        dest.write(chunk)
            except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
                _raise_from(
                    error_type,
                    f"Failed to extract ZIP member {member.filename}: {exc}",
                    exc,
                )
            if limit_error is not None:
                _raise(error_type, limit_error)
