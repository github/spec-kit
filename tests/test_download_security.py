"""Tests for bounded download and ZIP extraction helpers."""

from __future__ import annotations

import ast
import stat
import zipfile
from pathlib import Path

import pytest

from specify_cli._download_security import (
    is_https_or_localhost_http,
    read_response_limited,
    read_zip_member_limited,
    safe_extract_zip,
    verify_sha256,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_FILE_HASH_READ_ALLOWLIST = {
    ("src/specify_cli/extensions.py", "get_hash"),
    ("src/specify_cli/integrations/catalog.py", "get_hash"),
    ("src/specify_cli/presets/__init__.py", "get_hash"),
}


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


class _CustomZipError(ValueError):
    pass


def _constant_int(node: ast.AST) -> int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and isinstance(node.operand.value, int)
    ):
        return -node.operand.value
    return None


def _is_unbounded_read(call: ast.Call) -> bool:
    if call.args:
        size = _constant_int(call.args[0])
        return size is not None and size < 0

    for keyword in call.keywords:
        if keyword.arg == "size":
            size = _constant_int(keyword.value)
            return size is not None and size < 0

    return True


class _UnboundedReadVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self._function_stack: list[str] = []
        self.offenders: list[tuple[int, str]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._function_stack.append(node.name)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._function_stack.append(node.name)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "read"
            and _is_unbounded_read(node)
        ):
            function_name = self._function_stack[-1] if self._function_stack else ""
            self.offenders.append((node.lineno, function_name))
        self.generic_visit(node)


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


def test_remote_downloads_do_not_use_unbounded_response_reads():
    offenders = []
    for path in (REPO_ROOT / "src" / "specify_cli").rglob("*.py"):
        rel_path = path.relative_to(REPO_ROOT).as_posix()
        visitor = _UnboundedReadVisitor()
        visitor.visit(ast.parse(path.read_text(encoding="utf-8")))
        for line_number, function_name in visitor.offenders:
            if (rel_path, function_name) not in LOCAL_FILE_HASH_READ_ALLOWLIST:
                offenders.append(f"{rel_path}:{line_number}")

    assert offenders == []


def test_verify_sha256_rejects_mismatch():
    with pytest.raises(ValueError, match="checksum mismatch"):
        verify_sha256(b"payload", "sha256:" + "0" * 64)


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


# An empty member name is rejected by _safe_zip_name too, but zipfile cannot
# even write such an entry, so it is not testable through this API.
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
    # A symlink sitting next to benign members must be rejected before ANY
    # file is written: validation runs over the whole member list first, so an
    # unsafe member cannot leak a partially-extracted tree to disk.
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

    # Nothing should have been written - not even the benign member that
    # precedes the symlink in the archive.
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


def test_safe_extract_zip_bounds_actual_written_bytes_when_headers_understate_size(
    tmp_path, monkeypatch
):
    # Defense in depth: the pre-extraction check sums the *declared*
    # member.file_size values, which a crafted archive can understate so that
    # check passes. If the ZIP reader then yields more bytes than the header
    # promised, the extraction loop must still abort once the cumulative bytes
    # actually written exceed max_total_bytes. CPython's own zipfile happens to
    # bound member reads to file_size and CRC-check them, so we substitute a
    # reader that does not - exercising our guard rather than the stdlib's.
    zip_path = tmp_path / "liar.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("a.txt", "")  # declared file_size 0 means declared total stays 0
        zf.writestr("b.txt", "")

    class _OverreadingStream:
        """A member reader that yields more bytes than any header declared."""

        def __init__(self, payload: bytes):
            self._remaining = payload

        def read(self, size: int = -1) -> bytes:
            if size is None or size < 0:
                size = len(self._remaining)
            out, self._remaining = self._remaining[:size], self._remaining[size:]
            return out

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    # Each member streams 8 bytes despite declaring 0; the per-member cap (10 MiB
    # default) is untouched, so only the cumulative guard can stop this.
    monkeypatch.setattr(
        zipfile.ZipFile, "open", lambda self, *a, **k: _OverreadingStream(b"x" * 8)
    )

    # 8 bytes for "a.txt" (total 8 ≤ 12), then "b.txt" busts the 12-byte ceiling.
    with pytest.raises(ValueError, match="maximum uncompressed size"):
        safe_extract_zip(zip_path, tmp_path / "out", max_total_bytes=12)


def test_safe_extract_zip_wraps_bad_zip_file(tmp_path):
    zip_path = tmp_path / "bad.zip"
    zip_path.write_bytes(b"not a zip archive")

    with pytest.raises(_CustomZipError, match="Invalid ZIP archive"):
        safe_extract_zip(zip_path, tmp_path / "out", error_type=_CustomZipError)


def test_safe_extract_zip_wraps_filesystem_errors(tmp_path):
    zip_path = tmp_path / "ok.zip"
    blocked_parent = tmp_path / "blocked"
    blocked_parent.write_text("not a directory", encoding="utf-8")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("file.txt", "hello")

    with pytest.raises(_CustomZipError, match="Failed to create parent directory"):
        safe_extract_zip(
            zip_path,
            blocked_parent / "out",
            error_type=_CustomZipError,
        )


def test_safe_extract_zip_wraps_directory_filesystem_errors(tmp_path):
    zip_path = tmp_path / "ok.zip"
    blocked_parent = tmp_path / "blocked"
    blocked_parent.write_text("not a directory", encoding="utf-8")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.mkdir("dir")

    with pytest.raises(_CustomZipError, match="Failed to create ZIP directory"):
        safe_extract_zip(
            zip_path,
            blocked_parent / "out",
            error_type=_CustomZipError,
        )


def test_read_zip_member_limited_returns_member_within_limit(tmp_path):
    zip_path = tmp_path / "ok.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("extension.yml", "extension:\n  id: demo\n")

    with zipfile.ZipFile(zip_path, "r") as zf:
        data = read_zip_member_limited(zf, "extension.yml")

    assert data == b"extension:\n  id: demo\n"


def test_read_zip_member_limited_rejects_oversized_member(tmp_path):
    # A manifest whose declared size already blows the cap (the zip-bomb shape:
    # a few KB compressed that decompresses to gigabytes) is rejected before any
    # of it is read into memory.
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
