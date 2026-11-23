"""Exercise preset template resolution in a relocated, isolated project."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import stat
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
    install_scripts,
    json_stdout,
    make_repo,
    make_python3_path_shim,
    make_yaml_less_venv,
    ps_cmd,
    py_cmd,
    run,
)

SCRIPT = "resolve-template"


def _older_python_launcher(tmp_path: Path, route: str) -> str:
    """Fake the discovered version while requiring the real resolver to use another interpreter."""
    if os.name == "nt" and route != "bash":
        launcher = tmp_path / "old-python.cmd"
        launcher.write_text(
            '@echo off\nif "%1"=="--version" (echo Python 3.10.0 & exit /b 0)\nexit /b 42\n',
            encoding="utf-8",
        )
        return str(launcher)
    runner = tmp_path / "old-python.py"
    runner.write_text(
        """import sys
if sys.argv[1:] == ["--version"]:
    print("Python 3.10.0")
elif sys.argv[1] == "-c":
    class Version(tuple):
        major = 3
    sys.version_info = Version((3, 10, 0))
    exec(sys.argv[2])
else:
    raise SystemExit(42)
""",
        encoding="utf-8",
    )
    launcher = tmp_path / "old-python"
    launcher.write_text(
        "#!/bin/sh\nexec "
        + " ".join(shlex.quote(_bash_posix_path(path)) for path in (Path(sys.executable), runner))
        + ' "$@"\n',
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    return _bash_posix_path(launcher)


@pytest.mark.skipif(os.name == "nt" or not HAS_BASH, reason="requires a POSIX Bash PATH")
def test_extension_registry_can_use_only_the_stdlib_override(tmp_path: Path) -> None:
    project = make_repo(tmp_path)
    install_scripts(project, SCRIPT)
    extensions = project / ".specify/extensions"
    for name in ("enabled", "disabled"):
        template = extensions / name / "templates/plan-template.md"
        template.parent.mkdir(parents=True)
        template.write_text(name + "\n", encoding="utf-8")
    (extensions / ".registry").write_text(
        '{"extensions":{"enabled":{"priority":2},"disabled":{"priority":1,"enabled":false}}}',
        encoding="utf-8",
    )
    runtime = make_yaml_less_venv(tmp_path / "runtime")
    utilities = tmp_path / "utilities"
    utilities.mkdir()
    for name in ("cat", "dirname", "mktemp", "rm", "sort", "tr"):
        location = shutil.which(name)
        assert location, name
        (utilities / name).symlink_to(location)
    env = dict(clean_env(), PATH=str(utilities), SPECKIT_PYTHON_EXECUTABLE=str(runtime))
    command = bash_cmd(project, SCRIPT, "plan-template", "--json")
    bash = shutil.which("bash")
    assert bash
    command[0] = bash
    result = run(command, project, env, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json_stdout(result)["TEMPLATE_CONTENT"] == "enabled\n"


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

    if route != "python":
        fallback = run(
            command, project, dict(env, SPECKIT_PYTHON_EXECUTABLE=_older_python_launcher(tmp_path, route)),
            timeout=30,
        )
        assert fallback.returncode == 0, fallback.stderr
        assert json_stdout(fallback)["TEMPLATE_CONTENT"] == "# From the preset\n\n" + core

    registry = project / ".specify/presets/.registry"
    registry_data = json.loads(registry.read_text(encoding="utf-8"))
    del registry_data["presets"]["team"]["template_entries"]
    del registry_data["presets"]["team"]["template_projection_version"]
    registry.write_text(json.dumps(registry_data), encoding="utf-8")
    if os.name != "nt":
        registry.chmod(0o600)
    for execution_env in (env, dict(clean_env(), SPECKIT_PYTHON_EXECUTABLE=sys.executable)):
        missing = run(command, project, execution_env, timeout=30)
        assert missing.returncode != 0
        assert missing.stdout == ""
        assert "template data is missing" in missing.stderr
        assert "specify integration upgrade" in missing.stderr

    upgraded = run(specify + ["integration", "upgrade", "copilot"], project, timeout=60)
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    if os.name != "nt":
        assert stat.S_IMODE(registry.stat().st_mode) == 0o600

    registry_contents = registry.read_bytes()
    for damaged in (None, b"{", b"[" + registry_contents + b"]"):
        registry.unlink()
        if damaged is not None:
            registry.write_bytes(damaged)
        lost = run(command, project, env, timeout=30)
        assert lost.returncode != 0
        assert lost.stdout == ""
        assert "reinstall" in lost.stderr
        scripts = project / ".specify/scripts"
        other_variant, other_directory = ("ps", "powershell") if variant != "ps" else ("sh", "bash")
        before = {path: path.read_bytes() for path in scripts.rglob("*") if path.is_file()}
        failed_refresh = run(
            specify + ["integration", "upgrade", "copilot", "--script", other_variant],
            project, timeout=60,
        )
        assert failed_refresh.returncode != 0
        assert "reinstall" in failed_refresh.stdout + failed_refresh.stderr
        assert {path: path.read_bytes() for path in scripts.rglob("*") if path.is_file()} == before
        assert not (scripts / other_directory).is_dir() or any(
            path.is_relative_to(scripts / other_directory) for path in before
        )
        registry.write_bytes(registry_contents)

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
