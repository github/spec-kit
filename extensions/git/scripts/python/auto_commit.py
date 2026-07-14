#!/usr/bin/env python3
"""Git extension: auto_commit.py

Automatically commit changes after a Spec Kit command completes.
Python port of ``auto-commit.sh`` / ``auto-commit.ps1``.
Checks per-command config keys in git-config.yml before committing.

Usage: auto_commit.py <event_name>
  e.g.: auto_commit.py after_specify
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path


def _find_project_root(start: Path) -> Path | None:
    current = start
    while True:
        if (current / ".specify").is_dir() or (current / ".git").exists():
            return current
        if current.parent == current:
            return None
        current = current.parent


def _value_after_colon(line: str) -> str:
    return re.sub(r"^[^:]*:\s*", "", line)


def _strip_quotes(value: str) -> str:
    """Strip one leading quote and all trailing quotes, mirroring the bash sed."""
    value = re.sub(r"^[\"']", "", value)
    return re.sub(r"[\"']*$", "", value)


def _parse_auto_commit_config(
    config_file: Path, event_name: str
) -> tuple[bool, str]:
    """Parse the auto_commit section for this event, mirroring the bash line parser.

    Returns (enabled, commit_msg). Looks for auto_commit.<event_name>.enabled
    and .message, with auto_commit.default as fallback.
    """
    enabled = False
    commit_msg = ""
    default_enabled = False
    in_auto_commit = False
    in_event = False

    try:
        content = config_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        # Unreadable or non-UTF-8 config is treated like a missing one:
        # auto-commit stays disabled instead of crashing with a traceback.
        return False, ""
    for record in content.splitlines(keepends=True):
        if not record.endswith("\n"):
            break
        line = record[:-1]
        if line.startswith("auto_commit:"):
            in_auto_commit = True
            in_event = False
            continue

        # Exit auto_commit section on next top-level key
        if in_auto_commit and re.match(r"^[a-z]", line):
            break

        if not in_auto_commit:
            continue

        if re.match(r"^\s+default:\s", line):
            value = re.sub(r"\s", "", _value_after_colon(line)).lower()
            if value == "true":
                default_enabled = True

        if re.match(rf"^\s+{re.escape(event_name)}:", line):
            in_event = True
            continue

        if in_event:
            # Exit on next sibling key (same indent level as event name)
            if re.match(r"^\s{2}[a-z]", line) and not re.match(r"^\s{4}", line):
                in_event = False
                continue
            if re.search(r"\s+enabled:", line):
                value = re.sub(r"\s", "", _value_after_colon(line)).lower()
                if value == "true":
                    enabled = True
                elif value == "false":
                    enabled = False
            if re.search(r"\s+message:", line):
                commit_msg = _strip_quotes(_value_after_colon(line))

    # If event-specific key not found, use default — but only if the event
    # section didn't exist at all (an explicit false must win).
    if not enabled and default_enabled:
        if not re.search(rf"^\s*{re.escape(event_name)}:", content, re.MULTILINE):
            enabled = True

    return enabled, commit_msg


def main(argv: list[str]) -> int:
    event_name = argv[0] if argv else ""
    if not event_name:
        print(f"Usage: {Path(sys.argv[0]).name} <event_name>", file=sys.stderr)
        return 1

    script_dir = Path(__file__).resolve().parent
    repo_root = _find_project_root(script_dir) or Path.cwd()

    if shutil.which("git") is None:
        print("[specify] Warning: Git not found; skipped auto-commit", file=sys.stderr)
        return 0

    probe = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        print(
            "[specify] Warning: Not a Git repository; skipped auto-commit",
            file=sys.stderr,
        )
        return 0

    config_file = repo_root / ".specify" / "extensions" / "git" / "git-config.yml"
    if not config_file.is_file():
        # No config file — auto-commit disabled by default
        return 0

    enabled, commit_msg = _parse_auto_commit_config(config_file, event_name)
    if not enabled:
        return 0

    # Check if there are changes to commit
    def _quiet(*args: str) -> bool:
        return (
            subprocess.run(
                ["git", *args], cwd=repo_root, capture_output=True, text=True
            ).returncode
            == 0
        )

    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if _quiet("diff", "--quiet", "HEAD") and _quiet("diff", "--cached", "--quiet") and not untracked:
        print(f"[specify] No changes to commit after {event_name}", file=sys.stderr)
        return 0

    # Derive a human-readable command name from the event
    # e.g., after_specify -> specify, before_plan -> plan
    command_name = re.sub(r"^(after_|before_)", "", event_name)
    phase = "before" if event_name.startswith("before_") else "after"

    if not commit_msg:
        commit_msg = f"[Spec Kit] Auto-commit {phase} {command_name}"

    steps = [
        (["git", "add", "."], "git add"),
        (["git", "commit", "-q", "-m", commit_msg], "git commit"),
    ]
    for cmd, label in steps:
        result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
        if result.returncode != 0:
            output = (result.stdout + result.stderr).strip()
            print(f"[specify] Error: {label} failed: {output}", file=sys.stderr)
            return 1

    print(f"[OK] Changes committed {phase} {command_name}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
