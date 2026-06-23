"""Helpers for bounded HTTP downloads."""

from __future__ import annotations

from typing import NoReturn, TypeVar
from urllib.parse import urlparse


ErrorT = TypeVar("ErrorT", bound=Exception)

MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
READ_CHUNK_SIZE = 1024 * 1024

# Tighter ceiling for responses that are read fully into memory and parsed as
# JSON. The 50 MiB MAX_DOWNLOAD_BYTES default is sized for archive/payload
# downloads; JSON metadata responses are far smaller, so capping them close to
# their real size shrinks the memory-DoS surface and keeps the "too large"
# error reachable (rather than only triggering on tens of MiB). Pass it
# explicitly at each JSON call site so the intended bound is pinned there.
# METADATA covers fixed-shape single-object responses (an OAuth token, one
# release's metadata): a few KiB in practice, 1 MiB is already generous.
MAX_JSON_METADATA_BYTES = 1 * 1024 * 1024


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
