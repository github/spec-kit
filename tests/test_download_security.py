"""Tests for bounded download and ZIP extraction helpers."""

from __future__ import annotations

import stat
import zipfile
import re
from pathlib import Path

import pytest

from specify_cli._download_security import (
    read_response_limited,
    safe_extract_zip,
    verify_sha256,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_RESPONSE_READ_RE = re.compile(r"\b(?:resp|response)\.read\(\)")


class _Response:
    def __init__(self, data: bytes):
        self.data = data

    def read(self, size: int = -1) -> bytes:
        return self.data if size < 0 else self.data[:size]


def test_read_response_limited_rejects_oversized_download():
    with pytest.raises(ValueError, match="exceeds maximum size"):
        read_response_limited(_Response(b"abcde"), max_bytes=4)


def test_remote_downloads_do_not_use_unbounded_response_reads():
    offenders = []
    for path in (REPO_ROOT / "src" / "specify_cli").rglob("*.py"):
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if RAW_RESPONSE_READ_RE.search(line):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{line_number}")

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


def test_safe_extract_zip_rejects_symlinks(tmp_path):
    zip_path = tmp_path / "bad.zip"
    info = zipfile.ZipInfo("link")
    info.external_attr = (stat.S_IFLNK | 0o777) << 16

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(info, "target")

    with pytest.raises(ValueError, match="Unsafe symlink"):
        safe_extract_zip(zip_path, tmp_path / "out")


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


def test_safe_extract_zip_extracts_safe_archive(tmp_path):
    zip_path = tmp_path / "ok.zip"
    out_dir = tmp_path / "out"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("nested/file.txt", "hello")

    safe_extract_zip(zip_path, out_dir)

    assert (out_dir / "nested" / "file.txt").read_text(encoding="utf-8") == "hello"
