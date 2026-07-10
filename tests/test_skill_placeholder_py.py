"""resolve_skill_placeholders must support the py script variant (#3280)."""

from pathlib import Path

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


def test_py_interpreter_with_spaces_is_quoted(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "specify_cli.integrations.base.shutil.which", lambda name: None
    )
    monkeypatch.setattr(
        "specify_cli.integrations.base.sys.executable",
        r"C:\Program Files\Python\python.exe",
    )
    save_init_options(tmp_path, {"script": "py"})
    body = CommandRegistrar.resolve_skill_placeholders(
        "codex", FRONTMATTER, "Run {SCRIPT} now.", tmp_path
    )
    assert '"C:\\Program Files\\Python\\python.exe" ' in body


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
