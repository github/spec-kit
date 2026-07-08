"""Every command template with a scripts: block must render for --script py.

Covers #3283: each ``templates/commands/*.md`` that declares a ``scripts:``
frontmatter block carries a ``py:`` line, and ``process_template`` turns it
into a valid Python invocation (interpreter-prefixed, path rewritten to the
``.specify`` tree).
"""

import re
from pathlib import Path

import pytest

from specify_cli.integrations.base import IntegrationBase

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "commands"

SCRIPTED_TEMPLATES = sorted(
    p.name for p in TEMPLATES_DIR.glob("*.md") if "\nscripts:\n" in p.read_text()
)


@pytest.fixture(autouse=True)
def _pin_interpreter(monkeypatch):
    monkeypatch.setattr(
        "specify_cli.integrations.base.shutil.which",
        lambda name: "/usr/bin/python3" if name == "python3" else None,
    )


def test_scripted_templates_discovered():
    # Guard: the glob must find the known scripted templates, otherwise the
    # parametrized tests below would silently pass on an empty set.
    assert "plan.md" in SCRIPTED_TEMPLATES
    assert "implement.md" in SCRIPTED_TEMPLATES


@pytest.mark.parametrize("name", SCRIPTED_TEMPLATES)
def test_template_declares_py_script(name: str):
    content = (TEMPLATES_DIR / name).read_text()
    assert re.search(r"^\s*py: scripts/python/\S+\.py", content, re.MULTILINE), (
        f"{name} has a scripts: block but no py: line"
    )


@pytest.mark.parametrize("name", SCRIPTED_TEMPLATES)
def test_template_renders_python_invocation(name: str):
    content = (TEMPLATES_DIR / name).read_text()
    result = IntegrationBase.process_template(content, "agent", "py")
    assert "{SCRIPT}" not in result
    assert re.search(
        r"python3 \.specify/scripts/python/\w+\.py(?: --[\w-]+)*", result
    ), f"{name} did not render a Python invocation"


@pytest.mark.parametrize("name", SCRIPTED_TEMPLATES)
def test_sh_rendering_unchanged(name: str):
    # Negative: adding py: lines must not leak into sh rendering.
    content = (TEMPLATES_DIR / name).read_text()
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
        repo_root=Path(__file__).resolve().parents[1],
        console=Console(quiet=True),
        force=False,
    )
    dest = tmp_path / ".specify" / "scripts" / "python"
    assert (dest / "check_prerequisites.py").is_file()
    assert not (tmp_path / ".specify" / "scripts" / "powershell").exists()
