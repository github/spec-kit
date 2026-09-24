"""Extension command templates with a py: script line must route for --script py.

Covers the extension-command routing gap: the four bundled git/agent-context
command templates previously declared only sh/ps prose (and no ``scripts:``
frontmatter), so ``--script py`` could not resolve their existing Python
implementations.

Positive coverage:
  * each target template declares sh/ps/py
  * each py: path exists in the repo
  * ``process_template(..., "py")`` and ``resolve_skill_placeholders`` render
    a Python invocation (interpreter-prefixed, path rewritten under
    ``.specify/extensions/<id>/``)
  * the event dispatcher resolver returns a runnable py argv

Negative / compatibility coverage:
  * sh rendering is unchanged (no scripts/python leak)
  * a template missing py: still falls back / rejects as before
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

from specify_cli.agents import CommandRegistrar
from specify_cli.integrations.base import IntegrationBase

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# (template path relative to repo root, extension id, python script relative to repo root)
TARGETS = [
    (
        "extensions/git/commands/speckit.git.feature.md",
        "git",
        "extensions/git/scripts/python/create_new_feature_branch.py",
    ),
    (
        "extensions/git/commands/speckit.git.initialize.md",
        "git",
        "extensions/git/scripts/python/initialize_repo.py",
    ),
    (
        "extensions/git/commands/speckit.git.commit.md",
        "git",
        "extensions/git/scripts/python/auto_commit.py",
    ),
    (
        "extensions/agent-context/commands/speckit.agent-context.update.md",
        "agent-context",
        "extensions/agent-context/scripts/python/update_agent_context.py",
    ),
]

TARGET_IDS = [Path(rel).name for rel, _, _ in TARGETS]

_PY_LINE = re.compile(r"^\s*py: (scripts/python/\S+\.py)", re.MULTILINE)


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _py_script_from_frontmatter(rel: str) -> str | None:
    m = _PY_LINE.search(_read(rel))
    return m.group(1) if m else None


@pytest.fixture(autouse=True)
def _pin_interpreter(monkeypatch):
    """Pin the interpreter token so assertions are platform-stable."""
    monkeypatch.setattr(
        "specify_cli.integrations.base.shutil.which",
        lambda name: "/usr/bin/python3" if name == "python3" else None,
    )
    monkeypatch.setattr(
        "specify_cli.integrations.base.IntegrationBase._interpreter_runs",
        staticmethod(lambda path: True),
    )


@pytest.mark.parametrize(("rel", "_ext", "_py"), TARGETS, ids=TARGET_IDS)
def test_template_declares_all_three_variants(rel: str, _ext: str, _py: str):
    content = _read(rel)
    assert re.search(r"^\s*sh: scripts/", content, re.MULTILINE), f"{rel} missing sh:"
    assert re.search(r"^\s*ps: scripts/", content, re.MULTILINE), f"{rel} missing ps:"
    assert re.search(r"^\s*py: scripts/", content, re.MULTILINE), f"{rel} missing py:"


@pytest.mark.parametrize(("rel", "_ext", "py"), TARGETS, ids=TARGET_IDS)
def test_referenced_python_script_exists(rel: str, _ext: str, py: str):
    # Frontmatter paths are relative to the extension root (rewritten to
    # .specify/extensions/<id>/... at registration), not the repo root.
    script = _py_script_from_frontmatter(rel)
    assert script is not None, f"{rel} has no py: line"
    ext_root = (REPO_ROOT / rel).parent.parent  # .../commands/foo.md -> extension root
    assert (ext_root / script).is_file(), f"{rel} references missing {script}"
    # Cross-check against the expected implementation path for this command.
    resolved = (ext_root / script).resolve().relative_to(REPO_ROOT.resolve())
    assert resolved.as_posix() == py


@pytest.mark.parametrize(("rel", "ext", "_py"), TARGETS, ids=TARGET_IDS)
def test_process_template_renders_python_invocation(rel: str, ext: str, _py: str):
    content = _read(rel)
    result = IntegrationBase.process_template(
        content, "agent", "py", project_root=REPO_ROOT
    )
    # scripts: frontmatter block must be stripped from rendered output.
    if result.startswith("---"):
        fm_end = result.find("---", 3)
        frontmatter_section = result[3:fm_end] if fm_end != -1 else ""
        assert "scripts:" not in frontmatter_section, f"{rel}: scripts: not stripped"
    # If the body contains {SCRIPT}, it must resolve to a Python invocation.
    if "{SCRIPT}" in content:
        assert "{SCRIPT}" not in result, f"{rel}: unresolved SCRIPT under py"
        assert re.search(
            rf"python3 \.specify/extensions/{re.escape(ext)}/scripts/python/\w+\.py",
            result,
        ), f"{rel}: SCRIPT did not render a Python invocation"
    else:
        # Without {SCRIPT}, frontmatter selection still must not inject
        # an unresolved placeholder; body prose keeps its own platform list
        # (including the Python path we added intentionally).
        assert "{SCRIPT}" not in result


@pytest.mark.parametrize(("rel", "ext", "_py"), TARGETS, ids=TARGET_IDS)
def test_resolve_skill_placeholders_renders_python(
    rel: str, ext: str, _py: str, tmp_path, monkeypatch
):
    from specify_cli._init_options import save_init_options

    monkeypatch.setattr(
        "specify_cli.integrations.base.shutil.which",
        lambda name: "/usr/bin/python3" if name == "python3" else None,
    )
    monkeypatch.setattr(
        "specify_cli.integrations.base.IntegrationBase._interpreter_runs",
        staticmethod(lambda path: True),
    )
    save_init_options(tmp_path, {"script": "py"})

    content = _read(rel)
    # Simulate registration: rewrite extension-local script paths first.
    registrar = CommandRegistrar()
    # Extract frontmatter scripts dict via parse
    frontmatter, body = registrar.parse_frontmatter(content)
    frontmatter = registrar._adjust_script_paths(frontmatter, extension_id=ext)

    if "{SCRIPT}" in body:
        resolved = CommandRegistrar.resolve_skill_placeholders(
            "codex", frontmatter, body, tmp_path, extension_id=ext
        )
        assert "{SCRIPT}" not in resolved
        assert re.search(
            rf"python3 \.specify/extensions/{re.escape(ext)}/scripts/python/\w+\.py",
            resolved,
        ), f"{rel}: skill body did not render Python invocation"
    else:
        # No {SCRIPT} in body — frontmatter must still declare a py entry
        # pointing at the installed extension script location after rewrite.
        scripts = frontmatter.get("scripts") or {}
        assert "py" in scripts, f"{rel}: frontmatter scripts missing py after adjust"
        assert scripts["py"].startswith(
            f".specify/extensions/{ext}/scripts/python/"
        ), f"{rel}: py path not rewritten for extension: {scripts['py']!r}"


@pytest.mark.parametrize(("rel", "ext", "_py"), TARGETS, ids=TARGET_IDS)
def test_event_resolver_returns_python_argv(rel: str, ext: str, _py: str, tmp_path):
    """The event dispatcher must resolve a runnable py argv for each template."""
    from specify_cli.events import _resolve_event_command_argv

    # Install the template under .specify/extensions/<id>/commands/ as the
    # event resolver expects.
    cmd_dir = tmp_path / ".specify" / "extensions" / ext / "commands"
    cmd_dir.mkdir(parents=True)
    template = cmd_dir / Path(rel).name
    template.write_text(_read(rel), encoding="utf-8")

    # Also place the python script where the resolver looks (base = ext root).
    py_rel = _py_script_from_frontmatter(rel)
    assert py_rel is not None
    # scripts/python/foo.py relative to extension root
    script_dest = tmp_path / ".specify" / "extensions" / ext / py_rel
    script_dest.parent.mkdir(parents=True, exist_ok=True)
    script_dest.write_text("# test stub\n", encoding="utf-8")

    # Force requested variant to py via init-options.
    from specify_cli._init_options import save_init_options

    save_init_options(tmp_path, {"script": "py"})

    argv = _resolve_event_command_argv(template, tmp_path, ext)
    assert argv is not None, f"{rel}: event resolver returned no argv for py"
    assert argv[0] in (sys.executable, "python3", "python") or "python" in argv[0]
    assert any(a.endswith(".py") for a in argv), f"{rel}: argv has no .py script: {argv}"
    assert str(script_dest) in argv or any(
        Path(a).name == Path(py_rel).name for a in argv
    ), f"{rel}: argv does not point at {py_rel}: {argv}"


@pytest.mark.parametrize(("rel", "ext", "_py"), TARGETS, ids=TARGET_IDS)
def test_sh_rendering_keeps_bash_prose_and_strips_frontmatter(
    rel: str, ext: str, _py: str
):
    """Negative: sh rendering must strip scripts: and not inject a py invocation.

    The body prose intentionally lists all three platforms (including the
    Python path we added) so agents can pick; what must NOT happen under
    ``--script sh`` is the frontmatter-selected py command leaking in as an
    interpreter-prefixed ``{SCRIPT}`` replacement.
    """
    content = _read(rel)
    result = IntegrationBase.process_template(
        content, "agent", "sh", project_root=REPO_ROOT
    )
    # Frontmatter scripts: block must be stripped.
    if result.startswith("---"):
        fm_end = result.find("---", 3)
        frontmatter_section = result[3:fm_end] if fm_end != -1 else ""
        assert "scripts:" not in frontmatter_section
    # No interpreter-prefixed Python invocation from {SCRIPT} under sh.
    assert not re.search(rf"python3 \.specify/extensions/{re.escape(ext)}/scripts/python/", result)
    # Existing bash invocation prose must remain intact.
    assert f".specify/extensions/{ext}/scripts/bash/" in result


def test_missing_py_variant_rejects_when_only_opposite_shell():
    """Compatibility: a template with only the opposite platform shell and no
    py: must still raise the documented ValueError under --script py."""
    import os

    opposite = "ps" if os.name != "nt" else "sh"
    command = (
        "scripts/powershell/setup-plan.ps1 -Json"
        if opposite == "ps"
        else "scripts/bash/setup-plan.sh --json"
    )
    content = f"""---
description: x
scripts:
  {opposite}: {command}
---
Run {{SCRIPT}} now.
"""
    with pytest.raises(ValueError, match="No runnable script variant"):
        IntegrationBase.process_template(content, "agent", "py")


def test_select_script_variant_prefers_py_when_requested():
    scripts = {
        "sh": "scripts/bash/x.sh",
        "ps": "scripts/powershell/x.ps1",
        "py": "scripts/python/x.py",
    }
    assert IntegrationBase.select_script_variant("py", scripts) == "py"
    assert IntegrationBase.select_script_variant("sh", scripts) == "sh"
    assert IntegrationBase.select_script_variant("ps", scripts) == "ps"


def test_select_script_variant_missing_py_falls_back_to_platform_shell():
    """When py is requested but absent, fall back to platform shell (not raise
    if a shell is available)."""
    import os

    scripts = {
        "sh": "scripts/bash/x.sh",
        "ps": "scripts/powershell/x.ps1",
    }
    selected = IntegrationBase.select_script_variant("py", scripts)
    expected = "ps" if os.name == "nt" else "sh"
    assert selected == expected
