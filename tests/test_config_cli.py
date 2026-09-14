"""Behavior tests for post-initialization project configuration."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from specify_cli import app, load_init_options, save_init_options


runner = CliRunner()


def _project(tmp_path):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    save_init_options(
        project,
        {
            "ai": "codex",
            "feature_numbering": "sequential",
            "script": "sh",
            "speckit_version": "0.0.0-test",
        },
    )
    return project


def test_config_list_shows_initialization_settings(tmp_path, monkeypatch):
    project = _project(tmp_path)
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["config", "list"])

    assert result.exit_code == 0, result.output
    assert "feature-numbering" in result.output
    assert "sequential" in result.output
    assert "script" in result.output
    assert "sh" in result.output


def test_config_list_json_includes_options_and_extensions(tmp_path, monkeypatch):
    project = _project(tmp_path)
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["config", "list", "--json"])

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        "extensions": [],
        "init": load_init_options(project),
    }


def test_config_get_reads_a_persisted_setting(tmp_path, monkeypatch):
    project = _project(tmp_path)
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["config", "get", "feature-numbering"])

    assert result.exit_code == 0, result.output
    assert result.output.strip() == "sequential"


def test_config_set_feature_numbering_persists_a_supported_value(tmp_path, monkeypatch):
    project = _project(tmp_path)
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["config", "set", "feature-numbering", "timestamp"])

    assert result.exit_code == 0, result.output
    assert load_init_options(project)["feature_numbering"] == "timestamp"


@pytest.mark.parametrize("value", ["", "daily", "sequentially"])
def test_config_set_feature_numbering_rejects_unsupported_values(
    tmp_path, monkeypatch, value
):
    project = _project(tmp_path)
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["config", "set", "feature-numbering", value])

    assert result.exit_code != 0
    assert "sequential, timestamp" in result.output
    assert load_init_options(project)["feature_numbering"] == "sequential"


@pytest.mark.parametrize(
    ("key", "value", "guidance"),
    [
        ("script", "py", "specify integration upgrade"),
        ("ai", "claude", "specify integration use claude"),
        ("ai-skills", "true", "--integration-options"),
    ],
)
def test_config_routes_owned_settings_to_their_owning_command(
    tmp_path, monkeypatch, key, value, guidance
):
    project = _project(tmp_path)
    monkeypatch.chdir(project)
    before = load_init_options(project)

    result = runner.invoke(app, ["config", "set", key, value])

    assert result.exit_code != 0
    assert guidance in result.output
    assert load_init_options(project) == before


@pytest.mark.parametrize("key", ["here", "speckit-version"])
def test_config_rejects_read_only_metadata(tmp_path, monkeypatch, key):
    project = _project(tmp_path)
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["config", "set", key, "anything"])

    assert result.exit_code != 0
    assert "read-only" in result.output


def test_config_extension_reuses_extension_lifecycle_commands(tmp_path, monkeypatch):
    project = _project(tmp_path)
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["config", "extension", "list"])

    assert result.exit_code == 0, result.output
    assert "No extensions installed" in result.output


@pytest.mark.parametrize("contents", [b'{"ai": "copilot",}', b'[]', b'null', b'\xff'])
def test_config_set_preserves_invalid_existing_configuration(tmp_path, monkeypatch, contents):
    project = _project(tmp_path)
    monkeypatch.chdir(project)
    options_file = project / ".specify/init-options.json"
    options_file.write_bytes(contents)

    result = runner.invoke(app, ["config", "set", "feature-numbering", "timestamp"])

    assert result.exit_code != 0
    assert "init-options.json" in result.output
    assert options_file.read_bytes() == contents


def test_config_set_preserves_other_settings(tmp_path, monkeypatch):
    project = _project(tmp_path)
    monkeypatch.chdir(project)
    before = load_init_options(project)

    result = runner.invoke(app, ["config", "set", "feature-numbering", "timestamp"])

    assert result.exit_code == 0, result.output
    assert load_init_options(project) == {**before, "feature_numbering": "timestamp"}


def test_config_set_supports_legacy_project_without_options(tmp_path, monkeypatch):
    (tmp_path / ".specify").mkdir()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["config", "set", "feature-numbering", "timestamp"])

    assert result.exit_code == 0, result.output
    assert load_init_options(tmp_path) == {"feature_numbering": "timestamp"}
