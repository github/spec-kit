from __future__ import annotations

from specify_cli.extensions import _commands
from specify_cli.presets.command_disable import preset_disable


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


def test_disabling_preset_keeps_registered_command_artifacts(monkeypatch, tmp_path):
    state = {"enabled": True}
    calls = []

    class FakeRegistry:
        def is_installed(self, preset_id):
            return preset_id == "demo"

        def get(self, preset_id):
            return {"enabled": state["enabled"]}

        def update(self, preset_id, updates):
            state.update(updates)

    class FakePresetManager:
        def __init__(self, project_root):
            self.registry = FakeRegistry()

        def reconcile_constitution(self, message):
            calls.append(("constitution", message))

        def _reconcile_composed_commands(self, names):
            calls.append(("commands", names))

        def _reconcile_skills(self, names):
            calls.append(("skills", names))

    monkeypatch.setattr("specify_cli._require_specify_project", lambda: tmp_path)
    monkeypatch.setattr("specify_cli.presets.PresetManager", FakePresetManager)

    preset_disable("demo")

    assert state["enabled"] is False
    assert [call[0] for call in calls] == ["constitution"]
