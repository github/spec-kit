"""Parity tests for the Python setup-tasks port."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import requires_bash
from tests.parity_helpers import (
    HAS_POWERSHELL,
    bash_cmd,
    clean_env,
    install_scripts,
    json_stdout,
    make_repo,
    normalize_status_text,
    ps_cmd,
    py_cmd,
    run,
    write_feature_json,
)

SCRIPT = "setup-tasks"


def _setup_repo(tmp_path: Path) -> Path:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    write_feature_json(repo)
    feature = repo / "specs" / "001-my-feature"
    feature.mkdir(parents=True)
    (feature / "plan.md").write_text("# plan\n", encoding="utf-8")
    (feature / "spec.md").write_text("# spec\n", encoding="utf-8")
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True)
    (templates / "tasks-template.md").write_text("# Tasks Template\n", encoding="utf-8")
    return repo


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return _setup_repo(tmp_path)


@requires_bash
def test_python_json_output_matches_bash(repo: Path) -> None:
    feature = repo / "specs" / "001-my-feature"
    (feature / "research.md").write_text("# research\n", encoding="utf-8")
    (feature / "data-model.md").write_text("# model\n", encoding="utf-8")
    (feature / "quickstart.md").write_text("# quickstart\n", encoding="utf-8")
    (feature / "contracts" / "v1").mkdir(parents=True)

    bash = run(bash_cmd(repo, SCRIPT, "--json"), repo)
    py = run(py_cmd(repo, SCRIPT, "--json"), repo)

    assert py.returncode == bash.returncode == 0
    assert py.stderr == bash.stderr == ""
    assert json_stdout(py) == json_stdout(bash)


@requires_bash
def test_python_text_output_matches_bash(repo: Path) -> None:
    feature = repo / "specs" / "001-my-feature"
    (feature / "research.md").write_text("# research\n", encoding="utf-8")
    (feature / "contracts").mkdir()  # present but empty -> reported missing

    bash = run(bash_cmd(repo, SCRIPT), repo)
    py = run(py_cmd(repo, SCRIPT), repo)

    assert py.returncode == bash.returncode == 0
    assert py.stderr == bash.stderr == ""
    assert normalize_status_text(py.stdout) == normalize_status_text(bash.stdout)


@requires_bash
def test_python_override_template_wins_matches_bash(repo: Path) -> None:
    overrides = repo / ".specify" / "templates" / "overrides"
    overrides.mkdir(parents=True)
    (overrides / "tasks-template.md").write_text("# Override\n", encoding="utf-8")

    bash = run(bash_cmd(repo, SCRIPT, "--json"), repo)
    py = run(py_cmd(repo, SCRIPT, "--json"), repo)

    assert py.returncode == bash.returncode == 0
    assert json_stdout(py) == json_stdout(bash)
    assert json_stdout(py)["TASKS_TEMPLATE"].endswith("overrides/tasks-template.md")


@requires_bash
@pytest.mark.parametrize(
    "missing",
    ["plan.md", "spec.md", "tasks-template"],
    ids=["missing_plan", "missing_spec", "missing_tasks_template"],
)
def test_python_error_output_matches_bash(repo: Path, missing: str) -> None:
    if missing == "tasks-template":
        (repo / ".specify" / "templates" / "tasks-template.md").unlink()
    else:
        (repo / "specs" / "001-my-feature" / missing).unlink()

    bash = run(bash_cmd(repo, SCRIPT, "--json"), repo)
    py = run(py_cmd(repo, SCRIPT, "--json"), repo)

    assert py.returncode == bash.returncode == 1
    assert py.stdout == bash.stdout == ""
    assert py.stderr == bash.stderr


@requires_bash
def test_python_unknown_option_matches_bash(repo: Path) -> None:
    bash = run(bash_cmd(repo, SCRIPT, "--bogus"), repo)
    py = run(py_cmd(repo, SCRIPT, "--bogus"), repo)

    assert py.returncode == bash.returncode == 1
    assert py.stdout == bash.stdout == ""
    assert py.stderr == bash.stderr


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_powershell_unknown_option_matches_siblings(repo: Path) -> None:
    bash = run(bash_cmd(repo, SCRIPT, "--bogus"), repo)
    ps = run(ps_cmd(repo, SCRIPT, "--bogus"), repo)
    py = run(py_cmd(repo, SCRIPT, "--bogus"), repo)

    assert ps.returncode == bash.returncode == py.returncode == 1
    assert ps.stdout == bash.stdout == py.stdout == ""
    assert ps.stderr == bash.stderr == py.stderr


@requires_bash
def test_help_beats_unknown_option_matches_bash(repo: Path) -> None:
    """--help must win over a later unknown option and exit 0."""
    bash = run(bash_cmd(repo, SCRIPT, "--help", "--bogus"), repo)
    py = run(py_cmd(repo, SCRIPT, "--help", "--bogus"), repo)

    assert py.returncode == bash.returncode == 0
    assert py.stderr == bash.stderr == ""
    assert "Usage" in py.stdout and "Usage" in bash.stdout


@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_powershell_help_beats_unknown_option(repo: Path) -> None:
    """-Help must win over unknown-argument validation like the siblings."""
    ps = run(ps_cmd(repo, SCRIPT, "-Help", "--bogus"), repo)

    assert ps.returncode == 0, ps.stderr
    assert ps.stderr == ""
    assert "Usage" in ps.stdout


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
@pytest.mark.parametrize(
    "context", ["missing", "invalid_json", "invalid_utf8", "invalid_init_dir"]
)
def test_all_variants_feature_context_error_matches(
    tmp_path: Path, context: str
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    env = None
    if context == "invalid_json":
        (repo / ".specify" / "feature.json").write_text(
            "{not json", encoding="utf-8"
        )
    elif context == "invalid_utf8":
        (repo / ".specify" / "feature.json").write_bytes(b"\xff")
    elif context == "invalid_init_dir":
        env = clean_env()
        env["SPECIFY_INIT_DIR"] = str(tmp_path / "missing")

    bash = run(bash_cmd(repo, SCRIPT, "--json"), repo, env)
    ps = run(ps_cmd(repo, SCRIPT, "-Json"), repo, env)
    py = run(py_cmd(repo, SCRIPT, "--json"), repo, env)

    assert bash.returncode == ps.returncode == py.returncode == 1
    assert bash.stdout == ps.stdout == py.stdout == ""
    assert bash.stderr == ps.stderr == py.stderr


@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_python_json_output_matches_powershell(repo: Path) -> None:
    feature = repo / "specs" / "001-my-feature"
    (feature / "research.md").write_text("# research\n", encoding="utf-8")
    (feature / "contracts" / "v1").mkdir(parents=True)

    ps = run(ps_cmd(repo, SCRIPT, "-Json"), repo)
    py = run(py_cmd(repo, SCRIPT, "--json"), repo)

    assert py.returncode == ps.returncode == 0
    assert json_stdout(py) == json_stdout(ps)


@requires_bash
@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_missing_template_error_matches_all_variants(repo: Path) -> None:
    (repo / ".specify" / "templates" / "tasks-template.md").unlink()

    bash = run(bash_cmd(repo, SCRIPT, "--json"), repo)
    ps = run(ps_cmd(repo, SCRIPT, "-Json"), repo)
    py = run(py_cmd(repo, SCRIPT, "--json"), repo)

    assert bash.returncode == ps.returncode == py.returncode == 1
    assert bash.stdout == ps.stdout == py.stdout == ""
    assert bash.stderr == ps.stderr == py.stderr
