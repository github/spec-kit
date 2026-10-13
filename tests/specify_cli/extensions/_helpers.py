"""Shared helpers for extension command tests."""
from __future__ import annotations

import os
from pathlib import Path


MINIMAL_ZIP_BYTES = b"PK\x05\x06" + b"\x00" * 18


def open_test_download_zip(project_root, download_dir, zip_filename):
    """Create a transient download file using platform-appropriate semantics."""
    target = download_dir / zip_filename
    o_temporary = getattr(os, "O_TEMPORARY", 0)
    if o_temporary:
        return os.open(
            target,
            os.O_RDWR | os.O_CREAT | os.O_EXCL | o_temporary,
            0o600,
        )
    fd = os.open(target, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.unlink(target)
    except OSError:
        os.close(fd)
        raise
    return fd


def validate_safe_cache_dir(project_root):
    """Create the expected extension download cache for command tests."""
    download_dir = project_root / ".specify" / "extensions" / ".cache" / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


def can_create_symlink(tmp_path: Path) -> bool:
    """Return whether the current platform can create file symlinks."""
    target = tmp_path / "symlink-target.txt"
    link = tmp_path / "symlink-link.txt"
    target.write_text("ok", encoding="utf-8")
    try:
        os.symlink(target, link)
    except OSError:
        return False
    return link.is_symlink()
