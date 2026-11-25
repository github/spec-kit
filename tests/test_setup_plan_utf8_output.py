"""Regression tests for UTF-8 stdout/stderr handling in scripts/python/setup_plan.py."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.parity_helpers import PROJECT_ROOT, install_composition_stack, write_feature_json

PY_DIR = PROJECT_ROOT / "scripts" / "python"
NON_ASCII_REPO = "proj-日本語"
NON_ASCII_FEATURE = "001-后台信息架构-🎯"
NON_ASCII_TEMPLATE = "# Plan 🎯\n\nПравила: 功能 → звіт.\n"


def _clean_env(pythonioencoding: str) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("SPECIFY_") and key not in {"PYTHONPATH", "PYTHONUTF8"}
    }
    env["PYTHONIOENCODING"] = pythonioencoding
    return env


def _install_python_setup_plan(repo: Path) -> Path:
    py_dir = repo / ".specify" / "scripts" / "python"
    py_dir.mkdir(parents=True, exist_ok=True)
    for name in ("common.py", "setup_plan.py"):
        shutil.copy(PY_DIR / name, py_dir / name)
    shutil.copy(
        PROJECT_ROOT / "src" / "specify_cli" / "markdown_sections.py",
        py_dir / "markdown_sections.py",
    )
    return py_dir / "setup_plan.py"


def _run_raw(
    script: Path,
    *args: str,
    cwd: Path,
    pythonioencoding: str = "cp1252",
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    env = _clean_env(pythonioencoding)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        capture_output=True,
        check=False,
        env=env,
    )


def _setup_non_ascii_repo(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    repo = tmp_path / NON_ASCII_REPO
    (repo / ".specify").mkdir(parents=True)
    script = _install_python_setup_plan(repo)
    write_feature_json(repo, f"specs/{NON_ASCII_FEATURE}")
    feature = repo / "specs" / NON_ASCII_FEATURE
    feature.mkdir(parents=True)
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True)
    template = templates / "plan-template.md"
    template.write_bytes(NON_ASCII_TEMPLATE.encode("utf-8"))
    return repo, script, feature, template


@pytest.mark.parametrize("encoding_env", ["cp1252", "ascii"])
def test_text_mode_preserves_non_ascii_paths(tmp_path: Path, encoding_env: str) -> None:
    repo, script, feature, _ = _setup_non_ascii_repo(tmp_path)

    result = _run_raw(script, cwd=repo, pythonioencoding=encoding_env)

    stdout = result.stdout.decode("utf-8")
    stderr = result.stderr.decode("utf-8", errors="replace")
    assert result.returncode == 0, stderr
    assert stderr == ""
    assert f"IMPL_PLAN: {feature / 'plan.md'}" in stdout
    assert (feature / "plan.md").read_bytes() == NON_ASCII_TEMPLATE.encode("utf-8")


@pytest.mark.parametrize("encoding_env", ["cp1252", "ascii"])
def test_json_mode_keeps_ascii_json_with_non_ascii_paths(
    tmp_path: Path, encoding_env: str
) -> None:
    repo, script, feature, _ = _setup_non_ascii_repo(tmp_path)

    result = _run_raw(script, "--json", cwd=repo, pythonioencoding=encoding_env)

    stderr = result.stderr.decode("utf-8")
    assert result.returncode == 0, stderr
    assert "UnicodeEncodeError" not in stderr
    assert f"Copied plan template to {feature / 'plan.md'}" in stderr
    assert result.stdout.isascii()
    payload = json.loads(result.stdout.decode("ascii"))
    assert Path(payload["IMPL_PLAN"]) == feature / "plan.md"
    assert Path(payload["FEATURE_DIR"]) == feature


@pytest.mark.parametrize("encoding_env", ["cp1252", "ascii"])
def test_template_resolution_error_stderr_preserves_utf8_path(
    tmp_path: Path, encoding_env: str
) -> None:
    repo, script, _, _ = _setup_non_ascii_repo(tmp_path)
    install_composition_stack(repo, "plan-template", "# Core\n")
    broken_layer = (
        repo / ".specify" / "presets" / "wrap-pack" / "templates" / "plan-template.md"
    )
    broken_layer.write_text("# Broken wrapper without placeholder\n", encoding="utf-8")

    result = _run_raw(script, cwd=repo, pythonioencoding=encoding_env)

    stderr = result.stderr.decode("utf-8")
    assert result.returncode == 1
    assert result.stdout == b""
    assert "UnicodeEncodeError" not in stderr
    assert "Traceback" not in stderr
    assert NON_ASCII_REPO in stderr


@pytest.mark.parametrize("encoding_env", ["cp1252", "ascii"])
def test_invalid_init_dir_stderr_preserves_utf8_path(
    tmp_path: Path, encoding_env: str
) -> None:
    repo, script, _, _ = _setup_non_ascii_repo(tmp_path)
    missing = tmp_path / "ne-existe-pas-étape"

    result = _run_raw(
        script,
        cwd=repo,
        pythonioencoding=encoding_env,
        env_overrides={"SPECIFY_INIT_DIR": str(missing)},
    )

    stderr = result.stderr.decode("utf-8")
    assert result.returncode == 1
    assert "UnicodeEncodeError" not in stderr
    assert "Traceback" not in stderr
    assert f"SPECIFY_INIT_DIR does not point to an existing directory: {missing}" in stderr
