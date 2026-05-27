"""Tests for bounded download and ZIP extraction helpers."""

from __future__ import annotations

import ast
import stat
import zipfile
from pathlib import Path

import pytest

from specify_cli._download_security import (
    read_response_limited,
    safe_extract_zip,
    verify_sha256,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_FILE_HASH_READ_ALLOWLIST = {
    ("src/specify_cli/extensions.py", "get_hash"),
    ("src/specify_cli/integrations/catalog.py", "get_hash"),
    ("src/specify_cli/presets/__init__.py", "get_hash"),
}


class _Response:
    def __init__(self, data: bytes):
        self.data = data

    def read(self, size: int = -1) -> bytes:
        return self.data if size < 0 else self.data[:size]


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


@pytest.mark.parametrize("member_name", ["", ".", "./file.txt", "nested/./file.txt", "nested//file.txt"])
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


def test_safe_extract_zip_extracts_safe_archive(tmp_path):
    zip_path = tmp_path / "ok.zip"
    out_dir = tmp_path / "out"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("nested/file.txt", "hello")

    safe_extract_zip(zip_path, out_dir)

    assert (out_dir / "nested" / "file.txt").read_text(encoding="utf-8") == "hello"
