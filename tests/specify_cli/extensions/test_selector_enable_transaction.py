"""Enable must undo partial real writes and selector ownership changes."""

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app, shared_infra
from specify_cli.extensions import ExtensionManager, HookExecutor
from specify_cli.presets import PresetManager
from tests.specify_cli.presets.test_install_transaction import tree_state
from tests.specify_cli.presets.test_selector_provider_lifecycle import (
    ALIAS,
    COMMAND,
    extension,
    preset,
    project,
)


@pytest.mark.parametrize(
    "agent,skills,output",
    [
        ("gemini", False, f".gemini/commands/{COMMAND}.toml"),
        ("copilot", True, ".github/skills/speckit-provider-collect/SKILL.md"),
        ("codex", False, ".agents/skills/speckit-provider-collect/SKILL.md"),
    ],
)
@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize(
    "failure", ["write", "registry", "hooks", "preset_write", "none"]
)
def test_enable_restores_partial_outputs_and_ownership(
    tmp_path, monkeypatch, agent, skills, output, failure, fallback
):
    root = project(tmp_path, monkeypatch, agent, skills)
    target = root / output
    target.parent.parent.mkdir(parents=True, exist_ok=True)
    source = extension(tmp_path)
    path = source / "extension.yml"
    manifest = yaml.safe_load(path.read_text())
    manifest["provides"]["commands"][0]["aliases"] = [ALIAS]
    path.write_text(yaml.safe_dump(manifest))
    ExtensionManager(root).install_from_directory(source, "0.1.5")
    PresetManager(root).install_from_directory(
        preset(
            tmp_path, "selector", r"regex:speckit\.provider\..*", "SELECTOR BODY", True
        ),
        "0.1.5",
    )
    result = CliRunner().invoke(app, ["extension", "disable", "provider"])
    assert result.exit_code == 0, result.output
    if fallback:
        PresetManager(root).install_from_directory(
            preset(tmp_path, "fallback", COMMAND, "FALLBACK BODY", True),
            "0.1.5",
            priority=30,
        )
        assert target.exists()
    # Force a hook config write after the materialization phases.
    hook = root / ".specify/extensions.yml"
    hook.write_text(
        "hooks:\n  after_implement:\n    - extension: provider\n      enabled: false\n"
    )
    if failure == "registry":
        # Force a real ownership publication even when a surviving fallback
        # already owns this destination and registration would otherwise be a no-op.
        manager = PresetManager(root)
        manager.registry.update(
            "selector", {"registered_commands": {}, "registered_skills": {}}
        )
    before = tree_state(root)
    writes = []
    original = Path.write_text
    shared_write = shared_infra._write_shared_text

    def check(dest, content):
        if dest == target:
            assert target.exists()
            writes.append(content)
            if failure == "write" or (
                failure == "preset_write" and "SELECTOR BODY" in content
            ):
                raise OSError("real materialization failure")

    def write(path, content, *args, **kwargs):
        result = original(path, content, *args, **kwargs)
        check(path, content)
        return result

    def shared(project_path, dest, content):
        result = shared_write(project_path, dest, content)
        check(dest, content)
        return result

    monkeypatch.setattr(Path, "write_text", write)
    monkeypatch.setattr(shared_infra, "_write_shared_text", shared)
    if failure == "registry":
        registry_type = type(ExtensionManager(root).registry)
        original_update = registry_type.update

        def update(registry, identifier, updates):
            result = original_update(registry, identifier, updates)
            if "registered_commands" in updates or "registered_skills" in updates:
                assert target.exists()
                raise OSError("registry failure after write")
            return result

        monkeypatch.setattr(registry_type, "update", update)
        preset_registry_type = type(PresetManager(root).registry)
        preset_update = preset_registry_type.update

        def update_preset(registry, identifier, updates):
            result = preset_update(registry, identifier, updates)
            if target.exists() and (
                "registered_commands" in updates or "registered_skills" in updates
            ):
                raise OSError("preset registry failure after write")
            return result

        monkeypatch.setattr(preset_registry_type, "update", update_preset)
    if failure == "hooks":
        original_save = HookExecutor.save_project_config

        def save(executor, config):
            original_save(executor, config)
            assert target.exists()
            raise OSError("hook failure after write")

        monkeypatch.setattr(HookExecutor, "save_project_config", save)
    result = CliRunner().invoke(app, ["extension", "enable", "provider"])
    if failure == "none":
        assert result.exit_code == 0, result.output + str(result.exception)
        assert "SELECTOR BODY" in target.read_text()
        assert ExtensionManager(root).registry.get("provider")["enabled"] is True
        return
    assert result.exit_code != 0, result.output
    assert "unexpected keyword argument" not in str(result.exception)
    assert writes, str(result.exception)
    assert "enabled" not in result.output
    assert tree_state(root) == before
    assert ExtensionManager(root).registry.get("provider")["enabled"] is False


def test_refresh_default_remains_best_effort(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    manager = ExtensionManager(root)
    manager.install_from_directory(extension(tmp_path), "0.1.5")
    target = root / f".gemini/commands/{COMMAND}.toml"
    original = Path.write_text

    def write(path, content, *args, **kwargs):
        result = original(path, content, *args, **kwargs)
        if path == target:
            raise OSError("best effort writer failure")
        return result

    monkeypatch.setattr(Path, "write_text", write)
    manager.register_enabled_extensions_for_agent("gemini")
    with pytest.raises(OSError, match="best effort writer failure"):
        manager.register_enabled_extensions_for_agent("gemini", strict=True)
