#!/usr/bin/env python3
"""Resolve the active feature and its tasks.md for the github extension.

Deliberately self-contained: the github extension owns this script so that
``speckit.github.taskstoissues`` keeps working when the core ``taskstoissues``
command (and its ``check_prerequisites`` helper invocation) is deprecated and
removed. It is a trimmed twin of core ``check_prerequisites.py`` -- it resolves
the project root and the active feature directory, requires ``plan.md`` and
``tasks.md`` exactly as core's ``--require-tasks --include-tasks`` invocation
does, and reports the optional design docs that sit next to them. Core does not
require ``spec.md`` for this command, so neither does this script.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HELP_TEXT = """Usage: resolve_tasks.py [OPTIONS]

Resolve the active feature and its tasks.md for the github extension.

OPTIONS:
  --json      Output in JSON format
  --help, -h  Show this help message

EXAMPLES:
  ./resolve_tasks.py --json
"""


def _status_marker() -> str:
    """Return the status glyph, downgraded to ASCII when stdout cannot encode it.

    On Windows sys.stdout falls back to the ANSI code page whenever it is not a
    console - a pipe or a file redirect, which is how agents and workflow steps
    invoke these scripts - and U+2713 is unencodable in cp1252, so printing it
    raises UnicodeEncodeError and aborts the report right after
    "AVAILABLE_DOCS:". Mirrors core's _status_marker in
    scripts/python/check_prerequisites.py; "[OK]" is also what this script's
    PowerShell twin emits.
    """
    glyph = "✓"
    try:
        glyph.encode(getattr(sys.stdout, "encoding", None) or "utf-8")
    except (LookupError, UnicodeEncodeError):
        return "[OK]"
    return glyph


def _die(*lines: str) -> "None":
    for line in lines:
        print(line, file=sys.stderr)
    raise SystemExit(1)


def find_specify_root(start_dir: Path | None = None) -> Path | None:
    """Find the project root by searching upward for the .specify marker."""
    current = (start_dir or Path.cwd()).resolve()
    while True:
        if (current / ".specify").is_dir():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def get_project_root(script_file: Path) -> Path:
    """Resolve the project root, honouring an explicit SPECIFY_INIT_DIR override.

    Mirrors core ``get_repo_root``: strict on an invalid override, with no
    silent fallback to the current directory.
    """
    raw = os.environ.get("SPECIFY_INIT_DIR", "")
    if raw:
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        try:
            init_root = candidate.resolve(strict=True)
        except OSError:
            init_root = None
        if init_root is None or not init_root.is_dir():
            _die(
                "ERROR: SPECIFY_INIT_DIR does not point to an existing "
                f"directory: {raw}"
            )
        if not (init_root / ".specify").is_dir():
            _die(
                "ERROR: SPECIFY_INIT_DIR is not a Spec Kit project "
                f"(no .specify/ directory): {init_root}"
            )
        return init_root

    root = find_specify_root()
    if root is not None:
        return root

    # Installed scripts live at .specify/extensions/github/scripts/python/.
    root = find_specify_root(script_file.resolve().parent)
    if root is not None:
        return root

    _die("ERROR: Not inside a Spec Kit project (no .specify/ directory found).")
    raise AssertionError("unreachable")  # pragma: no cover - _die always exits


def read_feature_json_feature_directory(repo_root: Path) -> str:
    """Read .specify/feature.json's feature_directory value, or empty string."""
    feature_json = repo_root / ".specify" / "feature.json"
    if not feature_json.is_file():
        return ""
    try:
        data = json.loads(feature_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ""
    value = data.get("feature_directory") if isinstance(data, dict) else None
    return value if isinstance(value, str) else ""


def _dir_has_entries(path: Path) -> bool:
    """Whether path is a non-empty directory, treating an error as "no".

    Mirrors core's _dir_has_entries: probing an optional doc directory must
    never abort a resolution that is otherwise valid, which is also what the
    bash (``ls -A 2>/dev/null``) and PowerShell (``-ErrorAction
    SilentlyContinue``) twins do.
    """
    try:
        return path.is_dir() and any(path.iterdir())
    except OSError:
        return False


def persist_feature_json(repo_root: Path, feature_dir_value: str) -> None:
    """Write feature_directory to .specify/feature.json when it changed.

    Mirrors core's persist_feature_json, including the lexical prefix strip:
    with a symlinked <repo>/specs, resolve() would escape the repo and persist
    a machine-specific absolute path rather than the relative "specs/NNN-name"
    the bash and PowerShell twins store.
    """
    value = feature_dir_value
    relative = Path(value)
    if relative.is_absolute():
        try:
            value = relative.relative_to(repo_root).as_posix()
        except ValueError:
            value = str(relative)

    if read_feature_json_feature_directory(repo_root) == value:
        return

    specify_dir = repo_root / ".specify"
    specify_dir.mkdir(parents=True, exist_ok=True)
    (specify_dir / "feature.json").write_bytes(
        (json.dumps({"feature_directory": value}, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )
    )


def main(argv: list[str]) -> int:
    json_mode = False
    for arg in argv:
        if arg == "--json":
            json_mode = True
        elif arg in ("--help", "-h"):
            print(HELP_TEXT, end="")
            return 0
        else:
            print(
                f"ERROR: Unknown option '{arg}'. Use --help for usage information.",
                file=sys.stderr,
            )
            return 1

    repo_root = get_project_root(Path(__file__))

    # Resolve the feature directory. Priority:
    #   1. SPECIFY_FEATURE_DIRECTORY (explicit override)
    #   2. .specify/feature.json "feature_directory"
    # An override is persisted, exactly as core does, unless the orchestrator
    # sets SPECIFY_FEATURE_NO_PERSIST to keep the shared feature.json unchanged.
    raw_feature_dir = os.environ.get("SPECIFY_FEATURE_DIRECTORY", "")
    if raw_feature_dir and os.environ.get("SPECIFY_FEATURE_NO_PERSIST", "") not in (
        "1",
        "true",
    ):
        persist_feature_json(repo_root, raw_feature_dir)
    if not raw_feature_dir:
        raw_feature_dir = read_feature_json_feature_directory(repo_root)
        if not raw_feature_dir:
            _die(
                "ERROR: Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY "
                "or run the specify command to create .specify/feature.json."
            )

    feature_dir = Path(raw_feature_dir)
    if not feature_dir.is_absolute():
        feature_dir = repo_root / feature_dir

    if not feature_dir.is_dir():
        _die(
            f"ERROR: Feature directory not found: {feature_dir}",
            "Run the Spec Kit specify command first to "
            "create the feature structure.",
        )

    impl_plan = feature_dir / "plan.md"
    if not impl_plan.is_file():
        _die(
            f"ERROR: plan.md not found in {feature_dir}",
            "Run the Spec Kit plan command first to "
            "create the implementation plan.",
        )

    tasks = feature_dir / "tasks.md"
    if not tasks.is_file():
        _die(
            f"ERROR: tasks.md not found in {feature_dir}",
            "Run the Spec Kit tasks command first to "
            "create the task list.",
        )

    docs: list[str] = []
    if (feature_dir / "research.md").is_file():
        docs.append("research.md")
    if (feature_dir / "data-model.md").is_file():
        docs.append("data-model.md")
    if _dir_has_entries(feature_dir / "contracts"):
        docs.append("contracts/")
    if (feature_dir / "quickstart.md").is_file():
        docs.append("quickstart.md")
    docs.append("tasks.md")

    if json_mode:
        payload = {
            "FEATURE_DIR": str(feature_dir),
            "TASKS": str(tasks),
            "AVAILABLE_DOCS": docs,
        }
        # ASCII escapes decode to the same values and, unlike raw non-ASCII,
        # survive a legacy stdout such as cp1252 on a redirected Windows pipe.
        sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    else:
        print(f"FEATURE_DIR:{feature_dir}")
        print(f"TASKS:{tasks}")
        print("AVAILABLE_DOCS:")
        marker = _status_marker()
        for doc in docs:
            print(f"  {marker} {doc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
