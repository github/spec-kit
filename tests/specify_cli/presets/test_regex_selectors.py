from __future__ import annotations

import json

import pytest
import yaml

from specify_cli.extensions import CORE_COMMAND_NAMES, ExtensionRegistry
from specify_cli.presets import (
    PresetManager,
    PresetManifest,
    PresetRegistry,
    PresetResolver,
    PresetValidationError,
)
from specify_cli.presets._selectors import selector_matches


def _manifest(
    name: str, resource_type: str = "template", strategy: str = "replace"
) -> dict:
    return {
        "schema_version": "1.0",
        "preset": {
            "id": "preset",
            "name": "Preset",
            "version": "1.0.0",
            "description": "test",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {
            "templates": [
                {
                    "type": resource_type,
                    "name": name,
                    "file": "payload.md" if resource_type != "script" else "payload.sh",
                    "strategy": strategy,
                }
            ]
        },
    }


def _write_preset(
    project,
    preset_id: str,
    name: str,
    *,
    priority: int,
    strategy: str = "replace",
    resource_type: str = "template",
    body: str = "overlay\n",
):
    root = project / ".specify" / "presets" / preset_id
    root.mkdir(parents=True, exist_ok=True)
    data = _manifest(name, resource_type, strategy)
    data["preset"]["id"] = preset_id
    filename = data["provides"]["templates"][0]["file"]
    (root / filename).write_text(body, encoding="utf-8")
    (root / "preset.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    PresetRegistry(project / ".specify" / "presets").add(
        preset_id, {"enabled": True, "priority": priority, "version": "1.0.0"}
    )
    return root


def test_command_regex_expands_core_commands_to_exact_names(project_dir):
    selector_pack = _write_preset(
        project_dir,
        "command-selector",
        r"regex:^speckit\.(plan|tasks)$",
        priority=1,
        resource_type="command",
    )
    manager = PresetManager(project_dir)
    manifest = PresetManifest(selector_pack / "preset.yml")
    expanded = manager._expand_command_selectors(
        PresetResolver(project_dir), selector_pack, manifest.templates
    )
    names = {entry["name"] for entry in expanded}
    expected = {f"speckit.{name}" for name in CORE_COMMAND_NAMES}
    assert names == expected & {"speckit.plan", "speckit.tasks"}


def test_command_regex_expands_extension_command(project_dir):
    ext = project_dir / ".specify" / "extensions" / "demo"
    (ext / "commands").mkdir(parents=True)
    (ext / "commands" / "speckit.demo.md").write_text(
        "extension command\\n", encoding="utf-8"
    )
    _write_preset(
        project_dir,
        "command-selector",
        r"regex:^speckit\.demo$",
        priority=1,
        resource_type="command",
    )
    ExtensionRegistry(project_dir / ".specify" / "extensions").add(
        "demo", {"enabled": True, "priority": 10, "version": "1.0"}
    )
    pack = project_dir / ".specify" / "presets" / "command-selector"
    manager = PresetManager(project_dir)
    manifest = PresetManifest(pack / "preset.yml")
    expanded = manager._expand_command_selectors(
        PresetResolver(project_dir), pack, manifest.templates
    )
    assert [entry["name"] for entry in expanded] == ["speckit.demo"]


def test_command_regex_expands_lower_preset_and_excludes_own_or_higher(project_dir):
    lower = project_dir / ".specify" / "presets" / "lower"
    lower.mkdir(parents=True)
    (lower / "commands").mkdir()
    (lower / "payload.md").write_text("base\n", encoding="utf-8")
    lower_data = _manifest("speckit.lower", "command")
    lower_data["preset"]["id"] = "lower"
    lower_data["provides"]["templates"][0]["file"] = "payload.md"
    (lower / "preset.yml").write_text(yaml.safe_dump(lower_data), encoding="utf-8")
    PresetRegistry(project_dir / ".specify" / "presets").add(
        "lower", {"enabled": True, "priority": 10, "version": "1.0"}
    )
    selector_pack = _write_preset(
        project_dir,
        "selector",
        r"regex:^speckit\.lower$",
        priority=1,
        resource_type="command",
    )
    manager = PresetManager(project_dir)
    manifest = PresetManifest(selector_pack / "preset.yml")
    expanded = manager._expand_command_selectors(
        PresetResolver(project_dir), selector_pack, manifest.templates
    )
    assert [entry["name"] for entry in expanded] == ["speckit.lower"]


def test_command_regex_and_regex_overlap_preserves_both_entries(project_dir):
    selector_pack = _write_preset(
        project_dir,
        "double-selector",
        r"regex:^speckit\.plan$",
        priority=1,
        resource_type="command",
    )
    second = {"type": "command", "name": r"regex:^speckit\.plan$", "file": "payload.md"}
    manager = PresetManager(project_dir)
    manifest = PresetManifest(selector_pack / "preset.yml")
    expanded = manager._expand_command_selectors(
        PresetResolver(project_dir), selector_pack, [*manifest.templates, second]
    )
    assert [entry["name"] for entry in expanded] == ["speckit.plan", "speckit.plan"]


def test_command_regex_registration_tracks_and_cleans_only_concrete_names(project_dir):
    (
        project_dir / ".specify" / "templates" / "commands" / "speckit.plan.md"
    ).write_text("# Plan\n", encoding="utf-8")
    (
        project_dir / ".specify" / "templates" / "commands" / "speckit.tasks.md"
    ).write_text("# Tasks\n", encoding="utf-8")
    commands_dir = project_dir / ".agents" / "commands"
    commands_dir.mkdir(parents=True)
    (project_dir / ".specify" / "init-options.json").write_text(
        json.dumps({"ai": "amp", "ai_skills": False, "script": "sh"}),
        encoding="utf-8",
    )
    source_dir = project_dir / "selector-source"
    source_dir.mkdir()
    source = _write_preset(
        source_dir,
        "command-selector",
        r"regex:^speckit\.(plan|tasks)$",
        priority=10,
        resource_type="command",
    )
    # Core discovery in this isolated project uses the packaged command inventory.
    manager = PresetManager(project_dir)
    source = source_dir / ".specify" / "presets" / "command-selector"
    manifest = manager.install_from_directory(source, "0.1.0")
    metadata = manager.registry.get(manifest.id)
    registered = metadata["registered_commands"]
    tracked = {name for names in registered.values() for name in names}
    expected = {f"speckit.{name}" for name in CORE_COMMAND_NAMES} & {
        "speckit.plan",
        "speckit.tasks",
    }
    assert tracked == expected
    assert all(not name.startswith("regex:") for name in tracked)
    files = list(commands_dir.iterdir())
    assert files
    assert all(path.exists() for path in files)
    assert all(
        path.name.startswith(("speckit.plan", "speckit.tasks")) for path in files
    )
    assert all(not path.name.startswith("regex:") for path in files)
    manager.remove(manifest.id)


def test_command_regex_zero_match_and_fullmatch(project_dir):
    selector_pack = _write_preset(
        project_dir,
        "no-command-match",
        r"regex:^missing\.command$",
        priority=1,
        resource_type="command",
    )
    manager = PresetManager(project_dir)
    manifest = PresetManifest(selector_pack / "preset.yml")
    assert (
        manager._expand_command_selectors(
            PresetResolver(project_dir), selector_pack, manifest.templates
        )
        == []
    )


def test_command_regex_and_exact_overlap_keep_only_concrete_names(project_dir):
    _write_preset(
        project_dir,
        "overlap-selector",
        r"regex:^speckit\.plan$",
        priority=1,
        resource_type="command",
    )
    selector_pack = project_dir / ".specify" / "presets" / "overlap-selector"
    exact = {"type": "command", "name": "speckit.plan", "file": "commands/exact.md"}
    manager = PresetManager(project_dir)
    manifest = PresetManifest(selector_pack / "preset.yml")
    expanded = manager._expand_command_selectors(
        PresetResolver(project_dir), selector_pack, [exact, *manifest.templates]
    )
    assert "regex:" not in " ".join(entry["name"] for entry in expanded)
    assert [entry["name"] for entry in expanded].count("speckit.plan") == 2


def test_exact_name_manifest_still_validates(tmp_path):
    path = tmp_path / "preset.yml"
    path.write_text(yaml.safe_dump(_manifest("plan-template")), encoding="utf-8")
    manifest = PresetManifest(path)
    assert manifest.templates[0]["name"] == "plan-template"
    assert selector_matches("plan-template", "plan-template")
    assert not selector_matches("plan-template", "other-template")


def test_exact_name_manifest_keeps_legacy_trailing_newline_validation(tmp_path):
    # Legacy `re.match(r'^[...]$')` accepts one trailing newline; preserve it.
    path = tmp_path / "preset.yml"
    path.write_text(yaml.safe_dump(_manifest("plan-template\n")), encoding="utf-8")
    manifest = PresetManifest(path)
    assert manifest.templates[0]["name"] == "plan-template\n"


def test_regex_validation_and_fullmatch(tmp_path):
    path = tmp_path / "preset.yml"
    selector = r"regex:^plan-.*-template$"
    path.write_text(yaml.safe_dump(_manifest(selector)), encoding="utf-8")
    assert PresetManifest(path).templates[0]["name"] == selector
    assert selector_matches(selector, "plan-main-template")
    assert not selector_matches("regex:plan", "plan-template")


def _write_command_declarations(pack_dir, preset_id, declarations):
    pack_dir.mkdir(parents=True, exist_ok=True)
    for index, declaration in enumerate(declarations):
        payload = pack_dir / f"command-{index}.md"
        payload.write_text(declaration["body"], encoding="utf-8")
        declaration["file"] = payload.name
        declaration.pop("body")
    data = _manifest("unused", "command")
    data["preset"]["id"] = preset_id
    data["provides"]["templates"] = declarations
    (pack_dir / "preset.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    return pack_dir


def _install_test_preset(project_dir, preset_id, pack_dir, priority):
    PresetRegistry(project_dir / ".specify" / "presets").add(
        preset_id, {"enabled": True, "priority": priority, "version": "1.0.0"}
    )
    destination = project_dir / ".specify" / "presets" / preset_id
    destination.mkdir(parents=True, exist_ok=True)
    for path in pack_dir.iterdir():
        (destination / path.name).write_bytes(path.read_bytes())
    return destination


@pytest.mark.parametrize(
    ("strategy", "overlay", "expected"),
    [
        ("replace", "# Preset replacement\n", "# Preset replacement"),
        ("prepend", "# Preset prefix\n", "# Preset prefix\n\n\n# Core command"),
        ("append", "# Preset suffix\n", "# Core command\n\n\n# Preset suffix"),
        (
            "wrap",
            "# Wrapper start\n{CORE_TEMPLATE}\n# Wrapper end\n",
            "# Wrapper start\n# Core command\n\n# Wrapper end",
        ),
    ],
)
def test_command_regex_composes_over_core_for_each_strategy(
    project_dir, tmp_path, strategy, overlay, expected
):
    core_commands = project_dir / ".specify" / "templates" / "commands"
    core_commands.mkdir(parents=True, exist_ok=True)
    (core_commands / "plan.md").write_text("# Core command\n", encoding="utf-8")
    pack_dir = tmp_path / "selector"
    declaration = {
        "type": "command",
        "name": r"regex:^speckit\.plan$",
        "strategy": strategy,
        "body": overlay,
    }
    _write_command_declarations(pack_dir, "selector", [declaration])
    installed = _install_test_preset(project_dir, "selector", pack_dir, 1)

    content = PresetResolver(project_dir).resolve_content("speckit.plan", "command")

    assert content is not None
    assert content.strip() == expected.strip()
    layers = PresetResolver(project_dir).collect_all_layers("speckit.plan", "command")
    assert [layer["source"] for layer in layers] == ["selector v1.0.0", "core"]
    assert layers[0]["path"] == installed / "command-0.md"


def test_command_regex_expands_and_composes_over_extension_layer(project_dir, tmp_path):
    extension = project_dir / ".specify" / "extensions" / "demo"
    (extension / "commands").mkdir(parents=True)
    (extension / "commands" / "speckit.demo.md").write_text(
        "# Extension command\n", encoding="utf-8"
    )
    ExtensionRegistry(project_dir / ".specify" / "extensions").add(
        "demo", {"enabled": True, "priority": 10, "version": "1.0"}
    )
    pack_dir = tmp_path / "selector"
    _write_command_declarations(
        pack_dir,
        "selector",
        [
            {
                "type": "command",
                "name": r"regex:^speckit\.demo$",
                "strategy": "append",
                "body": "# Preset addition\n",
            }
        ],
    )
    _install_test_preset(project_dir, "selector", pack_dir, 1)

    content = PresetResolver(project_dir).resolve_content("speckit.demo", "command")

    assert content == "# Extension command\n\n\n# Preset addition\n"
    layers = PresetResolver(project_dir).collect_all_layers("speckit.demo", "command")
    assert [layer["source"] for layer in layers] == [
        "selector v1.0.0",
        "extension:demo v1.0",
    ]


def test_command_regex_expands_and_composes_over_lower_preset(project_dir, tmp_path):
    lower_pack = tmp_path / "lower"
    _write_command_declarations(
        lower_pack,
        "lower",
        [
            {
                "type": "command",
                "name": "speckit.lower",
                "strategy": "replace",
                "body": "# Lower preset command\n",
            }
        ],
    )
    _install_test_preset(project_dir, "lower", lower_pack, 10)
    selector_pack = tmp_path / "selector"
    _write_command_declarations(
        selector_pack,
        "selector",
        [
            {
                "type": "command",
                "name": r"regex:^speckit\.lower$",
                "strategy": "prepend",
                "body": "# Selector prefix\n",
            }
        ],
    )
    _install_test_preset(project_dir, "selector", selector_pack, 1)

    content = PresetResolver(project_dir).resolve_content("speckit.lower", "command")

    assert content == "# Selector prefix\n\n\n# Lower preset command\n"
    layers = PresetResolver(project_dir).collect_all_layers("speckit.lower", "command")
    assert [layer["source"] for layer in layers] == [
        "selector v1.0.0",
        "lower v1.0.0",
    ]


def test_command_regex_excludes_higher_preset_and_project_override(
    project_dir, tmp_path
):
    # The selector is lower priority than both the higher preset and the project
    # override. Neither may make a command eligible for selector expansion.
    higher_pack = tmp_path / "higher"
    _write_command_declarations(
        higher_pack,
        "higher",
        [
            {
                "type": "command",
                "name": "speckit.higher",
                "strategy": "replace",
                "body": "# Higher command\n",
            }
        ],
    )
    _install_test_preset(project_dir, "higher", higher_pack, 1)
    selector_pack = tmp_path / "selector"
    _write_command_declarations(
        selector_pack,
        "selector",
        [
            {
                "type": "command",
                "name": r"regex:^speckit\.(higher|override)$",
                "strategy": "append",
                "body": "# Selector addition\n",
            }
        ],
    )
    installed = _install_test_preset(project_dir, "selector", selector_pack, 10)
    override_dir = project_dir / ".specify" / "templates" / "overrides"
    override_dir.mkdir(parents=True)
    (override_dir / "speckit.override.md").write_text("# Project override\n")
    manager = PresetManager(project_dir)
    manifest = PresetManifest(installed / "preset.yml")

    expanded = manager._expand_command_selectors(
        PresetResolver(project_dir), installed, manifest.templates
    )

    assert expanded == []
    assert (
        PresetResolver(project_dir).collect_all_layers("speckit.higher", "command")[0][
            "source"
        ]
        == "higher v1.0.0"
    )
    assert (
        PresetResolver(project_dir).collect_all_layers("speckit.override", "command")[
            0
        ]["source"]
        == "project override"
    )


def test_three_overlapping_command_regexes_keep_declaration_order_and_compose(
    project_dir, tmp_path
):
    core_commands = project_dir / ".specify" / "templates" / "commands"
    core_commands.mkdir(parents=True, exist_ok=True)
    (core_commands / "plan.md").write_text("# Core command\n", encoding="utf-8")
    pack_dir = tmp_path / "selector"
    declarations = [
        {
            "type": "command",
            "name": r"regex:^speckit\.plan$",
            "strategy": "prepend",
            "body": "# Declared first\n",
        },
        {
            "type": "command",
            "name": r"regex:^speckit\.p.*$",
            "strategy": "append",
            "body": "# Declared second\n",
        },
        {
            "type": "command",
            "name": r"regex:^speckit\.pla.*n$",
            "strategy": "wrap",
            "body": "# Declared third start\n{CORE_TEMPLATE}\n# Declared third end\n",
        },
    ]
    _write_command_declarations(pack_dir, "selector", declarations)
    _install_test_preset(project_dir, "selector", pack_dir, 1)
    manager = PresetManager(project_dir)
    manifest = PresetManifest(
        project_dir / ".specify" / "presets" / "selector" / "preset.yml"
    )

    expanded = manager._expand_command_selectors(
        PresetResolver(project_dir),
        project_dir / ".specify" / "presets" / "selector",
        manifest.templates,
    )
    layers = PresetResolver(project_dir).collect_all_layers("speckit.plan", "command")
    content = PresetResolver(project_dir).resolve_content("speckit.plan", "command")

    assert [entry["name"] for entry in expanded] == [
        "speckit.plan",
        "speckit.plan",
        "speckit.plan",
    ]
    assert [layer["path"].name for layer in layers] == [
        "command-0.md",
        "command-1.md",
        "command-2.md",
        "plan.md",
    ]
    assert content is not None
    assert content.index("Declared first") < content.index("Declared third start")
    assert content.index("Declared third start") < content.index("Core command")
    assert content.index("Core command") < content.index("Declared third end")
    assert content.index("Declared third end") < content.index("Declared second")


def test_invalid_regex_fails_during_manifest_validation(tmp_path):
    path = tmp_path / "preset.yml"
    path.write_text(yaml.safe_dump(_manifest("regex:[unterminated")), encoding="utf-8")
    with pytest.raises(PresetValidationError, match="Invalid regex selector"):
        PresetManifest(path)


def test_template_regex_matches_core_resource_only(project_dir):
    _write_preset(
        project_dir, "regex-pack", "regex:.*-template$", priority=10, strategy="append"
    )
    layers = PresetResolver(project_dir).collect_all_layers("plan-template", "template")
    assert any(layer["source"].startswith("regex-pack") for layer in layers)
    assert (
        PresetResolver(project_dir).collect_all_layers("does-not-exist", "template")
        == []
    )


def test_template_regex_matches_extension_resource(project_dir):
    ext = project_dir / ".specify" / "extensions" / "demo"
    (ext / "templates").mkdir(parents=True)
    (ext / "templates" / "plan-template.md").write_text(
        "extension base\n", encoding="utf-8"
    )
    _write_preset(
        project_dir, "regex-pack", "regex:.*-template$", priority=10, strategy="append"
    )
    layers = PresetResolver(project_dir).collect_all_layers("plan-template", "template")
    assert any(layer["source"].startswith("regex-pack") for layer in layers)


def test_template_regex_matches_lower_priority_preset(project_dir):
    _write_preset(
        project_dir, "high", "regex:.*-template$", priority=1, strategy="append"
    )
    _write_preset(project_dir, "low", "plan-template", priority=10)
    layers = PresetResolver(project_dir).collect_all_layers("plan-template", "template")
    assert any(layer["source"].startswith("high") for layer in layers)
    assert any(layer["source"].startswith("low") for layer in layers)


def test_regex_does_not_match_higher_preset_or_create_resource(project_dir):
    _write_preset(project_dir, "higher", "only-higher", priority=1)
    _write_preset(project_dir, "lower", "regex:^only-higher$", priority=10)
    resolver = PresetResolver(project_dir)
    layers = resolver.collect_all_layers("only-higher", "template")
    assert any(layer["source"].startswith("higher") for layer in layers)
    assert not any(layer["source"].startswith("lower") for layer in layers)
    assert resolver.collect_all_layers("does-not-exist", "template") == []
    assert resolver.collect_all_layers("regex:^only-higher$", "template") == []


def test_same_priority_regex_layers_follow_preset_id_order(project_dir):
    # Registry tie-break is alphabetical ID; both selectors match the same core template.
    _write_preset(
        project_dir,
        "zeta-regex",
        "regex:^plan-template$",
        priority=10,
        strategy="append",
        body="zeta\n",
    )
    _write_preset(
        project_dir,
        "alpha-regex",
        "regex:^plan-template$",
        priority=10,
        strategy="append",
        body="alpha\n",
    )
    layers = PresetResolver(project_dir).collect_all_layers("plan-template", "template")
    regex_sources = [
        layer["source"].split()[0] for layer in layers if "-regex" in layer["source"]
    ]
    assert regex_sources == ["alpha-regex", "zeta-regex"]


def test_project_override_is_not_regex_lower_layer_proof(project_dir):
    overrides = project_dir / ".specify" / "templates" / "overrides"
    overrides.mkdir(parents=True)
    (overrides / "foo-template.md").write_text("override\n", encoding="utf-8")
    _write_preset(
        project_dir,
        "regex-pack",
        "regex:^foo-template$",
        priority=10,
        strategy="append",
    )
    resolver = PresetResolver(project_dir)
    layers = resolver.collect_all_layers("foo-template", "template")
    assert [layer["source"] for layer in layers] == ["project override"]


def test_project_override_does_not_hide_real_regex_lower_layer(project_dir):
    overrides = project_dir / ".specify" / "templates" / "overrides"
    overrides.mkdir(parents=True)
    (overrides / "foo-template.md").write_text("override\n", encoding="utf-8")
    _write_preset(
        project_dir,
        "regex-pack",
        "regex:^foo-template$",
        priority=10,
        strategy="append",
    )
    core = project_dir / ".specify" / "templates" / "foo-template.md"
    core.parent.mkdir(parents=True, exist_ok=True)
    core.write_text("core\n", encoding="utf-8")
    layers = PresetResolver(project_dir).collect_all_layers("foo-template", "template")
    assert [layer["source"] for layer in layers] == [
        "project override",
        "regex-pack v1.0.0",
        "core",
    ]


def test_exact_and_regex_layers_keep_existing_priority_composition(project_dir):
    _write_preset(
        project_dir,
        "higher-regex",
        "regex:^plan-template$",
        priority=1,
        strategy="append",
        body="A\n",
    )
    _write_preset(
        project_dir,
        "higher-exact",
        "plan-template",
        priority=2,
        strategy="prepend",
        body="B\n",
    )
    resolver = PresetResolver(project_dir)
    layers = resolver.collect_all_layers("plan-template", "template")
    assert [layer["source"].split(" ")[0] for layer in layers[:2]] == [
        "higher-regex",
        "higher-exact",
    ]
    result = resolver.resolve_content("plan-template", "template")
    assert result is not None and "A" in result and "B" in result


def test_script_regex_uses_same_resolver_and_strategy_restrictions(project_dir):
    core_scripts = project_dir / ".specify" / "templates" / "scripts"
    core_scripts.mkdir(parents=True)
    (core_scripts / "check-main.sh").write_text(
        "#!/bin/sh\necho core\n", encoding="utf-8"
    )
    _write_preset(
        project_dir,
        "script-regex",
        "regex:^check-.*$",
        priority=10,
        strategy="wrap",
        resource_type="script",
        body="#!/bin/sh\n{CORE_SCRIPT}\n",
    )
    resolver = PresetResolver(project_dir)
    assert any(
        layer["source"].startswith("script-regex")
        for layer in resolver.collect_all_layers("check-main", "script")
    )
    invalid = _manifest("regex:^check-.*$", "script", "append")
    path = project_dir / "invalid-script-preset.yml"
    path.write_text(yaml.safe_dump(invalid), encoding="utf-8")
    with pytest.raises(PresetValidationError, match="scripts only support"):
        PresetManifest(path)


def test_zero_match_is_non_fatal_and_has_no_layer(project_dir):
    _write_preset(project_dir, "no-match", "regex:^missing-resource$", priority=10)
    assert (
        PresetResolver(project_dir).collect_all_layers("missing-resource", "template")
        == []
    )
