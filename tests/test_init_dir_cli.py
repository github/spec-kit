"""Tests for the SPECIFY_INIT_DIR override in the Python CLI (`specify`).

PR #2892 taught the shell resolver (`get_repo_root` / `Get-RepoRoot`) to honor
SPECIFY_INIT_DIR, so the core slash-command scripts can target a member project
from a monorepo root. This extends the same validation rules to the Python CLI's
project resolution — `_require_specify_project()` (the chokepoint for every
project-scoped subcommand) and the `workflow run <file>` standalone-YAML path —
so those can target a member project without `cd` too.

The contract mirrors `tests/test_init_dir.py` (the shell side): the value names
the project root (the directory *containing* `.specify/`), relative paths
resolve against cwd, and an invalid value hard-errors with no silent fallback to
cwd. See proposals/monorepo-support and github/spec-kit discussion #2834.

SPECIFY_* vars are stripped from the environment for every test by the autouse
`_strip_specify_env` fixture in conftest.py; tests that want an override set it
explicitly via monkeypatch.
"""

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()


def _make_project(root, name):
    """Create <root>/<name>/.specify (the minimal Spec Kit project marker)."""
    proj = root / name
    (proj / ".specify").mkdir(parents=True)
    return proj


def _workflow_yaml(wf_id):
    """A minimal valid standalone workflow YAML with a single no-op shell step."""
    return yaml.dump(
        {
            "schema_version": "1.0",
            "workflow": {
                "id": wf_id,
                "name": wf_id,
                "version": "1.0.0",
                "description": f"standalone workflow {wf_id}",
            },
            "steps": [{"id": "noop", "type": "shell", "run": "echo done"}],
        }
    )


# ── chokepoint: _require_specify_project() via `workflow list` ───────────────
# `workflow list` is the lightest subcommand routed through the chokepoint: it
# resolves the project, then reads <project>/.specify/workflows/. An empty
# project prints "No workflows installed"; a failed resolution prints the error
# and exits non-zero.


def test_override_redirects_to_sibling_from_nonproject_cwd(tmp_path, monkeypatch):
    """A valid SPECIFY_INIT_DIR resolves the target even when cwd is not itself a
    project — without the override this would error 'Not a Spec Kit project'."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    web = _make_project(tmp_path, "web")
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(web))

    result = runner.invoke(app, ["workflow", "list"])
    assert result.exit_code == 0, result.output
    assert "No workflows installed" in result.output


def test_override_relative_path_normalized_against_cwd(tmp_path, monkeypatch):
    web = _make_project(tmp_path, "web")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SPECIFY_INIT_DIR", "web")

    result = runner.invoke(app, ["workflow", "list"])
    assert result.exit_code == 0, result.output
    assert "No workflows installed" in result.output
    assert web.exists()


def test_override_trailing_slash_tolerated(tmp_path, monkeypatch):
    _make_project(tmp_path, "web")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SPECIFY_INIT_DIR", "web/")

    result = runner.invoke(app, ["workflow", "list"])
    assert result.exit_code == 0, result.output
    assert "No workflows installed" in result.output


def test_override_redirects_bundle_commands(tmp_path, monkeypatch):
    web = _make_project(tmp_path, "web")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(web))

    result = runner.invoke(app, ["bundle", "list"])
    assert result.exit_code == 0, result.output
    assert "No bundles installed" in result.output


def test_unset_override_uses_cwd(tmp_path, monkeypatch):
    """With SPECIFY_INIT_DIR unset, the project is the current directory."""
    cwd_proj = _make_project(tmp_path, "cwd")
    monkeypatch.chdir(cwd_proj)

    result = runner.invoke(app, ["workflow", "list"])
    assert result.exit_code == 0, result.output
    assert "No workflows installed" in result.output


def test_empty_override_treated_as_unset(tmp_path, monkeypatch):
    """An empty SPECIFY_INIT_DIR behaves as unset (falls through to cwd), not as
    '.' — which from a deep non-project cwd would otherwise diverge."""
    cwd_proj = _make_project(tmp_path, "cwd")
    monkeypatch.chdir(cwd_proj)
    monkeypatch.setenv("SPECIFY_INIT_DIR", "")

    result = runner.invoke(app, ["workflow", "list"])
    assert result.exit_code == 0, result.output
    assert "No workflows installed" in result.output


def test_override_nonexistent_errors_no_fallback(tmp_path, monkeypatch):
    """A non-existent path hard-errors even from inside a valid project, proving
    there is no silent fallback to the cwd project."""
    cwd_proj = _make_project(tmp_path, "cwd")
    monkeypatch.chdir(cwd_proj)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(tmp_path / "does_not_exist"))

    result = runner.invoke(app, ["workflow", "list"])
    assert result.exit_code != 0
    assert "does not point to an existing directory" in result.output
    assert "No workflows installed" not in result.output  # no fallback to cwd


def test_override_nonexistent_errors_bundle_commands_no_fallback(tmp_path, monkeypatch):
    """Bundle commands also honor the strict override contract."""
    cwd_proj = _make_project(tmp_path, "cwd")
    monkeypatch.chdir(cwd_proj)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(tmp_path / "does_not_exist"))

    result = runner.invoke(app, ["bundle", "list"])
    assert result.exit_code != 0
    assert "does not point to an existing directory" in result.output
    assert "No bundles installed" not in result.output


def test_override_nonexistent_bundle_json_error_stays_off_stdout(tmp_path, monkeypatch):
    """Invalid override errors must not contaminate JSON stdout."""
    cwd_proj = _make_project(tmp_path, "cwd")
    monkeypatch.chdir(cwd_proj)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(tmp_path / "does_not_exist"))

    result = runner.invoke(app, ["bundle", "list", "--json"])
    assert result.exit_code != 0
    assert result.stdout == ""
    assert "does not point to an existing directory" in result.stderr


def test_override_symlinked_specify_errors_bundle_init_no_fallback(tmp_path, monkeypatch):
    """A symlinked override .specify must not make bundle init fall back to cwd."""
    web = tmp_path / "web"
    web.mkdir()
    real = tmp_path / "real-specify"
    real.mkdir()
    try:
        (web / ".specify").symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are not available in this environment")

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(web))

    result = runner.invoke(app, ["bundle", "init", "--offline"])
    assert result.exit_code != 0
    assert "symlinked .specify" in result.output
    assert not (elsewhere / ".specify").exists()


def test_override_without_specify_errors_no_fallback(tmp_path, monkeypatch):
    """A path that exists but lacks .specify/ hard-errors, no fallback."""
    cwd_proj = _make_project(tmp_path, "cwd")
    nodot = tmp_path / "nodot"
    nodot.mkdir()
    monkeypatch.chdir(cwd_proj)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(nodot))

    result = runner.invoke(app, ["workflow", "list"])
    assert result.exit_code != 0
    assert "not a Spec Kit project" in result.output
    assert "No workflows installed" not in result.output


def test_override_file_path_errors_no_fallback(tmp_path, monkeypatch):
    """A path that is a file (not a directory) hard-errors with the
    existing-directory message."""
    cwd_proj = _make_project(tmp_path, "cwd")
    a_file = tmp_path / "afile"
    a_file.write_text("x")
    monkeypatch.chdir(cwd_proj)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(a_file))

    result = runner.invoke(app, ["workflow", "list"])
    assert result.exit_code != 0
    assert "does not point to an existing directory" in result.output


# ── bypass: `workflow run <file>` ────────────────────────────────────────────


def test_override_redirects_workflow_run_file(tmp_path, monkeypatch):
    """Running a standalone YAML with SPECIFY_INIT_DIR set uses the target as the
    project root: run artifacts land under the target, not cwd."""
    web = _make_project(tmp_path, "web")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    workflow_file = elsewhere / "wf.yml"
    workflow_file.write_text(_workflow_yaml("override-run"), encoding="utf-8")
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(web))

    result = runner.invoke(app, ["workflow", "run", str(workflow_file)], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert (web / ".specify" / "workflows" / "runs").is_dir()
    assert not (elsewhere / ".specify").exists()  # cwd was not used as the project


def test_override_invalid_errors_workflow_run_file(tmp_path, monkeypatch):
    """An invalid SPECIFY_INIT_DIR hard-errors the file path too — no fallback to
    cwd's standalone-YAML behavior."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    workflow_file = elsewhere / "wf.yml"
    workflow_file.write_text(_workflow_yaml("x"), encoding="utf-8")
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(tmp_path / "does_not_exist"))

    result = runner.invoke(app, ["workflow", "run", str(workflow_file)])
    assert result.exit_code != 0
    assert "does not point to an existing directory" in result.output


def test_override_rejects_symlinked_specify(tmp_path, monkeypatch):
    """`workflow run <file>` refuses a symlinked .specify under the override
    target, matching the guard the cwd path applies (the override resolver's
    is_dir() check follows symlinks, so this is re-checked on the override path)."""
    web = tmp_path / "web"
    web.mkdir()
    real = tmp_path / "real-specify"
    real.mkdir()
    try:
        (web / ".specify").symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are not available in this environment")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    workflow_file = elsewhere / "wf.yml"
    workflow_file.write_text(_workflow_yaml("symlink-run"), encoding="utf-8")
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(web))

    result = runner.invoke(app, ["workflow", "run", str(workflow_file)])
    assert result.exit_code != 0
    assert "Refusing to use symlinked .specify path" in result.output


def test_override_rejects_symlinked_specify_json_error_stays_off_stdout(tmp_path, monkeypatch):
    """`workflow run --json <file>` must keep this hard error off stdout."""
    web = tmp_path / "web"
    web.mkdir()
    real = tmp_path / "real-specify"
    real.mkdir()
    try:
        (web / ".specify").symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are not available in this environment")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    workflow_file = elsewhere / "wf.yml"
    workflow_file.write_text(_workflow_yaml("symlink-json-run"), encoding="utf-8")
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(web))

    result = runner.invoke(app, ["workflow", "run", str(workflow_file), "--json"])
    assert result.exit_code != 0
    assert result.stdout == ""
    assert "Refusing to use symlinked .specify path" in result.stderr
