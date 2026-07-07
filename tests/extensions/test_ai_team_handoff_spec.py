"""Tests for AI Team handoff spec sync/resolve scripts and preset."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from tests.conftest import requires_bash

REPO_ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ROOT = REPO_ROOT / "extensions" / "ai-team"
COMMON_SH = REPO_ROOT / "scripts" / "bash" / "common.sh"
SYNC_SH = EXTENSION_ROOT / "scripts" / "bash" / "sync-handoff-spec.sh"
RESOLVE_SH = EXTENSION_ROOT / "scripts" / "bash" / "resolve-handoff-spec.sh"
PRESET_ROOT = EXTENSION_ROOT / "preset"


def _install_handoff_repo(repo: Path, feature_dir: str = "specs/001-test") -> Path:
    repo.mkdir(parents=True, exist_ok=True)
    (repo / ".specify" / "scripts" / "bash").mkdir(parents=True, exist_ok=True)
    shutil.copy(COMMON_SH, repo / ".specify" / "scripts" / "bash" / "common.sh")
    ext_scripts = repo / ".specify" / "extensions" / "ai-team" / "scripts" / "bash"
    ext_scripts.mkdir(parents=True, exist_ok=True)
    for name in (
        "handoff-spec-common.sh",
        "sync-handoff-spec.sh",
        "resolve-handoff-spec.sh",
    ):
        shutil.copy(EXTENSION_ROOT / "scripts" / "bash" / name, ext_scripts / name)
    (repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": feature_dir}),
        encoding="utf-8",
    )
    feat = repo / feature_dir
    feat.mkdir(parents=True, exist_ok=True)
    return feat


def _run_sync(repo: Path, env: dict, *args: str) -> subprocess.CompletedProcess[str]:
    sync_sh = repo / ".specify" / "extensions" / "ai-team" / "scripts" / "bash" / "sync-handoff-spec.sh"
    clean = {k: v for k, v in os.environ.items() if not k.startswith("SPECIFY_")}
    clean.update(env)
    return subprocess.run(
        ["bash", str(sync_sh), "--json", *args],
        cwd=repo,
        env=clean,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_resolve(repo: Path, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    resolve_sh = repo / ".specify" / "extensions" / "ai-team" / "scripts" / "bash" / "resolve-handoff-spec.sh"
    clean = {k: v for k, v in os.environ.items() if not k.startswith("SPECIFY_")}
    if env:
        clean.update(env)
    return subprocess.run(
        ["bash", str(resolve_sh), "--json"],
        cwd=repo,
        env=clean,
        capture_output=True,
        text=True,
        check=False,
    )


def test_ai_team_handoff_spec_hooks_registered():
    manifest = yaml.safe_load(
        (EXTENSION_ROOT / "extension.yml").read_text(encoding="utf-8")
    )
    hooks = manifest["hooks"]
    assert hooks["before_plan"]["command"] == "speckit.ai-team.handoff-spec-sync"
    assert hooks["before_plan"]["priority"] == 5
    assert hooks["before_tasks"]["command"] == "speckit.ai-team.handoff-spec.resolve"
    assert hooks["before_checklist"]["command"] == "speckit.ai-team.handoff-spec.resolve"


def test_ai_team_handoff_spec_preset_append_files():
    preset = yaml.safe_load((PRESET_ROOT / "preset.yml").read_text(encoding="utf-8"))
    assert preset["preset"]["id"] == "ai-team-handoff-spec"
    entries = preset["provides"]["templates"]
    names = {e["name"] for e in entries}
    assert names == {
        "speckit.plan",
        "speckit.tasks",
        "speckit.checklist",
        "speckit.analyze",
        "speckit.implement",
        "speckit.converge",
        "plan-template",
    }
    for entry in entries:
        rel = entry["file"]
        text = (PRESET_ROOT / rel).read_text(encoding="utf-8")
        assert "EFFECTIVE_SPEC" in text or "spec.override.md" in text
        assert entry.get("strategy") == "append"


@requires_bash
def test_sync_skipped_without_url(tmp_path: Path):
    repo = tmp_path / "proj"
    _install_handoff_repo(repo)
    result = _run_sync(repo, {})
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["SKIPPED"] is True


@requires_bash
def test_sync_bootstraps_spec_and_writes_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = tmp_path / "proj"
    feat = _install_handoff_repo(repo)
    fetched = "# Remote Requirement\n\nUser story P1: bootstrap from URL\n"
    fetch_src = tmp_path / "remote.md"
    fetch_src.write_text(fetched, encoding="utf-8")

    fake_curl = tmp_path / "curl"
    fake_curl.write_text(
        "#!/usr/bin/env bash\n"
        'cp "$MOCK_FETCH_SOURCE" "$5"\n',
        encoding="utf-8",
    )
    fake_curl.chmod(0o755)

    env = {
        "PATH": f"{tmp_path}:{os.environ.get('PATH', '')}",
        "HANDOFF_REQUIREMENT_URL": "https://example.com/requirements/remote.md",
        "MOCK_FETCH_SOURCE": str(fetch_src),
    }
    result = _run_sync(repo, env)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["SKIPPED"] is False
    assert data["SPEC_BOOTSTRAPPED"] is True
    assert (feat / "spec.md").exists()
    assert "handoff_requirement_url:" in (feat / "spec.md").read_text(encoding="utf-8")
    override = feat / "spec.override.md"
    assert override.exists()
    override_text = override.read_text(encoding="utf-8")
    assert "Remote Requirement" in override_text
    assert "https://example.com/requirements/remote.md" in override_text
    assert data["EFFECTIVE_SPEC"].endswith("spec.override.md")
    gitignore = (repo / ".gitignore").read_text(encoding="utf-8")
    assert "**/spec.override.md" in gitignore


@requires_bash
def test_sync_merges_existing_spec_baseline(tmp_path: Path):
    repo = tmp_path / "proj"
    feat = _install_handoff_repo(repo)
    (feat / "spec.md").write_text("# Public baseline\n\nP1 local spec\n", encoding="utf-8")
    fetched = "# Remote Requirement\n\nP1 remote spec\n"
    fetch_src = tmp_path / "remote.md"
    fetch_src.write_text(fetched, encoding="utf-8")

    fake_curl = tmp_path / "curl"
    fake_curl.write_text(
        "#!/usr/bin/env bash\n"
        'cp "$MOCK_FETCH_SOURCE" "$5"\n',
        encoding="utf-8",
    )
    fake_curl.chmod(0o755)

    env = {
        "PATH": f"{tmp_path}:{os.environ.get('PATH', '')}",
        "HANDOFF_REQUIREMENT_URL": "https://example.com/requirements/remote.md",
        "MOCK_FETCH_SOURCE": str(fetch_src),
    }
    result = _run_sync(repo, env)
    assert result.returncode == 0, result.stderr
    baseline = (feat / "spec.md").read_text(encoding="utf-8")
    assert baseline.startswith("# Public baseline")
    override_text = (feat / "spec.override.md").read_text(encoding="utf-8")
    assert "Public baseline (from spec.md)" in override_text
    assert "Handoff requirement (fetched)" in override_text


@requires_bash
def test_resolve_returns_effective_override(tmp_path: Path):
    repo = tmp_path / "proj"
    feat = _install_handoff_repo(repo)
    (feat / "spec.md").write_text("# spec\n", encoding="utf-8")
    (feat / "spec.override.md").write_text("# override\n", encoding="utf-8")
    result = _run_resolve(repo)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["EFFECTIVE_SPEC"].endswith("spec.override.md")
