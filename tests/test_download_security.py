"""Tests for bounded HTTP download helpers."""

from __future__ import annotations

import pytest

from specify_cli._download_security import (
    is_https_or_localhost_http,
    read_response_limited,
)


@pytest.mark.parametrize(
    "url, allowed",
    [
        ("https://example.com/preset.zip", True),
        ("http://localhost:8000/preset.zip", True),
        ("http://127.0.0.1/preset.zip", True),
        ("http://[::1]/preset.zip", True),
        # Non-loopback HTTP is rejected.
        ("http://example.com/preset.zip", False),
        # Loopback allowance is an exact-string match: 127.0.0.2 is not covered.
        ("http://127.0.0.2/preset.zip", False),
        # A hostname is always required, even for HTTPS.
        ("https:///preset.zip", False),
        ("https://", False),
    ],
)
def test_is_https_or_localhost_http(url, allowed):
    assert is_https_or_localhost_http(url) is allowed


class _Response:
    """Faithful stream stand-in: read() advances a cursor and returns b"" at EOF."""

    def __init__(self, data: bytes, *, chunk: int | None = None):
        self.data = data
        self.pos = 0
        # When set, never return more than *chunk* bytes per call even if more is
        # requested - simulates short reads (e.g. chunked transfer encoding).
        self.chunk = chunk

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = len(self.data) - self.pos
        if self.chunk is not None:
            size = min(size, self.chunk)
        out = self.data[self.pos : self.pos + size]
        self.pos += len(out)
        return out


def test_read_response_limited_rejects_oversized_download():
    with pytest.raises(ValueError, match="exceeds maximum size"):
        read_response_limited(_Response(b"abcde"), max_bytes=4)


def test_read_response_limited_returns_full_body_within_limit():
    assert read_response_limited(_Response(b"abcde"), max_bytes=10) == b"abcde"


def test_read_response_limited_enforces_bound_under_short_reads():
    # A server that streams more than max_bytes total while every read() returns
    # fewer bytes than requested (chunked encoding) must still be rejected - a
    # single read(max_bytes + 1) could be fooled, the accumulating loop cannot.
    response = _Response(b"x" * 100, chunk=8)
    with pytest.raises(ValueError, match="exceeds maximum size"):
        read_response_limited(response, max_bytes=16)
