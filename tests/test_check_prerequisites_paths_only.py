"""Regression tests for check-prerequisites paths-only behavior."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import requires_bash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASH_SCRIPT = PROJECT_ROOT / "scripts" / "bash" / "check-prerequisites.sh"
PS_SCRIPT = PROJECT_ROOT / "scripts" / "powershell" / "check-prerequisites.ps1"
HAS_PWSH = shutil.which("pwsh") is not None


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a minimal spec-kit-style git repo with a fixed feature directory."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=tmp_path, check=True)

    specify_dir = tmp_path / ".specify"
    specify_dir.mkdir()
    (specify_dir / "feature.json").write_text(
        json.dumps({"feature_directory": "specs/001-test"}), encoding="utf-8"
    )
    (tmp_path / "specs" / "001-test").mkdir(parents=True)
    return tmp_path


@requires_bash
def test_bash_paths_only_skips_branch_validation(git_repo: Path) -> None:
    result = subprocess.run(
        ["bash", str(BASH_SCRIPT), "--json", "--paths-only"],
        cwd=git_repo,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["BRANCH"] == "main"
    assert payload["FEATURE_DIR"].endswith("specs/001-test")


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh not available")
def test_powershell_paths_only_skips_branch_validation(git_repo: Path) -> None:
    result = subprocess.run(
        ["pwsh", "-NoLogo", "-NoProfile", "-File", str(PS_SCRIPT), "-Json", "-PathsOnly"],
        cwd=git_repo,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["BRANCH"] == "main"
    assert payload["FEATURE_DIR"].endswith("specs/001-test")
