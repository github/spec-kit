#!/usr/bin/env python3
"""Git extension: initialize_repo.py

Initialize a Git repository with an initial commit.
Python port of ``initialize-repo.sh`` / ``initialize-repo.ps1``.
Customizable — replace this script to add .gitignore templates,
default branch config, git-flow, LFS, signing, etc.
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


def _read_commit_message(repo_root: Path) -> str:
    """Read init_commit_message from git-config.yml, mirroring the bash sed pipeline."""
    default = "[Spec Kit] Initial commit"
    config_file = repo_root / ".specify" / "extensions" / "git" / "git-config.yml"
    if not config_file.is_file():
        return default
    try:
        lines = config_file.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return default
    for line in lines:
        if line.startswith("init_commit_message:"):
            value = re.sub(r"^init_commit_message:\s*", "", line)
            value = re.sub(r"^[\"']", "", value)
            value = re.sub(r"[\"']*$", "", value)
            if value:
                return value
    return default


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo_root = _find_project_root(script_dir) or Path.cwd()

    commit_msg = _read_commit_message(repo_root)

    if shutil.which("git") is None:
        print(
            "[specify] Warning: Git not found; skipped repository initialization",
            file=sys.stderr,
        )
        return 0

    probe = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if probe.returncode == 0:
        print("[specify] Git repository already initialized; skipping", file=sys.stderr)
        return 0

    steps = [
        (["git", "init", "-q"], "git init"),
        (["git", "add", "."], "git add"),
        (["git", "commit", "--allow-empty", "-q", "-m", commit_msg], "git commit"),
    ]
    for cmd, label in steps:
        result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
        if result.returncode != 0:
            output = (result.stdout + result.stderr).strip()
            print(f"[specify] Error: {label} failed: {output}", file=sys.stderr)
            return 1

    print("[OK] Git repository initialized", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
