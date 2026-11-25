"""Shared helpers for autopilot tests: import the stdlib-only core, build repos."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EXT_DIR = REPO_ROOT / "extensions" / "autopilot"
SCRIPTS_DIR = EXT_DIR / "scripts" / "python"
CLI = SCRIPTS_DIR / "autopilot.py"
FAKE_SPECIFY = Path(__file__).resolve().parent / "fake_specify.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=True
    )
    return result.stdout.strip()


def init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.name", "Autopilot Test")
    git(path, "config", "user.email", "autopilot-test@example.invalid")
    git(path, "config", "commit.gpgsign", "false")
    (path / "README.md").write_text("# demo\n", encoding="utf-8")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "init")
    return path


def install_extension(project: Path, config_text: str) -> None:
    """Copy the extension into .specify/ the way `specify extension add` lays it out."""
    target = project / ".specify" / "extensions" / "autopilot"
    shutil.copytree(EXT_DIR, target, ignore=shutil.ignore_patterns("__pycache__"))
    (target / "autopilot-config.yml").write_text(config_text, encoding="utf-8")
    workflow = project / ".specify" / "workflows" / "autopilot-epic"
    workflow.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "workflows" / "autopilot-epic" / "workflow.yml", workflow / "workflow.yml")


def run_cli(cwd: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    import os

    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, **(env or {})},
        timeout=300,
    )


SPEC_TEMPLATE = """# Feature Specification: Demo

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export (Priority: P1)

Export reports.

**Why this priority**: core value.

**Independent Test**: export a report.

**Acceptance Scenarios**:

1. **Given** a report, **When** exported, **Then** a CSV exists
2. **Given** an empty report, **When** exported, **Then** the CSV has a header only

---

### User Story 2 - Schedule (Priority: P2)

**Acceptance Scenarios**:

1. **Given** a schedule, **When** it fires, **Then** an export runs

### Edge Cases

1. Not a scenario: numbered edge case

## Requirements *(mandatory)*

1. Not a scenario either
"""
