"""Tests for bounded HTTP download helpers."""

from __future__ import annotations

import weakref

import pytest

from specify_cli._download_security import (
    is_https_or_localhost_http,
    is_loopback_url,
    read_response_limited,
)


@pytest.mark.parametrize(
    "url, allowed",
    [
        ("https://example.com/preset.zip", True),
        ("http://localhost:8000/preset.zip", True),
        ("http://127.0.0.1/preset.zip", True),
        ("http://127.0.0.2/preset.zip", True),
        ("http://127.255.255.254/preset.zip", True),
        ("http://[::1]/preset.zip", True),
        ("http://[0:0:0:0:0:0:0:1]/preset.zip", True),
        ("http://[::ffff:127.0.0.2]/preset.zip", True),
        ("http://[::1%25lo0]/preset.zip", True),
        # Non-loopback HTTP is rejected.
        ("http://example.com/preset.zip", False),
        ("http://192.0.2.1/preset.zip", False),
        ("http://[fe80::1]/preset.zip", False),
        ("http://[fe80::1%25lo0]/preset.zip", False),
        ("http://0.0.0.0/preset.zip", False),
        ("http://0/preset.zip", False),
        ("http://[::]/preset.zip", False),
        ("http://[::ffff:0.0.0.0]/preset.zip", False),
        # Ambiguous/platform-dependent spellings may never authorize HTTP.
        ("http://127.1/preset.zip", False),
        ("http://2130706433/preset.zip", False),
        ("http://0x7f000001/preset.zip", False),
        ("http://017700000001/preset.zip", False),
        ("http://0177.0.0.1/preset.zip", False),
        ("http://00177.0.0.1/preset.zip", False),
        ("http://localhost./preset.zip", False),
        ("http://ℓocalhost/preset.zip", False),
        ("http://127。0。0。1/preset.zip", False),
        # A hostname is always required, even for HTTPS.
        ("https:///preset.zip", False),
        ("https://", False),
        # Invalid ports must be rejected before urllib opens the URL.
        ("https://example.com:notaport/preset.zip", False),
        ("https://example.com:+443/preset.zip", False),
        ("https://example.com:65536/preset.zip", False),
        # urllib decodes escapes in the authority before connecting; reject
        # encoded reg-names so validation and connection cannot disagree.
        ("https://127%2e0%2e0%2e1/preset.zip", False),
        ("https://%31%32%37.0.0.1/preset.zip", False),
        ("https://local%68ost/preset.zip", False),
        ("https://example.com%3a443/preset.zip", False),
        ("https://[::1%lo0]/preset.zip", False),
        ("https://[::ffff:127%2e0.0.1]/preset.zip", False),
        ("https://[::ffff:7f00%3a1]/preset.zip", False),
        ("https://[::ffff%3a127.0.0.1]/preset.zip", False),
    ],
)
def test_is_https_or_localhost_http(url, allowed):
    assert is_https_or_localhost_http(url) is allowed


@pytest.mark.parametrize(
    "url",
    [
        "https://localhost/internal",
        "https://127.0.0.2/internal",
        "https://[::1]/internal",
        "https://[::1%25lo0]/internal",
        "https://[::ffff:127.0.0.2]/internal",
    ],
)
def test_is_loopback_url_recognizes_effective_loopback_literals(url):
    assert is_loopback_url(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "https://localhost./internal",
        "https://service.localhost/internal",
        "https://service.localhost./internal",
        "https://127.1/internal",
        "https://2130706433/internal",
        "https://0x7f000001/internal",
        "https://017700000001/internal",
        "https://0177.0.0.1/internal",
        "https://ℓocalhost/internal",
        "https://127。0。0。1/internal",
        "https://127%2e0%2e0%2e1/internal",
        "https://0.0.0.0/internal",
        "https://0/internal",
        "https://00.00.00.00/internal",
        "https://[::]/internal",
        "https://[::ffff:0.0.0.0]/internal",
    ],
)
def test_is_loopback_url_does_not_authorize_ambiguous_spellings(url):
    assert is_loopback_url(url) is False


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


class _RecordingResponse(_Response):
    def __init__(self, data: bytes, *, chunk: int | None = None):
        super().__init__(data, chunk=chunk)
        self.requested_sizes: list[int] = []

    def read(self, size: int = -1) -> bytes:
        self.requested_sizes.append(size)
        return super().read(size)


class _TrackedChunk(bytearray):
    pass


class _OneByteResponse:
    """Return distinct weak-referenceable chunks to detect retained fragments."""

    def __init__(self, count: int):
        self.remaining = count
        self.refs: list[weakref.ReferenceType[_TrackedChunk]] = []
        self.peak_live = 0

    def read(self, _size: int = -1) -> bytes | _TrackedChunk:
        if self.remaining == 0:
            return b""
        self.remaining -= 1
        chunk = _TrackedChunk(b"x")
        self.refs.append(weakref.ref(chunk))
        self.peak_live = max(
            self.peak_live,
            sum(ref() is not None for ref in self.refs),
        )
        return chunk


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


def test_read_response_limited_does_not_retain_short_read_fragments():
    response = _OneByteResponse(64)

    assert read_response_limited(response, max_bytes=64) == b"x" * 64
    assert response.peak_live <= 2


def test_read_response_limited_caps_underlying_reads_at_64_kib():
    response = _RecordingResponse(b"x" * (64 * 1024 + 1))

    with pytest.raises(ValueError, match="exceeds maximum size"):
        read_response_limited(response, max_bytes=64 * 1024)

    assert max(response.requested_sizes) <= 64 * 1024


@pytest.mark.parametrize("value", [None, "1", 1.5, True])
def test_read_response_limited_rejects_non_integer_limits(value):
    with pytest.raises(TypeError, match="integer"):
        read_response_limited(_Response(b""), max_bytes=value)


def test_read_response_limited_rejects_negative_limit_without_reading():
    response = _RecordingResponse(b"")

    with pytest.raises(ValueError, match="non-negative"):
        read_response_limited(response, max_bytes=-1)

    assert response.requested_sizes == []


def test_read_response_limited_allows_empty_response_at_zero_limit():
    assert read_response_limited(_Response(b""), max_bytes=0) == b""


class _CustomLimitError(Exception):
    pass


def test_read_response_limited_rejects_first_byte_at_zero_limit():
    with pytest.raises(_CustomLimitError, match="exceeds maximum size"):
        read_response_limited(
            _Response(b"x"),
            max_bytes=0,
            error_type=_CustomLimitError,
        )
