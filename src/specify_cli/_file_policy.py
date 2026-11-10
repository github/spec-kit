"""Strict project configuration bootstrap and explicit FileHelper handoff."""

from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import Any, NoReturn

from ._init_options import INIT_OPTIONS_FILE
from .file_helper import FileHelper, FileHelperError


class ProjectPolicyError(ValueError):
    """The project configuration cannot safely supply a filesystem policy."""


def _validate_options(options: Any) -> dict[str, Any]:
    if not isinstance(options, dict):
        raise ProjectPolicyError(f"{INIT_OPTIONS_FILE} must contain a JSON object")
    if "allow_symlinks" in options and type(options["allow_symlinks"]) is not bool:
        raise ProjectPolicyError(
            f"{INIT_OPTIONS_FILE}: allow_symlinks must be a JSON boolean (true or false)"
        )
    return options


def _reject_json_constant(value: str) -> NoReturn:
    raise ValueError(f"Non-JSON numeric constant: {value}")


def read_project_options(project_root: Path) -> dict[str, Any]:
    """Read without following configuration links; only absence defaults."""
    try:
        files = FileHelper(project_root)
    except (OSError, RuntimeError) as exc:
        raise ProjectPolicyError(
            f"Cannot establish project root for {INIT_OPTIONS_FILE}: {exc}"
        ) from exc
    try:
        text = files.read_text(INIT_OPTIONS_FILE)
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeError, FileHelperError) as exc:
        raise ProjectPolicyError(
            f"Cannot read {INIT_OPTIONS_FILE}: {exc}. "
            "Ensure the configuration hierarchy is non-symlinked and readable."
        ) from exc
    try:
        options = json.loads(text, parse_constant=_reject_json_constant)
    except (ValueError, RecursionError) as exc:
        raise ProjectPolicyError(
            f"Invalid JSON in {INIT_OPTIONS_FILE}: {exc}. Repair the configuration."
        ) from exc
    return _validate_options(options)


def project_files(project_root: Path) -> FileHelper:
    """Resolve current policy afresh and return an immutable operation owner."""
    options = read_project_options(project_root)
    try:
        return FileHelper(project_root, allow_symlinks=options.get("allow_symlinks", False))
    except (OSError, RuntimeError) as exc:
        raise ProjectPolicyError(f"Cannot establish project filesystem boundary: {exc}") from exc


def save_project_options(project_root: Path, options: dict[str, Any]) -> None:
    """Persist with deny-mode bootstrap and legacy metadata/text I/O behavior."""
    _validate_options(options)
    try:
        content = json.dumps(
            options, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
        ) + "\n"
    except (TypeError, ValueError, RecursionError) as exc:
        raise ProjectPolicyError(f"Cannot encode {INIT_OPTIONS_FILE} as JSON: {exc}") from exc
    try:
        files = FileHelper(project_root)
        # Validate the entire destination before creating even .specify.
        try:
            files.read_text(INIT_OPTIONS_FILE)
        except FileNotFoundError:
            pass
        from .integrations._file_changes import after_file_change, before_file_change

        destination = project_root / INIT_OPTIONS_FILE
        before_file_change(destination)
        files.mkdir(".specify", exist_ok=True)
        files.overwrite_text(INIT_OPTIONS_FILE, content)
        after_file_change(destination)
    except (OSError, UnicodeError, FileHelperError, RuntimeError) as exc:
        raise ProjectPolicyError(
            f"Cannot write {INIT_OPTIONS_FILE}: {exc}. "
            "Ensure the configuration hierarchy is non-symlinked and writable."
        ) from exc


def _existing_init_parent(target: Path) -> Path:
    ancestor = target.parent
    while not ancestor.exists() and not ancestor.is_symlink():
        ancestor = ancestor.parent
    return ancestor


def _validate_init_traversal(target: Path) -> None:
    # Windows presence probes can fold missing/../existing before filesystem access.
    for index, part in enumerate(target.parts):
        if part != "..":
            continue
        prefix = Path(*target.parts[:index])
        try:
            is_directory = stat.S_ISDIR(prefix.stat().st_mode)
        except FileNotFoundError as exc:
            raise FileHelperError(
                f"Parent traversal requires an existing directory before '..': {prefix}"
            ) from exc
        if not is_directory:
            raise FileHelperError(
                f"Parent traversal requires an existing directory before '..': {prefix}"
            )


def preflight_init_root(target: Path) -> Path:
    """Validate original init spelling and policy before project preparation."""
    target = target.absolute()
    try:
        _validate_init_traversal(target)
        if target.exists() or target.is_symlink():
            read_project_options(target)
        else:
            files = FileHelper(_existing_init_parent(target))
            try:
                files.read_bytes(target)
            except FileNotFoundError:
                pass
        return target.resolve()
    except (OSError, FileHelperError, RuntimeError) as exc:
        raise ProjectPolicyError(
            f"Cannot establish init project root {target}: {exc}"
        ) from exc


def prepare_init_root(target: Path) -> Path:
    """Create a missing init root beneath its nearest existing trusted parent.

    Existing explicit root aliases are trusted just like FileHelper roots.
    For new roots, deny traversal below the nearest existing directory.
    """
    target = target.absolute()
    _validate_init_traversal(target)
    if target.exists() or target.is_symlink():
        FileHelper(target)
        return target
    FileHelper(_existing_init_parent(target)).mkdir(target, parents=True, exist_ok=True)
    return target
