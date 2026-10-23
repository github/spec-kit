"""Deterministic tests for bundle-reference expansion."""
from __future__ import annotations

import pytest

from specify_cli.bundles import BundlerError
import specify_cli.bundles.expansion as expansion_module
from specify_cli.bundles.expansion import (
    MAX_REFERENCED_BUNDLES,
    ExpandedManifest,
    LoadedBundle,
    _component_differences,
    expand_manifest,
    format_chain,
    require_installable,
)
from specify_cli.bundles.manifest import BundleManifest, ComponentRef
from tests.specify_cli.bundles.helpers import FakeBundleLoader, reference_manifest_dict


def manifest(
    bundle_id: str,
    *,
    version: str = "1.0.0",
    bundles: list[dict] | None = None,
    **components,
) -> BundleManifest:
    data = reference_manifest_dict(
        bundles=bundles,
        bundle_id=bundle_id,
        **components,
    )
    data["bundle"]["version"] = version
    return BundleManifest.from_dict(data)


def loaded(*manifests: BundleManifest, source: str = "default", install_allowed: bool = True):
    return {
        (item.bundle.id, item.bundle.version): LoadedBundle(item, source, install_allowed)
        for item in manifests
    }


def test_flat_manifest_does_not_call_loader():
    root = BundleManifest.from_dict(reference_manifest_dict())
    loader = FakeBundleLoader({})
    expanded = expand_manifest(root, loader)
    assert expanded == ExpandedManifest.flat(root)
    assert loader.load_calls == []


def test_direct_and_transitive_references_are_depth_first_and_provenanced():
    leaf = manifest("leaf", extensions=[{"id": "leaf-ext", "version": "1.0.0"}])
    child = manifest(
        "child",
        bundles=[{"id": "leaf", "version": "1.0.0"}],
        extensions=[{"id": "child-ext", "version": "1.0.0"}],
    )
    root = manifest(
        "root",
        bundles=[{"id": "child", "version": "1.0.0"}],
        extensions=[{"id": "root-ext", "version": "1.0.0"}],
    )
    expanded = expand_manifest(root, FakeBundleLoader(loaded(leaf, child)))
    assert [item.id for item in expanded.components] == ["leaf-ext", "child-ext", "root-ext"]
    assert expanded.origins[("extensions", "leaf-ext")].origin == ("child", "leaf")
    assert expanded.references[1].via == ("child",)


def test_reference_only_root_and_same_component_overlap():
    first = manifest("first", extensions=[{"id": "shared", "version": "v1.0.0"}])
    second = manifest("second", extensions=[{"id": "shared", "version": "1.0.0"}])
    root = manifest(
        "root",
        bundles=[
            {"id": "first", "version": "1.0.0"},
            {"id": "second", "version": "1.0.0"},
        ],
    )
    expanded = expand_manifest(root, FakeBundleLoader(loaded(first, second)))
    assert [item.id for item in expanded.components] == ["shared"]
    assert expanded.origins[("extensions", "shared")].origin == ("first",)


def test_shared_bundle_is_loaded_and_expanded_once(monkeypatch):
    shared = manifest("shared", extensions=[{"id": "shared-ext", "version": "1.0.0"}])
    left = manifest("left", bundles=[{"id": "shared", "version": "1.0.0"}])
    right = manifest("right", bundles=[{"id": "shared", "version": "1.0.0"}])
    root = manifest(
        "root",
        bundles=[
            {"id": "left", "version": "1.0.0"},
            {"id": "right", "version": "1.0.0"},
        ],
    )
    loader = FakeBundleLoader(loaded(shared, left, right))
    import specify_cli.bundles.expansion as expansion_module

    calls: list[str] = []
    original_expand = expansion_module._expand

    def counted_expand(manifest, chain, state):
        calls.append(manifest.bundle.id)
        return original_expand(manifest, chain, state)

    monkeypatch.setattr(expansion_module, "_expand", counted_expand)
    expanded = expand_manifest(root, loader)
    assert loader.load_calls.count(("shared", "1.0.0")) == 1
    assert calls.count("shared") == 1
    assert [item.id for item in expanded.components] == ["shared-ext"]


def test_layered_shared_graph_expands_each_bundle_once(monkeypatch):
    leaf = manifest("leaf", extensions=[{"id": "leaf-ext", "version": "1.0.0"}])
    shared = manifest("shared", bundles=[{"id": "leaf", "version": "1.0.0"}])
    left = manifest("left", bundles=[{"id": "shared", "version": "1.0.0"}])
    right = manifest("right", bundles=[{"id": "shared", "version": "1.0.0"}])
    root = manifest(
        "root",
        bundles=[
            {"id": "left", "version": "1.0.0"},
            {"id": "right", "version": "1.0.0"},
        ],
    )
    loader = FakeBundleLoader(loaded(leaf, shared, left, right))
    calls: list[str] = []
    original_expand = expansion_module._expand

    def counted_expand(manifest, chain, state):
        calls.append(manifest.bundle.id)
        return original_expand(manifest, chain, state)

    monkeypatch.setattr(expansion_module, "_expand", counted_expand)
    expand_manifest(root, loader)
    assert len(calls) == len(set(calls))
    assert set(calls) == {"root", "left", "right", "shared", "leaf"}


def test_shorter_route_updates_override_and_preserves_cached_subplan():
    leaf = manifest("leaf", extensions=[{"id": "e", "version": "1.0.0"}])
    long = manifest("long", bundles=[{"id": "leaf", "version": "1.0.0"}])
    root = manifest(
        "root",
        bundles=[
            {"id": "long", "version": "1.0.0"},
            {"id": "leaf", "version": "1.0.0"},
        ],
        extensions=[{"id": "e", "version": "2.0.0"}],
    )
    loader = FakeBundleLoader(loaded(leaf, long))
    state = expansion_module._ExpansionState(loader)
    expansion_module._expand(long, ("root", "long"), state)
    cached_subplans = dict(state.subplans)
    root_plan = expansion_module._expand(root, ("root",), state)
    assert all(state.subplans[key] == plan for key, plan in cached_subplans.items())
    expanded = ExpandedManifest(
        root,
        [entry.component for entry in root_plan.entries],
        {
            (entry.component.kind, entry.component.id): expansion_module.ComponentOrigin(
                entry.origin, entry.overrides
            )
            for entry in root_plan.entries
        },
        state.references,
        expansion_module._format_warnings(root, root_plan.notices),
    )
    assert expanded.origins[("extensions", "e")].origin == ()
    assert next(ref for ref in expanded.references if ref.id == "leaf").via == ()
    assert len(expanded.warnings) == 1
    assert "root → leaf" in expanded.warnings[0]
    assert "root → long → leaf" not in expanded.warnings[0]


def test_shared_dependency_override_is_merged_once():
    dependency = manifest("dependency", extensions=[{"id": "e", "version": "1.0.0"}])
    first = manifest("first", bundles=[{"id": "dependency", "version": "1.0.0"}])
    second = manifest("second", bundles=[{"id": "dependency", "version": "1.0.0"}])
    root = manifest(
        "root",
        bundles=[
            {"id": "first", "version": "1.0.0"},
            {"id": "second", "version": "1.0.0"},
        ],
        extensions=[{"id": "e", "version": "2.0.0"}],
    )
    expanded = expand_manifest(root, FakeBundleLoader(loaded(dependency, first, second)))
    origin = expanded.origins[("extensions", "e")]
    assert len(expanded.warnings) == 1
    assert len(origin.overrides) == 1
    assert origin.overrides[0].origin == ("first", "dependency")
    assert "root → first → dependency" in expanded.warnings[0]
    assert "root → second → dependency" not in expanded.warnings[0]


def test_agreeing_copies_merge_override_histories_regardless_of_order():
    leaf = manifest("leaf", extensions=[{"id": "shared", "version": "1.0.0"}])
    plain = manifest("plain", extensions=[{"id": "shared", "version": "2.0.0"}])
    overriding = manifest(
        "overriding",
        bundles=[{"id": "leaf", "version": "1.0.0"}],
        extensions=[{"id": "shared", "version": "2.0.0"}],
    )

    for reference_ids in (("plain", "overriding"), ("overriding", "plain")):
        root = manifest(
            "root",
            bundles=[{"id": bundle_id, "version": "1.0.0"} for bundle_id in reference_ids],
        )
        expanded = expand_manifest(
            root, FakeBundleLoader(loaded(leaf, plain, overriding))
        )

        overrides = expanded.origins[("extensions", "shared")].overrides
        assert [(item.component.version, item.origin) for item in overrides] == [
            ("1.0.0", ("overriding", "leaf"))
        ]


def test_shorter_origin_preserves_agreeing_copy_override_history():
    leaf = manifest("leaf", extensions=[{"id": "shared", "version": "1.0.0"}])
    overriding = manifest(
        "overriding",
        bundles=[{"id": "leaf", "version": "1.0.0"}],
        extensions=[{"id": "shared", "version": "2.0.0"}],
    )
    long = manifest("long", bundles=[{"id": "overriding", "version": "1.0.0"}])
    plain = manifest("plain", extensions=[{"id": "shared", "version": "2.0.0"}])
    root = manifest(
        "root",
        bundles=[
            {"id": "long", "version": "1.0.0"},
            {"id": "plain", "version": "1.0.0"},
        ],
    )

    expanded = expand_manifest(
        root, FakeBundleLoader(loaded(leaf, overriding, long, plain))
    )

    origin = expanded.origins[("extensions", "shared")]
    assert origin.origin == ("plain",)
    assert [(item.component.version, item.origin) for item in origin.overrides] == [
        ("1.0.0", ("long", "overriding", "leaf"))
    ]


def test_agreeing_copy_keeps_first_component_spelling_and_shorter_origin():
    dependency = manifest("dependency", extensions=[{"id": "e", "version": "v1.0.0"}])
    first = manifest("first", bundles=[{"id": "dependency", "version": "1.0.0"}])
    root = manifest(
        "root",
        bundles=[
            {"id": "first", "version": "1.0.0"},
            {"id": "dependency", "version": "1.0.0"},
        ],
    )
    expanded = expand_manifest(root, FakeBundleLoader(loaded(dependency, first)))
    assert expanded.components[0].version == "v1.0.0"
    assert expanded.origins[("extensions", "e")].origin == ("dependency",)


def test_own_override_records_all_fields_and_own_position():
    child = manifest(
        "child",
        presets=[
            {"id": "style", "version": "1.0.0", "source": "a", "priority": 10, "strategy": "append"}
        ],
    )
    root = manifest(
        "root",
        bundles=[{"id": "child", "version": "1.0.0"}],
        presets=[
            {"id": "style", "version": "2.0.0", "source": "b", "priority": 20, "strategy": "replace"}
        ],
    )
    expanded = expand_manifest(root, FakeBundleLoader(loaded(child)))
    origin = expanded.origins[("presets", "style")]
    assert origin.origin == ()
    assert origin.overrides[0].origin == ("child",)
    warning = expanded.warnings[0]
    assert (
        "version 2.0.0 and source b and priority 20 and strategy replace (root) "
        "overrides"
    ) in warning
    assert "version 1.0.0 from root → child" in warning
    assert "source a from root → child" in warning
    assert "priority 10 from root → child" in warning
    assert "strategy append from root → child" in warning
    assert expanded.warnings.count(warning) == 1


def test_extension_priority_only_override_is_reported():
    child = manifest(
        "child", extensions=[{"id": "style", "version": "1.0.0", "priority": 10}]
    )
    root = manifest(
        "root",
        bundles=[{"id": "child", "version": "1.0.0"}],
        extensions=[{"id": "style", "version": "1.0.0", "priority": 20}],
    )

    expanded = expand_manifest(root, FakeBundleLoader(loaded(child)))

    origin = expanded.origins[("extensions", "style")]
    assert expanded.components[0].priority == 20
    assert origin.overrides[0].origin == ("child",)
    assert "priority 20 (root) overrides priority 10 from root → child" in expanded.warnings[0]


def test_own_override_and_agreeing_copy_keep_own_positions():
    child = manifest(
        "child",
        extensions=[{"id": "a", "version": "1.0.0"}, {"id": "b", "version": "1.0.0"}],
    )
    root = manifest(
        "root",
        bundles=[{"id": "child", "version": "1.0.0"}],
        extensions=[
            {"id": "c", "version": "1.0.0"},
            {"id": "a", "version": "2.0.0"},
        ],
    )
    expanded = expand_manifest(root, FakeBundleLoader(loaded(child)))
    assert [component.id for component in expanded.components] == ["b", "c", "a"]

    agreeing_child = manifest(
        "agreeing-child",
        extensions=[{"id": "a", "version": "1.0.0"}, {"id": "b", "version": "1.0.0"}],
    )
    agreeing_root = manifest(
        "agreeing-root",
        bundles=[{"id": "agreeing-child", "version": "1.0.0"}],
        extensions=[{"id": "c", "version": "1.0.0"}, {"id": "a", "version": "1.0.0"}],
    )
    agreeing = expand_manifest(agreeing_root, FakeBundleLoader(loaded(agreeing_child)))
    assert [component.id for component in agreeing.components] == ["b", "c", "a"]
    assert agreeing.warnings == []


def test_nested_override_is_resolved_before_parent_merge():
    leaf = manifest("leaf", extensions=[{"id": "e", "version": "1.0.0"}])
    child = manifest(
        "child",
        bundles=[{"id": "leaf", "version": "1.0.0"}],
        extensions=[{"id": "e", "version": "2.0.0"}],
    )
    root = manifest("root", bundles=[{"id": "child", "version": "1.0.0"}])
    expanded = expand_manifest(root, FakeBundleLoader(loaded(leaf, child)))
    assert expanded.components[0].version == "2.0.0"
    assert expanded.origins[("extensions", "e")].origin == ("child",)
    assert "root → child → leaf" in expanded.warnings[0]


@pytest.mark.parametrize(
    ("kind", "first_fields", "second_fields", "field", "first_value", "second_value"),
    [
        ("extensions", {"version": "1.0.0"}, {"version": "2.0.0"}, "version", "1.0.0", "2.0.0"),
        ("extensions", {"version": "1.0.0"}, {"version": None}, "version", "1.0.0", "<unpinned>"),
        ("extensions", {"source": "a"}, {"source": "b"}, "source", "a", "b"),
        ("extensions", {"source": None}, {"source": "a"}, "source", "<unset>", "a"),
        ("extensions", {"priority": 10}, {"priority": 20}, "priority", "10", "20"),
        ("presets", {"priority": 1}, {"priority": 2}, "priority", "1", "2"),
        ("presets", {"strategy": "append"}, {"strategy": "replace"}, "strategy", "append", "replace"),
    ],
)
def test_sibling_conflicts_include_field_values_and_chains(
    kind, first_fields, second_fields, field, first_value, second_value
):
    first = manifest("first", **{kind: [{"id": "e", **first_fields}]})
    second = manifest("second", **{kind: [{"id": "e", **second_fields}]})
    root = manifest(
        "root",
        bundles=[
            {"id": "first", "version": "1.0.0"},
            {"id": "second", "version": "1.0.0"},
        ],
    )
    with pytest.raises(BundlerError, match=field) as caught:
        expand_manifest(root, FakeBundleLoader(loaded(first, second)))
    message = str(caught.value)
    assert f"{field} {first_value} (root → first)" in message
    assert f"{field} {second_value} (root → second)" in message
    assert "declare 'e' in 'root'" in message


def test_multifield_preset_conflict_and_unset_source_are_reported():
    first = manifest("first", presets=[{"id": "p", "version": "1.0.0", "source": "a", "priority": 1, "strategy": "append"}])
    second = manifest("second", presets=[{"id": "p", "version": "1.0.0", "priority": 2, "strategy": "replace"}])
    root = manifest("root", bundles=[{"id": "first", "version": "1.0.0"}, {"id": "second", "version": "1.0.0"}])
    with pytest.raises(BundlerError) as caught:
        expand_manifest(root, FakeBundleLoader(loaded(first, second)))
    message = str(caught.value)
    assert "source a; priority 1; strategy append (root → first)" in message
    assert "source <unset>; priority 2; strategy replace (root → second)" in message


@pytest.mark.parametrize(
    ("root_id", "root_refs", "definitions", "chain"),
    [
        (
            "root",
            [{"id": "a", "version": "1.0.0"}],
            [manifest("a", bundles=[{"id": "a", "version": "1.0.0"}])],
            "root → a → a",
        ),
        (
            "root",
            [{"id": "a", "version": "1.0.0"}],
            [
                manifest("a", bundles=[{"id": "b", "version": "1.0.0"}]),
                manifest("b", bundles=[{"id": "a", "version": "1.0.0"}]),
            ],
            "root → a → b → a",
        ),
        (
            "root",
            [{"id": "a", "version": "1.0.0"}],
            [
                manifest("a", bundles=[{"id": "root", "version": "1.0.0"}]),
                manifest("root"),
            ],
            "root → a → root",
        ),
    ],
)
def test_cycles_are_rejected_with_full_chain(root_id, root_refs, definitions, chain):
    root = manifest(root_id, bundles=root_refs)
    with pytest.raises(BundlerError, match="cycle") as caught:
        expand_manifest(root, FakeBundleLoader(loaded(*definitions)))
    assert chain in str(caught.value)


def test_version_conflict_names_both_chains_and_matching_spellings_are_accepted():
    first = manifest("first", bundles=[{"id": "leaf", "version": "1.0.0"}])
    second = manifest("second", bundles=[{"id": "leaf", "version": "2.0.0"}])
    leaf1 = manifest("leaf", version="1.0.0")
    root = manifest(
        "root",
        bundles=[
            {"id": "first", "version": "1.0.0"},
            {"id": "second", "version": "1.0.0"},
        ],
    )
    with pytest.raises(BundlerError, match="versions") as caught:
        expand_manifest(root, FakeBundleLoader(loaded(first, second, leaf1)))
    message = str(caught.value)
    assert "1.0.0 (root → first)" in message
    assert "2.0.0 (root → second)" in message

    accepted_first = manifest("accepted-first", bundles=[{"id": "leaf", "version": "v1.0.0"}])
    accepted_second = manifest("accepted-second", bundles=[{"id": "leaf", "version": "1.0.0"}])
    accepted_root = manifest(
        "accepted-root",
        bundles=[
            {"id": "accepted-first", "version": "1.0.0"},
            {"id": "accepted-second", "version": "1.0.0"},
        ],
    )
    accepted_leaf = manifest("leaf", version="1.0.0")
    accepted_bundles = loaded(accepted_first, accepted_second, accepted_leaf)
    accepted_bundles[("leaf", "v1.0.0")] = LoadedBundle(accepted_leaf, "default", True)
    accepted_loader = FakeBundleLoader(accepted_bundles)
    accepted = expand_manifest(accepted_root, accepted_loader)
    assert [reference.id for reference in accepted.references] == [
        "accepted-first", "leaf", "accepted-second"
    ]
    leaf_reference = next(
        reference for reference in accepted.references if reference.id == "leaf"
    )
    assert leaf_reference.version == "v1.0.0"
    assert leaf_reference.via == ("accepted-first",)
    assert accepted_loader.load_calls.count(("leaf", "v1.0.0")) == 1


def test_depth_limit_accepts_ten_levels_and_rejects_eleven():
    bundles = []
    for index in range(10):
        bundles.append(
            manifest(
                f"b{index}",
                bundles=[]
                if index == 9
                else [{"id": f"b{index + 1}", "version": "1.0.0"}],
            )
        )
    root = manifest("root", bundles=[{"id": "b0", "version": "1.0.0"}])
    expanded = expand_manifest(root, FakeBundleLoader(loaded(*bundles)))
    assert [reference.id for reference in expanded.references] == [f"b{i}" for i in range(10)]

    too_deep = manifest("b10")
    bundles.append(too_deep)
    bundles[9] = manifest("b9", bundles=[{"id": "b10", "version": "1.0.0"}])
    with pytest.raises(BundlerError, match="depth exceeds 10") as caught:
        expand_manifest(root, FakeBundleLoader(loaded(*bundles)))
    assert (
        "root → b0 → b1 → b2 → b3 → b4 → b5 → b6 → b7 → b8 → b9 → b10"
        in str(caught.value)
    )


def test_cached_subtree_rechecks_depth_for_a_deeper_route():
    leaf = manifest("leaf")
    cached = manifest("cached", bundles=[{"id": "leaf", "version": "1.0.0"}])
    parent = manifest("parent", bundles=[{"id": "cached", "version": "1.0.0"}])
    # The route through parent is intentionally lengthened after cached has
    # already been completed through the direct route.
    current = parent
    definitions = [leaf, cached, parent]
    for index in range(8):
        current = manifest(
            f"deep{index}",
            bundles=[{"id": current.bundle.id, "version": "1.0.0"}],
        )
        definitions.append(current)
    root = manifest(
        "root",
        bundles=[
            {"id": "cached", "version": "1.0.0"},
            {"id": current.bundle.id, "version": "1.0.0"},
        ],
    )
    with pytest.raises(BundlerError, match="depth exceeds 10") as caught:
        expand_manifest(root, FakeBundleLoader(loaded(*definitions)))
    assert (
        "root → deep7 → deep6 → deep5 → deep4 → deep3 → deep2 → deep1 → "
        "deep0 → parent → cached → leaf"
    ) in str(caught.value)

    current = parent
    definitions = [leaf, cached, parent]
    for index in range(7):
        current = manifest(
            f"deep{index}",
            bundles=[{"id": current.bundle.id, "version": "1.0.0"}],
        )
        definitions.append(current)
    root = manifest(
        "root",
        bundles=[
            {"id": "cached", "version": "1.0.0"},
            {"id": current.bundle.id, "version": "1.0.0"},
        ],
    )
    expanded = expand_manifest(root, FakeBundleLoader(loaded(*definitions)))
    assert [reference.id for reference in expanded.references] == [
        "cached", "leaf", "deep6", "deep5", "deep4", "deep3", "deep2", "deep1", "deep0", "parent"
    ]


def test_reference_limit_is_checked_before_loading():
    refs = [{"id": f"b{i}", "version": "1.0.0"} for i in range(MAX_REFERENCED_BUNDLES + 1)]
    root = manifest("root", bundles=refs)
    children = [manifest(f"b{i}") for i in range(MAX_REFERENCED_BUNDLES)]
    loader = FakeBundleLoader(loaded(*children))
    with pytest.raises(BundlerError, match="50"):
        expand_manifest(root, loader)
    assert loader.load_calls == [(f"b{i}", "1.0.0") for i in range(MAX_REFERENCED_BUNDLES)]


@pytest.mark.parametrize("explicit_first", [False, True])
def test_explicit_source_mismatch_is_rejected_in_both_traversal_orders(explicit_first):
    child = manifest("child")
    left_ref = {"id": "child", "version": "1.0.0"}
    right_ref = {"id": "child", "version": "1.0.0", "source": "other"}
    left = manifest("left", bundles=[left_ref])
    right = manifest("right", bundles=[right_ref])
    refs = [
        {"id": "right", "version": "1.0.0"},
        {"id": "left", "version": "1.0.0"},
    ] if explicit_first else [
        {"id": "left", "version": "1.0.0"},
        {"id": "right", "version": "1.0.0"},
    ]
    root = manifest("root", bundles=refs)
    loader = FakeBundleLoader(loaded(child, left, right))
    with pytest.raises(BundlerError, match="requires source"):
        expand_manifest(root, loader)
    if explicit_first:
        assert loader.load_calls[:2] == [("right", "1.0.0"), ("child", "1.0.0")]


@pytest.mark.parametrize("left_explicit", [False, True])
def test_omitted_and_matching_explicit_sources_reuse_cache(left_explicit):
    child = manifest("child")
    left = manifest(
        "left",
        bundles=[
            {"id": "child", "version": "1.0.0", **({"source": "default"} if left_explicit else {})}
        ],
    )
    right = manifest(
        "right",
        bundles=[
            {"id": "child", "version": "1.0.0", **({} if left_explicit else {"source": "default"})}
        ],
    )
    root = manifest(
        "root",
        bundles=[
            {"id": "left", "version": "1.0.0"},
            {"id": "right", "version": "1.0.0"},
        ],
    )
    loader = FakeBundleLoader(loaded(child, left, right))
    expanded = expand_manifest(root, loader)
    assert [ref.id for ref in expanded.references].count("child") == 1
    assert loader.load_calls.count(("child", "1.0.0")) == 1


def test_loaded_manifest_identity_and_version_are_verified():
    root = manifest("root", bundles=[{"id": "child", "version": "1.0.0"}])
    wrong_id = manifest("other")
    with pytest.raises(BundlerError, match="loaded manifest"):
        expand_manifest(root, FakeBundleLoader({("child", "1.0.0"): LoadedBundle(wrong_id, "default", True)}))
    wrong_version = manifest("child", version="2.0.0")
    with pytest.raises(BundlerError, match="loaded manifest version"):
        expand_manifest(root, FakeBundleLoader({("child", "1.0.0"): LoadedBundle(wrong_version, "default", True)}))


def test_kind_order_is_stable_after_expansion():
    child = manifest(
        "child",
        workflows=[{"id": "w", "version": "1.0.0"}],
        extensions=[{"id": "e", "version": "1.0.0"}],
    )
    root = manifest(
        "root",
        bundles=[{"id": "child", "version": "1.0.0"}],
        steps=[{"id": "s"}],
        presets=[{"id": "p", "version": "1.0.0", "priority": 1, "strategy": "append"}],
    )
    expanded = expand_manifest(root, FakeBundleLoader(loaded(child)))
    assert [component.kind for component in expanded.components] == [
        "extensions", "presets", "steps", "workflows"
    ]


def test_source_mismatch_on_cache_hit_and_loader_error_context():
    child = manifest("child")
    left = manifest("left", bundles=[{"id": "child", "version": "1.0.0"}])
    right = manifest(
        "right",
        bundles=[{"id": "child", "version": "1.0.0", "source": "other"}],
    )
    root = manifest(
        "root",
        bundles=[
            {"id": "left", "version": "1.0.0"},
            {"id": "right", "version": "1.0.0"},
        ],
    )
    with pytest.raises(BundlerError) as excinfo:
        expand_manifest(root, FakeBundleLoader(loaded(child, left, right)))
    message = str(excinfo.value)
    assert message.count("Bundle reference") == 1
    assert "winning catalog is 'default'" in message
    assert "loaded bundle source" not in message

    missing = manifest("root", bundles=[{"id": "missing", "version": "1.0.0"}])
    with pytest.raises(BundlerError, match=r"Cannot resolve bundle reference missing@1.0.0 \(root\)"):
        expand_manifest(missing, FakeBundleLoader({}))

    nested = manifest("nested", bundles=[{"id": "missing", "version": "1.0.0"}])
    root = manifest("root", bundles=[{"id": "nested", "version": "1.0.0"}])
    with pytest.raises(
        BundlerError,
        match=r"Cannot resolve bundle reference missing@1.0.0 \(root → nested\)",
    ):
        expand_manifest(root, FakeBundleLoader(loaded(nested)))


def test_loader_programming_errors_are_not_rewritten_as_resolution_errors():
    root = manifest("root", bundles=[{"id": "child", "version": "1.0.0"}])

    class BrokenLoader:
        def load(self, ref, chain):
            raise TypeError("loader contract violated")

    with pytest.raises(TypeError, match="loader contract violated"):
        expand_manifest(root, BrokenLoader())


def test_require_installable_and_formatting():
    child = manifest("community")
    root = manifest("root", bundles=[{"id": "community", "version": "1.0.0"}])
    expanded = expand_manifest(root, FakeBundleLoader(loaded(child, install_allowed=False)))
    with pytest.raises(BundlerError, match="discovery-only"):
        require_installable(expanded)
    assert format_chain(("root", "community")) == "root → community"


def test_component_difference_uses_strict_pinned_rules():
    assert _component_differences(
        ComponentRef("steps", "lint", None), ComponentRef("steps", "lint", "1.0.0")
    ) == ["version"]
    assert _component_differences(
        ComponentRef("extensions", "e", "v1.0.0"), ComponentRef("extensions", "e", "1.0.0")
    ) == []


def _layered_override_graph(layers: int):
    """Build `layers` of two-way sharing above one bundle that overrides a leaf."""
    def refs(*ids):
        return [{"id": item, "version": "1.0.0"} for item in ids]

    bundles = [
        manifest("leaf", extensions=[{"id": "e", "version": "1.0.0"}]),
        manifest(
            "base",
            bundles=refs("leaf"),
            extensions=[{"id": "e", "version": "2.0.0"}],
        ),
    ]
    previous: tuple[str, ...] = ("base",)
    for layer in range(layers):
        current = (f"l{layer}a", f"l{layer}b")
        bundles.extend(manifest(name, bundles=refs(*previous)) for name in current)
        previous = current
    return bundles, previous


@pytest.mark.parametrize("layers", [1, 4, 7])
@pytest.mark.parametrize("reverse", [False, True])
def test_layered_sharing_keeps_one_override_per_declaration(layers, reverse):
    bundles, top = _layered_override_graph(layers)
    ordered = tuple(reversed(top)) if reverse else top
    root = manifest(
        "root", bundles=[{"id": name, "version": "1.0.0"} for name in ordered]
    )

    expanded = expand_manifest(root, FakeBundleLoader(loaded(*bundles)))

    overrides = expanded.origins[("extensions", "e")].overrides
    assert len(overrides) == 1
    assert overrides[0].component.version == "1.0.0"
    expected_chain = (
        tuple(f"l{layer}a" for layer in reversed(range(layers))) + ("base", "leaf")
    )
    assert overrides[0].origin == expected_chain


def test_distinct_discarded_declarations_stay_separate_records():
    first = manifest("first", extensions=[{"id": "e", "version": "1.0.0"}])
    second = manifest("second", extensions=[{"id": "e", "version": "3.0.0"}])
    base = manifest(
        "base",
        bundles=[
            {"id": "first", "version": "1.0.0"},
            {"id": "second", "version": "1.0.0"},
        ],
        extensions=[{"id": "e", "version": "2.0.0"}],
    )
    left = manifest("left", bundles=[{"id": "base", "version": "1.0.0"}])
    right = manifest("right", bundles=[{"id": "base", "version": "1.0.0"}])
    root = manifest(
        "root",
        bundles=[
            {"id": "left", "version": "1.0.0"},
            {"id": "right", "version": "1.0.0"},
        ],
    )

    expanded = expand_manifest(
        root, FakeBundleLoader(loaded(first, second, base, left, right))
    )

    overrides = expanded.origins[("extensions", "e")].overrides
    assert sorted((item.component.version, item.origin) for item in overrides) == [
        ("1.0.0", ("left", "base", "first")),
        ("3.0.0", ("left", "base", "second")),
    ]


@pytest.mark.parametrize("omitted_first", [False, True])
def test_sibling_omitted_and_default_extension_priority_agree(omitted_first):
    omitted = {"id": "style", "version": "1.0.0"}
    default = {"id": "style", "version": "1.0.0", "priority": 10}
    first = manifest("first", extensions=[omitted if omitted_first else default])
    second = manifest("second", extensions=[default if omitted_first else omitted])
    root = manifest(
        "root",
        bundles=[{"id": "first", "version": "1.0.0"}, {"id": "second", "version": "1.0.0"}],
    )

    expanded = expand_manifest(root, FakeBundleLoader(loaded(first, second)))

    assert [ref.id for ref in expanded.components] == ["style"]
    assert expanded.warnings == []


@pytest.mark.parametrize("parent_explicit", [False, True])
def test_parent_declaration_with_equivalent_extension_priority_is_not_an_override(parent_explicit):
    child_ref = {"id": "style", "version": "1.0.0", **({} if parent_explicit else {"priority": 10})}
    parent_ref = {"id": "style", "version": "1.0.0", **({"priority": 10} if parent_explicit else {})}
    child = manifest("child", extensions=[child_ref])
    root = manifest(
        "root", bundles=[{"id": "child", "version": "1.0.0"}], extensions=[parent_ref]
    )

    expanded = expand_manifest(root, FakeBundleLoader(loaded(child)))

    assert expanded.warnings == []
    assert expanded.origins[("extensions", "style")].overrides == ()


def test_sibling_extension_priority_non_default_still_conflicts_with_omitted():
    first = manifest("first", extensions=[{"id": "style", "version": "1.0.0"}])
    second = manifest("second", extensions=[{"id": "style", "version": "1.0.0", "priority": 11}])
    root = manifest(
        "root",
        bundles=[{"id": "first", "version": "1.0.0"}, {"id": "second", "version": "1.0.0"}],
    )

    with pytest.raises(BundlerError, match="priority"):
        expand_manifest(root, FakeBundleLoader(loaded(first, second)))
