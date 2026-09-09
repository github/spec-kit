"""Cross-platform regression tests for paths-only feature-directory parsing."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMMON_PS = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"
CHECK_PREREQS_PS = PROJECT_ROOT / "scripts" / "powershell" / "check-prerequisites.ps1"

HAS_PWSH = shutil.which("pwsh") is not None
_WINDOWS_POWERSHELL = (
    (shutil.which("powershell.exe") or shutil.which("powershell"))
    if os.name == "nt"
    else None
)


@pytest.mark.skipif(
    not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available"
)
def test_ps_paths_only_handles_windows_style_feature_dir_on_any_host(
    tmp_path: Path,
) -> None:
    """A persisted backslash path must produce the same BRANCH on every host OS."""
    repo = tmp_path / "proj"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init", "-q"], cwd=repo, check=True
    )

    scripts = repo / ".specify" / "scripts" / "powershell"
    scripts.mkdir(parents=True)
    shutil.copy(COMMON_PS, scripts / "common.ps1")
    shutil.copy(CHECK_PREREQS_PS, scripts / "check-prerequisites.ps1")
    (repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": "specs\\001-my-feature"}),
        encoding="utf-8",
    )

    env = os.environ.copy()
    for key in list(env):
        if key.startswith("SPECIFY_"):
            env.pop(key)

    exe = "pwsh" if HAS_PWSH else _WINDOWS_POWERSHELL
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(scripts / "check-prerequisites.ps1"), "-Json", "-PathsOnly"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["BRANCH"] == "001-my-feature"
