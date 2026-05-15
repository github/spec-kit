"""Tests for architecture extension artifact initialization."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import requires_bash


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARCHITECTURE_EXTENSION = PROJECT_ROOT / "extensions" / "arch"
SETUP_ARCH_SH = ARCHITECTURE_EXTENSION / "scripts" / "bash" / "setup-arch.sh"
SETUP_ARCH_PS = ARCHITECTURE_EXTENSION / "scripts" / "powershell" / "setup-arch.ps1"
ARCH_TEMPLATES = [
    "architecture-template.md",
    "architecture-scenario-template.md",
    "architecture-logical-template.md",
    "architecture-process-template.md",
    "architecture-development-template.md",
    "architecture-physical-template.md",
]

HAS_PWSH = shutil.which("pwsh") is not None
_POWERSHELL = shutil.which("powershell.exe") or shutil.which("powershell")


def _install_bash_scripts(repo: Path) -> None:
    d = repo / ".specify" / "extensions" / "arch" / "scripts" / "bash"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(SETUP_ARCH_SH, d / "setup-arch.sh")


def _install_ps_scripts(repo: Path) -> None:
    d = repo / ".specify" / "extensions" / "arch" / "scripts" / "powershell"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(SETUP_ARCH_PS, d / "setup-arch.ps1")


def _install_templates(repo: Path) -> None:
    d = repo / ".specify" / "extensions" / "arch" / "templates"
    d.mkdir(parents=True, exist_ok=True)
    for name in ARCH_TEMPLATES:
        shutil.copy(ARCHITECTURE_EXTENSION / "templates" / name, d / name)


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("SPECIFY_"):
            env.pop(key)
    return env


def _powershell_script_arg(exe: str, script: Path) -> str:
    if sys.platform != "win32" and str(exe).endswith("powershell.exe") and shutil.which("wslpath"):
        result = subprocess.run(
            ["wslpath", "-w", str(script)],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    return str(script)


@pytest.fixture
def arch_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir()
    (repo / ".specify").mkdir()
    _install_templates(repo)
    _install_bash_scripts(repo)
    _install_ps_scripts(repo)
    return repo


def _json_from_output(output: str) -> dict[str, str]:
    for line in reversed(output.strip().splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)
    raise AssertionError(f"No JSON object found in output:\n{output}")


def _assert_arch_json(repo: Path, data: dict[str, str], *, exact_paths: bool = True) -> None:
    expected = {
        "ARCH_FILE": repo / ".specify" / "memory" / "architecture.md",
        "ARCH_DIR": repo / ".specify" / "memory",
        "SCENARIO_VIEW": repo / ".specify" / "memory" / "architecture-scenario-view.md",
        "LOGICAL_VIEW": repo / ".specify" / "memory" / "architecture-logical-view.md",
        "PROCESS_VIEW": repo / ".specify" / "memory" / "architecture-process-view.md",
        "DEVELOPMENT_VIEW": repo / ".specify" / "memory" / "architecture-development-view.md",
        "PHYSICAL_VIEW": repo / ".specify" / "memory" / "architecture-physical-view.md",
    }
    assert set(data) == set(expected)
    for key, path in expected.items():
        if exact_paths:
            assert Path(data[key]) == path
        else:
            normalized = data[key].replace("\\", "/")
            assert normalized.endswith(path.relative_to(repo).as_posix())
        assert path.is_file() if key != "ARCH_DIR" else path.is_dir()


@requires_bash
def test_setup_arch_bash_creates_all_artifacts_and_json(arch_repo: Path) -> None:
    script = arch_repo / ".specify" / "extensions" / "arch" / "scripts" / "bash" / "setup-arch.sh"
    result = subprocess.run(
        ["bash", str(script), "--json"],
        cwd=arch_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode == 0, result.stderr + result.stdout
    data = _json_from_output(result.stdout)
    _assert_arch_json(arch_repo, data)
    assert "Scenario View" in (arch_repo / ".specify" / "memory" / "architecture-scenario-view.md").read_text(encoding="utf-8")


@requires_bash
def test_setup_arch_bash_preserves_existing_files(arch_repo: Path) -> None:
    existing = arch_repo / ".specify" / "memory" / "architecture-scenario-view.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("# Custom Scenario\n", encoding="utf-8")

    script = arch_repo / ".specify" / "extensions" / "arch" / "scripts" / "bash" / "setup-arch.sh"
    result = subprocess.run(
        ["bash", str(script), "--json"],
        cwd=arch_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert existing.read_text(encoding="utf-8") == "# Custom Scenario\n"


@pytest.mark.skipif(not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available")
def test_setup_arch_powershell_creates_all_artifacts_and_json(arch_repo: Path) -> None:
    script = arch_repo / ".specify" / "extensions" / "arch" / "scripts" / "powershell" / "setup-arch.ps1"
    exe = "pwsh" if HAS_PWSH else _POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", _powershell_script_arg(exe, script), "-Json"],
        cwd=arch_repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )

    assert result.returncode == 0, result.stderr + result.stdout
    data = _json_from_output(result.stdout)
    _assert_arch_json(arch_repo, data, exact_paths=False)
