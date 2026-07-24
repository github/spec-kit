"""Tests for bounded download and ZIP extraction helpers."""

from __future__ import annotations

import stat
import struct
import weakref
import zipfile
import zlib

import pytest

from specify_cli._download_security import (
    MAX_ZIP_CENTRAL_DIRECTORY_BYTES,
    build_safe_download_path,
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

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        return False


class _CustomZipError(ValueError):
    pass


class _ExplodingResponse:
    def read(self, _size: int = -1) -> bytes:
        raise zlib.error("corrupt compressed data")

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        return False


class _FakeZipArchive:
    def __init__(
        self,
        response,
        *,
        filename: str = "extension.yml",
        file_size: int = 0,
    ):
        self.response = response
        self.info = zipfile.ZipInfo(filename)
        self.info.file_size = file_size

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        return False

    def getinfo(self, _name):
        return self.info

    def infolist(self):
        return [self.info]

    def open(self, _member, _mode="r"):
        return self.response


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


def test_read_response_limited_escapes_control_characters_in_label():
    with pytest.raises(ValueError) as exc_info:
        read_response_limited(
            _Response(b"x"),
            max_bytes=0,
            label="bad\x1b[2J download",
        )

    assert "\x1b" not in str(exc_info.value)
    assert "\\x1b" in str(exc_info.value)


@pytest.mark.parametrize(
    "identifier",
    [
        "../outside",
        "..\\outside",
        "a" * 256,
        "delete\x7f",
        "csi\x9b[2J",
        "\ud800",
    ],
)
def test_build_safe_download_path_rejects_nonportable_identifiers(
    tmp_path, identifier
):
    with pytest.raises(ValueError, match="Unsafe archive download filename"):
        build_safe_download_path(
            tmp_path,
            identifier,
            "1.0.0",
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


def _legacy_zip_eocd(
    *,
    entries: int,
    central_directory_size: int,
    central_directory_offset: int = 0,
    comment_size: int = 0,
) -> bytes:
    return struct.pack(
        "<4s4H2LH",
        b"PK\x05\x06",
        0,
        0,
        entries,
        entries,
        central_directory_size,
        central_directory_offset,
        comment_size,
    )


def test_safe_extract_zip_preflights_declared_entry_count(tmp_path, monkeypatch):
    zip_path = tmp_path / "too-many.zip"
    zip_path.write_bytes(
        _legacy_zip_eocd(entries=513, central_directory_size=0)
    )
    monkeypatch.setattr(
        zipfile,
        "ZipFile",
        lambda *_args, **_kwargs: pytest.fail("ZipFile constructor was called"),
    )

    with pytest.raises(ValueError, match="too many entries"):
        safe_extract_zip(zip_path, tmp_path / "out")


def test_safe_extract_zip_preflights_actual_entry_count_when_eocd_lies(
    tmp_path, monkeypatch
):
    central_header = b"PK\x01\x02" + b"\x00" * 42
    central_directory = central_header * 513
    zip_path = tmp_path / "lying-count.zip"
    zip_path.write_bytes(
        central_directory
        + _legacy_zip_eocd(
            entries=1,
            central_directory_size=len(central_directory),
        )
    )
    monkeypatch.setattr(
        zipfile,
        "ZipFile",
        lambda *_args, **_kwargs: pytest.fail("ZipFile constructor was called"),
    )

    with pytest.raises(ValueError, match="too many entries"):
        safe_extract_zip(zip_path, tmp_path / "out")


def test_safe_extract_zip_rejects_truncated_last_eocd_comment(
    tmp_path, monkeypatch
):
    trailing_eocd = _legacy_zip_eocd(
        entries=0,
        central_directory_size=0,
        comment_size=1,
    )
    zip_path = tmp_path / "ambiguous-eocd.zip"
    zip_path.write_bytes(
        _legacy_zip_eocd(
            entries=0,
            central_directory_size=0,
            comment_size=len(trailing_eocd),
        )
        + trailing_eocd
    )
    monkeypatch.setattr(
        zipfile,
        "ZipFile",
        lambda *_args, **_kwargs: pytest.fail("ZipFile constructor was called"),
    )

    with pytest.raises(ValueError, match="Invalid ZIP archive"):
        safe_extract_zip(zip_path, tmp_path / "out")


def test_safe_extract_zip_rejects_zip64_before_zipfile_construction(
    tmp_path, monkeypatch
):
    zip64_eocd = struct.pack(
        "<4sQ2H2L4Q",
        b"PK\x06\x06",
        44,
        45,
        45,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    zip64_locator = struct.pack(
        "<4sLQL",
        b"PK\x06\x07",
        0,
        0,
        1,
    )
    zip_path = tmp_path / "zip64.zip"
    zip_path.write_bytes(
        zip64_eocd
        + zip64_locator
        + _legacy_zip_eocd(
            entries=0xFFFF,
            central_directory_size=0xFFFFFFFF,
            central_directory_offset=0xFFFFFFFF,
        )
    )
    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == []
    monkeypatch.setattr(
        zipfile,
        "ZipFile",
        lambda *_args, **_kwargs: pytest.fail("ZipFile constructor was called"),
    )

    with pytest.raises(ValueError, match="ZIP64"):
        safe_extract_zip(zip_path, tmp_path / "out")


def test_safe_extract_zip_rejects_central_entry_from_another_disk(tmp_path):
    zip_path = tmp_path / "multi-disk-entry.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("file.txt", "contents")

    archive = bytearray(zip_path.read_bytes())
    central_header = archive.index(b"PK\x01\x02")
    struct.pack_into("<H", archive, central_header + 34, 1)
    zip_path.write_bytes(archive)

    with pytest.raises(ValueError, match="Multi-disk"):
        safe_extract_zip(zip_path, tmp_path / "out")


def test_safe_extract_zip_caps_central_directory_before_zipfile(
    tmp_path, monkeypatch
):
    zip_path = tmp_path / "large-directory.zip"
    zip_path.write_bytes(
        _legacy_zip_eocd(
            entries=1,
            central_directory_size=MAX_ZIP_CENTRAL_DIRECTORY_BYTES + 1,
        )
    )
    monkeypatch.setattr(
        zipfile,
        "ZipFile",
        lambda *_args, **_kwargs: pytest.fail("ZipFile constructor was called"),
    )

    with pytest.raises(ValueError, match="central directory exceeds"):
        safe_extract_zip(zip_path, tmp_path / "out")


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


def test_safe_extract_zip_wraps_unsupported_zip_version(tmp_path):
    zip_path = tmp_path / "unsupported.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("file.txt", "contents")

    archive = bytearray(zip_path.read_bytes())
    central_header = archive.index(b"PK\x01\x02")
    struct.pack_into("<H", archive, central_header + 6, 99)
    zip_path.write_bytes(archive)

    with pytest.raises(_CustomZipError, match="Invalid ZIP archive"):
        safe_extract_zip(zip_path, tmp_path / "out", error_type=_CustomZipError)


def test_read_zip_member_limited_returns_member_within_limit(tmp_path):
    zip_path = tmp_path / "ok.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("extension.yml", "extension:\n  id: demo\n")

    with zipfile.ZipFile(zip_path, "r") as zf:
        data = read_zip_member_limited(zf, "extension.yml")

    assert data == b"extension:\n  id: demo\n"


def test_read_zip_member_limited_does_not_retain_short_read_fragments():
    response = _OneByteResponse(64)
    archive = _FakeZipArchive(response, file_size=64)

    assert (
        read_zip_member_limited(archive, "extension.yml", max_bytes=64)
        == b"x" * 64
    )
    assert response.peak_live <= 2


@pytest.mark.parametrize("value", [None, "1", 1.5, True])
def test_read_zip_member_limited_rejects_non_integer_limits(value):
    archive = _FakeZipArchive(_OneByteResponse(0))

    with pytest.raises(TypeError, match="integer"):
        read_zip_member_limited(archive, "extension.yml", max_bytes=value)


def test_read_zip_member_limited_rejects_negative_limit_without_opening():
    archive = _FakeZipArchive(_OneByteResponse(0))

    with pytest.raises(ValueError, match="non-negative"):
        read_zip_member_limited(archive, "extension.yml", max_bytes=-1)


def test_read_zip_member_limited_rejects_oversized_member(tmp_path):
    zip_path = tmp_path / "bomb.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("extension.yml", "a" * 5000)

    with zipfile.ZipFile(zip_path, "r") as zf:
        with pytest.raises(ValueError, match="exceeds maximum size"):
            read_zip_member_limited(zf, "extension.yml", max_bytes=16)


def test_read_zip_member_limited_rejects_when_declared_size_is_too_small():
    archive = _FakeZipArchive(_OneByteResponse(5), file_size=1)

    with pytest.raises(ValueError, match="exceeds maximum size"):
        read_zip_member_limited(
            archive,
            "extension.yml",
            max_bytes=4,
        )


def test_read_zip_member_limited_escapes_control_characters_in_errors():
    member_name = "bad\x1b[2J/extension.yml"
    archive = _FakeZipArchive(
        _OneByteResponse(0),
        filename=member_name,
        file_size=5,
    )

    with pytest.raises(ValueError) as exc_info:
        read_zip_member_limited(
            archive,
            member_name,
            max_bytes=4,
        )

    assert "\x1b" not in str(exc_info.value)
    assert "\\x1b" in str(exc_info.value)


def test_read_zip_member_limited_wraps_missing_member(tmp_path):
    zip_path = tmp_path / "ok.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("other.txt", "x")

    with zipfile.ZipFile(zip_path, "r") as zf:
        with pytest.raises(_CustomZipError, match="ZIP member not found"):
            read_zip_member_limited(zf, "extension.yml", error_type=_CustomZipError)


def test_read_zip_member_limited_wraps_decompression_errors():
    archive = _FakeZipArchive(_ExplodingResponse(), file_size=1)

    with pytest.raises(_CustomZipError, match="Failed to read ZIP member"):
        read_zip_member_limited(
            archive,
            "extension.yml",
            error_type=_CustomZipError,
        )


@pytest.mark.parametrize(
    "members",
    [
        [("nested\\file.txt", "first"), ("nested/file.txt", "second")],
        [("node", "file"), ("node/child.txt", "child")],
        [("node/child.txt", "child"), ("node", "file")],
        [("Readme.txt", "first"), ("README.TXT", "second")],
        [("caf\u00e9.txt", "first"), ("cafe\u0301.txt", "second")],
    ],
)
def test_safe_extract_zip_rejects_conflicting_paths_before_writing(
    tmp_path, members
):
    zip_path = tmp_path / "conflict.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for name, contents in members:
            zf.writestr(name, contents)

    out_dir = tmp_path / "out"
    with pytest.raises(ValueError, match="Conflicting path"):
        safe_extract_zip(zip_path, out_dir)

    assert not out_dir.exists() or not any(out_dir.rglob("*"))


@pytest.mark.parametrize(
    "member_name",
    [
        "file::$DATA",
        "file.",
        "file ",
        " leading.txt",
        "NUL.txt",
        "COM\u00b9.log",
        "COM1 .txt",
        "CONOUT$.log",
        "nested/name?.txt",
        "nested/control\u0001.txt",
        "nested/delete\u007f.txt",
        "nested/csi\u009b[2J.txt",
    ],
)
def test_safe_extract_zip_rejects_nonportable_member_names(tmp_path, member_name):
    zip_path = tmp_path / "nonportable.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(member_name, "contents")

    out_dir = tmp_path / "out"
    with pytest.raises(ValueError, match="Unsafe path"):
        safe_extract_zip(zip_path, out_dir)

    assert not out_dir.exists() or not any(out_dir.rglob("*"))


@pytest.mark.parametrize(
    "member_name",
    [
        "a" * 256,
        "a/" * 2048 + "file.txt",
    ],
)
def test_safe_extract_zip_rejects_excessively_long_paths(tmp_path, member_name):
    zip_path = tmp_path / "nonportable.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(member_name, "contents")

    out_dir = tmp_path / "out"
    with pytest.raises(ValueError, match="Unsafe path"):
        safe_extract_zip(zip_path, out_dir)

    assert not out_dir.exists() or not any(out_dir.rglob("*"))


@pytest.mark.parametrize(
    ("control_character", "escaped_character"),
    [
        ("\x1b", "\\x1b"),
        ("\x7f", "\\x7f"),
        ("\x9b", "\\x9b"),
    ],
)
def test_safe_extract_zip_escapes_unicode_control_characters_in_errors(
    tmp_path,
    control_character,
    escaped_character,
):
    zip_path = tmp_path / "terminal-control.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(f"bad{control_character}[2J.txt", "contents")

    with pytest.raises(ValueError) as exc_info:
        safe_extract_zip(zip_path, tmp_path / "out")

    assert control_character not in str(exc_info.value)
    assert escaped_character in str(exc_info.value)


def test_safe_extract_zip_accepts_single_decomposed_unicode_name(tmp_path):
    zip_path = tmp_path / "unicode.zip"
    out_dir = tmp_path / "out"
    decomposed_name = "cafe\u0301.txt"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(decomposed_name, "contents")

    safe_extract_zip(zip_path, out_dir)

    assert (out_dir / decomposed_name).read_text(encoding="utf-8") == "contents"


def test_safe_extract_zip_wraps_decompression_errors(tmp_path, monkeypatch):
    zip_path = tmp_path / "corrupt.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("extension.yml", "x")

    archive = _FakeZipArchive(_ExplodingResponse(), file_size=1)
    monkeypatch.setattr(zipfile, "ZipFile", lambda *_args, **_kwargs: archive)

    with pytest.raises(_CustomZipError, match="Failed to extract ZIP member"):
        safe_extract_zip(
            zip_path,
            tmp_path / "out",
            error_type=_CustomZipError,
        )


def test_safe_extract_zip_enforces_actual_member_size(tmp_path, monkeypatch):
    zip_path = tmp_path / "lying-size.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("extension.yml", "x")

    archive = _FakeZipArchive(_OneByteResponse(5), file_size=1)
    monkeypatch.setattr(zipfile, "ZipFile", lambda *_args, **_kwargs: archive)

    with pytest.raises(ValueError, match="exceeds maximum size"):
        safe_extract_zip(
            zip_path,
            tmp_path / "out",
            max_member_bytes=4,
        )


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
