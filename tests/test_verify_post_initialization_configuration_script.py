"""End-to-end coverage for the local post-initialization verifier."""

from __future__ import annotations

import os
import subprocess
import sysconfig
from pathlib import Path

import pytest

from tests.conftest import requires_bash


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "verify-post-initialization-configuration.sh"
SPECIFY = Path(sysconfig.get_path("scripts")) / ("specify.exe" if os.name == "nt" else "specify")
pytestmark = requires_bash


@pytest.mark.parametrize("relative", [False, True], ids=["absolute-path", "relative-path"])
def test_verifier_checks_post_initialization_configuration(relative) -> None:
    """The helper validates the documented local configuration workflow."""
    executable = Path(os.path.relpath(SPECIFY, REPO_ROOT)) if relative else SPECIFY
    result = subprocess.run(
        ["bash", str(SCRIPT), "--specify", executable.as_posix()],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Post-initialization configuration verified." in result.stdout


def test_verifier_preserves_project_from_inherited_override(tmp_path, monkeypatch):
    project = tmp_path / "existing"
    init = subprocess.run(
        [str(SPECIFY), "init", str(project), "--integration", "copilot", "--ignore-agent-tools", "--script", "sh"],
        capture_output=True,
        text=True,
    )
    assert init.returncode == 0, init.stdout + init.stderr
    before = {
        path.relative_to(project): path.read_bytes()
        for path in project.rglob("*") if path.is_file()
    }
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(project))

    result = subprocess.run(
        ["bash", str(SCRIPT), "--specify", SPECIFY.as_posix()],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    after = {
        path.relative_to(project): path.read_bytes()
        for path in project.rglob("*") if path.is_file()
    }
    assert after == before
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Post-initialization configuration verified." in result.stdout
