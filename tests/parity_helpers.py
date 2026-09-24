"""Shared helpers for the core-script Python parity tests."""

from __future__ import annotations

import json
import os
import shlex
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
    # A --without-pip venv still honors an inherited PYTHONPATH, so leaving
    # this set could make a "no-PyYAML" test interpreter import PyYAML
    # anyway, silently skipping the delegated-parsing path under test.
    env.pop("PYTHONPATH", None)
    # Tests exercising SPECKIT_PYTHON_EXECUTABLE/SPECKIT_PYTHON set them
    # explicitly; an ambient value in the host environment would otherwise
    # silently override the "unset" baseline for every other test.
    env.pop("SPECKIT_PYTHON_EXECUTABLE", None)
    env.pop("SPECKIT_PYTHON", None)
    return env


def venv_python3_exe(venv_dir: Path) -> Path:
    """Path to the python3 executable of a venv created with ``--without-pip``."""
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python3"


def make_yaml_less_venv(venv_dir: Path) -> Path:
    """Create a ``--without-pip`` venv and return its python3 executable.

    Asserts the interpreter cannot actually import PyYAML, since it could
    otherwise be visible via an inherited ``PYTHONPATH`` despite
    ``--without-pip``, silently invalidating tests that assume it lacks one.
    """
    subprocess.run(
        [sys.executable, "-m", "venv", "--without-pip", str(venv_dir)],
        check=True,
        capture_output=True,
    )
    exe = venv_python3_exe(venv_dir)
    assert exe.is_file()
    probe = subprocess.run(
        [str(exe), "-c", "import yaml"],
        capture_output=True,
        env=clean_env(),
        check=False,
    )
    assert probe.returncode != 0, "venv unexpectedly has PyYAML importable"
    return exe


def _bash_posix_path(path: Path) -> str:
    """Convert a Windows path to the POSIX form the available bash expects."""
    resolved = str(path.resolve())
    if os.name != "nt":
        return resolved
    converted = subprocess.run(
        [
            "bash",
            "-lc",
            'command -v cygpath >/dev/null 2>&1 && cygpath -u "$1"',
            "bash",
            resolved,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if converted.returncode == 0 and converted.stdout.strip():
        return converted.stdout.strip()
    drive = path.drive.rstrip(":").lower()
    posix = path.as_posix()
    return f"/mnt/{drive}{posix[2:]}" if drive else posix


def make_python3_path_shim(shim_dir: Path) -> Path:
    """Create a deterministic ``python3`` shim that execs the current pytest
    interpreter, so a test can put a guaranteed PyYAML-capable interpreter
    first on PATH as the *default* ``python3`` a script finds via its
    python3 -> python -> py -3 fallback chain (as opposed to the
    SPECKIT_PYTHON(_EXECUTABLE) override, which names its interpreter
    explicitly and never depends on PATH lookup).
    """
    shim_dir.mkdir(parents=True, exist_ok=True)
    python_exe = Path(sys.executable).resolve()

    shell_shim = shim_dir / "python3"
    shell_shim.write_text(
        f"#!/usr/bin/env sh\nexec {shlex.quote(_bash_posix_path(python_exe))} \"$@\"\n",
        encoding="utf-8",
        newline="\n",
    )
    shell_shim.chmod(0o755)

    if os.name == "nt":
        cmd_shim = shim_dir / "python3.cmd"
        cmd_shim.write_text(f'@echo off\r\n"{python_exe}" %*\r\n', encoding="utf-8")

    return shim_dir


def collation_range_locale() -> str | None:
    """A locale whose ``[a-z]`` bracket range is collation-ordered, or ``None``.

    glibc resolves a bracket-expression *range* through the locale's collation
    table, so under ``en_US.UTF-8`` ``[^a-z0-9]`` leaves accented lowercase
    letters alone while ``C.UTF-8`` and the POSIX locale strip them. Probe
    ``sed`` directly rather than trusting a locale name: the environments where
    the divergence cannot be reproduced (no such locale installed, a non-glibc
    libc, Git-for-Windows) are exactly the ones where the probe comes back
    clean, so the caller can skip.
    """
    for name in ("en_US.UTF-8", "en_US.utf8"):
        env = clean_env()
        env["LC_ALL"] = name
        env["LANG"] = name
        try:
            probe = subprocess.run(
                ["sed", "s/[^a-z0-9]/-/g"],
                input="é\n",
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
        except OSError:  # pragma: no cover - sed missing entirely
            return None
        if probe.returncode == 0 and "é" in probe.stdout:
            return name
    return None


def run(
    cmd: list[str],
    repo: Path,
    env: dict[str, str] | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a script variant.

    ``timeout`` guards cases whose regression mode is a hang rather than a bad
    value; without it such a failure would stall the suite instead of failing
    it. ``subprocess.TimeoutExpired`` propagates so the test reports the hang.
    """
    return subprocess.run(
        cmd,
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env if env is not None else clean_env(),
        timeout=timeout,
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


def install_composition_stack(
    repo: Path, template_name: str, core_content: str
) -> str:
    """Install wrap/prepend/append presets over a core template."""
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True, exist_ok=True)
    (templates / f"{template_name}.md").write_bytes(core_content.encode("utf-8"))

    layers = [
        ("wrap-pack", 1, "wrap", "## Wrapper\n{CORE_TEMPLATE}\n## End\n"),
        ("prepend-pack", 2, "prepend", "# Prepended\n"),
        ("append-pack", 3, "append", "# Appended\n"),
    ]
    registry: dict[str, object] = {"presets": {}}
    registry_presets = registry["presets"]
    assert isinstance(registry_presets, dict)

    for preset_id, priority, strategy, content in layers:
        preset_dir = repo / ".specify" / "presets" / preset_id
        template_dir = preset_dir / "templates"
        template_dir.mkdir(parents=True)
        (template_dir / f"{template_name}.md").write_bytes(content.encode("utf-8"))
        (preset_dir / "preset.yml").write_text(
            "provides:\n"
            "  templates:\n"
            "    - type: template\n"
            f"      name: {template_name}\n"
            f"      file: templates/{template_name}.md\n"
            f"      strategy: {strategy}\n",
            encoding="utf-8",
        )
        registry_presets[preset_id] = {
            "enabled": True,
            "priority": priority,
        }

    (repo / ".specify" / "presets" / ".registry").write_text(
        json.dumps(registry, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    appended = "# Appended\n"
    prepended = "# Prepended\n"
    wrapper = "## Wrapper\n{CORE_TEMPLATE}\n## End\n"
    composed = f"{core_content}\n\n{appended}"
    composed = f"{prepended}\n\n{composed}"
    return wrapper.replace("{CORE_TEMPLATE}", composed)


def break_wrap_layer(repo: Path, template_name: str) -> None:
    """Replace the installed wrap layer with one missing its placeholder."""
    (
        repo
        / ".specify"
        / "presets"
        / "wrap-pack"
        / "templates"
        / f"{template_name}.md"
    ).write_text("# Broken wrapper\n", encoding="utf-8")


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
