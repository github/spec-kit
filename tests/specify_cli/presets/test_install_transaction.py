"""Real filesystem regression coverage for preset install rollback."""

from __future__ import annotations

import copy
import os
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.presets import PresetManager, PresetRegistry
from tests.specify_cli.presets._helpers import (
    PresetArtifactTestHelpers,
    install_constitution_sync_preset,
    make_convention_constitution_preset,
)


def tree_state(root):
    return {
        path.relative_to(root).as_posix(): (
            ("link", os.readlink(path))
            if path.is_symlink()
            else ("dir",)
            if path.is_dir()
            else ("file", path.read_bytes(), path.stat().st_mode)
        )
        for path in root.rglob("*")
    }


@pytest.mark.parametrize("cleanup_failure", [False, True])
@pytest.mark.parametrize("mode", ["commands", "skills", "global-skills"])
def test_fresh_competing_install_restores_winner(
    project_dir, temp_dir, monkeypatch, cleanup_failure, mode
):
    helper = PresetArtifactTestHelpers()
    home = temp_dir / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    helper._write_init_options(
        project_dir,
        ai="hermes" if mode == "global-skills" else "bob",
        ai_skills=mode != "commands",
    )
    (project_dir / ".claude" / "commands").mkdir(parents=True)
    manager = PresetManager(project_dir)
    old = helper._create_command_preset(
        temp_dir, "old-winner", "speckit.demo", "old", "original winner"
    )
    manager.install_from_directory(old, "0.1.5", priority=20)
    source = helper._create_multi_command_preset(
        temp_dir, "challenger", ["speckit.demo", "speckit.new"]
    )
    before = tree_state(project_dir)
    home_before = tree_state(home)
    registry_before = copy.deepcopy(manager.registry.data)
    operation_error = RuntimeError("install failed after materialization")
    original_skills = manager._register_skills
    cleanup_calls = []

    def fail_skills(*args, **kwargs):
        original_skills(*args, **kwargs)
        assert tree_state(project_dir) != before
        # Prove the competing winner actually replaced a concrete output.
        output_root = home if mode == "global-skills" else project_dir
        outputs = [p for p in output_root.rglob("*") if p.is_file()]
        assert any(b"speckit.demo body" in p.read_bytes() for p in outputs)
        raise operation_error

    def fail_cleanup(commands):
        cleanup_calls.append("commands")
        raise OSError("command cleanup failed")

    original_unregister_skills = manager._unregister_skills

    def cleanup_skills(*args, **kwargs):
        cleanup_calls.append("skills")
        return original_unregister_skills(*args, **kwargs)

    monkeypatch.setattr(manager, "_register_skills", fail_skills)
    monkeypatch.setattr(manager, "_unregister_skills", cleanup_skills)
    if cleanup_failure:
        monkeypatch.setattr(manager, "_unregister_commands", fail_cleanup)
    with pytest.raises(RuntimeError) as caught:
        manager.install_from_directory(source, "0.1.5", priority=1)
    assert caught.value is operation_error
    assert "skills" in cleanup_calls
    if cleanup_failure:
        assert cleanup_calls == ["commands", "skills"]
        assert any("command cleanup failed" in n for n in caught.value.__notes__)
    assert tree_state(project_dir) == before
    assert tree_state(home) == home_before
    assert manager.registry.data == registry_before
    assert PresetRegistry(manager.presets_dir).data == registry_before


@pytest.mark.parametrize("failure", ["registry", "skills", "remove"])
def test_forced_regex_install_restores_exact_bytes(
    project_dir, temp_dir, monkeypatch, failure
):
    helper = PresetArtifactTestHelpers()
    helper._write_init_options(project_dir, ai="bob", ai_skills=False)
    commands = project_dir / ".bob" / "commands"
    commands.mkdir(parents=True)
    manager = PresetManager(project_dir)
    install_constitution_sync_preset(manager)
    base = helper._create_command_preset(
        temp_dir, "base", "speckit.demo", "base", "base body"
    )
    manager.install_from_directory(base, "0.1.5", priority=20)
    source = helper._create_command_preset(
        temp_dir, "regex-overlay", "speckit.demo", "overlay", "overlay body"
    )
    manifest_path = source / "preset.yml"
    manifest = yaml.safe_load(manifest_path.read_text())
    declaration = manifest["provides"]["templates"][0]
    declaration["name"] = r"regex:^speckit\.demo$"
    declaration["strategy"] = "append"
    manifest_path.write_text(yaml.safe_dump(manifest))
    manager.install_from_directory(source, "0.1.5", priority=1)
    output = commands / "speckit.demo.md"
    # Regeneration cannot preserve these deliberate local bytes or permissions.
    output.write_bytes(output.read_bytes() + b"\r\nlocal exact edit\r\n")
    output.chmod(0o600)
    (commands / "user-link.md").symlink_to("speckit.demo.md")
    before = tree_state(project_dir)
    registry_before = copy.deepcopy(manager.registry.data)
    operation_error = OSError(f"realistic {failure} failure")

    def fail(*args, **kwargs):
        raise operation_error

    if failure == "registry":
        original_add = manager.registry.add

        def partial_add(*args, **kwargs):
            original_add(*args, **kwargs)
            raise operation_error

        monkeypatch.setattr(manager.registry, "add", partial_add)
    elif failure == "skills":
        monkeypatch.setattr(manager, "_register_skills", fail)
    else:
        original_remove = manager.remove

        def partial_remove(*args, **kwargs):
            original_remove(*args, **kwargs)
            raise operation_error

        monkeypatch.setattr(manager, "remove", partial_remove)
    with pytest.raises(OSError) as caught:
        manager.install_from_directory(source, "0.1.5", priority=1, force=True)
    assert caught.value is operation_error
    assert tree_state(project_dir) == before
    assert manager.registry.data == registry_before
    assert PresetRegistry(manager.presets_dir).data == registry_before


def test_priority_real_constitution_write_failure_is_atomic(
    project_dir, temp_dir, monkeypatch
):
    helper = PresetArtifactTestHelpers()
    helper._write_init_options(project_dir, ai="claude", ai_skills=False)
    (project_dir / ".claude" / "commands").mkdir(parents=True)
    manager = PresetManager(project_dir)
    install_constitution_sync_preset(manager)
    constitution = make_convention_constitution_preset(temp_dir)
    manager.install_from_directory(constitution, "0.1.5", priority=20)
    winner = helper._create_command_preset(
        temp_dir, "winner", "speckit.demo", "winner", "winner"
    )
    (winner / "templates").mkdir()
    (winner / "templates" / "constitution-template.md").write_text("# Winner\n")
    manager.install_from_directory(winner, "0.1.5", priority=5)
    before = tree_state(project_dir)
    sidecar = project_dir / ".specify" / "memory" / ".constitution-template.json"
    memory = sidecar.parent / "constitution.md"
    original_replace = os.replace
    calls = []

    def fail_sidecar_replace(src, dst, *args, **kwargs):
        if Path(dst) == sidecar:
            calls.append(sidecar)
            # Constitution has really changed before its provenance write fails.
            assert memory.read_text() == "# Convention Constitution\n"
            raise OSError("provenance write denied")
        return original_replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "replace", fail_sidecar_replace)
    monkeypatch.setattr(Path, "cwd", lambda: project_dir)
    result = CliRunner().invoke(
        app, ["preset", "set-priority", "convention-constitution", "1"]
    )
    assert isinstance(result.exception, OSError), result.output
    assert str(result.exception) == "provenance write denied"
    assert calls == [sidecar]
    assert tree_state(project_dir) == before
