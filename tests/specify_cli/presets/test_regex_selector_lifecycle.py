from __future__ import annotations

import json
from pathlib import Path

import yaml

from specify_cli.extensions import _commands
from specify_cli.presets import PresetManager
from specify_cli.presets.command_disable import preset_disable


def _write_preset(
    root: Path, preset_id: str, declarations: list[dict], files: dict[str, str]
) -> Path:
    preset = root / preset_id
    preset.mkdir(parents=True)
    for relative, content in files.items():
        target = preset / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    (preset / "preset.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "preset": {
                    "id": preset_id,
                    "name": preset_id,
                    "version": "1.0.0",
                    "description": "test",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {"templates": declarations},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return preset


def _write_core(project: Path, name: str, text: str = "Core body") -> None:
    target = (
        project
        / ".specify"
        / "templates"
        / "commands"
        / f"{name.rsplit('.', 1)[-1]}.md"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"---\ndescription: core\n---\n{text}\n", encoding="utf-8")


def _active_claude(project: Path) -> None:
    options = project / ".specify" / "init-options.json"
    options.parent.mkdir(parents=True, exist_ok=True)
    options.write_text(
        json.dumps({"ai": "claude", "ai_skills": True}), encoding="utf-8"
    )
    (project / ".claude" / "skills").mkdir(parents=True, exist_ok=True)


def test_extension_change_refresh_targets_only_active_integration(
    monkeypatch, tmp_path
):
    calls = []

    class FakePresetManager:
        def __init__(self, project_root):
            assert project_root == tmp_path

        def register_enabled_presets_for_agent(self, agent):
            calls.append(agent)

    monkeypatch.setattr(
        "specify_cli._init_options.load_init_options",
        lambda project_root: {"ai": "active-agent"},
    )
    monkeypatch.setattr("specify_cli.presets.PresetManager", FakePresetManager)

    _commands._refresh_presets_and_warn(tmp_path)

    assert calls == ["active-agent"]


def test_extension_change_refresh_skips_when_no_integration_selected(
    monkeypatch, tmp_path
):
    class UnexpectedPresetManager:
        def __init__(self, project_root):
            raise AssertionError("should not construct without an active agent")

    monkeypatch.setattr(
        "specify_cli._init_options.load_init_options", lambda project_root: {}
    )
    monkeypatch.setattr("specify_cli.presets.PresetManager", UnexpectedPresetManager)

    _commands._refresh_presets_and_warn(tmp_path)


def test_disabling_preset_reconciles_registered_artifacts(monkeypatch, tmp_path):
    state = {"enabled": True}
    calls = []

    class FakeRegistry:
        def list_by_priority(self, include_disabled=False):
            return [("demo", {"enabled": state["enabled"]})]

        def is_installed(self, preset_id):
            return preset_id == "demo"

        def get(self, preset_id):
            return {"enabled": state["enabled"], "registered_commands": {}}

        def update(self, preset_id, updates):
            state.update(updates)
            calls.append(("registry", updates))

    class FakePresetManager:
        def __init__(self, project_root):
            self.registry = FakeRegistry()

        def _collect_selector_command_names(self, resolver):
            return {"speckit.plan"}

        def _expand_command_selectors(self, resolver, preset_dir, declarations):
            return declarations

        @property
        def presets_dir(self):
            return tmp_path / ".specify" / "presets"

        def _skill_names_for_command(self, command_name):
            return [command_name.replace(".", "-")]

        def _reconcile_composed_commands(self, names):
            calls.append(("commands", names))

        def _reconcile_skills(self, names):
            calls.append(("skills", names))

        def reconcile_constitution(self, message):
            calls.append(("constitution", message))

    monkeypatch.setattr("specify_cli._require_specify_project", lambda: tmp_path)
    monkeypatch.setattr("specify_cli.presets.PresetManager", FakePresetManager)

    preset_disable("demo")

    assert state["enabled"] is False
    assert calls[0][0] == "commands"
    assert ("commands", ["speckit.plan"]) in calls
    assert ("skills", ["speckit.plan"]) in calls
    assert calls[-1][0] == "constitution"


def _run_preset_command(project: Path, *args: str) -> None:
    from unittest.mock import patch
    from typer.testing import CliRunner
    from specify_cli import app

    with patch("specify_cli._require_specify_project", return_value=project):
        result = CliRunner().invoke(app, ["preset", *args])
    assert result.exit_code == 0, result.output


def test_regex_selector_disable_and_reenable_materializes_real_artifacts(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    _active_claude(project)
    _write_core(project, "speckit.plan")
    source = _write_preset(
        tmp_path,
        "regex-owner",
        [
            {
                "type": "command",
                "name": r"regex:^speckit\.plan$",
                "file": "commands/plan.md",
                "description": "selector plan",
            }
        ],
        {"commands/plan.md": "---\ndescription: selector plan\n---\nSelector body\n"},
    )
    # Native-skill agents restore their core layer from this local file on disable.
    core_file = project / ".specify" / "templates" / "commands" / "plan.md"
    core_file.parent.mkdir(parents=True, exist_ok=True)
    core_file.write_text(
        "---\ndescription: core plan\n---\nCore body\n", encoding="utf-8"
    )
    manager = PresetManager(project)
    manager.install_from_directory(source, "0.1.5")
    skill = project / ".claude" / "skills" / "speckit-plan" / "SKILL.md"
    assert skill.exists() and "Selector body" in skill.read_text(encoding="utf-8")
    metadata = manager.registry.get("regex-owner")
    assert "speckit.plan" in metadata["registered_commands"]["claude"]
    assert "speckit-plan" in metadata["registered_skills"]["claude"]
    assert all(
        "regex:" not in name for name in metadata["registered_commands"]["claude"]
    )
    assert all("regex:" not in name for name in metadata["registered_skills"]["claude"])

    _run_preset_command(project, "disable", "regex-owner")
    assert "Core body" in skill.read_text(encoding="utf-8")
    assert "Selector body" not in skill.read_text(encoding="utf-8")
    metadata = PresetManager(project).registry.get("regex-owner")
    assert not metadata.get("registered_commands", {}).get("claude")
    assert not metadata.get("registered_skills", {}).get("claude")

    _run_preset_command(project, "enable", "regex-owner")
    assert skill.exists()
    metadata = PresetManager(project).registry.get("regex-owner")
    assert "speckit.plan" in metadata["registered_commands"]["claude"]
    assert "speckit-plan" in metadata["registered_skills"]["claude"]


def test_regex_composition_is_concretely_tracked_and_removed(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    _active_claude(project)
    _write_core(project, "speckit.plan")
    exact = _write_preset(
        tmp_path,
        "exact-owner",
        [
            {
                "type": "command",
                "name": "speckit.plan",
                "file": "commands/plan.md",
                "description": "exact",
            }
        ],
        {"commands/plan.md": "---\ndescription: exact\n---\nExact body\n"},
    )
    regex = _write_preset(
        tmp_path,
        "regex-compose",
        [
            {
                "type": "command",
                "name": r"regex:^speckit\.plan$",
                "file": "commands/plan.md",
                "description": "regex composed",
                "strategy": "append",
                "aliases": ["plan-alias"],
            }
        ],
        {
            "commands/plan.md": "---\ndescription: regex composed\nstrategy: append\n---\nRegex addition\n"
        },
    )
    manager = PresetManager(project)
    manager.install_from_directory(exact, "0.1.5", priority=20)
    manager.install_from_directory(regex, "0.1.5", priority=10)
    skill = project / ".claude" / "skills" / "speckit-plan" / "SKILL.md"
    assert skill.exists()
    assert "Exact body" in skill.read_text(encoding="utf-8")
    assert "Regex addition" in skill.read_text(encoding="utf-8")
    metadata = manager.registry.get("regex-compose")
    assert "speckit.plan" in metadata["registered_commands"]["claude"]
    assert "speckit-plan" in metadata["registered_skills"]["claude"]
    assert all(
        "regex:" not in name for name in metadata["registered_commands"]["claude"]
    )
    _run_preset_command(project, "set-priority", "regex-compose", "30")
    assert "Regex addition" not in skill.read_text(encoding="utf-8")
    _run_preset_command(project, "set-priority", "regex-compose", "10")
    assert "Regex addition" in skill.read_text(encoding="utf-8")
    assert manager.remove("regex-compose") is True
    assert skill.exists()
    assert "Regex addition" not in skill.read_text(encoding="utf-8")
