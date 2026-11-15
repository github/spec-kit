"""Shared source-directory installation filtering for extensions and presets."""

import re
from pathlib import Path
from typing import Callable, List, Optional, Set

import pathspec


def load_install_ignore(
    source_dir: Path,
    ignore_filename: str,
    validation_error: type[Exception],
) -> Optional[Callable[[str, List[str]], Set[str]]]:
    """Load a UTF-8 ignore file as a copytree callback, or return None if absent.

    Match the extension installer's Git-style patterns, including whitespace
    trimming and backslash normalization. Only the named root ignore file is
    read; there are no default exclusions except the ignore filename itself.
    A non-file path, invalid encoding, or invalid patterns raise the caller's
    domain validation error before copying.
    Excluded directories are pruned by copytree, so child negations cannot
    restore files inside them unless the parent directory is also re-included.
    """
    ignore_file = source_dir / ignore_filename
    if not ignore_file.exists():
        return None
    if not ignore_file.is_file():
        raise validation_error(f"{ignore_filename} is not a regular file: {ignore_file}")

    # Accept UTF-8 with or without the BOM emitted by Windows PowerShell 5.1.
    # Strip it after decoding so error offsets remain relative to the file.
    try:
        raw = ignore_file.read_text(encoding="utf-8").removeprefix("\ufeff")
    except UnicodeDecodeError as e:
        raise validation_error(
            f"{ignore_filename} is not valid UTF-8: {ignore_file} "
            f"({e.reason} at byte {e.start})"
        )
    lines: List[str] = raw.splitlines()

    # Normalise backslashes in patterns so Windows-authored files work
    normalised: List[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            normalised.append(stripped.replace("\\", "/"))
        else:
            # Preserve blanks/comments so pathspec line numbers stay stable
            normalised.append(line)

    # Always ignore the ignore file itself, even after a negation pattern.
    normalised.append(ignore_filename)

    try:
        spec = pathspec.GitIgnoreSpec.from_lines(normalised)
    except (ValueError, re.error) as e:
        # Locate the first malformed source rule only on failure. Valid files
        # compile once; the appended self-exclusion is not a source line.
        location = ""
        for line_number, pattern in enumerate(normalised[:len(lines)], start=1):
            try:
                pathspec.GitIgnoreSpec.from_lines([pattern])
            except (ValueError, re.error):
                location = f" at line {line_number}: {pattern!r}"
                break
        raise validation_error(
            f"Invalid patterns in {ignore_filename}: {ignore_file}{location} ({e})"
        ) from e

    def _ignore(directory: str, entries: List[str]) -> Set[str]:
        ignored: Set[str] = set()
        rel_dir = Path(directory).relative_to(source_dir)
        for entry in entries:
            rel_path = str(rel_dir / entry) if str(rel_dir) != "." else entry
            # Normalise to forward slashes for consistent matching
            rel_path_fwd = rel_path.replace("\\", "/")

            entry_full = Path(directory) / entry
            if entry_full.is_dir():
                # Append '/' so directory-only patterns (e.g. tests/) match
                if spec.match_file(rel_path_fwd + "/"):
                    ignored.add(entry)
            else:
                if spec.match_file(rel_path_fwd):
                    ignored.add(entry)
        return ignored

    return _ignore
