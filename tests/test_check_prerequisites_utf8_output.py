"""Regression tests for UTF-8 output in check_prerequisites.py."""

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

from tests.parity_helpers import PROJECT_ROOT, write_feature_json

PY_DIR = PROJECT_ROOT / "scripts" / "python"
NON_ASCII_REPO = "proj-\u65e5\u672c\u8a9e"
NON_ASCII_FEATURE = "001-\u529f\u80fd-\U0001f3af"


def _clean_env(pythonioencoding: str) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("SPECIFY_")
        and key not in {"PYTHONPATH", "PYTHONUTF8"}
    }
    env["PYTHONIOENCODING"] = pythonioencoding
    return env


def _install_python_check_prerequisites(repo: Path) -> Path:
    py_dir = repo / ".specify" / "scripts" / "python"
    py_dir.mkdir(parents=True, exist_ok=True)
    for name in ("common.py", "check_prerequisites.py"):
        shutil.copy(PY_DIR / name, py_dir / name)
    return py_dir / "check_prerequisites.py"


def _run_raw(
    script: Path,
    *args: str,
    cwd: Path,
    pythonioencoding: str,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        capture_output=True,
        check=False,
        env=_clean_env(pythonioencoding),
    )


def _setup_non_ascii_repo(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo = tmp_path / NON_ASCII_REPO
    (repo / ".specify").mkdir(parents=True)
    script = _install_python_check_prerequisites(repo)
    write_feature_json(repo, f"specs/{NON_ASCII_FEATURE}")
    feature = repo / "specs" / NON_ASCII_FEATURE
    feature.mkdir(parents=True)
    (feature / "plan.md").write_text("# plan\n", encoding="utf-8")
    (feature / "spec.md").write_text("# spec\n", encoding="utf-8")
    return repo, script, feature


def _load_check_prerequisites_module(script: Path):
    spec = importlib.util.spec_from_file_location(
        "test_check_prerequisites_mod", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


@pytest.mark.parametrize("encoding_env", ["cp1252", "ascii"])
def test_text_mode_preserves_non_ascii_feature_path(
    tmp_path: Path, encoding_env: str
) -> None:
    repo, script, feature = _setup_non_ascii_repo(tmp_path)
    assert feature.is_dir()

    result = _run_raw(script, cwd=repo, pythonioencoding=encoding_env)

    stdout = result.stdout.decode("utf-8")
    stderr = result.stderr.decode("utf-8", errors="replace")
    assert result.returncode == 0, stderr
    assert f"FEATURE_DIR:{feature}" in stdout
    assert "Traceback" not in stderr


@pytest.mark.parametrize("encoding_env", ["cp1252", "ascii"])
def test_paths_only_text_mode_preserves_non_ascii_paths(
    tmp_path: Path, encoding_env: str
) -> None:
    repo, script, feature = _setup_non_ascii_repo(tmp_path)
    assert feature.is_dir()

    result = _run_raw(
        script, "--paths-only", cwd=repo, pythonioencoding=encoding_env
    )

    stdout = result.stdout.decode("utf-8")
    stderr = result.stderr.decode("utf-8", errors="replace")
    assert result.returncode == 0, stderr
    assert f"REPO_ROOT: {repo}" in stdout
    assert f"FEATURE_DIR: {feature}" in stdout
    assert "Traceback" not in stderr


@pytest.mark.parametrize("args", [("--json",), ("--paths-only", "--json")])
@pytest.mark.parametrize("encoding_env", ["cp1252", "ascii"])
def test_json_modes_remain_ascii_and_preserve_non_ascii_feature_path(
    tmp_path: Path, args: tuple[str, ...], encoding_env: str
) -> None:
    repo, script, feature = _setup_non_ascii_repo(tmp_path)
    assert feature.is_dir()

    result = _run_raw(script, *args, cwd=repo, pythonioencoding=encoding_env)

    stderr = result.stderr.decode("utf-8", errors="replace")
    assert result.returncode == 0, stderr
    assert result.stdout.isascii()
    payload = json.loads(result.stdout.decode("ascii"))
    assert Path(payload["FEATURE_DIR"]) == feature


@pytest.mark.parametrize("encoding_env", ["cp1252", "ascii"])
def test_missing_plan_stderr_preserves_non_ascii_feature_path(
    tmp_path: Path, encoding_env: str
) -> None:
    repo, script, feature = _setup_non_ascii_repo(tmp_path)
    (feature / "plan.md").unlink()
    assert feature.is_dir()

    result = _run_raw(script, cwd=repo, pythonioencoding=encoding_env)

    stderr = result.stderr.decode("utf-8")
    assert result.returncode == 1
    assert "ERROR: plan.md not found in " + str(feature) in stderr
    assert "\\u" not in stderr


def test_in_process_main_keeps_ascii_marker_fallback_on_narrow_stream(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "proj-ascii"
    (repo / ".specify").mkdir(parents=True)
    script = _install_python_check_prerequisites(repo)
    write_feature_json(repo, "specs/001-my-feature")
    feature = repo / "specs" / "001-my-feature"
    feature.mkdir(parents=True)
    (feature / "plan.md").write_text("# plan\n", encoding="utf-8")
    (feature / "spec.md").write_text("# spec\n", encoding="utf-8")
    (feature / "research.md").write_text("# research\n", encoding="utf-8")

    module = _load_check_prerequisites_module(script)

    raw_out = io.BytesIO()
    narrow_out = io.TextIOWrapper(raw_out, encoding="cp1252")
    monkeypatch.chdir(repo)
    monkeypatch.delenv("SPECIFY_INIT_DIR", raising=False)
    monkeypatch.delenv("SPECIFY_FEATURE", raising=False)
    monkeypatch.delenv("SPECIFY_FEATURE_DIRECTORY", raising=False)
    monkeypatch.setattr(sys, "stdout", narrow_out)

    code = module.main(["--include-tasks"])
    narrow_out.flush()
    rendered = raw_out.getvalue().decode("cp1252")
    assert code == 0
    assert "[OK] research.md" in rendered
    assert "[FAIL] quickstart.md" in rendered


def test_script_entrypoint_tolerates_streams_without_reconfigure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, script, feature = _setup_non_ascii_repo(tmp_path)
    assert feature.is_dir()
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
    assert f"FEATURE_DIR:{feature}" in out.getvalue()


class _ReconfigureRaisesStringIO(io.StringIO):
    def reconfigure(self, **kwargs: object) -> None:
        raise ValueError("stream cannot be reconfigured")


def test_script_entrypoint_tolerates_reconfigure_value_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, script, feature = _setup_non_ascii_repo(tmp_path)
    out = _ReconfigureRaisesStringIO()
    err = _ReconfigureRaisesStringIO()
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
    assert f"FEATURE_DIR:{feature}" in out.getvalue()
