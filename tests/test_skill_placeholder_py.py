"""resolve_skill_placeholders must support the py script variant (#3280)."""

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from specify_cli._init_options import save_init_options
from specify_cli.agents import CommandRegistrar

FRONTMATTER = {
    "scripts": {
        "sh": "scripts/bash/setup-plan.sh --json",
        "ps": "scripts/powershell/setup-plan.ps1 -Json",
        "py": "scripts/python/setup_plan.py --json",
    }
}


def _resolve(tmp_path: Path, script: str | None, monkeypatch) -> str:
    monkeypatch.setattr(
        "specify_cli.integrations.base.shutil.which",
        lambda name: "/usr/bin/python3" if name == "python3" else None,
    )
    monkeypatch.setattr(
        "specify_cli.integrations.base.IntegrationBase._interpreter_runs",
        staticmethod(lambda path: True),
    )
    if script:
        save_init_options(tmp_path, {"script": script})
    return CommandRegistrar.resolve_skill_placeholders(
        "codex", FRONTMATTER, "Run {SCRIPT} now.", tmp_path
    )


def test_py_variant_prefixes_interpreter(tmp_path, monkeypatch):
    body = _resolve(tmp_path, "py", monkeypatch)
    assert "python3 .specify/scripts/python/setup_plan.py --json" in body
    assert "{SCRIPT}" not in body


def test_sh_variant_is_not_prefixed(tmp_path, monkeypatch):
    body = _resolve(tmp_path, "sh", monkeypatch)
    assert ".specify/scripts/bash/setup-plan.sh --json" in body
    assert "python3" not in body


def test_py_interpreter_with_spaces_uses_powershell_call_operator(
    tmp_path, monkeypatch
):
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
    save_init_options(tmp_path, {"script": "py"})
    body = CommandRegistrar.resolve_skill_placeholders(
        "codex", FRONTMATTER, "Run {SCRIPT} now.", tmp_path
    )
    assert f"& '{quoted_interpreter}' " in body


def test_missing_py_variant_falls_back_to_available_script(tmp_path, monkeypatch):
    """script=py with a template that only ships sh/ps must not leave {SCRIPT} unresolved."""
    monkeypatch.setattr(
        "specify_cli.integrations.base.shutil.which",
        lambda name: "/usr/bin/python3" if name == "python3" else None,
    )
    save_init_options(tmp_path, {"script": "py"})
    frontmatter = {
        "scripts": {
            "sh": "scripts/bash/setup-plan.sh --json",
            "ps": "scripts/powershell/setup-plan.ps1 -Json",
        }
    }
    body = CommandRegistrar.resolve_skill_placeholders(
        "codex", frontmatter, "Run {SCRIPT} now.", tmp_path
    )
    assert "{SCRIPT}" not in body
    assert "setup-plan" in body


def test_py_install_includes_python_and_fallback_scripts(tmp_path, monkeypatch):
    from specify_cli import _install_shared_infra

    monkeypatch.setattr(
        "specify_cli.integrations.base.shutil.which",
        lambda name: "/usr/bin/python3" if name == "python3" else None,
    )
    _install_shared_infra(tmp_path, "py", force=True)

    assert (tmp_path / ".specify/scripts/python/setup_plan.py").is_file()
    assert (tmp_path / ".specify/scripts/python/setup_tasks.py").is_file()

    save_init_options(tmp_path, {"script": "py"})
    frontmatter = {
        "scripts": {
            "sh": "scripts/bash/check-prerequisites.sh --json",
            "ps": "scripts/powershell/check-prerequisites.ps1 -Json",
        }
    }
    body = CommandRegistrar.resolve_skill_placeholders(
        "codex", frontmatter, "Run {SCRIPT} now.", tmp_path
    )
    fallback = (
        ".specify/scripts/bash/check-prerequisites.sh"
        if "scripts/bash/" in body
        else ".specify/scripts/powershell/check-prerequisites.ps1"
    )
    assert (tmp_path / fallback).is_file()


def test_py_rejects_one_sided_opposite_platform_fallback(
    tmp_path, monkeypatch
):
    from specify_cli import _install_shared_infra
    from specify_cli import shared_infra

    class WindowsOs:
        name = "nt"

        def __getattr__(self, attr):
            return getattr(os, attr)

    monkeypatch.setattr(shared_infra, "os", WindowsOs())
    monkeypatch.setattr(
        "specify_cli.integrations.base.platform.system", lambda: "Windows"
    )
    _install_shared_infra(tmp_path, "py", force=True)

    save_init_options(tmp_path, {"script": "py"})
    frontmatter = {
        "scripts": {
            "sh": "scripts/bash/check-prerequisites.sh --json",
        }
    }
    with pytest.raises(ValueError, match="No runnable script variant"):
        CommandRegistrar.resolve_skill_placeholders(
            "codex", frontmatter, "Run {SCRIPT} now.", tmp_path
        )

    assert not (
        tmp_path / ".specify/scripts/bash/check-prerequisites.sh"
    ).exists()
