"""Regression tests for provider-scoped resolver candidate discovery."""

import pytest
import yaml

from specify_cli.extensions import ExtensionRegistry
from specify_cli.presets import PresetRegistry, PresetResolver


def _extension(project_dir, extension_id, filename, *, declared=False):
    root = project_dir / ".specify" / "extensions" / extension_id
    candidate = root / filename
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(f"# {extension_id} base\n", encoding="utf-8")
    if declared:
        (root / "extension.yml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "1.0",
                    "extension": {
                        "id": extension_id,
                        "name": extension_id,
                        "version": "1.0.0",
                        "description": "resolver fixture",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "commands": [
                            {
                                "name": "speckit.target.collect",
                                "file": filename,
                                "description": "collect",
                            }
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )
    return candidate


def _preset(project_dir, preset_id, declarations, *, priority=1):
    root = project_dir / ".specify" / "presets" / preset_id
    root.mkdir(parents=True, exist_ok=True)
    (root / "payload.md").write_text("overlay\n", encoding="utf-8")
    (root / "preset.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "preset": {
                    "id": preset_id,
                    "name": preset_id,
                    "version": "1.0.0",
                    "description": "resolver fixture",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {"templates": declarations},
            }
        ),
        encoding="utf-8",
    )
    PresetRegistry(root.parent).add(
        preset_id, {"version": "1.0.0", "priority": priority, "enabled": True}
    )
    return root / "payload.md"


@pytest.mark.parametrize("registered", [False, True])
@pytest.mark.parametrize(
    "filename,declared",
    [
        ("commands/target.collect.md", False),
        ("templates/commands/target.collect.md", False),
        ("commands/actual.md", True),
        ("commands/speckit.target.collect.md", False),
    ],
)
def test_each_extension_candidate_is_emitted_once_with_own_attribution(
    project_dir, registered, filename, declared
):
    candidate = _extension(project_dir, "target", filename, declared=declared)
    # An earlier unrelated orphan must not discover target's namespace fallback.
    unrelated = project_dir / ".specify" / "extensions" / "aaa-orphan"
    unrelated.mkdir()
    if registered:
        ExtensionRegistry(project_dir / ".specify" / "extensions").add(
            "target", {"enabled": True, "version": "1.0.0", "priority": 20}
        )
    resolver = PresetResolver(project_dir)
    layers = resolver.collect_all_layers("speckit.target.collect", "command")
    assert len(layers) == 1
    assert layers[0]["path"] == candidate
    assert layers[0]["extension_id"] == "target"
    assert layers[0]["extension_dir"] == (
        project_dir / ".specify" / "extensions" / "target"
    )
    assert layers[0]["source"] == (
        "extension:target v1.0.0" if registered else "extension:target (unregistered)"
    )
    assert resolver.resolve("speckit.target.collect", "command") == candidate
    assert (
        resolver.resolve_content("speckit.target.collect", "command")
        == "# target base\n"
    )


@pytest.mark.parametrize("declared", [False, True])
def test_disabled_namespace_is_never_revived_by_unrelated_extension(
    project_dir, declared
):
    _extension(project_dir, "target", "commands/target.collect.md", declared=declared)
    (project_dir / ".specify" / "extensions" / "aaa-orphan").mkdir()
    registry = ExtensionRegistry(project_dir / ".specify" / "extensions")
    registry.add("target", {"enabled": False, "version": "1.0.0"})
    resolver = PresetResolver(project_dir)
    assert resolver.collect_all_layers("speckit.target.collect", "command") == []
    assert resolver.resolve("speckit.target.collect", "command") is None
    assert resolver.resolve_content("speckit.target.collect", "command") is None


@pytest.mark.parametrize("template_type", ["command", "template", "script"])
def test_missing_manifest_command_never_falls_back_to_legacy_file(
    project_dir, template_type
):
    candidate = _extension(
        project_dir, "target", "commands/target.collect.md", declared=True
    )
    manifest_path = candidate.parents[1] / "extension.yml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["provides"]["commands"][0]["file"] = "commands/missing.md"
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    resolver = PresetResolver(project_dir)
    assert resolver.collect_all_layers("speckit.target.collect", template_type) == []
    assert resolver.resolve("speckit.target.collect", template_type) is None


@pytest.mark.parametrize("template_type", ["template", "script"])
def test_legacy_command_is_not_a_template_or_script_layer(project_dir, template_type):
    _extension(project_dir, "target", "commands/target.collect.md")
    resolver = PresetResolver(project_dir)
    assert resolver.collect_all_layers("speckit.target.collect", template_type) == []
    assert resolver.resolve("speckit.target.collect", template_type) is None
    assert resolver.resolve_content("speckit.target.collect", template_type) is None


@pytest.mark.parametrize("enabled", [False, True])
def test_regex_eligibility_uses_enabled_legacy_namespace_base(project_dir, enabled):
    candidate = _extension(project_dir, "target", "commands/target.collect.md")
    ExtensionRegistry(project_dir / ".specify" / "extensions").add(
        "target", {"enabled": enabled, "version": "1.0.0"}
    )
    overlay = _preset(
        project_dir,
        "selector",
        [
            {
                "type": "command",
                "name": r"regex:^speckit\.target\.collect$",
                "file": "payload.md",
                "strategy": "append",
            }
        ],
    )
    resolver = PresetResolver(project_dir)
    layers = resolver.collect_all_layers("speckit.target.collect", "command")
    if enabled:
        assert [layer["path"] for layer in layers] == [overlay, candidate]
        assert resolver.resolve("speckit.target.collect", "command") == overlay
        assert resolver.resolve_content("speckit.target.collect", "command") == (
            "# target base\n\n\noverlay\n"
        )
    else:
        assert layers == []
        assert resolver.resolve("speckit.target.collect", "command") is None
        assert resolver.resolve_content("speckit.target.collect", "command") is None


def test_distinct_providers_and_exact_regex_declarations_are_not_deduplicated(
    project_dir,
):
    base = _extension(project_dir, "target", "commands/actual.md", declared=True)
    other = _extension(project_dir, "other", "commands/actual.md", declared=True)
    ExtensionRegistry(project_dir / ".specify" / "extensions").add(
        "target", {"enabled": True, "priority": 1, "version": "1.0.0"}
    )
    declarations = [
        {
            "type": "command",
            "name": name,
            "file": "payload.md",
            "strategy": "append",
        }
        for name in ("speckit.target.collect", r"regex:^speckit\.target\.collect$")
    ]
    overlay = _preset(project_dir, "selector", declarations)
    lower = _preset(project_dir, "lower", [declarations[0]], priority=2)
    resolver = PresetResolver(project_dir)
    layers = resolver.collect_all_layers("speckit.target.collect", "command")
    assert [layer["path"] for layer in layers] == [overlay, overlay, lower, base, other]
    assert resolver.resolve_content("speckit.target.collect", "command") == (
        "# target base\n\n\noverlay\n\n\noverlay\n\n\noverlay\n"
    )
