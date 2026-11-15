"""Public JSON contracts for installed preset and extension info."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import ExtensionManager
from specify_cli.presets import PresetManager


runner = CliRunner()

SOURCE = {"kind": "catalog", "catalog": "speckit-official"}
# provenance of each contribution, as in #4213; SOURCE is where the pack was installed from
PRESET_SOURCE = {"layer": "preset", "presetId": "info-preset"}
EXTENSION_SOURCE = {"layer": "extension", "extensionId": "info-ext"}


def _project(tmp_path):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    return project


def _preset(project, preset_id="info-preset"):
    preset_dir = project / ".specify" / "presets" / preset_id
    preset_dir.mkdir(parents=True)
    (preset_dir / "preset.yml").write_text(
        "schema_version: \"1.0\"\n"
        "preset:\n"
        f"  id: {preset_id}\n"
        "  name: Info Preset\n"
        "  version: \"1.0.0\"\n"
        "  description: preset description\n"
        "  author: Preset Author\n"
        "requires:\n"
        "  speckit_version: \">=0.1.0\"\n"
        "provides:\n"
        "  templates:\n"
        "    - type: command\n"
        "      name: speckit.plan\n"
        "      file: commands/plan.md\n"
        "      description: Wrapped plan\n"
        "      strategy: WRAP\n"
        "    - type: template\n"
        "      name: spec-template\n"
        "      file: templates/spec.md\n"
        "    - type: script\n"
        "      name: setup-plan\n"
        "      file: scripts/setup-plan.sh\n"
        "      strategy: wrap\n",
        encoding="utf-8",
    )
    PresetManager(project).registry.add(
        preset_id, {"version": "1.0.0", "source": SOURCE, "priority": 3}
    )


def _extension(project, extension_id="info-ext"):
    extension_dir = project / ".specify" / "extensions" / extension_id
    extension_dir.mkdir(parents=True)
    (extension_dir / "extension.yml").write_text(
        "schema_version: \"1.0\"\n"
        "extension:\n"
        f"  id: {extension_id}\n"
        "  name: Info Extension\n"
        "  version: \"1.0.0\"\n"
        "  description: extension description\n"
        "requires:\n"
        "  speckit_version: \">=0.1.0\"\n"
        "provides:\n"
        "  commands:\n"
        f"    - name: speckit.{extension_id}.check\n"
        "      file: commands/check.md\n"
        "      description: Run the check\n"
        "  templates:\n"
        "    - name: report\n"
        "      file: templates/report.md\n"
        "  scripts:\n"
        "    - name: collect\n"
        "      file: scripts/collect.sh\n"
        "      runtimes: [bash, python]\n"
        "    - name: notify\n"
        "      file: scripts/notify.sh\n"
        "hooks:\n"
        "  before_plan:\n"
        f"    command: speckit.{extension_id}.check\n"
        "  after_tasks:\n"
        f"    - command: speckit.{extension_id}.check\n"
        "      priority: 5\n"
        "      optional: false\n"
        f"    - command: speckit.{extension_id}.check\n"
        "      priority: 20\n"
        "    - command: speckit.tasks\n"
        "      optional: false\n",
        encoding="utf-8",
    )
    ExtensionManager(project).registry.add(
        extension_id, {"version": "1.0.0", "source": SOURCE, "priority": 4}
    )


def _json_result(result):
    assert result.exit_code == 0, result.output
    assert result.stderr == ""
    return json.loads(result.stdout)


def _without_provides(item):
    return {key: value for key, value in item.items() if key != "provides"}


def test_preset_info_json_expands_the_list_item(tmp_path, monkeypatch):
    project = _project(tmp_path)
    _preset(project)
    monkeypatch.chdir(project)

    listed = _json_result(runner.invoke(app, ["preset", "list", "--json"]))[0]
    info = _json_result(runner.invoke(app, ["preset", "info", "info-preset", "--json"]))

    assert set(info) == set(_without_provides(listed)) | {"commands", "templates", "scripts"}
    assert {key: info[key] for key in _without_provides(listed)} == _without_provides(listed)
    assert info["source"] == SOURCE
    assert info["commands"] == [
        {
            "name": "speckit.plan",
            "description": "Wrapped plan",
            "source": PRESET_SOURCE,
            "sourcePath": "commands/plan.md",
            "strategy": "wrap",
        }
    ]
    assert info["templates"] == [
        {
            "name": "spec-template",
            "description": "",
            "source": PRESET_SOURCE,
            "sourcePath": "templates/spec.md",
            "strategy": "replace",
        }
    ]
    assert info["scripts"] == [
        {
            "name": "setup-plan",
            "description": "",
            "source": PRESET_SOURCE,
            "sourcePath": "scripts/setup-plan.sh",
            "strategy": "wrap",
        }
    ]



def test_preset_info_json_gives_an_empty_description_as_a_string(tmp_path, monkeypatch):
    # ``description:`` with no value reads as None; the preset manifest accepts it
    project = _project(tmp_path)
    _preset(project)
    manifest = project / ".specify" / "presets" / "info-preset" / "preset.yml"
    text = manifest.read_text(encoding="utf-8")
    manifest.write_text(text.replace("      description: Wrapped plan\n", "      description:\n"), encoding="utf-8")
    monkeypatch.chdir(project)

    info = _json_result(runner.invoke(app, ["preset", "info", "info-preset", "--json"]))

    assert info["commands"][0]["description"] == ""


def test_a_direct_call_to_preset_info_keeps_the_human_readable_view(tmp_path, monkeypatch, capsys):
    from specify_cli.presets.command_info import preset_info

    project = _project(tmp_path)
    _preset(project)
    monkeypatch.chdir(project)

    preset_info("info-preset")

    out = capsys.readouterr().out
    assert "Preset: Info Preset" in out
    with pytest.raises(json.JSONDecodeError):
        json.loads(out)

def test_extension_info_json_expands_the_list_item(tmp_path, monkeypatch):
    project = _project(tmp_path)
    _extension(project)
    monkeypatch.chdir(project)

    listed = _json_result(runner.invoke(app, ["extension", "list", "--json"]))[0]
    info = _json_result(runner.invoke(app, ["extension", "info", "info-ext", "--json"]))

    assert set(info) == set(_without_provides(listed)) | {
        "commands", "templates", "scripts", "hooks"
    }
    assert {key: info[key] for key in _without_provides(listed)} == _without_provides(listed)
    assert info["commands"] == [
        {
            "name": "speckit.info-ext.check",
            "description": "Run the check",
            "source": EXTENSION_SOURCE,
            "sourcePath": "commands/check.md",
        }
    ]
    assert info["templates"] == [
        {"name": "report", "description": "", "source": EXTENSION_SOURCE, "sourcePath": "templates/report.md"}
    ]
    assert info["scripts"] == [
        {
            "name": "collect",
            "description": "",
            "source": EXTENSION_SOURCE,
            "sourcePath": "scripts/collect.sh",
            "runtimes": ["bash", "python"],
        },
        {"name": "notify", "description": "", "source": EXTENSION_SOURCE, "sourcePath": "scripts/notify.sh"},
    ]


def test_extension_info_json_hooks_use_registration_defaults_and_last_declaration(
    tmp_path, monkeypatch
):
    project = _project(tmp_path)
    _extension(project)
    monkeypatch.chdir(project)

    info = _json_result(runner.invoke(app, ["extension", "info", "info-ext", "--json"]))

    assert info["hooks"] == [
        {
            "trigger": "before_plan",
            "targetCommand": "speckit.info-ext.check",
            "optional": True,
            "priority": 10,
        },
        {
            "trigger": "after_tasks",
            "targetCommand": "speckit.info-ext.check",
            "optional": True,
            "priority": 20,
        },
        {
            "trigger": "after_tasks",
            "targetCommand": "speckit.tasks",
            "optional": False,
            "priority": 10,
        },
    ]


def test_extension_info_json_resolves_a_unique_display_name(tmp_path, monkeypatch):
    project = _project(tmp_path)
    _extension(project)
    monkeypatch.chdir(project)

    info = _json_result(runner.invoke(app, ["extension", "info", "info extension", "--json"]))

    assert info["id"] == "info-ext"


def test_extension_info_json_rejects_an_ambiguous_display_name(tmp_path, monkeypatch):
    project = _project(tmp_path)
    _extension(project, "info-ext")
    _extension(project, "other-ext")
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["extension", "info", "Info Extension", "--json"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert json.loads(result.stderr) == {
        "error": "Extension name 'Info Extension' is ambiguous; use one of the IDs: info-ext, other-ext"
    }


@pytest.mark.parametrize(("command", "kind"), [("preset", "Preset"), ("extension", "Extension")])
def test_info_json_for_a_pack_that_is_not_installed_is_stderr_only(
    command, kind, tmp_path, monkeypatch
):
    monkeypatch.chdir(_project(tmp_path))

    result = runner.invoke(app, [command, "info", "missing", "--json"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert json.loads(result.stderr) == {"error": f"{kind} 'missing' is not installed"}


@pytest.mark.parametrize("command", ["preset", "extension"])
def test_info_json_outside_a_project_is_stderr_only(command, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, [command, "info", "anything", "--json"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert json.loads(result.stderr)["error"].startswith("Not a Spec Kit project")


@pytest.mark.parametrize(
    ("command", "parameter"), [("preset", "preset_id"), ("extension", "extension")]
)
def test_info_json_usage_errors_are_stderr_only(command, parameter):
    result = runner.invoke(app, [command, "info", "--json"])

    assert result.exit_code == 2
    assert result.stdout == ""
    assert json.loads(result.stderr) == {"error": f"Missing parameter: {parameter}"}


def test_preset_info_json_cannot_be_combined_with_versions(tmp_path, monkeypatch):
    project = _project(tmp_path)
    _preset(project)
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["preset", "info", "info-preset", "--json", "--versions"])

    assert result.exit_code == 2
    assert result.stdout == ""
    assert result.stderr == '{"error": "--json cannot be combined with --versions"}\n'


def test_extension_info_json_cannot_be_combined_with_versions(tmp_path, monkeypatch):
    project = _project(tmp_path)
    _extension(project)
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["extension", "info", "info-ext", "--json", "--versions"])

    assert result.exit_code == 2
    assert result.stdout == ""
    assert result.stderr == '{"error": "--json cannot be combined with --versions"}\n'
