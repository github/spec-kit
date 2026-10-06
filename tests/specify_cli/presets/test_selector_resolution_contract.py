"""Direct lookup, source attribution, and composition share selector ordering."""

import re

import pytest
import yaml

from specify_cli.presets import (
    PresetManager,
    PresetManifest,
    PresetRegistry,
    PresetResolver,
    PresetValidationError,
)


def _write_preset(project, identifier, declarations, priority=1):
    root = project / ".specify" / "presets" / identifier
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for index, (name, resource_type, strategy, body) in enumerate(declarations):
        filename = f"payload-{index}.{'sh' if resource_type == 'script' else 'md'}"
        if body is not None:
            (root / filename).write_text(body, encoding="utf-8")
        entries.append(
            {
                "name": name,
                "type": resource_type,
                "strategy": strategy,
                "file": filename,
            }
        )
    (root / "preset.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "preset": {
                    "id": identifier,
                    "name": identifier,
                    "version": "1.0.0",
                    "description": "Selector contract regression",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {"templates": entries},
            }
        ),
        encoding="utf-8",
    )
    PresetRegistry(project / ".specify" / "presets").add(
        identifier, {"enabled": True, "priority": priority, "version": "1.0.0"}
    )
    return root


def _name(resource_type):
    return (
        "speckit.selector-contract"
        if resource_type == "command"
        else "selector-contract"
    )


def _assert_parity(
    resolver, name, resource_type, expected_paths, expected_sources, content
):
    layers = resolver.collect_all_layers(name, resource_type)
    assert [layer["path"] for layer in layers] == expected_paths
    assert [layer["source"] for layer in layers] == expected_sources
    assert resolver.resolve(name, resource_type) == expected_paths[0]
    assert resolver.resolve_with_source(name, resource_type) == {
        "path": str(expected_paths[0]),
        "source": expected_sources[0],
    }
    assert resolver.resolve_content(name, resource_type) == content


@pytest.mark.parametrize("resource_type", ["template", "command", "script"])
@pytest.mark.parametrize("order", ["regex-exact", "exact-regex", "regex-regex"])
def test_overlapping_declarations_share_manifest_order(tmp_path, resource_type, order):
    name = _name(resource_type)
    regex = f"regex:{re.escape(name)}"
    names = {
        "regex-exact": [regex, name],
        "exact-regex": [name, regex],
        "regex-regex": [regex, f"regex:^{re.escape(name)}$"],
    }[order]
    pack = _write_preset(
        tmp_path,
        "selector",
        [
            (entry, resource_type, "replace", f"body-{index}")
            for index, entry in enumerate(names)
        ],
    )
    lower = _write_preset(
        tmp_path, "lower", [(name, resource_type, "replace", "base")], 10
    )
    suffix = "sh" if resource_type == "script" else "md"
    _assert_parity(
        PresetResolver(tmp_path),
        name,
        resource_type,
        [
            pack / f"payload-0.{suffix}",
            pack / f"payload-1.{suffix}",
            lower / f"payload-0.{suffix}",
        ],
        ["selector v1.0.0", "selector v1.0.0", "lower v1.0.0"],
        "body-0",
    )


@pytest.mark.parametrize("resource_type", ["template", "command", "script"])
@pytest.mark.parametrize("regex_first", [True, False])
def test_exact_and_regex_compose_over_lower_without_deduplication(
    tmp_path, resource_type, regex_first
):
    name = _name(resource_type)
    names = [f"regex:{re.escape(name)}", name]
    if not regex_first:
        names.reverse()
    placeholder = "$CORE_SCRIPT" if resource_type == "script" else "{CORE_TEMPLATE}"
    pack = _write_preset(
        tmp_path,
        "selector",
        [
            (entry, resource_type, "wrap", f"layer-{index}[{placeholder}]")
            for index, entry in enumerate(names)
        ],
    )
    lower = _write_preset(
        tmp_path, "lower", [(name, resource_type, "replace", "base")], 10
    )
    suffix = "sh" if resource_type == "script" else "md"
    _assert_parity(
        PresetResolver(tmp_path),
        name,
        resource_type,
        [
            pack / f"payload-0.{suffix}",
            pack / f"payload-1.{suffix}",
            lower / f"payload-0.{suffix}",
        ],
        ["selector v1.0.0", "selector v1.0.0", "lower v1.0.0"],
        "layer-0[layer-1[base]]",
    )


@pytest.mark.parametrize("overlap", ["regex-exact", "regex-regex"])
def test_overlaps_using_the_same_file_are_not_deduplicated(tmp_path, overlap):
    name = _name("template")
    pack = _write_preset(
        tmp_path,
        "selector",
        [
            (f"regex:{name}", "template", "wrap", "overlay[{CORE_TEMPLATE}]"),
            (
                name if overlap == "regex-exact" else f"regex:^{name}$",
                "template",
                "wrap",
                "unused",
            ),
        ],
    )
    manifest_path = pack / "preset.yml"
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    data["provides"]["templates"][1]["file"] = "payload-0.md"
    manifest_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    lower = _write_preset(
        tmp_path, "lower", [(name, "template", "replace", "base")], 10
    )
    _assert_parity(
        PresetResolver(tmp_path),
        name,
        "template",
        [pack / "payload-0.md", pack / "payload-0.md", lower / "payload-0.md"],
        ["selector v1.0.0", "selector v1.0.0", "lower v1.0.0"],
        "overlay[overlay[base]]",
    )


@pytest.mark.parametrize("missing", ["exact", "regex", "both"])
def test_unusable_declarations_skip_to_the_first_usable_layer(tmp_path, missing):
    name = _name("template")
    pack = _write_preset(
        tmp_path,
        "selector",
        [
            (
                name,
                "template",
                "replace",
                None if missing in {"exact", "both"} else "exact",
            ),
            (
                f"regex:{name}",
                "template",
                "replace",
                None if missing in {"regex", "both"} else "regex",
            ),
        ],
    )
    # A matching declaration still prevents a stray conventional file winning.
    (pack / f"{name}.md").write_text("stray", encoding="utf-8")
    lower = _write_preset(
        tmp_path, "lower", [(name, "template", "replace", "base")], 10
    )
    paths, sources = [], []
    if missing not in {"exact", "both"}:
        paths.append(pack / "payload-0.md")
        sources.append("selector v1.0.0")
    if missing not in {"regex", "both"}:
        paths.append(pack / "payload-1.md")
        sources.append("selector v1.0.0")
    paths.append(lower / "payload-0.md")
    sources.append("lower v1.0.0")
    content = {"exact": "regex", "regex": "exact", "both": "base"}[missing]
    _assert_parity(PresetResolver(tmp_path), name, "template", paths, sources, content)


def test_own_exact_declaration_does_not_make_regex_eligible(tmp_path):
    name = _name("template")
    pack = _write_preset(
        tmp_path,
        "selector",
        [
            (f"regex:{name}", "template", "replace", "ineligible"),
            (name, "template", "replace", "exact"),
        ],
    )
    _assert_parity(
        PresetResolver(tmp_path),
        name,
        "template",
        [pack / "payload-1.md"],
        ["selector v1.0.0"],
        "exact",
    )


INVALID_PATTERNS = [
    pytest.param("[unterminated", re.error, id="grammar"),
    pytest.param("a{999999999999999999999}", OverflowError, id="huge-repetition"),
    pytest.param("(" * 2000 + "a" + ")" * 2000, RecursionError, id="deep-nesting"),
]


@pytest.mark.parametrize("pattern,compile_error", INVALID_PATTERNS)
def test_regex_compile_failures_become_manifest_validation_errors(
    tmp_path, pattern, compile_error
):
    pack = _write_preset(
        tmp_path, "malformed", [(f"regex:{pattern}", "template", "replace", "bad")]
    )
    with pytest.raises(PresetValidationError, match="Invalid regex selector") as caught:
        PresetManifest(pack / "preset.yml")
    assert isinstance(caught.value.__cause__, compile_error)


@pytest.mark.parametrize("pattern,compile_error", INVALID_PATTERNS)
def test_installed_malformed_selector_is_isolated_from_healthy_presets(
    tmp_path, pattern, compile_error
):
    name = _name("template")
    _write_preset(
        tmp_path, "malformed", [(f"regex:{pattern}", "template", "replace", "bad")]
    )
    healthy = _write_preset(
        tmp_path, "healthy", [(name, "template", "replace", "healthy")], 10
    )
    installed = {
        entry["id"]: entry for entry in PresetManager(tmp_path).list_installed()
    }
    assert set(installed) == {"malformed", "healthy"}
    assert installed["malformed"]["description"] == "⚠️ Corrupted preset"
    assert installed["malformed"]["enabled"] is False
    assert installed["healthy"]["enabled"] is True
    _assert_parity(
        PresetResolver(tmp_path),
        name,
        "template",
        [healthy / "payload-0.md"],
        ["healthy v1.0.0"],
        "healthy",
    )


@pytest.mark.parametrize(
    "selector", ["regex:a{1000}", "regex:(?:selector-)?contract", "selector-contract"]
)
def test_valid_regex_and_exact_names_remain_accepted(tmp_path, selector):
    pack = _write_preset(
        tmp_path, "valid", [(selector, "template", "replace", "valid")]
    )
    assert PresetManifest(pack / "preset.yml").templates[0]["name"] == selector
