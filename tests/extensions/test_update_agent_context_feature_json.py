"""Tests that update-agent-context.sh/.ps1 prefer feature.json over mtime."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from tests.conftest import requires_bash

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UPDATE_AGENT_CTX_SH = (
    PROJECT_ROOT / "extensions" / "agent-context" / "scripts" / "bash" / "update-agent-context.sh"
)
UPDATE_AGENT_CTX_PS = (
    PROJECT_ROOT / "extensions" / "agent-context" / "scripts" / "powershell" / "update-agent-context.ps1"
)

HAS_PWSH = shutil.which("pwsh") is not None
_WINDOWS_POWERSHELL = (shutil.which("powershell.exe") or shutil.which("powershell")) if os.name == "nt" else None


def _setup_project(root: Path, context_file: str = "CLAUDE.md") -> None:
    """Write the minimal agent-context extension config."""
    cfg_dir = root / ".specify" / "extensions" / "agent-context"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "agent-context-config.yml").write_text(
        f"context_file: {context_file}\n"
        "context_markers:\n"
        "  start: '<!-- SPECKIT START -->'\n"
        "  end: '<!-- SPECKIT END -->'\n",
        encoding="utf-8",
    )


def _write_feature_json(root: Path, feature_directory: str) -> None:
    specify_dir = root / ".specify"
    specify_dir.mkdir(parents=True, exist_ok=True)
    (specify_dir / "feature.json").write_text(
        json.dumps({"feature_directory": feature_directory}),
        encoding="utf-8",
    )


def _make_plan(root: Path, feature_dir: str, content: str = "# plan\n") -> Path:
    p = root / feature_dir / "plan.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


@requires_bash
def test_bash_uses_feature_json_when_plan_exists(tmp_path: Path) -> None:
    """feature.json points to the active feature; that plan.md is injected."""
    _setup_project(tmp_path)
    _make_plan(tmp_path, "specs/001-active")
    _write_feature_json(tmp_path, "specs/001-active")

    result = subprocess.run(
        ["bash", str(UPDATE_AGENT_CTX_SH)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    ctx = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "specs/001-active/plan.md" in ctx


@requires_bash
def test_bash_ignores_newer_stale_plan_when_feature_json_present(tmp_path: Path) -> None:
    """An older spec's plan.md modified more recently must NOT win over feature.json."""
    _setup_project(tmp_path)

    # Create active feature plan first, then touch the stale one to make it newer.
    _make_plan(tmp_path, "specs/001-active")
    time.sleep(0.05)
    _make_plan(tmp_path, "specs/000-stale")

    _write_feature_json(tmp_path, "specs/001-active")

    result = subprocess.run(
        ["bash", str(UPDATE_AGENT_CTX_SH)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    ctx = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "specs/001-active/plan.md" in ctx
    assert "specs/000-stale/plan.md" not in ctx


@requires_bash
def test_bash_falls_back_to_mtime_when_feature_json_absent(tmp_path: Path) -> None:
    """No feature.json → mtime fallback selects the most recently modified plan."""
    _setup_project(tmp_path)
    _make_plan(tmp_path, "specs/000-old")
    time.sleep(0.05)
    _make_plan(tmp_path, "specs/001-newer")

    result = subprocess.run(
        ["bash", str(UPDATE_AGENT_CTX_SH)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    ctx = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "specs/001-newer/plan.md" in ctx


@requires_bash
def test_bash_falls_back_to_mtime_when_plan_not_yet_created(tmp_path: Path) -> None:
    """feature.json exists but plan.md not yet written → fall back to mtime."""
    _setup_project(tmp_path)
    _make_plan(tmp_path, "specs/000-old")
    # feature.json points to 001-new but its plan.md doesn't exist yet
    _write_feature_json(tmp_path, "specs/001-new")

    result = subprocess.run(
        ["bash", str(UPDATE_AGENT_CTX_SH)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    ctx = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "specs/000-old/plan.md" in ctx


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_ps_uses_feature_json_when_plan_exists(tmp_path: Path) -> None:
    """PowerShell: feature.json points to the active feature; that plan is injected."""
    _setup_project(tmp_path)
    _make_plan(tmp_path, "specs/001-active")
    _write_feature_json(tmp_path, "specs/001-active")

    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(UPDATE_AGENT_CTX_PS)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    ctx = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "specs/001-active/plan.md" in ctx


@pytest.mark.skipif(not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available")
def test_ps_ignores_newer_stale_plan_when_feature_json_present(tmp_path: Path) -> None:
    """PowerShell: stale plan touched more recently must not win over feature.json."""
    _setup_project(tmp_path)
    _make_plan(tmp_path, "specs/001-active")
    time.sleep(0.05)
    _make_plan(tmp_path, "specs/000-stale")
    _write_feature_json(tmp_path, "specs/001-active")

    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(UPDATE_AGENT_CTX_PS)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    ctx = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "specs/001-active/plan.md" in ctx
    assert "specs/000-stale/plan.md" not in ctx
