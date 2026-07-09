"""Command templates with a py: script line must render for --script py.

Covers #3283: ``py:`` lines in the ``scripts:`` frontmatter of
``templates/commands/*.md`` reference Python scripts that exist in the repo,
and ``process_template`` turns them into a valid Python invocation
(interpreter-prefixed, path rewritten to the ``.specify`` tree).

``plan.md`` and ``tasks.md`` gain their ``py:`` lines together with
``setup_plan.py``/``setup_tasks.py`` in the core-scripts port (#3280); the
existence check below enforces that ordering.
"""

import re
from pathlib import Path

import pytest

from specify_cli.integrations.base import IntegrationBase

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
    dest = tmp_path / ".specify" / "scripts" / "python"
    assert (dest / "check_prerequisites.py").is_file()
    assert not (tmp_path / ".specify" / "scripts" / "powershell").exists()
