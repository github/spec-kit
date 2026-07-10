"""Tests for AI Team handoff spec sync scripts and preset."""

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


def test_ai_team_handoff_spec_hooks_registered():
    manifest = yaml.safe_load(
        (EXTENSION_ROOT / "extension.yml").read_text(encoding="utf-8")
    )
    hooks = manifest["hooks"]
    assert hooks["before_plan"]["command"] == "speckit.ai-team.handoff-spec-sync"
    assert hooks["before_plan"]["priority"] == 5
    assert "before_tasks" not in hooks
    assert "before_analyze" not in hooks
    assert "before_implement" not in hooks
    assert "before_converge" not in hooks
    assert "before_checklist" not in hooks


def test_ai_team_handoff_spec_preset_files():
    preset = yaml.safe_load((PRESET_ROOT / "preset.yml").read_text(encoding="utf-8"))
    assert preset["preset"]["id"] == "ai-team-handoff-spec"
    entries = preset["provides"]["templates"]
    names = {e["name"] for e in entries}
    assert names == {
        "speckit.plan",
        "speckit.tasks",
        "speckit.converge",
        "speckit.bug.test",
        "speckit.constitution",
        "plan-template",
        "constitution-template",
    }
    by_name = {e["name"]: e for e in entries}
    expected_strategies = {
        "speckit.plan": "prepend",
        "speckit.tasks": "prepend",
        "speckit.converge": "wrap",
        "speckit.bug.test": "append",
        "speckit.constitution": "replace",
        "plan-template": "prepend",
        "constitution-template": "replace",
    }
    handoff_stop = "remote handoff pointer and `spec.override.md` is missing"
    for entry in entries:
        rel = entry["file"]
        text = (PRESET_ROOT / rel).read_text(encoding="utf-8")
        name = entry["name"]
        assert entry.get("strategy") == expected_strategies[name]
        if name == "plan-template":
            assert "spec.override" in text or "handoff" in text.lower()
            assert handoff_stop in text
        elif name == "constitution-template":
            assert "Scope and Authority" in text
            assert "Governance" in text
        elif name == "speckit.constitution":
            assert "amend-first" in text
            assert ".specify/memory/constitution.md" in text
        elif name == "speckit.bug.test":
            assert "evidence board" in text.lower()
            assert "checks" in text.lower()
        else:
            assert "spec.override.md" in text
            assert handoff_stop in text
        if expected_strategies[name] == "wrap":
            assert "{CORE_TEMPLATE}" in text
    converge_text = (PRESET_ROOT / by_name["speckit.converge"]["file"]).read_text(
        encoding="utf-8"
    )
    assert "evidence board" in converge_text.lower()
    assert "checks" in converge_text.lower()


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
        'cp "$MOCK_FETCH_SOURCE" "${!#}"\n',
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
        'cp "$MOCK_FETCH_SOURCE" "${!#}"\n',
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
