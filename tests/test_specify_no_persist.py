"""Tests for SPECIFY_NO_PERSIST, the env-level equivalent of --no-persist (#4128).

Scripts like setup-plan/setup-tasks call get_feature_paths() without
--no-persist, so every invocation with SPECIFY_FEATURE_DIRECTORY set
overwrites .specify/feature.json. In multi-agent setups where several
processes each set their own SPECIFY_FEATURE_DIRECTORY, this creates a
write-write race on the shared file. SPECIFY_NO_PERSIST lets an orchestrator
suppress that write across every script invocation without having to patch
each call site.
"""

import json
import shutil
from pathlib import Path

import pytest

from tests.conftest import requires_bash
from tests.parity_helpers import (
    HAS_POWERSHELL,
    PROJECT_ROOT,
    bash_cmd,
    clean_env,
    install_scripts,
    make_repo,
    ps_cmd,
    py_cmd,
    run,
)

SCRIPT = "setup-plan"
PLAN_TEMPLATE = PROJECT_ROOT / "templates" / "plan-template.md"


def _setup_repo(tmp_path: Path, name: str = "proj") -> Path:
    repo = make_repo(tmp_path, name)
    install_scripts(repo, SCRIPT)
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True, exist_ok=True)
    shutil.copy(PLAN_TEMPLATE, templates / "plan-template.md")
    return repo


def _feature_json(repo: Path) -> dict | None:
    fj = repo / ".specify" / "feature.json"
    if not fj.is_file():
        return None
    return json.loads(fj.read_text(encoding="utf-8"))


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return _setup_repo(tmp_path)


@requires_bash
def test_bash_persists_by_default(repo: Path) -> None:
    (repo / "specs" / "001-a").mkdir(parents=True)
    env = clean_env()
    env["SPECIFY_FEATURE_DIRECTORY"] = "specs/001-a"
    result = run(bash_cmd(repo, SCRIPT, "--json"), repo, env)
    assert result.returncode == 0, result.stderr
    assert _feature_json(repo) == {"feature_directory": "specs/001-a"}


@requires_bash
def test_bash_specify_no_persist_suppresses_write(repo: Path) -> None:
    (repo / "specs" / "001-a").mkdir(parents=True)
    env = clean_env()
    env["SPECIFY_FEATURE_DIRECTORY"] = "specs/001-a"
    env["SPECIFY_NO_PERSIST"] = "1"
    result = run(bash_cmd(repo, SCRIPT, "--json"), repo, env)
    assert result.returncode == 0, result.stderr
    assert _feature_json(repo) is None


@requires_bash
def test_bash_specify_no_persist_does_not_clobber_existing_pin(repo: Path) -> None:
    """A second agent's SPECIFY_FEATURE_DIRECTORY must not overwrite the
    first agent's persisted feature.json when SPECIFY_NO_PERSIST is set."""
    (repo / "specs" / "001-a").mkdir(parents=True)
    (repo / "specs" / "002-b").mkdir(parents=True)
    env = clean_env()
    env["SPECIFY_FEATURE_DIRECTORY"] = "specs/001-a"
    result = run(bash_cmd(repo, SCRIPT, "--json"), repo, env)
    assert result.returncode == 0, result.stderr
    assert _feature_json(repo) == {"feature_directory": "specs/001-a"}

    env["SPECIFY_FEATURE_DIRECTORY"] = "specs/002-b"
    env["SPECIFY_NO_PERSIST"] = "1"
    result = run(bash_cmd(repo, SCRIPT, "--json"), repo, env)
    assert result.returncode == 0, result.stderr
    assert _feature_json(repo) == {"feature_directory": "specs/001-a"}


@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_ps_specify_no_persist_suppresses_write(repo: Path) -> None:
    (repo / "specs" / "001-a").mkdir(parents=True)
    env = clean_env()
    env["SPECIFY_FEATURE_DIRECTORY"] = "specs/001-a"
    env["SPECIFY_NO_PERSIST"] = "true"
    result = run(ps_cmd(repo, SCRIPT, "-Json"), repo, env)
    assert result.returncode == 0, result.stderr
    assert _feature_json(repo) is None


def test_py_specify_no_persist_suppresses_write(repo: Path) -> None:
    (repo / "specs" / "001-a").mkdir(parents=True)
    env = clean_env()
    env["SPECIFY_FEATURE_DIRECTORY"] = "specs/001-a"
    env["SPECIFY_NO_PERSIST"] = "1"
    result = run(py_cmd(repo, SCRIPT, "--json"), repo, env)
    assert result.returncode == 0, result.stderr
    assert _feature_json(repo) is None


# create-new-feature writes .specify/feature.json directly (not via
# get_feature_paths()), so it must honor SPECIFY_NO_PERSIST separately.

CREATE_SCRIPT = "create-new-feature"
SPEC_TEMPLATE_BODY = "# Spec Template\n\nBody.\n"


def _create_feature_repo(tmp_path: Path, name: str = "proj") -> Path:
    repo = make_repo(tmp_path, name)
    install_scripts(repo, CREATE_SCRIPT)
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True, exist_ok=True)
    (templates / "spec-template.md").write_text(SPEC_TEMPLATE_BODY, encoding="utf-8")
    return repo


@requires_bash
def test_bash_create_new_feature_no_persist_suppresses_write(tmp_path: Path) -> None:
    repo = _create_feature_repo(tmp_path)
    env = clean_env()
    env["SPECIFY_NO_PERSIST"] = "1"
    result = run(bash_cmd(repo, CREATE_SCRIPT, "--json", "x"), repo, env)
    assert result.returncode == 0, result.stderr
    assert _feature_json(repo) is None


@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_ps_create_new_feature_no_persist_suppresses_write(tmp_path: Path) -> None:
    repo = _create_feature_repo(tmp_path)
    env = clean_env()
    env["SPECIFY_NO_PERSIST"] = "true"
    result = run(ps_cmd(repo, CREATE_SCRIPT, "-Json", "x"), repo, env)
    assert result.returncode == 0, result.stderr
    assert _feature_json(repo) is None


def test_py_create_new_feature_no_persist_suppresses_write(tmp_path: Path) -> None:
    repo = _create_feature_repo(tmp_path)
    env = clean_env()
    env["SPECIFY_NO_PERSIST"] = "1"
    result = run(py_cmd(repo, CREATE_SCRIPT, "--json", "x"), repo, env)
    assert result.returncode == 0, result.stderr
    assert _feature_json(repo) is None
