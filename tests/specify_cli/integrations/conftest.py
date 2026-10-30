"""Shared fixtures for mirrored integration command tests."""

import pytest

from tests.specify_cli.integrations._helpers import _copy_project_template, _init_project


@pytest.fixture(scope="module")
def status_copilot_template(tmp_path_factory):
    return _init_project(tmp_path_factory.mktemp("status-copilot"), "copilot")

@pytest.fixture(scope="module")
def status_claude_template(tmp_path_factory):
    return _init_project(tmp_path_factory.mktemp("status-claude"), "claude")

@pytest.fixture
def copilot_project(tmp_path, status_copilot_template):
    return _copy_project_template(tmp_path, status_copilot_template)

@pytest.fixture
def claude_project(tmp_path, status_claude_template):
    return _copy_project_template(tmp_path, status_claude_template)


@pytest.fixture
def tasks_preset_src(tmp_path):
    preset = tmp_path / "tasks-preset"
    (preset / "commands").mkdir(parents=True)
    (preset / "commands/speckit.tasks.md").write_bytes(
        b"---\ndescription: Tasks override\n---\nPreset tasks body\n"
    )
    (preset / "preset.yml").write_bytes(b"""schema_version: '1.0'
preset: {id: tasks-preset, name: Tasks Preset, version: 1.0.0, description: x}
requires: {speckit_version: '>=0.1.0'}
provides:
  templates:
  - {type: command, name: speckit.tasks, file: commands/speckit.tasks.md}
""")
    return preset
