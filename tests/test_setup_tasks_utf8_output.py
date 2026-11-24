"""Regression tests for UTF-8 stdout/stderr handling in scripts/python/setup_tasks.py."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.parity_helpers import (
    PROJECT_ROOT,
    install_composition_stack,
    normalize_status_text,
    write_feature_json,
)

PY_DIR = PROJECT_ROOT / "scripts" / "python"
NON_ASCII_REPO = "proj-日本語"
NON_ASCII_FEATURE = "001-后台信息架构-🎯"
NON_ASCII_TEMPLATE = "# Tasks 🎯\n\nПравила: 功能 → звіт.\n"


def _clean_env(pythonioencoding: str | None) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("SPECIFY_") and key not in {"PYTHONPATH", "PYTHONUTF8"}
    }
    if pythonioencoding is None:
        env.pop("PYTHONIOENCODING", None)
    else:
        env["PYTHONIOENCODING"] = pythonioencoding
    return env


def _install_python_setup_tasks(repo: Path) -> Path:
    py_dir = repo / ".specify" / "scripts" / "python"
    py_dir.mkdir(parents=True, exist_ok=True)
    for name in ("common.py", "setup_tasks.py"):
        shutil.copy(PY_DIR / name, py_dir / name)
    shutil.copy(
        PROJECT_ROOT / "src" / "specify_cli" / "markdown_sections.py",
        py_dir / "markdown_sections.py",
    )
    return py_dir / "setup_tasks.py"


def _run_raw(
    script: Path,
    *args: str,
    cwd: Path,
    pythonioencoding: str | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        capture_output=True,
        check=False,
        env=_clean_env(pythonioencoding),
    )


def _setup_non_ascii_repo(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    repo = tmp_path / NON_ASCII_REPO
    (repo / ".specify").mkdir(parents=True)
    script = _install_python_setup_tasks(repo)
    write_feature_json(repo, f"specs/{NON_ASCII_FEATURE}")
    feature = repo / "specs" / NON_ASCII_FEATURE
    feature.mkdir(parents=True)
    (feature / "spec.md").write_text("# spec\n", encoding="utf-8")
    (feature / "plan.md").write_text("# plan\n", encoding="utf-8")
    (feature / "research.md").write_text("# research\n", encoding="utf-8")
    (feature / "contracts" / "v1").mkdir(parents=True)
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True)
    template = templates / "tasks-template.md"
    template.write_bytes(NON_ASCII_TEMPLATE.encode("utf-8"))
    return repo, script, feature, template


def _load_setup_tasks_module(script: Path):
    spec = importlib.util.spec_from_file_location("test_setup_tasks_mod", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "encoding_env",
    [
        "cp1252",
        "ascii",
        pytest.param(
            None,
            marks=pytest.mark.skipif(
                os.name != "nt",
                reason="Default redirected pipe code page is Windows-specific",
            ),
            id="windows-default-pipe",
        ),
    ],
)
def test_text_mode_preserves_non_ascii_paths_under_legacy_code_pages(
    tmp_path: Path, encoding_env: str | None
) -> None:
    repo, script, feature, template = _setup_non_ascii_repo(tmp_path)

    result = _run_raw(script, cwd=repo, pythonioencoding=encoding_env)

    stdout = result.stdout.decode("utf-8")
    stderr = result.stderr.decode("utf-8", errors="replace")
    assert result.returncode == 0, stderr
    assert stderr == ""
    assert f"FEATURE_DIR: {feature}" in stdout
    assert f"TASKS_TEMPLATE: {template}" in stdout
    normalized = normalize_status_text(stdout)
    assert "[OK] research.md" in normalized
    assert "[FAIL] data-model.md" in normalized
    assert "[OK] contracts/" in normalized
    assert "[FAIL] quickstart.md" in normalized


@pytest.mark.parametrize("encoding_env", ["cp1252", "ascii"])
def test_help_preserves_non_ascii_script_path_under_legacy_code_pages(
    tmp_path: Path, encoding_env: str
) -> None:
    repo, script, _, _ = _setup_non_ascii_repo(tmp_path)

    result = _run_raw(script, "--help", cwd=repo, pythonioencoding=encoding_env)

    stdout = result.stdout.decode("utf-8")
    stderr = result.stderr.decode("utf-8", errors="replace")
    assert result.returncode == 0, stderr
    assert stderr == ""
    assert "Usage:" in stdout
    assert NON_ASCII_REPO in stdout


@pytest.mark.parametrize("encoding_env", ["cp1252", "ascii"])
def test_json_mode_remains_pure_ascii_for_non_ascii_paths_and_template(
    tmp_path: Path, encoding_env: str
) -> None:
    repo, script, feature, template = _setup_non_ascii_repo(tmp_path)

    result = _run_raw(script, "--json", cwd=repo, pythonioencoding=encoding_env)

    stderr = result.stderr.decode("utf-8", errors="replace")
    assert result.returncode == 0, stderr
    assert stderr == ""
    assert result.stdout.isascii()
    payload = json.loads(result.stdout.decode("ascii"))
    assert Path(payload["FEATURE_DIR"]) == feature
    assert Path(payload["TASKS_TEMPLATE"]) == template
    assert payload["TASKS_TEMPLATE_CONTENT"] == NON_ASCII_TEMPLATE
    assert payload["AVAILABLE_DOCS"] == ["research.md", "contracts/"]


@pytest.mark.parametrize("missing", ["plan.md", "spec.md"])
@pytest.mark.parametrize("json_flag", [[], ["--json"]], ids=["text", "json"])
@pytest.mark.parametrize("encoding_env", ["cp1252", "ascii"])
def test_missing_prerequisite_stderr_preserves_utf8_paths(
    tmp_path: Path,
    missing: str,
    json_flag: list[str],
    encoding_env: str,
) -> None:
    repo, script, feature, _ = _setup_non_ascii_repo(tmp_path)
    (feature / missing).unlink()

    result = _run_raw(script, *json_flag, cwd=repo, pythonioencoding=encoding_env)

    stderr = result.stderr.decode("utf-8")
    assert result.returncode == 1
    assert result.stdout == b""
    assert "UnicodeEncodeError" not in stderr
    assert "Traceback" not in stderr
    assert f"ERROR: {missing} not found in {feature}" in stderr
    assert "\\u540e" not in stderr


@pytest.mark.parametrize("encoding_env", ["cp1252", "ascii"])
def test_missing_tasks_template_stderr_preserves_utf8_repo_root(
    tmp_path: Path, encoding_env: str
) -> None:
    repo, script, _, template = _setup_non_ascii_repo(tmp_path)
    template.unlink()

    result = _run_raw(script, "--json", cwd=repo, pythonioencoding=encoding_env)

    stderr = result.stderr.decode("utf-8")
    assert result.returncode == 1
    assert result.stdout == b""
    assert "UnicodeEncodeError" not in stderr
    assert f"for {repo}" in stderr


@pytest.mark.parametrize("encoding_env", ["cp1252", "ascii"])
def test_template_resolution_error_stderr_preserves_utf8_details(
    tmp_path: Path, encoding_env: str
) -> None:
    repo, script, _, _ = _setup_non_ascii_repo(tmp_path)
    install_composition_stack(repo, "tasks-template", "# Core\n")
    broken_layer = (
        repo / ".specify" / "presets" / "wrap-pack" / "templates" / "tasks-template.md"
    )
    broken_layer.write_text("# Broken wrapper without placeholder\n", encoding="utf-8")

    result = _run_raw(script, "--json", cwd=repo, pythonioencoding=encoding_env)

    stderr = result.stderr.decode("utf-8")
    assert result.returncode == 1
    assert result.stdout == b""
    assert "UnicodeEncodeError" not in stderr
    assert "ERROR:" in stderr
    assert NON_ASCII_REPO in stderr


@pytest.mark.parametrize("encoding_env", ["cp1252", "ascii"])
def test_unknown_non_ascii_option_stderr_preserves_utf8(
    tmp_path: Path, encoding_env: str
) -> None:
    repo, script, _, _ = _setup_non_ascii_repo(tmp_path)

    result = _run_raw(script, "--选项", cwd=repo, pythonioencoding=encoding_env)

    stderr = result.stderr.decode("utf-8")
    assert result.returncode == 1
    assert result.stdout == b""
    assert "UnicodeEncodeError" not in stderr
    assert "ERROR: Unknown option '--选项'" in stderr


def test_in_process_main_keeps_ascii_marker_fallback_on_narrow_stream(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "proj-ascii"
    (repo / ".specify").mkdir(parents=True)
    script = _install_python_setup_tasks(repo)
    write_feature_json(repo, "specs/001-my-feature")
    feature = repo / "specs" / "001-my-feature"
    feature.mkdir(parents=True)
    (feature / "spec.md").write_text("# spec\n", encoding="utf-8")
    (feature / "plan.md").write_text("# plan\n", encoding="utf-8")
    (feature / "research.md").write_text("# research\n", encoding="utf-8")
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True)
    (templates / "tasks-template.md").write_text("# Tasks\n", encoding="utf-8")

    module = _load_setup_tasks_module(script)

    raw_out = io.BytesIO()
    narrow_out = io.TextIOWrapper(raw_out, encoding="cp1252")
    monkeypatch.chdir(repo)
    monkeypatch.delenv("SPECIFY_INIT_DIR", raising=False)
    monkeypatch.delenv("SPECIFY_FEATURE", raising=False)
    monkeypatch.delenv("SPECIFY_FEATURE_DIRECTORY", raising=False)
    monkeypatch.setattr(sys, "stdout", narrow_out)

    code = module.main([])
    narrow_out.flush()
    rendered = raw_out.getvalue().decode("cp1252")
    assert code == 0
    assert "[OK] research.md" in rendered
    assert "[FAIL] data-model.md" in rendered


def test_script_entrypoint_tolerates_streams_without_reconfigure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, script, feature, _ = _setup_non_ascii_repo(tmp_path)
    out = io.StringIO()
    err = io.StringIO()
    monkeypatch.chdir(repo)
    monkeypatch.delenv("SPECIFY_INIT_DIR", raising=False)
    monkeypatch.delenv("SPECIFY_FEATURE", raising=False)
    monkeypatch.delenv("SPECIFY_FEATURE_DIRECTORY", raising=False)
    monkeypatch.setattr(sys, "argv", [str(script)])
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(script), run_name="__main__")

    assert exc_info.value.code == 0
    assert err.getvalue() == ""
    assert f"FEATURE_DIR: {feature}" in out.getvalue()
