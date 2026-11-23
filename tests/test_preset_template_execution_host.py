"""Exercise preset template resolution in a relocated, isolated project."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from tests.conftest import HAS_BASH
from tests.parity_helpers import (
    HAS_POWERSHELL,
    WINDOWS_POWERSHELL,
    _bash_posix_path,
    bash_cmd,
    clean_env,
    json_stdout,
    make_python3_path_shim,
    make_yaml_less_venv,
    ps_cmd,
    py_cmd,
    run,
)

SCRIPT = "resolve-template"


@pytest.mark.parametrize(
    ("route", "variant"),
    [("python", "py"), ("bash", "sh"), ("powershell", "ps"), ("windows-powershell", "ps")],
)
def test_installed_preset_resolves_on_an_execution_host_without_pyyaml(
    tmp_path: Path, route: str, variant: str,
) -> None:
    if route == "bash" and not HAS_BASH:
        pytest.skip("Bash unavailable")
    if route == "powershell" and not HAS_POWERSHELL:
        pytest.skip("PowerShell unavailable")
    if route == "windows-powershell":
        if os.name != "nt":
            pytest.skip("Windows PowerShell 5.1 requires Windows")
        assert WINDOWS_POWERSHELL, "Native Windows PowerShell must be available"

    specify = [sys.executable, "-c", "from specify_cli import main; main()"]
    initialized = run(specify + [
        "init", "project", "--integration", "copilot", "--script", variant,
        "--non-interactive", "--ignore-agent-tools",
    ], tmp_path, timeout=60)
    assert initialized.returncode == 0, initialized.stdout + initialized.stderr
    project = tmp_path / "project"
    source = tmp_path / "source"
    source.mkdir()
    prefix = source / "préface-功能.md"
    (source / "preset.yml").write_text(
        'schema_version: "1.0"\n'
        "preset: {id: team, name: Team, version: '1.0.0', description: Team templates}\n"
        "requires: {speckit_version: '>=1'}\n"
        "provides:\n"
        "  templates:\n"
        f"    - {{type: template, name: plan-template, file: {prefix.name}, strategy: prepend}}\n",
        encoding="utf-8",
    )
    prefix.write_text("# From the preset", encoding="utf-8")
    installed = run(specify + ["preset", "add", "--dev", str(source)], project, timeout=60)
    assert installed.returncode == 0, installed.stdout + installed.stderr

    project = project.rename(tmp_path / "relocated project")
    execution_python = make_yaml_less_venv(tmp_path / "execution host")
    shim = make_python3_path_shim(tmp_path / "execution path", execution_python)
    env = clean_env()
    env["PATH"] = f"{shim}{os.pathsep}{env['PATH']}"
    template = "plan-template"
    if route == "bash":
        command = bash_cmd(project, SCRIPT, template, "--json")
    elif route in ("powershell", "windows-powershell"):
        env["PYTHONIOENCODING"] = "ascii"
        command = ps_cmd(project, SCRIPT, template, "-Json")
        if route == "windows-powershell":
            command[0] = WINDOWS_POWERSHELL
    else:
        command = py_cmd(project, SCRIPT, template, "--json")
        command[0] = str(execution_python)

    core = (project / ".specify/templates/plan-template.md").read_bytes().decode("utf-8")
    result = run(command, project, env, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json_stdout(result)["TEMPLATE_CONTENT"] == "# From the preset\n\n" + core

    registry = project / ".specify/presets/.registry"
    registry_data = json.loads(registry.read_text(encoding="utf-8"))
    del registry_data["presets"]["team"]["template_entries"]
    registry.write_text(json.dumps(registry_data), encoding="utf-8")
    missing = run(command, project, env, timeout=30)
    assert missing.returncode != 0
    assert missing.stdout == ""
    assert "missing" in missing.stderr
    assert "specify integration upgrade" in missing.stderr

    upgraded = run(specify + ["integration", "upgrade", "copilot"], project, timeout=60)
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr

    installed_preset = project / ".specify/presets/team"
    manifest = installed_preset / "preset.yml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("prepend", "append"),
        encoding="utf-8",
    )
    stale = run(command, project, env, timeout=30)
    assert stale.returncode != 0
    assert stale.stdout == ""
    assert "stale" in stale.stderr
    assert "specify integration upgrade" in stale.stderr

    upgraded = run(specify + ["integration", "upgrade", "copilot"], project, timeout=60)
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    resolved = run(command, project, env, timeout=30)
    assert resolved.returncode == 0, resolved.stderr
    assert json_stdout(resolved)["TEMPLATE_CONTENT"] == core + "\n\n# From the preset"

    prefix.write_text("# From the replacement", encoding="utf-8")
    updated = run(specify + ["preset", "update", "team", "--dev", str(source)], project, timeout=60)
    assert updated.returncode == 0, updated.stdout + updated.stderr
    if route != "python":
        env["PATH"] = clean_env()["PATH"]
        env["SPECKIT_PYTHON_EXECUTABLE"] = (
            _bash_posix_path(execution_python) if route == "bash" else str(execution_python)
        )
    resolved = run(command, project, env, timeout=30)
    assert resolved.returncode == 0, resolved.stderr
    assert json_stdout(resolved)["TEMPLATE_CONTENT"] == "# From the replacement\n\n" + core

    command_preset = run(specify + ["preset", "add", "lean"], project, timeout=60)
    assert command_preset.returncode == 0, command_preset.stdout + command_preset.stderr
    removed = run(specify + ["preset", "remove", "team"], project, timeout=60)
    assert removed.returncode == 0, removed.stdout + removed.stderr
    resolved = run(command, project, env, timeout=30)
    assert resolved.returncode == 0, resolved.stderr
    assert json_stdout(resolved)["TEMPLATE_CONTENT"] == core
