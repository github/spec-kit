import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMON_PS1 = REPO_ROOT / "scripts" / "powershell" / "common.ps1"

HAS_PWSH = shutil.which("pwsh") is not None
_WINDOWS_POWERSHELL = (
    (shutil.which("powershell.exe") or shutil.which("powershell"))
    if os.name == "nt"
    else None
)


def _write_stub_python3(bin_dir: Path) -> None:
    if os.name == "nt":
        stub = bin_dir / "python3.cmd"
        stub.write_text("@echo off\r\nexit /b 9009\r\n", encoding="ascii")
    else:
        stub = bin_dir / "python3"
        stub.write_text("#!/bin/sh\nexit 9\n", encoding="ascii")
        stub.chmod(0o755)


def _write_working_python(bin_dir: Path) -> None:
    if os.name == "nt":
        shim = bin_dir / "python.cmd"
        shim.write_text(f'@"{sys.executable}" %*\r\n', encoding="utf-8")
    else:
        shim = bin_dir / "python"
        shim.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
        shim.chmod(0o755)


def _restricted_path(bin_dir: Path) -> str:
    parts = [str(bin_dir)]
    if os.name == "nt":
        parts += [
            r"C:\Windows\System32",
            r"C:\Windows\System32\WindowsPowerShell\v1.0",
        ]
    else:
        parts += ["/usr/bin", "/bin"]
    return os.pathsep.join(parts)


def _run_driver(exe: str, bin_dir: Path, tmp_path: Path) -> dict:
    driver = tmp_path / "driver.ps1"
    driver.write_text(
        "param([string]$CommonPath)\n"
        ". $CommonPath\n"
        "$cmd = Get-Python3Command\n"
        "if ($null -eq $cmd -or @($cmd).Count -eq 0) {\n"
        "    @{ command = $null } | ConvertTo-Json -Compress\n"
        "    exit 0\n"
        "}\n"
        "$v = & @($cmd)[0] --version 2>&1 | Out-String\n"
        "$code = $LASTEXITCODE\n"
        "@{ command = @($cmd); version = \"$v\"; exitcode = $code }"
        " | ConvertTo-Json -Compress\n",
        encoding="ascii",
    )
    env = {k: v for k, v in os.environ.items() if not k.startswith("SPECIFY_")}
    env["PATH"] = _restricted_path(bin_dir)
    result = subprocess.run(
        [exe, "-NoProfile", "-File", str(driver), str(COMMON_PS1)],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
        cwd=str(tmp_path),
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.skipif(
    not (HAS_PWSH or _WINDOWS_POWERSHELL), reason="no PowerShell available"
)
@pytest.mark.parametrize(
    "exe", ["pwsh" if HAS_PWSH else None, _WINDOWS_POWERSHELL], ids=["pwsh", "winps"]
)
def test_get_python3_command_skips_stub_python3(tmp_path, exe):
    if exe is None:
        pytest.skip("interpreter not available")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_stub_python3(bin_dir)
    _write_working_python(bin_dir)

    data = _run_driver(exe, bin_dir, tmp_path)

    assert data["command"], "expected a usable interpreter, got none"
    assert data["command"][0] != "python3", (
        f"returned unvalidated stub python3: {data['command']}"
    )
    assert data["exitcode"] == 0, data["version"]
    assert data["version"].startswith("Python 3"), data["version"]
