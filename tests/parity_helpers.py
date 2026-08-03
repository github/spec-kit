"""Shared helpers for the core-script Python parity tests."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASH_DIR = PROJECT_ROOT / "scripts" / "bash"
PS_DIR = PROJECT_ROOT / "scripts" / "powershell"
PY_DIR = PROJECT_ROOT / "scripts" / "python"

HAS_PWSH = shutil.which("pwsh") is not None
WINDOWS_POWERSHELL = (
    (shutil.which("powershell.exe") or shutil.which("powershell"))
    if os.name == "nt"
    else None
)
POWERSHELL_EXE = "pwsh" if HAS_PWSH else WINDOWS_POWERSHELL
HAS_POWERSHELL = POWERSHELL_EXE is not None


def make_repo(tmp_path: Path, name: str = "proj") -> Path:
    repo = tmp_path / name
    (repo / ".specify").mkdir(parents=True)
    return repo


def install_scripts(repo: Path, script: str) -> None:
    """Install the bash/powershell/python twins of a kebab-case script name."""
    py_name = script.replace("-", "_")

    bash_dir = repo / ".specify" / "scripts" / "bash"
    bash_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(BASH_DIR / "common.sh", bash_dir / "common.sh")
    shutil.copy(BASH_DIR / f"{script}.sh", bash_dir / f"{script}.sh")

    ps_dir = repo / ".specify" / "scripts" / "powershell"
    ps_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(PS_DIR / "common.ps1", ps_dir / "common.ps1")
    shutil.copy(PS_DIR / f"{script}.ps1", ps_dir / f"{script}.ps1")

    py_dir = repo / ".specify" / "scripts" / "python"
    py_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(PY_DIR / "common.py", py_dir / "common.py")
    shutil.copy(PY_DIR / f"{py_name}.py", py_dir / f"{py_name}.py")


def bash_cmd(repo: Path, script: str, *args: str) -> list[str]:
    return ["bash", str(repo / ".specify" / "scripts" / "bash" / f"{script}.sh"), *args]


def py_cmd(repo: Path, script: str, *args: str) -> list[str]:
    py_name = script.replace("-", "_")
    return [
        sys.executable,
        str(repo / ".specify" / "scripts" / "python" / f"{py_name}.py"),
        *args,
    ]


def ps_cmd(repo: Path, script: str, *args: str) -> list[str]:
    assert POWERSHELL_EXE, "no PowerShell available; guard the test with HAS_POWERSHELL"
    return [
        POWERSHELL_EXE,
        "-NoProfile",
        "-File",
        str(repo / ".specify" / "scripts" / "powershell" / f"{script}.ps1"),
        *args,
    ]


def clean_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("SPECIFY_"):
            env.pop(key)
    return env


def run(
    cmd: list[str], repo: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env if env is not None else clean_env(),
    )


def json_stdout(result: subprocess.CompletedProcess[str]) -> object:
    return json.loads(result.stdout)


def write_feature_json(
    repo: Path, feature_directory: str = "specs/001-my-feature"
) -> None:
    (repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": feature_directory}, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


def normalize_repo_paths(text: str, repo: Path) -> str:
    """Replace the repo path with a placeholder so two-repo runs compare equal."""
    repo_paths = sorted({str(repo), str(repo.resolve())}, key=len, reverse=True)
    for repo_path in repo_paths:
        text = text.replace(repo_path, "<REPO>")
    return text.replace("\r\n", "\n")


def normalize_script_names(text: str, repo: Path, script: str) -> str:
    """Replace per-runtime script paths (argv[0] in usage/help output)."""
    py_name = script.replace("-", "_")
    bash_script = str(repo / ".specify" / "scripts" / "bash" / f"{script}.sh")
    py_script = str(repo / ".specify" / "scripts" / "python" / f"{py_name}.py")
    return text.replace(bash_script, "<SCRIPT>").replace(py_script, "<SCRIPT>")


def normalize_status_text(text: str) -> str:
    return (
        text.replace("  ✓ ", "  [OK] ")
        .replace("  ✗ ", "  [FAIL] ")
        .replace("\r\n", "\n")
    )
