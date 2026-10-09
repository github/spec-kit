"""Fault injection at priority and disable transaction boundaries."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.presets import PresetManager
from tests.specify_cli.presets._helpers import (
    PresetArtifactTestHelpers,
    install_constitution_sync_preset,
    make_convention_constitution_preset,
)


def tree_state(root):
    return {
        str(path.relative_to(root)): (
            ("link", os.readlink(path))
            if path.is_symlink()
            else ("dir",)
            if path.is_dir()
            else ("file", path.read_bytes(), path.stat().st_mode)
        )
        for path in root.rglob("*")
    }


@pytest.mark.parametrize("mode", ["commands", "skills", "global-skills"])
@pytest.mark.parametrize(
    "stage", ["scan", "commands", "skills", "ownership", "constitution"]
)
@pytest.mark.parametrize("raw_priority", [True, "high", None, "missing"])
def test_priority_failure_restores_exact_state(
    project_dir, temp_dir, monkeypatch, stage, raw_priority, mode
):
    helper = PresetArtifactTestHelpers()
    home = temp_dir / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    helper._write_init_options(
        project_dir,
        ai="hermes" if mode == "global-skills" else "claude",
        ai_skills=mode != "commands",
    )
    (project_dir / ".claude" / "commands").mkdir(parents=True)
    helper._create_skill(project_dir / ".claude" / "skills", "speckit-demo")
    manager = PresetManager(project_dir)
    for preset_id, priority in [("first", 5), ("second", 20)]:
        source = helper._create_command_preset(
            temp_dir, preset_id, "speckit.demo", preset_id, preset_id
        )
        manager.install_from_directory(source, "0.1.5", priority=priority)
    metadata = manager.registry.get("second")
    if raw_priority == "missing":
        metadata.pop("priority")
    else:
        metadata["priority"] = raw_priority
    manager.registry.restore("second", metadata)
    memory = project_dir / ".specify" / "memory"
    memory.mkdir(exist_ok=True)
    (memory / "constitution.md").write_bytes(b"exact constitution\r\n")
    (memory / ".constitution-template.json").write_bytes(b"exact provenance")
    before = tree_state(project_dir)
    home_before = tree_state(home)
    calls = []
    method = {
        "scan": "_collect_selector_command_names",
        "commands": "_reconcile_composed_commands",
        "skills": "_reconcile_skills",
        "ownership": "_merge_pack_registered_commands"
        if mode == "commands"
        else "_merge_pack_registered_skills",
        "constitution": "_reconcile_constitution",
    }[stage]
    original = getattr(PresetManager, method)

    def fail(self, *args, **kwargs):
        calls.append(1)
        if stage == "scan" and len(calls) == 1:
            return original(self, *args, **kwargs)
        if stage != "scan":
            original(self, *args, **kwargs)
            (memory / "constitution.md").write_text("partially overwritten")
        raise RuntimeError(f"injected {stage}")

    monkeypatch.setattr(PresetManager, method, fail)
    monkeypatch.setattr(Path, "cwd", lambda: project_dir)
    result = CliRunner().invoke(app, ["preset", "set-priority", "second", "1"])
    assert isinstance(result.exception, RuntimeError), result.output
    assert str(result.exception) == f"injected {stage}"
    assert len(calls) == (2 if stage == "scan" else 1)
    assert tree_state(project_dir) == before
    assert tree_state(home) == home_before
    assert PresetManager(project_dir).registry.get("second") == metadata


@pytest.mark.parametrize("stage", ["commands", "skills", "ownership"])
def test_disable_cleanup_failure_still_reconciles_constitution(
    project_dir, temp_dir, monkeypatch, stage
):
    helper = PresetArtifactTestHelpers()
    helper._write_init_options(project_dir, ai="claude", ai_skills=False)
    (project_dir / ".claude" / "commands").mkdir(parents=True)
    manager = PresetManager(project_dir)
    install_constitution_sync_preset(manager)
    source = make_convention_constitution_preset(temp_dir)
    command = helper._create_command_preset(
        temp_dir, "command-source", "speckit.demo", "demo", "demo"
    )
    # A command and a convention constitution belong to the same disabled preset.
    import yaml

    manifest = yaml.safe_load((source / "preset.yml").read_text())
    manifest["provides"]["templates"].extend(
        yaml.safe_load((command / "preset.yml").read_text())["provides"]["templates"]
    )
    import shutil

    shutil.copytree(command / "commands", source / "commands")
    (source / "preset.yml").write_text(yaml.safe_dump(manifest))
    manager.install_from_directory(source, "0.1.5", priority=1)
    metadata = manager.registry.get("convention-constitution")
    memory = project_dir / ".specify" / "memory" / "constitution.md"
    assert memory.read_text() == "# Convention Constitution\n"
    original_commands = PresetManager._reconcile_composed_commands
    original_skills = PresetManager._reconcile_skills

    def cleanup_failure(self, names):
        if self.registry.get("convention-constitution")["enabled"] is False:
            raise RuntimeError("cleanup failure")
        return (original_commands if stage == "commands" else original_skills)(
            self, names
        )

    if stage == "ownership":
        from specify_cli.presets import PresetRegistry

        original_update = PresetRegistry.update

        def update(self, preset_id, values):
            if (
                preset_id == "convention-constitution"
                and "registered_commands" in values
                and self.get(preset_id)["enabled"] is False
            ):
                raise RuntimeError("ownership cleanup failure")
            return original_update(self, preset_id, values)

        monkeypatch.setattr(PresetRegistry, "update", update)
    else:
        monkeypatch.setattr(
            PresetManager,
            "_reconcile_composed_commands"
            if stage == "commands"
            else "_reconcile_skills",
            cleanup_failure,
        )
    monkeypatch.setattr(Path, "cwd", lambda: project_dir)
    with pytest.warns(UserWarning, match="provenance was preserved"):
        result = CliRunner().invoke(
            app, ["preset", "disable", "convention-constitution"]
        )
    assert result.exit_code == 0, result.output
    after = PresetManager(project_dir).registry.get("convention-constitution")
    assert after["enabled"] is False
    assert after["registered_commands"] == metadata["registered_commands"]
    assert after["registered_skills"] == metadata["registered_skills"]
    assert memory.read_text() != "# Convention Constitution\n"
