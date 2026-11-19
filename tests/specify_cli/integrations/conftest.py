"""Shared fixtures for mirrored integration command tests."""

import shutil

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


@pytest.fixture
def packaged_scripts_0644(tmp_path_factory, monkeypatch):
    """Serve the shared scripts from a copy with every file at 0644.

    That is how the wheel ships them, so the execute-bit tests fail without the
    fix whatever modes the checkout running the tests has.
    """
    from specify_cli import shared_infra

    real_source = shared_infra.shared_scripts_source
    copy = tmp_path_factory.mktemp("packaged-scripts") / "scripts"

    def source(*, core_pack, repo_root):
        if not copy.exists():
            shutil.copytree(real_source(core_pack=core_pack, repo_root=repo_root), copy)
            for path in copy.rglob("*"):
                if path.is_file():
                    path.chmod(0o644)
        return copy

    monkeypatch.setattr(shared_infra, "shared_scripts_source", source)
    return copy
