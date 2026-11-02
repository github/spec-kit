"""Regression tests for the git extension's feature-branch fetch guard (#5199).

`check_existing_branches` runs `git fetch --all --prune` for non-dry-run
invocations. Without ``GIT_TERMINAL_PROMPT=0`` an HTTPS remote that has no
usable credential helper makes git prompt on the tty, so the mandatory
``before_specify`` hook (and therefore ``/speckit.specify``) blocks instead of
continuing. The dry-run path already guarded ``git ls-remote``; these tests pin
the same guard on the real fetch path in all three implementations.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import requires_bash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXT_SCRIPTS = PROJECT_ROOT / "extensions" / "git" / "scripts"
PY_SCRIPT = EXT_SCRIPTS / "python" / "create_new_feature_branch.py"
BASH_SCRIPT = EXT_SCRIPTS / "bash" / "create-new-feature-branch.sh"
PS1_SCRIPT = EXT_SCRIPTS / "powershell" / "create-new-feature-branch.ps1"

HAS_PWSH = shutil.which("pwsh") is not None


def _load_python_script():
    spec = importlib.util.spec_from_file_location(
        "ext_create_new_feature_branch", PY_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves annotations through sys.modules[cls.__module__].
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


def _run(command, cwd: Path, log: Path):
    env = {**os.environ, "STUB_LOG": str(log)}
    env.pop("GIT_TERMINAL_PROMPT", None)
    return subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True)


def test_python_fetch_disables_terminal_prompt(tmp_path, monkeypatch):
    module = _load_python_script()
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()

    calls = []

    class _Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(cmd, **kwargs):
        calls.append((list(cmd), kwargs))
        return _Result()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    module.check_existing_branches(tmp_path, specs_dir, False, "")

    fetch_calls = [call for call in calls if call[0][:2] == ["git", "fetch"]]
    assert len(fetch_calls) == 1, calls
    assert fetch_calls[0][1]["env"]["GIT_TERMINAL_PROMPT"] == "0"


@requires_bash
def test_bash_fetch_disables_terminal_prompt(tmp_path):
    _init_repo(tmp_path)
    log = tmp_path / "prompt.log"
    harness = tmp_path / "harness.sh"
    harness.write_text(
        "#!/usr/bin/env bash\n"
        "git() {\n"
        '  if [ "$1" = fetch ]; then\n'
        '    printf \'%s\' "${GIT_TERMINAL_PROMPT-<unset>}" > "$STUB_LOG"\n'
        "    return 0\n"
        "  fi\n"
        '  command git "$@"\n'
        "}\n"
        "export -f git\n"
        f'exec bash "{BASH_SCRIPT.as_posix()}" --short-name probe-fetch-guard "fetch guard"\n',
        encoding="utf-8",
    )

    _run(["bash", str(harness)], cwd=tmp_path, log=log)

    assert log.read_text(encoding="utf-8") == "0"


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh is not available")
def test_powershell_fetch_disables_terminal_prompt(tmp_path):
    _init_repo(tmp_path)
    log = tmp_path / "prompt.log"
    harness = tmp_path / "harness.ps1"
    harness.write_text(
        "function git {\n"
        "  if ($args[0] -eq 'fetch') {\n"
        f"    Set-Content -NoNewline -Path '{log}' -Value \"$($env:GIT_TERMINAL_PROMPT)\"\n"
        "    return\n"
        "  }\n"
        "  $real = (Get-Command git.exe -CommandType Application).Source\n"
        "  & $real @args\n"
        "}\n"
        f". '{PS1_SCRIPT}' -ShortName 'probe-fetch-guard' 'fetch guard'\n",
        encoding="utf-8",
    )

    _run(["pwsh", "-NoProfile", "-File", str(harness)], cwd=tmp_path, log=log)

    assert log.read_text(encoding="utf-8") == "0"



