"""Tests for bounded download and ZIP extraction helpers."""

from __future__ import annotations

import stat
import weakref
import zipfile

import pytest

from specify_cli._download_security import (
    is_https_or_localhost_http,
    is_loopback_url,
    read_response_limited,
    read_zip_member_limited,
    safe_extract_zip,
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


class _CustomZipError(ValueError):
    pass


def test_read_response_limited_rejects_oversized_download():
    with pytest.raises(ValueError, match="exceeds maximum size"):
        read_response_limited(_Response(b"abcde"), max_bytes=4)


def test_read_response_limited_returns_full_body_within_limit():
    assert read_response_limited(_Response(b"abcde"), max_bytes=10) == b"abcde"


def test_read_response_limited_enforces_bound_under_short_reads():
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


@pytest.mark.parametrize(
    "member_name",
    [
        "../evil.txt",
        "nested/../../evil.txt",
        "nested\\..\\evil.txt",
        "C:\\Windows\\evil.txt",
        "C:drive-relative.txt",
    ],
)
def test_safe_extract_zip_rejects_traversal(tmp_path, member_name):
    zip_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(member_name, "nope")

    with pytest.raises(ValueError, match="Unsafe path"):
        safe_extract_zip(zip_path, tmp_path / "out")


@pytest.mark.parametrize("member_name", [".", "./file.txt", "nested/./file.txt", "nested//file.txt"])
def test_safe_extract_zip_rejects_dot_path_segments(tmp_path, member_name):
    zip_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(member_name, "nope")

    with pytest.raises(_CustomZipError, match="Unsafe path"):
        safe_extract_zip(zip_path, tmp_path / "out", error_type=_CustomZipError)


def test_safe_extract_zip_rejects_symlinks(tmp_path):
    zip_path = tmp_path / "bad.zip"
    info = zipfile.ZipInfo("link")
    info.external_attr = (stat.S_IFLNK | 0o777) << 16

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(info, "target")

    with pytest.raises(ValueError, match="Unsafe symlink"):
        safe_extract_zip(zip_path, tmp_path / "out")


def test_safe_extract_zip_rejects_symlink_without_partial_extraction(tmp_path):
    zip_path = tmp_path / "mixed.zip"
    link = zipfile.ZipInfo("evil-link")
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("safe/first.txt", "hello")
        zf.writestr(link, "target")
        zf.writestr("safe/second.txt", "world")

    out_dir = tmp_path / "out"
    with pytest.raises(ValueError, match="Unsafe symlink"):
        safe_extract_zip(zip_path, out_dir)

    assert not out_dir.exists() or not any(out_dir.rglob("*"))


def test_safe_extract_zip_rejects_oversized_member(tmp_path):
    zip_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("big.txt", "abcde")

    with pytest.raises(ValueError, match="exceeds maximum size"):
        safe_extract_zip(zip_path, tmp_path / "out", max_member_bytes=4)


def test_safe_extract_zip_rejects_too_many_entries(tmp_path):
    zip_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("one.txt", "1")
        zf.writestr("two.txt", "2")

    with pytest.raises(ValueError, match="too many entries"):
        safe_extract_zip(zip_path, tmp_path / "out", max_entries=1)


def test_safe_extract_zip_rejects_total_uncompressed_size(tmp_path):
    zip_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("one.txt", "123")
        zf.writestr("two.txt", "456")

    with pytest.raises(ValueError, match="maximum uncompressed size"):
        safe_extract_zip(zip_path, tmp_path / "out", max_total_bytes=5)


def test_safe_extract_zip_wraps_bad_zip_file(tmp_path):
    zip_path = tmp_path / "bad.zip"
    zip_path.write_bytes(b"not a zip archive")

    with pytest.raises(_CustomZipError, match="Invalid ZIP archive"):
        safe_extract_zip(zip_path, tmp_path / "out", error_type=_CustomZipError)


def test_read_zip_member_limited_returns_member_within_limit(tmp_path):
    zip_path = tmp_path / "ok.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("extension.yml", "extension:\n  id: demo\n")

    with zipfile.ZipFile(zip_path, "r") as zf:
        data = read_zip_member_limited(zf, "extension.yml")

    assert data == b"extension:\n  id: demo\n"


def test_read_zip_member_limited_rejects_oversized_member(tmp_path):
    zip_path = tmp_path / "bomb.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("extension.yml", "a" * 5000)

    with zipfile.ZipFile(zip_path, "r") as zf:
        with pytest.raises(ValueError, match="exceeds maximum size"):
            read_zip_member_limited(zf, "extension.yml", max_bytes=16)


def test_read_zip_member_limited_wraps_missing_member(tmp_path):
    zip_path = tmp_path / "ok.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("other.txt", "x")

    with zipfile.ZipFile(zip_path, "r") as zf:
        with pytest.raises(_CustomZipError, match="ZIP member not found"):
            read_zip_member_limited(zf, "extension.yml", error_type=_CustomZipError)


def test_safe_extract_zip_extracts_safe_archive(tmp_path):
    zip_path = tmp_path / "ok.zip"
    out_dir = tmp_path / "out"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("nested/file.txt", "hello")

    safe_extract_zip(zip_path, out_dir)

    assert (out_dir / "nested" / "file.txt").read_text(encoding="utf-8") == "hello"


def test_safe_extract_zip_treats_normalized_trailing_backslash_as_directory(tmp_path):
    zip_path = tmp_path / "ok.zip"
    out_dir = tmp_path / "out"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("nested\\", "")
        zf.writestr("nested/file.txt", "hello")

    safe_extract_zip(zip_path, out_dir)

    assert (out_dir / "nested").is_dir()
    assert (out_dir / "nested" / "file.txt").read_text(encoding="utf-8") == "hello"
