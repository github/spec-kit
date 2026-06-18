"""Regression tests for PowerShell 5.1 compatibility (GitHub issue #2680).

PowerShell 5.1 (built-in on Windows) defaults to the system's legacy encoding
when reading .ps1 files.  Non-ASCII characters in UTF-8-encoded scripts cause
parse errors because multi-byte sequences are misinterpreted as individual bytes.

These tests ensure that all shipped .ps1 files remain ASCII-only so they work
on both PowerShell 5.1 and 7+.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# All directories that contain shipped PowerShell scripts.
_PS1_DIRS = [
    REPO_ROOT / "scripts" / "powershell",
    REPO_ROOT / "extensions" / "git" / "scripts" / "powershell",
]


def _collect_ps1_files():
    """Yield all .ps1 files under the known script directories."""
    for d in _PS1_DIRS:
        if d.is_dir():
            yield from sorted(d.rglob("*.ps1"))


_PS1_FILES = list(_collect_ps1_files())


@pytest.mark.parametrize("ps1_file", _PS1_FILES, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_ps1_file_is_ascii_only(ps1_file: Path):
    """Every .ps1 file must contain only ASCII characters (PS 5.1 compat)."""
    content = ps1_file.read_bytes()
    non_ascii = [
        (i + 1, byte)
        for i, byte in enumerate(content)
        if byte > 127
    ]
    assert not non_ascii, (
        f"{ps1_file.relative_to(REPO_ROOT)} contains non-ASCII bytes "
        f"(PowerShell 5.1 incompatible): "
        f"first at byte offset {non_ascii[0][0]} (0x{non_ascii[0][1]:02x})"
    )


def test_ps1_files_discovered():
    """Sanity check: at least the known script files are found."""
    names = {p.name for p in _PS1_FILES}
    assert "common.ps1" in names
    assert "initialize-repo.ps1" in names
