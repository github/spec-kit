"""Public JSON contracts for installed preset and extension lists."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli._installed_list_json import _normalized_source
from specify_cli.extensions import ExtensionManager
from specify_cli.presets import PresetManager
from tests.conftest import strip_ansi


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
    source = {"kind": "catalog", "catalog": "speckit-official"}
    manager.registry.add("test-preset", {"version": "1.0.0", "source": source, "priority": 3})

    record = manager.list_installed()[0]
    assert record["template_count"] == 3
    assert record["_json_source"] == source
    assert record["_json_provides"] == {"commands": 1, "templates": 1, "scripts": 1, "hooks": 0}

    monkeypatch.chdir(project)
    payload = _json_result(runner.invoke(app, ["preset", "list", "--json"]))

    assert len(payload) == 1
    item = payload[0]
    assert set(item) == {
        "id", "name", "description", "version", "author", "priority", "enabled", "source", "provides"
    }
    assert item["author"] == "Preset Author"
    assert item["source"] == source
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


def test_catalog_install_producers_persist_structured_source_and_keep_local_default(
    tmp_path, monkeypatch
):
    project = _project(tmp_path)
    source_project = tmp_path / "sources"
    (source_project / ".specify").mkdir(parents=True)
    _preset(source_project, "catalog-preset")
    _preset(source_project, "local-preset")
    _extension(source_project, "catalog-extension")
    _extension(source_project, "local-extension")
    for extension_id in ("catalog-extension", "local-extension"):
        manifest_path = (
            source_project / ".specify" / "extensions" / extension_id / "extension.yml"
        )
        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8").replace(
                "speckit.example-ext.example", f"speckit.{extension_id}.example"
            ),
            encoding="utf-8",
        )

    preset_manager = PresetManager(project)
    preset_manager.install_from_directory(
        source_project / ".specify" / "presets" / "catalog-preset",
        "1.0.0",
        catalog_name="  preset-catalog  ",
    )
    preset_manager.install_from_directory(
        source_project / ".specify" / "presets" / "local-preset",
        "1.0.0",
        catalog_name="  ",
    )

    extension_manager = ExtensionManager(project)
    extension_manager.install_from_directory(
        source_project / ".specify" / "extensions" / "catalog-extension",
        "1.0.0",
        register_commands=False,
        catalog_name="  extension-catalog  ",
    )
    extension_manager.install_from_directory(
        source_project / ".specify" / "extensions" / "local-extension",
        "1.0.0",
        register_commands=False,
        catalog_name="  ",
    )

    assert preset_manager.registry.get("catalog-preset")["source"] == {
        "kind": "catalog",
        "catalog": "preset-catalog",
    }
    assert preset_manager.registry.get("local-preset")["source"] == "local"
    assert extension_manager.registry.get("catalog-extension")["source"] == {
        "kind": "catalog",
        "catalog": "extension-catalog",
    }
    assert extension_manager.registry.get("local-extension")["source"] == "local"

    monkeypatch.chdir(project)
    presets = _json_result(runner.invoke(app, ["preset", "list", "--json"]))
    extensions = _json_result(runner.invoke(app, ["extension", "list", "--json"]))
    assert {item["id"]: item["source"] for item in presets} == {
        "catalog-preset": {"kind": "catalog", "catalog": "preset-catalog"},
        "local-preset": {"kind": "local"},
    }
    assert {item["id"]: item["source"] for item in extensions} == {
        "catalog-extension": {"kind": "catalog", "catalog": "extension-catalog"},
        "local-extension": {"kind": "local"},
    }


def test_preset_json_order_uses_priority_then_id_despite_install_order(tmp_path, monkeypatch):
    project = _project(tmp_path)
    source_project = tmp_path / "sources"
    (source_project / ".specify").mkdir(parents=True)
    for preset_id in ("zebra", "later", "alpha"):
        _preset(source_project, preset_id)

    manager = PresetManager(project)
    manager.install_from_directory(
        source_project / ".specify" / "presets" / "zebra", "1.0.0", priority=5
    )
    manager.install_from_directory(
        source_project / ".specify" / "presets" / "later", "1.0.0", priority=9
    )
    manager.install_from_directory(
        source_project / ".specify" / "presets" / "alpha", "1.0.0", priority=5
    )

    monkeypatch.chdir(project)
    payload = _json_result(runner.invoke(app, ["preset", "list", "--json"]))
    assert [item["id"] for item in payload] == ["alpha", "zebra", "later"]


def test_extension_json_order_uses_priority_then_id_despite_install_order(
    tmp_path, monkeypatch
):
    project = _project(tmp_path)
    source_project = tmp_path / "sources"
    (source_project / ".specify").mkdir(parents=True)
    for extension_id in ("zebra", "later", "alpha"):
        _extension(source_project, extension_id)
        manifest_path = (
            source_project / ".specify" / "extensions" / extension_id / "extension.yml"
        )
        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8").replace(
                "speckit.example-ext.example", f"speckit.{extension_id}.example"
            ),
            encoding="utf-8",
        )

    manager = ExtensionManager(project)
    for extension_id, priority in (("zebra", 5), ("later", 9), ("alpha", 5)):
        manager.install_from_directory(
            source_project / ".specify" / "extensions" / extension_id,
            "1.0.0",
            register_commands=False,
            priority=priority,
        )
    manager.registry.update("zebra", {"enabled": False})

    monkeypatch.chdir(project)
    payload = _json_result(runner.invoke(app, ["extension", "list", "--json"]))

    assert [item["id"] for item in payload] == ["alpha", "zebra", "later"]
    assert payload[1]["enabled"] is False


def test_extension_list_json_is_installed_only_for_available_and_all(tmp_path, monkeypatch):
    project = _project(tmp_path)
    _extension(project, "example-ext")
    source = {"kind": "catalog", "catalog": "speckit-official"}
    ExtensionManager(project).registry.add("example-ext", {"version": "1.0.0", "source": source})

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
    assert item["source"] == source
    assert item["provides"] == {"commands": 1, "templates": 0, "scripts": 0, "hooks": 0}


def test_empty_json_lists_are_successful_arrays(tmp_path, monkeypatch):
    project = _project(tmp_path)
    monkeypatch.chdir(project)

    assert _json_result(runner.invoke(app, ["preset", "list", "--json"])) == []
    assert _json_result(runner.invoke(app, ["extension", "list", "--json"])) == []


@pytest.mark.parametrize("command", ["preset", "extension"])
@pytest.mark.parametrize(
    "args",
    [("--json", "--unknown"), ("--unknown", "--json")],
)
def test_json_usage_errors_are_stderr_only_and_preserve_exit_code(command, args):
    result = runner.invoke(app, [command, "list", *args])

    assert result.exit_code == 2
    assert result.stdout == ""
    assert json.loads(result.stderr) == {"error": "No such option: --unknown"}


@pytest.mark.parametrize(
    ("command", "manager"),
    [("preset", PresetManager), ("extension", ExtensionManager)],
)
def test_json_runtime_errors_are_stderr_only(command, manager, tmp_path, monkeypatch):
    project = _project(tmp_path)
    monkeypatch.chdir(project)
    monkeypatch.setattr(
        manager, "list_installed", lambda _self: (_ for _ in ()).throw(RuntimeError("boom"))
    )

    result = runner.invoke(app, [command, "list", "--json"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == '{"error": "boom"}\n'


@pytest.mark.parametrize("command", ["preset", "extension"])
def test_non_json_usage_errors_keep_human_output(command):
    result = runner.invoke(app, [command, "list", "--unknown"])
    output = strip_ansi(result.output)

    assert result.exit_code == 2
    assert "Usage:" in output
    assert "No such option: --unknown" in output
    assert '{"error":' not in output


@pytest.mark.parametrize("command", ["preset", "extension"])
def test_json_help_remains_human_help(command):
    result = runner.invoke(app, [command, "list", "--json", "--help"])
    output = strip_ansi(result.output)

    assert result.exit_code == 0
    assert "--json" in output
    assert result.stderr == ""


@pytest.mark.parametrize("command", ["preset", "extension"])
def test_jsonish_does_not_enable_json_usage_errors(command):
    result = runner.invoke(app, [command, "list", "--jsonish"])
    output = strip_ansi(result.output)

    assert result.exit_code == 2
    assert "No such option: --jsonish" in output
    assert '{"error":' not in output


def test_preset_list_json_preserves_catalog_source_for_corrupt_records(tmp_path, monkeypatch):
    project = _project(tmp_path)
    source = {"kind": "catalog", "catalog": "speckit-official"}
    PresetManager(project).registry.add("broken-preset", {"version": "1.0.0", "source": source})

    monkeypatch.chdir(project)
    item = _json_result(runner.invoke(app, ["preset", "list", "--json"]))[0]

    assert item["author"] is None
    assert item["source"] == source
    assert item["provides"] == {"commands": 0, "templates": 0, "scripts": 0}


def test_extension_list_json_preserves_catalog_source_for_corrupt_records(tmp_path, monkeypatch):
    project = _project(tmp_path)
    source = {"kind": "catalog", "catalog": "speckit-official"}
    ExtensionManager(project).registry.add("broken-extension", {"version": "1.0.0", "source": source})

    monkeypatch.chdir(project)
    item = _json_result(runner.invoke(app, ["extension", "list", "--json"]))[0]

    assert item["source"] == source
    assert item["provides"] == {"commands": 0, "templates": 0, "scripts": 0, "hooks": 0}


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ({"kind": "local", "catalog": "ignored", "extra": "ignored"}, {"kind": "local"}),
        (
            {"kind": "catalog", "catalog": "speckit-official", "extra": "ignored"},
            {"kind": "catalog", "catalog": "speckit-official"},
        ),
        ([], {"kind": "local"}),
        ({"kind": "catalog"}, {"kind": "local"}),
        ({"kind": "catalog", "catalog": "   "}, {"kind": "local"}),
        ({"kind": "catalog", "catalog": 1}, {"kind": "local"}),
    ],
)
def test_normalized_source_whitelists_valid_shapes_and_falls_back(source, expected):
    assert _normalized_source(source) == expected


def test_installed_list_json_falls_back_for_legacy_unknown_and_malformed_sources(tmp_path, monkeypatch):
    project = _project(tmp_path)
    _preset(project, "legacy-preset")
    _preset(project, "malformed-preset")
    _extension(project, "unknown-ext")
    PresetManager(project).registry.add("legacy-preset", {"version": "1.0.0", "source": "catalog"})
    PresetManager(project).registry.add(
        "malformed-preset", {"version": "1.0.0", "source": {"kind": "catalog", "catalog": []}}
    )
    ExtensionManager(project).registry.add(
        "unknown-ext", {"version": "1.0.0", "source": {"kind": "remote", "catalog": "other"}}
    )

    monkeypatch.chdir(project)
    presets = _json_result(runner.invoke(app, ["preset", "list", "--json"]))
    extension = _json_result(runner.invoke(app, ["extension", "list", "--json"]))[0]

    assert {item["id"]: item["source"] for item in presets} == {
        "legacy-preset": {"kind": "local"},
        "malformed-preset": {"kind": "local"},
    }
    assert extension["source"] == {"kind": "local"}


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
