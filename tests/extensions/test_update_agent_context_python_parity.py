"""Parity tests: update_agent_context.py vs update-agent-context.sh/.ps1.

Each test prepares two identical project trees, runs the bash script in one
and the Python port in the other, then compares exit codes, output (with
project roots normalized) and the resulting context-file bytes. PowerShell
tests compare the resulting file content only and are skipped when ``pwsh``
is unavailable.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.extensions.test_extension_agent_context import (
    BASH,
    EXT_DIR,
    POWERSHELL,
    _bundled_script_env,
)

PY_SCRIPT = EXT_DIR / "scripts" / "python" / "update_agent_context.py"
BASH_SCRIPT = EXT_DIR / "scripts" / "bash" / "update-agent-context.sh"
PS_SCRIPT = EXT_DIR / "scripts" / "powershell" / "update-agent-context.ps1"

requires_posix_bash = pytest.mark.skipif(
    not BASH or os.name == "nt",
    reason="POSIX bash required for side-by-side parity runs",
)


def run_bash(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [BASH, str(BASH_SCRIPT), *args],
        cwd=project_root,
        env=_bundled_script_env(project_root, for_bash=True),
        capture_output=True,
        text=True,
        timeout=30,
    )


def run_python(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PY_SCRIPT), *args],
        cwd=project_root,
        env=_bundled_script_env(project_root),
        capture_output=True,
        text=True,
        timeout=30,
    )


def run_powershell(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PS_SCRIPT),
            *args,
        ],
        cwd=project_root,
        env=_bundled_script_env(project_root),
        capture_output=True,
        text=True,
        timeout=30,
    )


def normalize(text: str, project_root: Path) -> str:
    return text.replace(str(project_root.resolve()), "__ROOT__").replace(
        str(project_root), "__ROOT__"
    )


def write_config(project_root: Path, **overrides: object) -> None:
    """Write the extension config as JSON (valid YAML, PS-parseable too)."""
    cfg: dict = {
        "context_file": overrides.get("context_file", ""),
        "context_files": overrides.get("context_files", []),
        "context_markers": overrides.get(
            "context_markers",
            {"start": "<!-- SPECKIT START -->", "end": "<!-- SPECKIT END -->"},
        ),
    }
    cfg_dir = project_root / ".specify" / "extensions" / "agent-context"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "agent-context-config.yml").write_text(
        json.dumps(cfg), encoding="utf-8"
    )


def make_project(root: Path, **config: object) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    write_config(root, **config)
    return root


def add_plan(project_root: Path, feature_dir: str = "specs/001-demo") -> None:
    plan = project_root / feature_dir / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("# plan\n", encoding="utf-8")
    (project_root / ".specify").mkdir(parents=True, exist_ok=True)
    (project_root / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": feature_dir}), encoding="utf-8"
    )


def twin_projects(tmp_path: Path, **config: object) -> tuple[Path, Path]:
    return (
        make_project(tmp_path / "proj-a", **config),
        make_project(tmp_path / "proj-b", **config),
    )


def assert_parity(
    bash: subprocess.CompletedProcess,
    py: subprocess.CompletedProcess,
    repo_a: Path,
    repo_b: Path,
) -> None:
    assert py.returncode == bash.returncode, py.stderr + bash.stderr
    assert normalize(py.stdout, repo_b) == normalize(bash.stdout, repo_a)
    assert normalize(py.stderr, repo_b) == normalize(bash.stderr, repo_a)


# ── Fresh file and upsert behavior ───────────────────────────────────────────


@requires_posix_bash
def test_python_creates_fresh_context_file_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")
    add_plan(repo_a)
    add_plan(repo_b)

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content_a = (repo_a / "AGENTS.md").read_bytes()
    content_b = (repo_b / "AGENTS.md").read_bytes()
    assert content_a == content_b
    assert b"at specs/001-demo/plan.md" in content_b


@requires_posix_bash
def test_python_replaces_existing_section_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")
    existing = (
        "# My project\n\n"
        "<!-- SPECKIT START -->\nstale section\n<!-- SPECKIT END -->\n"
        "\nTrailing prose stays.\n"
    )
    for repo in (repo_a, repo_b):
        add_plan(repo)
        (repo / "AGENTS.md").write_text(existing, encoding="utf-8")

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_text(encoding="utf-8")
    assert content == (repo_a / "AGENTS.md").read_text(encoding="utf-8")
    assert "stale section" not in content
    assert content.startswith("# My project\n")
    assert "Trailing prose stays." in content


@requires_posix_bash
@pytest.mark.parametrize(
    "existing",
    [
        "# Doc\n<!-- SPECKIT START -->\ndangling start\n",
        "dangling end\n<!-- SPECKIT END -->\nrest\n",
        "no markers at all",
    ],
    ids=["start-only", "end-only", "no-markers-no-newline"],
)
def test_python_handles_partial_markers_matching_bash(
    tmp_path: Path, existing: str
) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")
    for repo in (repo_a, repo_b):
        add_plan(repo)
        (repo / "AGENTS.md").write_text(existing, encoding="utf-8")

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    assert (repo_a / "AGENTS.md").read_bytes() == (repo_b / "AGENTS.md").read_bytes()


@requires_posix_bash
def test_python_custom_markers_matching_bash(tmp_path: Path) -> None:
    markers = {"start": "<!-- CTX BEGIN -->", "end": "<!-- CTX FINISH -->"}
    repo_a, repo_b = twin_projects(
        tmp_path, context_file="AGENTS.md", context_markers=markers
    )
    existing = "intro\n<!-- CTX BEGIN -->\nold\n<!-- CTX FINISH -->\noutro\n"
    for repo in (repo_a, repo_b):
        add_plan(repo)
        (repo / "AGENTS.md").write_text(existing, encoding="utf-8")

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_text(encoding="utf-8")
    assert content == (repo_a / "AGENTS.md").read_text(encoding="utf-8")
    assert "<!-- CTX BEGIN -->" in content
    assert "old" not in content


@requires_posix_bash
def test_python_multiple_context_files_dedup_matching_bash(tmp_path: Path) -> None:
    files = ["AGENTS.md", "docs/CONTEXT.md", "AGENTS.md"]
    repo_a, repo_b = twin_projects(tmp_path, context_files=files)
    add_plan(repo_a)
    add_plan(repo_b)

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    assert bash.stdout.count("agent-context: updated") == 2
    for name in ("AGENTS.md", "docs/CONTEXT.md"):
        assert (repo_a / name).read_bytes() == (repo_b / name).read_bytes()


@requires_posix_bash
def test_python_normalizes_crlf_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")
    existing = b"# Doc\r\n\r\n<!-- SPECKIT START -->\r\nold\r\n<!-- SPECKIT END -->\r\ntail\r\n"
    for repo in (repo_a, repo_b):
        add_plan(repo)
        (repo / "AGENTS.md").write_bytes(existing)

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_bytes()
    assert content == (repo_a / "AGENTS.md").read_bytes()
    assert b"\r" not in content


@requires_posix_bash
def test_python_mdc_frontmatter_repair_matching_bash(tmp_path: Path) -> None:
    mdc = ".cursor/rules/specify-rules.mdc"
    cases = {
        "missing": "# Rules\n",
        "false-value": "---\ndescription: rules\nalwaysApply: false\n---\n\n# Rules\n",
        "no-key": "---\ndescription: rules\n---\n\n# Rules\n",
    }
    for name, existing in cases.items():
        repo_a = make_project(tmp_path / f"a-{name}", context_file=mdc)
        repo_b = make_project(tmp_path / f"b-{name}", context_file=mdc)
        for repo in (repo_a, repo_b):
            add_plan(repo)
            target = repo / mdc
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(existing, encoding="utf-8")

        bash = run_bash(repo_a)
        py = run_python(repo_b)

        assert_parity(bash, py, repo_a, repo_b)
        content = (repo_b / mdc).read_text(encoding="utf-8")
        assert content == (repo_a / mdc).read_text(encoding="utf-8"), name
        assert "alwaysApply: true" in content, name


# ── Plan-path resolution ─────────────────────────────────────────────────────


@requires_posix_bash
def test_python_explicit_plan_argument_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")

    bash = run_bash(repo_a, "specs/009-explicit/plan.md")
    py = run_python(repo_b, "specs/009-explicit/plan.md")

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_bytes()
    assert content == (repo_a / "AGENTS.md").read_bytes()
    assert b"at specs/009-explicit/plan.md" in content


@requires_posix_bash
def test_python_mtime_fallback_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")
    now = time.time()
    for repo in (repo_a, repo_b):
        for feature, age in (("specs/000-old", 10), ("specs/001-new", 0)):
            plan = repo / feature / "plan.md"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text("# plan\n", encoding="utf-8")
            os.utime(plan, (now - age, now - age))

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_bytes()
    assert content == (repo_a / "AGENTS.md").read_bytes()
    assert b"at specs/001-new/plan.md" in content


@requires_posix_bash
def test_python_prefers_feature_json_over_mtime_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")
    now = time.time()
    for repo in (repo_a, repo_b):
        add_plan(repo, "specs/001-active")
        stale = repo / "specs" / "000-stale" / "plan.md"
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("# plan\n", encoding="utf-8")
        os.utime(repo / "specs" / "001-active" / "plan.md", (now - 10, now - 10))
        os.utime(stale, (now, now))

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_bytes()
    assert content == (repo_a / "AGENTS.md").read_bytes()
    assert b"at specs/001-active/plan.md" in content


@requires_posix_bash
def test_python_no_plan_omits_at_line_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file="AGENTS.md")

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    content = (repo_b / "AGENTS.md").read_bytes()
    assert content == (repo_a / "AGENTS.md").read_bytes()
    assert b"\nat " not in content


# ── Config gates and path validation ─────────────────────────────────────────


@requires_posix_bash
def test_python_missing_config_matching_bash(tmp_path: Path) -> None:
    repo_a = tmp_path / "proj-a"
    repo_b = tmp_path / "proj-b"
    repo_a.mkdir()
    repo_b.mkdir()

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    assert py.returncode == 0
    assert "not found; nothing to do." in py.stderr


@requires_posix_bash
def test_python_unparseable_config_matching_bash(tmp_path: Path) -> None:
    repo_a = tmp_path / "proj-a"
    repo_b = tmp_path / "proj-b"
    for repo in (repo_a, repo_b):
        cfg_dir = repo / ".specify" / "extensions" / "agent-context"
        cfg_dir.mkdir(parents=True)
        (cfg_dir / "agent-context-config.yml").write_text(
            "context_file: [unclosed\n", encoding="utf-8"
        )

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    assert py.returncode == 0
    assert "cannot update context." in py.stderr
    assert "agent-context: skipping update (see above for details)." in py.stderr


@requires_posix_bash
def test_python_empty_config_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path)

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    assert py.returncode == 0
    assert "context_files/context_file not set" in py.stderr


@requires_posix_bash
def test_python_self_seed_from_init_options_matching_bash(tmp_path: Path) -> None:
    repo_a, repo_b = twin_projects(tmp_path)
    for repo in (repo_a, repo_b):
        add_plan(repo)
        (repo / ".specify" / "init-options.json").write_text(
            json.dumps({"integration": "claude"}), encoding="utf-8"
        )
        shutil.copy(
            EXT_DIR / "agent-context-defaults.json",
            repo
            / ".specify"
            / "extensions"
            / "agent-context"
            / "agent-context-defaults.json",
        )

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    assert (repo_a / "CLAUDE.md").read_bytes() == (repo_b / "CLAUDE.md").read_bytes()


@requires_posix_bash
@pytest.mark.parametrize(
    "bad_path",
    ["/etc/AGENTS.md", "docs\\AGENTS.md", "../outside.md", "nested/../../escape.md"],
    ids=["absolute", "backslash", "dotdot", "nested-dotdot"],
)
def test_python_rejects_escaping_paths_matching_bash(
    tmp_path: Path, bad_path: str
) -> None:
    repo_a, repo_b = twin_projects(tmp_path, context_file=bad_path)

    bash = run_bash(repo_a)
    py = run_python(repo_b)

    assert_parity(bash, py, repo_a, repo_b)
    assert py.returncode == 1
    assert not (repo_b / "AGENTS.md").exists()


# ── PowerShell parity (content only) ─────────────────────────────────────────


@pytest.mark.skipif(not POWERSHELL, reason="no PowerShell available")
def test_python_fresh_context_file_matches_powershell(tmp_path: Path) -> None:
    repo_a = make_project(tmp_path / "proj-ps", context_file="AGENTS.md")
    repo_b = make_project(tmp_path / "proj-py", context_file="AGENTS.md")
    add_plan(repo_a)
    add_plan(repo_b)

    ps = run_powershell(repo_a)
    py = run_python(repo_b)

    assert ps.returncode == py.returncode == 0, ps.stderr + py.stderr
    assert (repo_a / "AGENTS.md").read_bytes() == (repo_b / "AGENTS.md").read_bytes()


@pytest.mark.skipif(not POWERSHELL, reason="no PowerShell available")
def test_python_upsert_matches_powershell(tmp_path: Path) -> None:
    repo_a = make_project(tmp_path / "proj-ps", context_file="AGENTS.md")
    repo_b = make_project(tmp_path / "proj-py", context_file="AGENTS.md")
    existing = (
        "# My project\n\n"
        "<!-- SPECKIT START -->\nstale\n<!-- SPECKIT END -->\n"
        "\ntail\n"
    )
    for repo in (repo_a, repo_b):
        add_plan(repo)
        (repo / "AGENTS.md").write_text(existing, encoding="utf-8")

    ps = run_powershell(repo_a)
    py = run_python(repo_b)

    assert ps.returncode == py.returncode == 0, ps.stderr + py.stderr
    assert (repo_a / "AGENTS.md").read_bytes() == (repo_b / "AGENTS.md").read_bytes()
