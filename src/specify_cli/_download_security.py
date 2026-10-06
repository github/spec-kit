"""Helpers for bounded downloads and archive extraction."""

from __future__ import annotations

import io
import re
import socket
import stat
import struct
import tarfile
import unicodedata
import zipfile
import zlib
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from ipaddress import IPv4Address, IPv6Address, ip_address
from itertools import pairwise
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import BinaryIO, Literal, NoReturn, TypeVar
from urllib.parse import ParseResult, urlparse


ErrorT = TypeVar("ErrorT", bound=Exception)
ArchiveFormat = Literal["zip", "tar.gz"]

MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
MAX_ZIP_ENTRIES = 512
MAX_ZIP_MEMBER_BYTES = 10 * 1024 * 1024
MAX_ZIP_TOTAL_BYTES = 50 * 1024 * 1024
MAX_ZIP_PATH_BYTES = 4096
MAX_ZIP_COMPONENT_BYTES = 255
# ``ZipFile`` reads this whole structure into memory. Four MiB leaves roughly
# 8 KiB of filename/extra/comment metadata for each of the 512 allowed entries.
MAX_ZIP_CENTRAL_DIRECTORY_BYTES = 4 * 1024 * 1024
READ_CHUNK_SIZE = 64 * 1024

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

_WINDOWS_INVALID_FILENAME_CHARS = frozenset('<>:"|?*')
_WINDOWS_RESERVED_FILENAME = re.compile(
    r"^(?:con|prn|aux|nul|conin\$|conout\$|"
    r"com[1-9\u00b9\u00b2\u00b3]|lpt[1-9\u00b9\u00b2\u00b3])$",
    re.IGNORECASE,
)
_ZIP_EOCD = struct.Struct("<4s4H2LH")
_ZIP_EOCD_SIGNATURE = b"PK\x05\x06"
_ZIP64_LOCATOR_SIGNATURE = b"PK\x06\x07"
_ZIP_CENTRAL_HEADER_SIZE = 46
_ZIP_CENTRAL_SIGNATURE = b"PK\x01\x02"
_ZIP_LOCAL_HEADER_SIZE = 30
_ZIP_LOCAL_SIGNATURE = b"PK\x03\x04"
_ZIP_EXTRA_HEADER = struct.Struct("<HH")
_ZIP64_EXTRA_FIELD_ID = 0x0001
_ZIP64_MIN_EXTRACT_VERSION = 45
_ZIP_UINT16_MAX = (1 << 16) - 1
_ZIP_UINT32_MAX = (1 << 32) - 1
_ZIP_MAX_COMMENT_BYTES = (1 << 16) - 1
_BOUNDED_ZIP_COMPRESSION_METHODS = frozenset(
    (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
)
#: Decompression failures a truncated or corrupt gzip stream raises from
#: ``tarfile``. Most are wrapped in ``TarError``, but two escape raw, and
#: neither derives from ``TarError`` or ``OSError``, so both bypass a
#: ``(TarError, OSError)`` handler:
#:
#: * ``EOFError`` -- from the gzip layer when the stream ends before its
#:   end-of-stream marker, i.e. a truncated archive.
#: * ``zlib.error`` -- from a corrupt deflate block. ``tarfile`` converts this
#:   to ``ReadError`` while reading a member *header*, but the forward seek it
#:   performs to skip member *data* sits outside that conversion, so a corrupt
#:   region past the first header escapes raw.
_TAR_DECOMPRESSION_ERRORS = (tarfile.TarError, EOFError, zlib.error)

_ARCHIVE_CONTENT_TYPES: dict[str, ArchiveFormat] = {
    "application/gzip": "tar.gz",
    "application/x-gzip": "tar.gz",
    "application/x-tar+gzip": "tar.gz",
    "application/zip": "zip",
    "application/x-zip-compressed": "zip",
}


def archive_format_from_name(name: str) -> ArchiveFormat | None:
    """Return the supported archive format declared by a path or URL."""
    try:
        path = urlparse(name).path.lower()
    except (TypeError, ValueError):
        return None
    if path.endswith(".tar.gz") or path.endswith(".tgz"):
        return "tar.gz"
    if path.endswith(".zip"):
        return "zip"
    return None


def archive_format_from_content_type(content_type: str | None) -> ArchiveFormat | None:
    """Return the supported archive format declared by an HTTP Content-Type."""
    if not isinstance(content_type, str):
        return None
    media_type = content_type.partition(";")[0].strip().lower()
    return _ARCHIVE_CONTENT_TYPES.get(media_type)


def archive_suffix(archive_format: ArchiveFormat) -> str:
    """Return the canonical filename suffix for *archive_format*."""
    if archive_format == "zip":
        return ".zip"
    if archive_format == "tar.gz":
        return ".tar.gz"
    raise ValueError(f"Unsupported archive format: {archive_format!r}")


def detect_archive_format(
    archive_path: Path,
    *,
    archive_file: BinaryIO | None = None,
    source_name: str | None = None,
    content_type: str | None = None,
    error_type: type[ErrorT] = ValueError,
) -> ArchiveFormat:
    """Validate the declared archive format against the file contents.

    A recognized path/URL suffix is authoritative. For remote responses whose
    final URL has no archive suffix, a recognized Content-Type may declare the
    format instead. When both declarations are recognized they must agree, and
    the resulting declaration must match the archive bytes.
    """
    archive_path = Path(archive_path)
    name_format = archive_format_from_name(
        source_name if source_name is not None else str(archive_path)
    )
    content_format = archive_format_from_content_type(content_type)
    if (
        name_format is not None
        and content_format is not None
        and name_format != content_format
    ):
        _raise(
            error_type,
            f"Archive format mismatch: filename declares {name_format} but "
            f"Content-Type declares {content_format}",
        )
    declared_format = name_format or content_format

    with ExitStack() as stack:
        if archive_file is None:
            try:
                archive_file = stack.enter_context(archive_path.open("rb"))
            except OSError as exc:
                _raise_from(error_type, f"Invalid archive: {archive_path}", exc)
        try:
            archive_file.seek(0)
            is_zip = zipfile.is_zipfile(archive_file)
            archive_file.seek(0)
            signature = archive_file.read(4)
            # Let the bounded ZIP preflight report structural errors such as
            # impossible entry counts. ``is_zipfile`` rejects those before the
            # extractor can produce the established security diagnostic.
            is_zip = is_zip or signature in {
                b"PK\x03\x04",
                b"PK\x05\x06",
                b"PK\x07\x08",
            }
            is_gzip = signature[:2] == b"\x1f\x8b"
            archive_file.seek(0)
            is_tar_gz = False
            if is_gzip:
                try:
                    with tarfile.open(fileobj=archive_file, mode="r:gz"):
                        is_tar_gz = True
                except _TAR_DECOMPRESSION_ERRORS:
                    # A truncated gzip stream raises a bare EOFError here rather
                    # than a TarError, so catching only TarError let it escape
                    # this probe as a raw exception instead of leaving
                    # ``is_tar_gz`` False and reporting the format mismatch.
                    pass
            archive_file.seek(0)
        except OSError as exc:
            _raise_from(error_type, f"Invalid archive: {archive_path}", exc)

    actual_format: ArchiveFormat | None
    if is_zip and not is_tar_gz:
        actual_format = "zip"
    elif is_tar_gz and not is_zip:
        actual_format = "tar.gz"
    else:
        actual_format = None
    if declared_format is None:
        if actual_format is None:
            _raise(
                error_type,
                "Unsupported archive format; expected .zip, .tar.gz, or .tgz",
            )
        declared_format = actual_format
    if actual_format != declared_format:
        actual_label = actual_format or "invalid/unsupported data"
        _raise(
            error_type,
            f"Archive format mismatch: expected {declared_format}, got {actual_label}",
        )
    return declared_format


def _ip_address_without_scope(
    hostname: str,
) -> IPv4Address | IPv6Address | None:
    """Parse a canonical IP literal, validating an optional IPv6 zone ID."""
    if "%" in hostname:
        # Accept only the RFC 6874 ``%25<zone>`` spelling. Other escapes can
        # alter the IPv6 address when urllib unquotes the authority.
        address_text, separator, zone = hostname.partition("%25")
        if (
            not separator
            or ":" not in address_text
            or "%" in address_text
            or "%" in zone
        ):
            return None
        if not zone or any(
            not (character.isascii() and (character.isalnum() or character in "._~-"))
            for character in zone
        ):
            return None
    else:
        address_text = hostname
    try:
        address = ip_address(address_text)
    except ValueError:
        return None
    if "%" in hostname and not isinstance(address, IPv6Address):
        return None
    return address


def _is_ip_loopback(address: IPv4Address | IPv6Address | None) -> bool:
    if address is None:
        return False
    mapped = getattr(address, "ipv4_mapped", None)
    return address.is_loopback or bool(mapped and mapped.is_loopback)


def _is_ip_local_redirect_target(
    address: IPv4Address | IPv6Address | None,
) -> bool:
    """Treat loopback and unspecified listener aliases as local targets."""
    if address is None:
        return False
    mapped = getattr(address, "ipv4_mapped", None)
    return _is_ip_loopback(address) or address.is_unspecified or bool(
        mapped and mapped.is_unspecified
    )


def _parse_url(url: str) -> ParseResult | None:
    """Parse *url*, rejecting missing hosts and malformed ports."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        # Accessing ``port`` performs urllib's range and syntax validation.
        parsed.port
    except (TypeError, ValueError):
        return None
    if not hostname:
        return None

    if "%" in hostname:
        # urllib unquotes reg-name/IPv4 authorities before connecting. Reject
        # them so encoded dots, characters, ports, or brackets cannot make the
        # validated hostname differ from the effective target. The only safe
        # percent form retained is a validated bracketed IPv6 zone ID.
        if _ip_address_without_scope(hostname) is None:
            return None
    elif ":" not in hostname:
        try:
            hostname.encode("idna")
        except UnicodeError:
            return None
    return parsed


def _is_definite_loopback_host(hostname: str) -> bool:
    """Recognize only unambiguous hosts that may safely authorize HTTP."""
    if not hostname.isascii():
        return False
    if hostname == "localhost":
        return True
    return _is_ip_loopback(_ip_address_without_scope(hostname))


def _is_potential_local_target_host(hostname: str) -> bool:
    """Conservatively classify aliases that could reach a local listener."""
    if ":" in hostname:
        return _is_ip_local_redirect_target(_ip_address_without_scope(hostname))
    try:
        host = hostname.encode("idna").decode("ascii").lower().removesuffix(".")
    except UnicodeError:
        return False
    if host == "localhost" or host.endswith(".localhost"):
        return True

    address = _ip_address_without_scope(host)
    if address is None:
        # Historical IPv4 spellings are resolver-dependent. They are never
        # trusted to authorize HTTP, but treating them as potentially local
        # prevents them from bypassing a remote-to-loopback redirect check.
        try:
            address = ip_address(socket.inet_aton(host))
        except OSError:
            return False
    return _is_ip_local_redirect_target(address)


def is_loopback_url(url: str) -> bool:
    """Return whether *url* has an unambiguous loopback host."""
    parsed = _parse_url(url)
    return parsed is not None and _is_definite_loopback_host(parsed.hostname)


def _is_potential_local_target_url(url: str) -> bool:
    parsed = _parse_url(url)
    return parsed is not None and _is_potential_local_target_host(parsed.hostname)


def is_https_or_localhost_http(url: str) -> bool:
    """Return True if *url* is HTTPS, or HTTP limited to loopback hosts.

    Shared scheme-safety predicate used by the auth HTTP redirect handler and
    direct URL validations in CLI download flows.

    A hostname is always required: a URL without one (e.g. ``https:///x``)
    has no real target and is rejected regardless of scheme.

    The HTTP exception is deliberately limited to unambiguous ``localhost``
    and canonical IPv4/IPv6 loopback literals. Ambiguous numeric, Unicode, and
    unspecified-address aliases are classified defensively for redirects but
    never authorize HTTP. No DNS lookup is performed; DNS and hosts-file
    aliases require connection-level rebinding protection outside this helper.
    """
    parsed = _parse_url(url)
    if parsed is None:
        return False
    return parsed.scheme == "https" or (
        parsed.scheme == "http" and _is_definite_loopback_host(parsed.hostname)
    )


def is_safe_download_redirect(old_url: str, new_url: str) -> bool:
    """Return whether a redirect preserves the shared download URL policy."""
    if not is_https_or_localhost_http(new_url):
        return False
    return not _is_potential_local_target_url(new_url) or is_loopback_url(old_url)


def _raise(error_type: type[ErrorT], message: str) -> NoReturn:
    raise error_type(message)


def _raise_from(error_type: type[ErrorT], message: str, exc: Exception) -> NoReturn:
    raise error_type(message) from exc


class _ReadLimitExceeded(Exception):
    """Internal signal used to keep domain-specific errors at call sites."""


def _validate_non_negative_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def _validate_max_bytes(max_bytes: int) -> None:
    _validate_non_negative_int(max_bytes, "max_bytes")


def _read_limited(response, max_bytes: int) -> bytes:
    """Read a stream with bounded requests and without retaining fragments."""
    output = io.BytesIO()
    total = 0
    limit = max_bytes + 1
    while total < limit:
        chunk = response.read(min(READ_CHUNK_SIZE, limit - total))
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise _ReadLimitExceeded
        output.write(chunk)
    return output.getvalue()


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
    _validate_max_bytes(max_bytes)
    try:
        return _read_limited(response, max_bytes)
    except _ReadLimitExceeded:
        _raise(error_type, f"{label!r} exceeds maximum size of {max_bytes} bytes")


def build_safe_download_path(
    target_dir: Path,
    identifier: object,
    version: object,
    *,
    error_type: type[ErrorT] = ValueError,
    label: str = "archive",
    suffix: str = ".zip",
) -> Path:
    """Build a portable single-component archive path inside *target_dir*."""
    if not isinstance(identifier, str) or not isinstance(version, str):
        _raise(
            error_type,
            f"Unsafe {label} download filename derived from "
            f"{identifier!r} and {version!r}",
        )

    if suffix not in {".zip", ".tar.gz", ".tgz"}:
        _raise(error_type, f"Unsupported archive download suffix: {suffix!r}")
    filename = f"{identifier}-{version}{suffix}"
    try:
        filename_too_long = (
            len(filename.encode("utf-8")) > MAX_ZIP_COMPONENT_BYTES
        )
    except UnicodeEncodeError:
        filename_too_long = True
    posix_path = PurePosixPath(filename)
    windows_path = PureWindowsPath(filename)
    if (
        filename_too_long
        or posix_path.name != filename
        or windows_path.name != filename
        or any(unicodedata.category(character) == "Cc" for character in filename)
        or any(
            character in _WINDOWS_INVALID_FILENAME_CHARS
            for character in filename
        )
        or filename.endswith((" ", "."))
    ):
        _raise(
            error_type,
            f"Unsafe {label} download filename derived from "
            f"{identifier!r} and {version!r}",
        )
    return Path(target_dir) / filename


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
    _validate_max_bytes(max_bytes)
    member_label = label or name
    try:
        info = zf.getinfo(name)
    except KeyError as exc:
        _raise_from(error_type, f"ZIP member not found: {name!r}", exc)
    if info.file_size > max_bytes:
        _raise(
            error_type,
            f"ZIP member {member_label!r} exceeds maximum size of {max_bytes} bytes",
        )

    try:
        with zf.open(name, "r") as source:
            return _read_limited(source, max_bytes)
    except _ReadLimitExceeded:
        _raise(
            error_type,
            f"ZIP member {member_label!r} exceeds maximum size of {max_bytes} bytes",
        )
    except Exception as exc:
        _raise_from(
            error_type,
            f"Failed to read ZIP member {member_label!r}: {exc!r}",
            exc,
        )


def normalize_archive_member_name(
    name: str,
    *,
    archive_label: str = "archive",
    error_type: type[ErrorT] = ValueError,
) -> str:
    """Return a normalized, portable archive member name or raise if unsafe."""
    if "\x00" in name:
        _raise(error_type, f"Unsafe path in {archive_label} archive: {name!r}")

    normalized = name.replace("\\", "/")
    try:
        encoded_name = normalized.encode("utf-8")
    except UnicodeEncodeError:
        _raise(error_type, f"Unsafe path in {archive_label} archive: {name!r}")
    if len(encoded_name) > MAX_ZIP_PATH_BYTES:
        _raise(
            error_type,
            f"Unsafe path in {archive_label} archive: {name!r} "
            "(not portable across supported filesystems)",
        )
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
            f"Unsafe path in {archive_label} archive: {name!r} "
            "(potential path traversal)",
        )
    for part in raw_parts:
        reserved_stem = part.partition(".")[0].partition(":")[0].rstrip(" ")
        if (
            len(part.encode("utf-8")) > MAX_ZIP_COMPONENT_BYTES
            or any(
                unicodedata.category(character) == "Cc"
                for character in part
            )
            or any(character in _WINDOWS_INVALID_FILENAME_CHARS for character in part)
            or part.startswith(" ")
            or part.endswith((" ", "."))
            or _WINDOWS_RESERVED_FILENAME.fullmatch(reserved_stem)
        ):
            _raise(
                error_type,
                f"Unsafe path in {archive_label} archive: {name!r} "
                "(not portable across supported filesystems)",
            )
    return normalized


def normalize_zip_member_name(
    name: str,
    *,
    error_type: type[ErrorT] = ValueError,
) -> str:
    """Return a normalized, portable ZIP member name or raise if unsafe."""
    return normalize_archive_member_name(
        name,
        archive_label="ZIP",
        error_type=error_type,
    )


def portable_archive_path_key(name: str) -> tuple[str, ...]:
    """Return a comparison key for filesystems with case/Unicode folding."""
    normalized_name = name.replace("\\", "/")
    return tuple(
        unicodedata.normalize("NFC", part.casefold())
        for part in normalized_name.removesuffix("/").split("/")
    )


def portable_zip_path_key(name: str) -> tuple[str, ...]:
    """Backward-compatible ZIP-specific alias for portable archive keys."""
    return portable_archive_path_key(name)


def _raise_zip64(error_type: type[ErrorT]) -> NoReturn:
    _raise(
        error_type,
        "ZIP64 archives are not supported by the bounded extractor",
    )


def _preflight_zip_entry_features(
    extract_version: int,
    compression_method: int,
    *,
    error_type: type[ErrorT],
) -> None:
    """Enforce the formats whose output can be bounded by ``ZipExtFile``.

    Python's BZIP2 and LZMA ``ZipExtFile`` paths do not pass the requested
    output length to the decompressor; only STORED and DEFLATED preserve this
    module's hard memory bound. APPNOTE assigns extract version 4.5 to ZIP64
    size extensions. Because this field declares the minimum extractor feature
    level, reject 4.5 and every newer level for the supported methods,
    independently of the usual size sentinels and extra field.
    """
    if compression_method not in _BOUNDED_ZIP_COMPRESSION_METHODS:
        _raise(
            error_type,
            f"Unsupported ZIP compression method {compression_method}; "
            "the bounded extractor supports only STORED and DEFLATED",
        )
    if extract_version >= _ZIP64_MIN_EXTRACT_VERSION:
        _raise(
            error_type,
            "ZIP64 or newer ZIP features requiring extractor version 4.5 or "
            "newer are not supported by the bounded extractor",
        )


def _reject_zip64_extra_fields(
    extra: bytes,
    zip_path: Path,
    *,
    error_type: type[ErrorT],
) -> None:
    """Reject ZIP64 extra fields and malformed complete extra records."""
    offset = 0
    while offset + _ZIP_EXTRA_HEADER.size <= len(extra):
        field_id, field_size = _ZIP_EXTRA_HEADER.unpack_from(extra, offset)
        field_end = offset + _ZIP_EXTRA_HEADER.size + field_size
        if field_id == _ZIP64_EXTRA_FIELD_ID:
            _raise_zip64(error_type)
        if field_end > len(extra):
            _raise(error_type, f"Invalid ZIP archive: {zip_path}")
        offset = field_end


def _preflight_zip_local_header(
    archive_file,
    zip_path: Path,
    *,
    error_type: type[ErrorT],
    archive_prefix_size: int,
    central_directory_start: int,
    local_header_offset: int,
) -> None:
    """Reject local-entry ZIP64 indicators before ``ZipFile`` is constructed."""
    physical_offset = archive_prefix_size + local_header_offset
    if (
        physical_offset < archive_prefix_size
        or physical_offset + _ZIP_LOCAL_HEADER_SIZE > central_directory_start
    ):
        _raise(error_type, f"Invalid ZIP archive: {zip_path}")

    archive_file.seek(physical_offset)
    header = archive_file.read(_ZIP_LOCAL_HEADER_SIZE)
    if (
        len(header) != _ZIP_LOCAL_HEADER_SIZE
        or header[:4] != _ZIP_LOCAL_SIGNATURE
    ):
        _raise(error_type, f"Invalid ZIP archive: {zip_path}")

    extract_version = struct.unpack_from("<H", header, 4)[0]
    compression_method = struct.unpack_from("<H", header, 8)[0]
    _preflight_zip_entry_features(
        extract_version,
        compression_method,
        error_type=error_type,
    )

    compressed_size, uncompressed_size = struct.unpack_from("<LL", header, 18)
    if (
        compressed_size == _ZIP_UINT32_MAX
        or uncompressed_size == _ZIP_UINT32_MAX
    ):
        _raise_zip64(error_type)

    filename_size, extra_size = struct.unpack_from("<HH", header, 26)
    extra_offset = physical_offset + _ZIP_LOCAL_HEADER_SIZE + filename_size
    if extra_offset + extra_size > central_directory_start:
        _raise(error_type, f"Invalid ZIP archive: {zip_path}")

    archive_file.seek(extra_offset)
    extra = archive_file.read(extra_size)
    if len(extra) != extra_size:
        _raise(error_type, f"Invalid ZIP archive: {zip_path}")
    _reject_zip64_extra_fields(extra, zip_path, error_type=error_type)


def _preflight_zip_central_directory(
    archive_file,
    zip_path: Path,
    *,
    error_type: type[ErrorT],
    max_entries: int,
) -> None:
    """Bound and count the central directory before ``ZipFile`` materializes it."""
    archive_file.seek(0, 2)
    file_size = archive_file.tell()
    tail_size = min(file_size, _ZIP_EOCD.size + _ZIP_MAX_COMMENT_BYTES)
    archive_file.seek(file_size - tail_size)
    tail = archive_file.read(tail_size)

    # ZipFile selects the last EOCD signature in the search window. Inspect
    # exactly that record too: falling back to an earlier signature would let
    # the preflight validate one central directory while ZipFile materializes
    # another.
    eocd_index = tail.rfind(_ZIP_EOCD_SIGNATURE)
    if eocd_index < 0 or eocd_index + _ZIP_EOCD.size > len(tail):
        _raise(error_type, f"Invalid ZIP archive: {zip_path}")
    eocd = _ZIP_EOCD.unpack_from(tail, eocd_index)
    comment_size = eocd[-1]
    if eocd_index + _ZIP_EOCD.size + comment_size != len(tail):
        _raise(error_type, f"Invalid ZIP archive: {zip_path}")

    eocd_offset = file_size - len(tail) + eocd_index
    if eocd_offset >= 20:
        archive_file.seek(eocd_offset - 20)
        if archive_file.read(4) == _ZIP64_LOCATOR_SIGNATURE:
            _raise_zip64(error_type)

    (
        _signature,
        disk_number,
        central_directory_disk,
        entries_on_disk,
        declared_entries,
        central_directory_size,
        central_directory_offset,
        _comment_size,
    ) = eocd
    if (
        disk_number != 0
        or central_directory_disk != 0
        or entries_on_disk != declared_entries
    ):
        _raise(error_type, "Multi-disk ZIP archives are not supported")
    if (
        declared_entries == _ZIP_UINT16_MAX
        or central_directory_size == _ZIP_UINT32_MAX
        or central_directory_offset == _ZIP_UINT32_MAX
    ):
        _raise_zip64(error_type)
    if declared_entries > max_entries:
        _raise(
            error_type,
            f"ZIP archive contains too many entries "
            f"({declared_entries} > {max_entries})",
        )
    if central_directory_size > MAX_ZIP_CENTRAL_DIRECTORY_BYTES:
        _raise(
            error_type,
            f"ZIP central directory exceeds maximum size of "
            f"{MAX_ZIP_CENTRAL_DIRECTORY_BYTES} bytes",
        )

    central_directory_start = eocd_offset - central_directory_size
    if (
        central_directory_start < 0
        or central_directory_offset > central_directory_start
    ):
        _raise(error_type, f"Invalid ZIP archive: {zip_path}")
    archive_prefix_size = central_directory_start - central_directory_offset

    consumed = 0
    actual_entries = 0
    local_header_offsets: list[int] = []
    while consumed < central_directory_size:
        archive_file.seek(central_directory_start + consumed)
        remaining = central_directory_size - consumed
        if remaining < _ZIP_CENTRAL_HEADER_SIZE:
            _raise(error_type, f"Invalid ZIP archive: {zip_path}")
        header = archive_file.read(_ZIP_CENTRAL_HEADER_SIZE)
        if (
            len(header) != _ZIP_CENTRAL_HEADER_SIZE
            or header[:4] != _ZIP_CENTRAL_SIGNATURE
        ):
            _raise(error_type, f"Invalid ZIP archive: {zip_path}")

        extract_version = struct.unpack_from("<H", header, 6)[0]
        compression_method = struct.unpack_from("<H", header, 10)[0]
        _preflight_zip_entry_features(
            extract_version,
            compression_method,
            error_type=error_type,
        )

        compressed_size, uncompressed_size = struct.unpack_from("<LL", header, 20)
        disk_number_start = struct.unpack_from("<H", header, 34)[0]
        local_header_offset = struct.unpack_from("<L", header, 42)[0]
        if (
            compressed_size == _ZIP_UINT32_MAX
            or uncompressed_size == _ZIP_UINT32_MAX
            or local_header_offset == _ZIP_UINT32_MAX
            or disk_number_start == _ZIP_UINT16_MAX
        ):
            _raise_zip64(error_type)
        if disk_number_start != 0:
            _raise(error_type, "Multi-disk ZIP archives are not supported")

        filename_size, extra_size, comment_size = struct.unpack_from(
            "<HHH", header, 28
        )
        variable_size = filename_size + extra_size + comment_size
        record_size = _ZIP_CENTRAL_HEADER_SIZE + variable_size
        if record_size > remaining:
            _raise(error_type, f"Invalid ZIP archive: {zip_path}")
        variable_data = archive_file.read(variable_size)
        if len(variable_data) != variable_size:
            _raise(error_type, f"Invalid ZIP archive: {zip_path}")
        extra = variable_data[filename_size : filename_size + extra_size]
        _reject_zip64_extra_fields(extra, zip_path, error_type=error_type)
        local_header_offsets.append(local_header_offset)

        consumed += record_size
        actual_entries += 1
        if actual_entries > max_entries:
            _raise(
                error_type,
                f"ZIP archive contains too many entries "
                f"({actual_entries} > {max_entries})",
            )

    if actual_entries != declared_entries:
        _raise(error_type, f"Invalid ZIP archive: {zip_path}")

    for local_header_offset in local_header_offsets:
        _preflight_zip_local_header(
            archive_file,
            zip_path,
            error_type=error_type,
            archive_prefix_size=archive_prefix_size,
            central_directory_start=central_directory_start,
            local_header_offset=local_header_offset,
        )


@contextmanager
def open_zip_bounded(
    zip_path: Path,
    *,
    archive_file: BinaryIO | None = None,
    error_type: type[ErrorT] = ValueError,
    max_entries: int = MAX_ZIP_ENTRIES,
) -> Iterator[zipfile.ZipFile]:
    """Open an untrusted ZIP after a bounded-memory header preflight."""
    _validate_non_negative_int(max_entries, "max_entries")
    zip_path = Path(zip_path)
    with ExitStack() as stack:
        if archive_file is None:
            try:
                archive_file = stack.enter_context(zip_path.open("rb"))
            except OSError as exc:
                _raise_from(error_type, f"Invalid ZIP archive: {zip_path}", exc)
        try:
            _preflight_zip_central_directory(
                archive_file,
                zip_path,
                error_type=error_type,
                max_entries=max_entries,
            )
        except OSError as exc:
            _raise_from(error_type, f"Invalid ZIP archive: {zip_path}", exc)
        try:
            archive_file.seek(0)
            zf = stack.enter_context(zipfile.ZipFile(archive_file, "r"))
        except Exception as exc:
            _raise_from(error_type, f"Invalid ZIP archive: {zip_path}", exc)
        yield zf


def safe_extract_zip(
    zip_path: Path,
    target_dir: Path,
    *,
    archive_file: BinaryIO | None = None,
    error_type: type[ErrorT] = ValueError,
    max_entries: int = MAX_ZIP_ENTRIES,
    max_member_bytes: int = MAX_ZIP_MEMBER_BYTES,
    max_total_bytes: int = MAX_ZIP_TOTAL_BYTES,
) -> None:
    """Extract a ZIP archive after path, symlink, and size validation."""
    _validate_non_negative_int(max_member_bytes, "max_member_bytes")
    _validate_non_negative_int(max_total_bytes, "max_total_bytes")
    try:
        target_root = target_dir.resolve()
    except OSError as exc:
        _raise_from(error_type, f"Invalid ZIP extraction target: {target_dir}", exc)

    with open_zip_bounded(
        zip_path,
        archive_file=archive_file,
        error_type=error_type,
        max_entries=max_entries,
    ) as zf:
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
        validated_paths: dict[tuple[str, ...], tuple[str, bool]] = {}
        total_size = 0
        for member in members:
            normalized_name = normalize_zip_member_name(
                member.filename,
                error_type=error_type,
            )
            is_dir = member.is_dir() or normalized_name.endswith("/")
            path_key = portable_archive_path_key(normalized_name)

            existing = validated_paths.get(path_key)
            if existing is not None:
                _raise(
                    error_type,
                    f"Conflicting path in ZIP archive: {member.filename} conflicts "
                    f"with {existing[0]}",
                )
            validated_paths[path_key] = (member.filename, is_dir)

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

        # Tuple sorting places every path immediately before its descendants.
        # One adjacent comparison per entry detects file/directory conflicts
        # without repeatedly rebuilding every path prefix.
        for (
            (path_key, (original, is_dir)),
            (next_key, (next_original, _next_is_dir)),
        ) in pairwise(sorted(validated_paths.items())):
            if (
                not is_dir
                and len(next_key) > len(path_key)
                and next_key[: len(path_key)] == path_key
            ):
                _raise(
                    error_type,
                    f"Conflicting path in ZIP archive: {original} conflicts "
                    f"with {next_original}",
                )

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
            except Exception as exc:
                _raise_from(
                    error_type,
                    f"Failed to extract ZIP member {member.filename}: {exc}",
                    exc,
                )
            if limit_error is not None:
                _raise(error_type, limit_error)


def safe_extract_tar(
    archive_path: Path,
    target_dir: Path,
    *,
    archive_file: BinaryIO | None = None,
    error_type: type[ErrorT] = ValueError,
    max_entries: int = MAX_ZIP_ENTRIES,
    max_member_bytes: int = MAX_ZIP_MEMBER_BYTES,
    max_total_bytes: int = MAX_ZIP_TOTAL_BYTES,
) -> None:
    """Extract a gzip-compressed tar after ZIP-equivalent safety validation."""
    _validate_non_negative_int(max_entries, "max_entries")
    _validate_non_negative_int(max_member_bytes, "max_member_bytes")
    _validate_non_negative_int(max_total_bytes, "max_total_bytes")
    archive_path = Path(archive_path)
    try:
        target_root = target_dir.resolve()
    except OSError as exc:
        _raise_from(error_type, f"Invalid tar extraction target: {target_dir}", exc)

    try:
        if archive_file is not None:
            archive_file.seek(0)
        archive = tarfile.open(
            archive_path if archive_file is None else None,
            mode="r:gz",
            fileobj=archive_file,
        )
    except (*_TAR_DECOMPRESSION_ERRORS, OSError) as exc:
        _raise_from(error_type, f"Invalid tar.gz archive: {archive_path}", exc)

    with archive:
        validated: list[tuple[tarfile.TarInfo, str, bool]] = []
        validated_paths: dict[tuple[str, ...], tuple[str, bool]] = {}
        total_size = 0
        try:
            for index, member in enumerate(archive, start=1):
                if index > max_entries:
                    _raise(
                        error_type,
                        f"tar.gz archive contains too many entries "
                        f"({index} > {max_entries})",
                    )
                normalized_name = normalize_archive_member_name(
                    member.name,
                    archive_label="tar.gz",
                    error_type=error_type,
                )
                is_dir = member.isdir()
                if member.issym():
                    _raise(
                        error_type,
                        f"Unsafe symlink in tar.gz archive: {member.name}",
                    )
                if member.islnk():
                    _raise(
                        error_type,
                        f"Unsafe hard link in tar.gz archive: {member.name}",
                    )
                if not is_dir and not member.isreg():
                    _raise(
                        error_type,
                        f"Unsafe member type in tar.gz archive: {member.name}",
                    )

                path_key = portable_archive_path_key(normalized_name)
                existing = validated_paths.get(path_key)
                if existing is not None:
                    _raise(
                        error_type,
                        f"Conflicting path in tar.gz archive: {member.name} "
                        f"conflicts with {existing[0]}",
                    )
                validated_paths[path_key] = (member.name, is_dir)

                member_path = (target_dir / normalized_name).resolve()
                try:
                    member_path.relative_to(target_root)
                except ValueError:
                    _raise(
                        error_type,
                        f"Unsafe path in tar.gz archive: {member.name} "
                        "(potential path traversal)",
                    )

                if not is_dir:
                    if member.size > max_member_bytes:
                        _raise(
                            error_type,
                            f"tar.gz member {member.name} exceeds maximum size "
                            f"of {max_member_bytes} bytes",
                        )
                    total_size += member.size
                    if total_size > max_total_bytes:
                        _raise(
                            error_type,
                            f"tar.gz archive exceeds maximum uncompressed size "
                            f"of {max_total_bytes} bytes",
                        )
                validated.append((member, normalized_name, is_dir))
        except (*_TAR_DECOMPRESSION_ERRORS, OSError) as exc:
            _raise_from(
                error_type,
                f"Invalid tar.gz archive: {archive_path}",
                exc,
            )

        for (
            (path_key, (original, is_dir)),
            (next_key, (next_original, _next_is_dir)),
        ) in pairwise(sorted(validated_paths.items())):
            if (
                not is_dir
                and len(next_key) > len(path_key)
                and next_key[: len(path_key)] == path_key
            ):
                _raise(
                    error_type,
                    f"Conflicting path in tar.gz archive: {original} conflicts "
                    f"with {next_original}",
                )

        total_written = 0
        for member, normalized_name, is_dir in validated:
            member_path = target_dir / normalized_name
            if is_dir:
                try:
                    member_path.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    _raise_from(
                        error_type,
                        f"Failed to create tar.gz directory {member.name}: {exc}",
                        exc,
                    )
                continue
            try:
                member_path.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    _raise(
                        error_type,
                        f"Failed to read tar.gz member {member.name}",
                    )
                written = 0
                limit_error: str | None = None
                with source, member_path.open("wb") as dest:
                    while True:
                        chunk = source.read(READ_CHUNK_SIZE)
                        if not chunk:
                            break
                        written += len(chunk)
                        if written > max_member_bytes:
                            limit_error = (
                                f"tar.gz member {member.name} exceeds maximum size "
                                f"of {max_member_bytes} bytes"
                            )
                            break
                        total_written += len(chunk)
                        if total_written > max_total_bytes:
                            limit_error = (
                                f"tar.gz archive exceeds maximum uncompressed size "
                                f"of {max_total_bytes} bytes"
                            )
                            break
                        dest.write(chunk)
            except Exception as exc:
                _raise_from(
                    error_type,
                    f"Failed to extract tar.gz member {member.name}: {exc}",
                    exc,
                )
            if limit_error is not None:
                _raise(error_type, limit_error)


def safe_extract_archive(
    archive_path: Path,
    target_dir: Path,
    *,
    archive_file: BinaryIO | None = None,
    source_name: str | None = None,
    content_type: str | None = None,
    error_type: type[ErrorT] = ValueError,
    max_entries: int = MAX_ZIP_ENTRIES,
    max_member_bytes: int = MAX_ZIP_MEMBER_BYTES,
    max_total_bytes: int = MAX_ZIP_TOTAL_BYTES,
) -> ArchiveFormat:
    """Detect and securely extract a supported archive."""
    archive_format = detect_archive_format(
        archive_path,
        archive_file=archive_file,
        source_name=source_name,
        content_type=content_type,
        error_type=error_type,
    )
    extractor = safe_extract_zip if archive_format == "zip" else safe_extract_tar
    extractor(
        archive_path,
        target_dir,
        archive_file=archive_file,
        error_type=error_type,
        max_entries=max_entries,
        max_member_bytes=max_member_bytes,
        max_total_bytes=max_total_bytes,
    )
    return archive_format
