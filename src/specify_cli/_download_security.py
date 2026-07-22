"""Helpers for bounded HTTP downloads."""

from __future__ import annotations

import io
import socket
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import NoReturn, TypeVar
from urllib.parse import ParseResult, urlparse


ErrorT = TypeVar("ErrorT", bound=Exception)

MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
READ_CHUNK_SIZE = 64 * 1024

# Tighter ceiling for responses that are read fully into memory and parsed as
# JSON. The 50 MiB MAX_DOWNLOAD_BYTES default is sized for archive/payload
# downloads; JSON metadata responses are far smaller, so capping them close to
# their real size shrinks the memory-DoS surface and keeps the "too large"
# error reachable (rather than only triggering on tens of MiB). Pass it
# explicitly at each JSON call site so the intended bound is pinned there.
# METADATA covers fixed-shape single-object responses (an OAuth token, one
# release's metadata): a few KiB in practice, 1 MiB is already generous.
MAX_JSON_METADATA_BYTES = 1 * 1024 * 1024


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
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int):
        raise TypeError("max_bytes must be an integer")
    if max_bytes < 0:
        raise ValueError("max_bytes must be non-negative")

    output = io.BytesIO()
    total = 0
    limit = max_bytes + 1
    while total < limit:
        chunk = response.read(min(READ_CHUNK_SIZE, limit - total))
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            _raise(error_type, f"{label} exceeds maximum size of {max_bytes} bytes")
        output.write(chunk)
    return output.getvalue()
