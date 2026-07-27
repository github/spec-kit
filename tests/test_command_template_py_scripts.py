"""Command templates with a py: script line must render for --script py.

Covers #3283: ``py:`` lines in the ``scripts:`` frontmatter of
``templates/commands/*.md`` reference Python scripts that exist in the repo,
and ``process_template`` turns them into a valid Python invocation
(interpreter-prefixed, path rewritten to the ``.specify`` tree).

``plan.md`` and ``tasks.md`` gain their ``py:`` lines together with
``setup_plan.py``/``setup_tasks.py`` in the core-scripts port (#3280); the
existence check below enforces that ordering.
"""

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from specify_cli.integrations.base import IntegrationBase
from tests.parity_helpers import HAS_POWERSHELL, POWERSHELL_EXE

REPO_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates" / "commands"

_PY_LINE = re.compile(r"^\s*py: (scripts/python/\S+\.py)", re.MULTILINE)


def _py_script(name: str) -> str | None:
    match = _PY_LINE.search((TEMPLATES_DIR / name).read_text(encoding="utf-8"))
    return match.group(1) if match else None


PY_TEMPLATES = sorted(
    p.name for p in TEMPLATES_DIR.glob("*.md") if _py_script(p.name)
)


@pytest.fixture(autouse=True)
def _pin_interpreter(monkeypatch):
    monkeypatch.setattr(
        "specify_cli.integrations.base.shutil.which",
        lambda name: "/usr/bin/python3" if name == "python3" else None,
    )
    # On Windows, ``resolve_python_interpreter`` guards the ``which`` result
    # with a real ``_interpreter_runs`` subprocess probe (#3304). The mocked
    # ``/usr/bin/python3`` path does not exist on a Windows runner, so the
    # probe would fail and the resolver would fall back to ``sys.executable``
    # (a ``...python.exe`` path), breaking the ``python3``-anchored assertion.
    # Pin the probe to True so the interpreter token stays ``python3`` on all
    # platforms.
    monkeypatch.setattr(
        "specify_cli.integrations.base.IntegrationBase._interpreter_runs",
        staticmethod(lambda path: True),
    )


def test_py_templates_discovered():
    # Guard: the glob must find the known py-scripted templates, otherwise
    # the parametrized tests below would silently pass on an empty set.
    assert "implement.md" in PY_TEMPLATES
    assert "clarify.md" in PY_TEMPLATES


@pytest.mark.parametrize("name", PY_TEMPLATES)
def test_referenced_python_script_exists(name: str):
    # A py: line must never point at a script the repo does not ship —
    # rendering would produce a broken invocation at runtime.
    script = _py_script(name)
    assert (REPO_ROOT / script).is_file(), f"{name} references missing {script}"


@pytest.mark.parametrize("name", PY_TEMPLATES)
def test_template_renders_python_invocation(name: str):
    content = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    result = IntegrationBase.process_template(content, "agent", "py")
    assert "{SCRIPT}" not in result
    assert re.search(
        r"python3 \.specify/scripts/python/\w+\.py(?: --[\w-]+)*", result
    ), f"{name} did not render a Python invocation"


def test_py_missing_variant_rejects_opposite_shell_only():
    opposite_variant = "sh" if os.name == "nt" else "ps"
    opposite_command = (
        "scripts/bash/setup-plan.sh --json"
        if opposite_variant == "sh"
        else "scripts/powershell/setup-plan.ps1 -Json"
    )
    content = """---
scripts:
  {variant}: {command}
---
Run {{SCRIPT}} now.
""".format(variant=opposite_variant, command=opposite_command)

    with pytest.raises(ValueError, match="No runnable script variant"):
        IntegrationBase.process_template(content, "agent", "py")


def test_missing_script_preference_keeps_available_shell(monkeypatch):
    monkeypatch.setattr(
        "specify_cli.integrations.base.platform.system", lambda: "Windows"
    )

    selected = IntegrationBase.select_script_variant(
        None, {"sh": "scripts/bash/setup-plan.sh --json"}
    )

    assert selected == "sh"


def test_spaced_python_interpreter_uses_powershell_call_operator(monkeypatch):
    interpreter = r"C:\Program Files\Py$thon's\python.exe"
    quoted_interpreter = interpreter.replace("'", "''")
    monkeypatch.setattr(
        "specify_cli.integrations.base.shutil.which", lambda name: None
    )
    monkeypatch.setattr(
        "specify_cli.integrations.base.sys.executable",
        interpreter,
    )
    monkeypatch.setattr(
        "specify_cli.integrations.base.os", SimpleNamespace(name="nt")
    )

    content = "---\nscripts:\n  py: scripts/python/setup_plan.py --json\n---\n{SCRIPT}\n"
    result = IntegrationBase.process_template(content, "agent", "py")

    assert (
        f"& '{quoted_interpreter}' "
        ".specify/scripts/python/setup_plan.py --json"
    ) in result


def test_spaced_python_interpreter_uses_posix_shell_quoting(monkeypatch):
    interpreter = "/opt/Python $HOME's/bin/python"
    monkeypatch.setattr(
        "specify_cli.integrations.base.shutil.which", lambda name: None
    )
    monkeypatch.setattr(
        "specify_cli.integrations.base.sys.executable",
        interpreter,
    )
    monkeypatch.setattr(
        "specify_cli.integrations.base.os", SimpleNamespace(name="posix")
    )

    content = "---\nscripts:\n  py: scripts/python/setup_plan.py --json\n---\n{SCRIPT}\n"
    result = IntegrationBase.process_template(content, "agent", "py")

    assert (
        f"{shlex.quote(interpreter)} "
        ".specify/scripts/python/setup_plan.py --json"
    ) in result


@pytest.mark.skipif(not HAS_POWERSHELL, reason="no PowerShell available")
def test_spaced_python_interpreter_invocation_runs_in_powershell(
    tmp_path, monkeypatch
):
    interpreter_dir = tmp_path / "Python With Spaces"
    interpreter_dir.mkdir()
    if os.name == "nt":
        interpreter = interpreter_dir / "python.cmd"
        interpreter.write_text(f'@"{sys.executable}" %*\n', encoding="utf-8")
    else:
        interpreter = interpreter_dir / "python"
        interpreter.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8"
        )
        interpreter.chmod(0o755)

    (tmp_path / "probe.py").write_text("print('ok')\n", encoding="utf-8")
    monkeypatch.setattr(
        "specify_cli.integrations.base.shutil.which", lambda name: None
    )
    monkeypatch.setattr(
        "specify_cli.integrations.base.sys.executable", str(interpreter)
    )
    monkeypatch.setattr(
        "specify_cli.integrations.base.os", SimpleNamespace(name="nt")
    )

    content = "---\nscripts:\n  py: probe.py\n---\n{SCRIPT}\n"
    command = IntegrationBase.process_template(content, "agent", "py").splitlines()[-1]
    result = subprocess.run(
        [POWERSHELL_EXE, "-NoProfile", "-Command", command],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


@pytest.mark.parametrize("name", PY_TEMPLATES)
def test_sh_rendering_unchanged(name: str):
    # Negative: adding py: lines must not leak into sh rendering.
    content = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    result = IntegrationBase.process_template(content, "agent", "sh")
    assert "{SCRIPT}" not in result
    assert "scripts/python" not in result


def test_install_shared_infra_copies_python_scripts(tmp_path):
    # --script py must install scripts/python/ into .specify/scripts/python/
    # so the rendered invocations point at files that exist.
    from rich.console import Console

    from specify_cli.shared_infra import install_shared_infra

    install_shared_infra(
        tmp_path,
        "py",
        version="0.0.0",
        core_pack=None,
        repo_root=REPO_ROOT,
        console=Console(quiet=True),
        force=False,
    )
    scripts_dir = tmp_path / ".specify" / "scripts"
    assert (scripts_dir / "python" / "check_prerequisites.py").is_file()
    shell_variant = "powershell" if os.name == "nt" else "bash"
    other_variant = "bash" if os.name == "nt" else "powershell"
    assert (scripts_dir / shell_variant).is_dir()
    assert not (scripts_dir / other_variant).exists()
