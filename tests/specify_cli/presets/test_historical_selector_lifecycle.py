"""Real historical destination regressions for preset enable/disable."""

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app, save_init_options
from specify_cli.presets import PresetManager

from .test_selector_provider_lifecycle import COMMAND, preset, project

LAYOUTS = [
    ("gemini", False, f".gemini/commands/{COMMAND}.toml"),
    ("copilot", True, ".github/skills/speckit-provider-collect/SKILL.md"),
    ("claude", True, ".claude/skills/speckit-provider-collect/SKILL.md"),
]


def activate(root, agent, skills):
    (root / ".bob/commands").mkdir(parents=True, exist_ok=True)
    save_init_options(root, {"ai": agent, "ai_skills": skills, "script": "sh"})
    PresetManager(root).register_enabled_presets_for_agent(agent)


def invoke(operation, identifier):
    result = CliRunner().invoke(app, ["preset", operation, identifier])
    assert result.exit_code == 0, (result.output, result.exception)
    return result


@pytest.mark.parametrize("agent,skills,relative", LAYOUTS)
def test_disable_rewrites_inactive_fallback_before_dropping_ownership(
    tmp_path, monkeypatch, agent, skills, relative
):
    root = project(tmp_path, monkeypatch, agent, skills)
    if agent == "claude":
        (root / ".claude/skills").mkdir(parents=True)
    manager = PresetManager(root)
    manager.install_from_directory(
        preset(tmp_path, "fallback", COMMAND, "FALLBACK BODY"), "0.1.5", priority=20
    )
    manager.install_from_directory(
        preset(tmp_path, "selector", r"regex:speckit\.provider\..*", "SELECTOR BODY"),
        "0.1.5",
        priority=5,
    )
    historical = root / relative
    assert "SELECTOR BODY" in historical.read_text()
    activate(root, "bob", False)
    active = root / f".bob/commands/{COMMAND}.md"
    assert "SELECTOR BODY" in active.read_text()

    invoke("disable", "selector")
    assert "FALLBACK BODY" in historical.read_text()
    assert "SELECTOR BODY" not in historical.read_text()
    assert "FALLBACK BODY" in active.read_text()
    manager = PresetManager(root)
    disabled = manager.registry.get("selector")
    assert disabled["enabled"] is False
    assert disabled["registered_commands"] == {}
    assert disabled["registered_skills"] == {}
    fallback = manager.registry.get("fallback")
    key = "registered_skills" if skills else "registered_commands"
    assert agent in fallback[key]
    before = historical.read_bytes()
    invoke("disable", "selector")
    manager.register_enabled_presets_for_agent("bob")
    manager.register_enabled_presets_for_agent("bob")
    assert historical.read_bytes() == before
    assert "SELECTOR BODY" not in active.read_text()


@pytest.mark.parametrize("agent,skills,relative", LAYOUTS)
def test_enable_regex_with_empty_disabled_expansion_updates_historical_targets(
    tmp_path, monkeypatch, agent, skills, relative
):
    root = project(tmp_path, monkeypatch, agent, skills)
    if agent == "claude":
        (root / ".claude/skills").mkdir(parents=True)
    manager = PresetManager(root)
    manager.install_from_directory(
        preset(tmp_path, "fallback", COMMAND, "FALLBACK BODY"), "0.1.5", priority=20
    )
    manager.install_from_directory(
        preset(tmp_path, "selector", r"regex:speckit\.provider\..*", "SELECTOR BODY"),
        "0.1.5",
        priority=5,
    )
    invoke("disable", "selector")
    historical = root / relative
    assert "FALLBACK BODY" in historical.read_text()
    activate(root, "bob", False)
    from specify_cli.presets._resolver import PresetResolver

    manager = PresetManager(root)
    resolver = PresetResolver(root)
    directory = manager.presets_dir / "selector"
    declarations = resolver._get_manifest(directory).templates
    assert manager._expand_command_selectors(resolver, directory, declarations) == []
    invoke("enable", "selector")
    assert "SELECTOR BODY" in historical.read_text()
    assert "SELECTOR BODY" in (root / f".bob/commands/{COMMAND}.md").read_text()
    winner = PresetManager(root).registry.get("selector")
    key = "registered_skills" if skills else "registered_commands"
    assert agent in winner[key]
    invoke("disable", "selector")
    invoke("disable", "selector")
    PresetManager(root).register_enabled_presets_for_agent("bob")
    assert "FALLBACK BODY" in historical.read_text()
    assert "SELECTOR BODY" not in historical.read_text()


@pytest.mark.parametrize("agent,skills,relative", LAYOUTS[:2])
def test_historical_zero_layer_cleanup_failure_retains_retryable_tracking(
    tmp_path, monkeypatch, agent, skills, relative
):
    root = project(tmp_path, monkeypatch, agent, skills)
    manager = PresetManager(root)
    manager.install_from_directory(
        preset(tmp_path, "provider", COMMAND, "PROVIDER BODY"), "0.1.5"
    )
    historical = root / relative
    before = manager.registry.get("provider")
    activate(root, "bob", False)
    if skills:
        original = shutil.rmtree

        def fail_target(path, *args, **kwargs):
            if Path(path) == historical.parent:
                raise OSError("historical target blocked")
            return original(path, *args, **kwargs)

        monkeypatch.setattr(shutil, "rmtree", fail_target)
    else:
        original = Path.unlink

        def fail_target(path, *args, **kwargs):
            if path == historical:
                raise OSError("historical target blocked")
            return original(path, *args, **kwargs)

        monkeypatch.setattr(Path, "unlink", fail_target)
    with pytest.warns(UserWarning, match="provenance was preserved for retry"):
        invoke("disable", "provider")
    assert "PROVIDER BODY" in historical.read_text()
    retained = PresetManager(root).registry.get("provider")
    assert retained["enabled"] is False
    key = "registered_skills" if skills else "registered_commands"
    assert retained[key][agent] == before[key][agent]
    if skills:
        monkeypatch.setattr(shutil, "rmtree", original)
    else:
        monkeypatch.setattr(Path, "unlink", original)
    invoke("disable", "provider")
    assert not historical.exists()
    metadata = PresetManager(root).registry.get("provider")
    assert metadata["registered_commands"] == {}
    assert metadata["registered_skills"] == {}
    invoke("disable", "provider")
    PresetManager(root).register_enabled_presets_for_agent("bob")
    assert not historical.exists()


def test_disable_fallback_keeps_foreign_inactive_skill(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, "copilot", True)
    manager = PresetManager(root)
    manager.install_from_directory(
        preset(tmp_path, "fallback", COMMAND, "FALLBACK BODY"), "0.1.5", priority=20
    )
    manager.install_from_directory(
        preset(tmp_path, "selector", r"regex:speckit\.provider\..*", "SELECTOR BODY"),
        "0.1.5",
        priority=5,
    )
    activate(root, "bob", False)
    skill = root / ".github/skills/speckit-provider-collect/SKILL.md"
    foreign = "---\nmetadata:\n  source: user:custom\n---\nUSER BODY\n"
    skill.write_text(foreign)
    invoke("disable", "selector")
    assert skill.read_text() == foreign
    invoke("enable", "selector")
    assert skill.read_text() == foreign
