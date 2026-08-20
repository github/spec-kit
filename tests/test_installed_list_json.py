"""Public JSON contracts for installed preset and extension lists."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import ExtensionManager
from specify_cli.presets import PresetManager


runner = CliRunner()


def _project(tmp_path):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    return project


def _preset(project, preset_id, *, author="Preset Author"):
    preset_dir = project / ".specify" / "presets" / preset_id
    preset_dir.mkdir(parents=True)
    author_line = f'  author: "{author}"\n' if author is not None else ""
    (preset_dir / "preset.yml").write_text(
        "schema_version: \"1.0\"\n"
        "preset:\n"
        f"  id: {preset_id}\n"
        f"  name: {preset_id} name\n"
        "  version: \"1.0.0\"\n"
        "  description: preset description\n"
        f"{author_line}"
        "requires:\n"
        "  speckit_version: \">=0.1.0\"\n"
        "provides:\n"
        "  templates:\n"
        "    - type: template\n"
        "      name: base-template\n"
        "      file: templates/base.md\n"
        "    - type: command\n"
        "      name: speckit.example\n"
        "      file: commands/example.md\n"
        "    - type: script\n"
        "      name: setup-script\n"
        "      file: scripts/setup.py\n",
        encoding="utf-8",
    )


def _extension(project, extension_id, *, author=None):
    extension_dir = project / ".specify" / "extensions" / extension_id
    extension_dir.mkdir(parents=True)
    author_line = f'  author: "{author}"\n' if author is not None else ""
    (extension_dir / "extension.yml").write_text(
        "schema_version: \"1.0\"\n"
        "extension:\n"
        f"  id: {extension_id}\n"
        f"  name: {extension_id} name\n"
        "  version: \"1.0.0\"\n"
        "  description: extension description\n"
        f"{author_line}"
        "requires:\n"
        "  speckit_version: \">=0.1.0\"\n"
        "provides:\n"
        "  commands:\n"
        "    - name: speckit.example-ext.example\n"
        "      file: commands/example.md\n",
        encoding="utf-8",
    )


def _json_result(result):
    assert result.exit_code == 0, result.output
    assert result.stderr == ""
    return json.loads(result.stdout)


def test_preset_list_json_uses_canonical_wire_object_and_keeps_flat_manager_keys(tmp_path, monkeypatch):
    project = _project(tmp_path)
    _preset(project, "test-preset")
    manager = PresetManager(project)
    manager.registry.add("test-preset", {"version": "1.0.0", "source": "catalog", "priority": 3})

    record = manager.list_installed()[0]
    assert record["template_count"] == 3
    assert record["_json_provides"] == {"commands": 1, "templates": 1, "scripts": 1, "hooks": 0}

    monkeypatch.chdir(project)
    payload = _json_result(runner.invoke(app, ["preset", "list", "--json"]))

    assert len(payload) == 1
    item = payload[0]
    assert set(item) == {
        "id", "name", "description", "version", "author", "priority", "enabled", "source", "provides"
    }
    assert item["author"] == "Preset Author"
    assert item["source"] == {"kind": "catalog"}
    assert item["provides"] == {"commands": 1, "templates": 1, "scripts": 1}
    assert "hooks" not in item["provides"]


def test_preset_list_json_defaults_legacy_source_and_author(tmp_path, monkeypatch):
    project = _project(tmp_path)
    _preset(project, "legacy-preset", author=None)
    PresetManager(project).registry.add("legacy-preset", {"version": "1.0.0"})

    monkeypatch.chdir(project)
    item = _json_result(runner.invoke(app, ["preset", "list", "--json"]))[0]

    assert item["author"] is None
    assert item["source"] == {"kind": "local"}


def test_extension_list_json_is_installed_only_for_available_and_all(tmp_path, monkeypatch):
    project = _project(tmp_path)
    _extension(project, "example-ext")
    ExtensionManager(project).registry.add("example-ext", {"version": "1.0.0", "source": "unknown"})

    monkeypatch.chdir(project)
    expected = _json_result(runner.invoke(app, ["extension", "list", "--json"]))
    available = _json_result(runner.invoke(app, ["extension", "list", "--json", "--available"]))
    all_extensions = _json_result(runner.invoke(app, ["extension", "list", "--json", "--all"]))

    assert available == expected == all_extensions
    item = expected[0]
    assert set(item) == {
        "id", "name", "description", "version", "author", "priority", "enabled", "source", "provides"
    }
    assert item["author"] is None
    assert item["source"] == {"kind": "local"}
    assert item["provides"] == {"commands": 1, "templates": 0, "scripts": 0, "hooks": 0}


def test_empty_json_lists_are_successful_arrays(tmp_path, monkeypatch):
    project = _project(tmp_path)
    monkeypatch.chdir(project)

    assert _json_result(runner.invoke(app, ["preset", "list", "--json"])) == []
    assert _json_result(runner.invoke(app, ["extension", "list", "--json"])) == []


def test_preset_list_json_degrades_corrupt_records_and_malformed_sources(tmp_path, monkeypatch):
    project = _project(tmp_path)
    PresetManager(project).registry.add("broken-preset", {"version": "1.0.0", "source": []})

    monkeypatch.chdir(project)
    item = _json_result(runner.invoke(app, ["preset", "list", "--json"]))[0]

    assert item["author"] is None
    assert item["source"] == {"kind": "local"}
    assert item["provides"] == {"commands": 0, "templates": 0, "scripts": 0}


def test_extension_json_counts_multiple_hooks_for_one_event(tmp_path, monkeypatch):
    project = _project(tmp_path)
    extension_dir = project / ".specify" / "extensions" / "multi-hook"
    extension_dir.mkdir(parents=True)
    (extension_dir / "extension.yml").write_text(
        "schema_version: \"1.0\"\n"
        "extension:\n"
        "  id: multi-hook\n"
        "  name: Multi Hook\n"
        "  version: \"1.0.0\"\n"
        "  description: Multiple hooks on one event\n"
        "requires:\n"
        "  speckit_version: \">=0.1.0\"\n"
        "provides:\n"
        "  commands:\n"
        "    - name: speckit.multi-hook.one\n"
        "      file: commands/one.md\n"
        "hooks:\n"
        "  after_plan:\n"
        "    - command: speckit.multi-hook.one\n"
        "    - command: speckit.multi-hook.two\n",
        encoding="utf-8",
    )
    manager = ExtensionManager(project)
    manager.registry.add("multi-hook", {"version": "1.0.0"})

    assert manager.list_installed()[0]["hook_count"] == 1

    monkeypatch.chdir(project)
    item = _json_result(runner.invoke(app, ["extension", "list", "--json"]))[0]

    assert item["provides"]["hooks"] == 2


def test_text_list_rendering_retains_legacy_flat_counts(tmp_path, monkeypatch):
    project = _project(tmp_path)
    _preset(project, "text-preset")
    PresetManager(project).registry.add("text-preset", {"version": "1.0.0"})
    _extension(project, "example-ext")
    ExtensionManager(project).registry.add("example-ext", {"version": "1.0.0"})

    monkeypatch.chdir(project)
    preset_result = runner.invoke(app, ["preset", "list"])
    extension_result = runner.invoke(app, ["extension", "list"])

    assert preset_result.exit_code == extension_result.exit_code == 0
    assert "Templates: 3" in preset_result.stdout
    assert "Commands: 1 | Hooks: 0" in extension_result.stdout


def test_preset_json_project_resolution_error_is_stderr_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["preset", "list", "--json"])

    assert result.exit_code != 0
    assert result.stdout == ""
    assert json.loads(result.stderr) == {"error": "Not a Spec Kit project (no .specify/ directory)"}


def test_extension_json_runtime_error_is_stderr_only(tmp_path, monkeypatch):
    project = _project(tmp_path)
    monkeypatch.chdir(project)

    def fail_list(_self):
        raise RuntimeError("list failed")

    monkeypatch.setattr(ExtensionManager, "list_installed", fail_list)
    result = runner.invoke(app, ["extension", "list", "--json"])

    assert result.exit_code != 0
    assert result.stdout == ""
    assert json.loads(result.stderr) == {"error": "list failed"}
