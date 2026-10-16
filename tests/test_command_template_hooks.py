"""Core command hook dispatch is present in every rendered script variant."""

from pathlib import Path

import pytest

from specify_cli.integrations.base import IntegrationBase
from specify_cli.agents import CommandRegistrar

ROOT = Path(__file__).parent.parent
TEMPLATES = ROOT / "templates" / "commands"
NAMES = (
    "analyze", "checklist", "clarify", "constitution", "converge",
    "implement", "plan", "specify", "tasks", "taskstoissues",
)


def test_all_core_hook_templates_discovered():
    assert set(NAMES) <= {path.stem for path in TEMPLATES.glob("*.md")}


@pytest.mark.parametrize("name", NAMES)
def test_both_boundaries_and_error_handling(name):
    text = (TEMPLATES / f"{name}.md").read_text(encoding="utf-8")
    assert f"{{PRE_HOOK_SCRIPT}} {name}" in text
    assert f"{{POST_HOOK_SCRIPT}} {name}" in text
    assert text.index("{PRE_HOOK_SCRIPT}") < text.index("{POST_HOOK_SCRIPT}")
    assert text.count("no hooks were checked") == 2
    assert text.count("including mandatory hooks") == 2
    assert text.count("wait for completion") == 2
    assert text.count("without executing them automatically") == 2


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("variant,dir,ext", [
    ("sh", "bash", "sh"), ("ps", "powershell", "ps1"), ("py", "python", "py"),
])
def test_hook_scripts_render_and_exist(name, variant, dir, ext):
    text = (TEMPLATES / f"{name}.md").read_text(encoding="utf-8")
    result = IntegrationBase.process_template(text, "copilot", variant)
    assert "{PRE_HOOK_SCRIPT}" not in result
    assert "{POST_HOOK_SCRIPT}" not in result
    for phase in ("pre", "post"):
        path = f".specify/scripts/{dir}/{phase}{'-' if variant != 'py' else '_'}hooks.{ext}"
        assert path in result
        assert (ROOT / "scripts" / dir / f"{phase}{'-' if variant != 'py' else '_'}hooks.{ext}").is_file()


@pytest.mark.parametrize("name", NAMES)
def test_no_repeated_yaml_hook_instructions(name):
    text = (TEMPLATES / f"{name}.md").read_text(encoding="utf-8")
    assert "hooks.before_" not in text
    assert "hooks.after_" not in text
    assert "If the YAML cannot be parsed" not in text


@pytest.mark.parametrize("variant,dir,ext", [
    ("sh", "bash", "sh"), ("ps", "powershell", "ps1"), ("py", "python", "py"),
])
def test_preset_wrap_and_skill_registrar_resolve_hook_scripts(tmp_path, variant, dir, ext):
    config = tmp_path / ".specify"
    config.mkdir()
    (config / "init-options.json").write_text(
        f'{{"script": "{variant}"}}', encoding="utf-8"
    )
    body = "{PRE_HOOK_SCRIPT} plan\n{POST_HOOK_SCRIPT} plan"
    rendered = CommandRegistrar.resolve_skill_placeholders(
        "copilot",
        {"scripts": {variant: "scripts/python/setup_plan.py --json"}},
        body, tmp_path,
    )
    assert "{PRE_HOOK_SCRIPT}" not in rendered
    assert "{POST_HOOK_SCRIPT}" not in rendered
    assert f".specify/scripts/{dir}/" in rendered
    assert f"hooks.{ext}" in rendered
