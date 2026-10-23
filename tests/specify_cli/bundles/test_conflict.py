"""Unit tests for conflict detection (T034): integration clash and overlap precedence."""
from __future__ import annotations

from specify_cli.bundles._commands import _bundle_overlaps
from specify_cli.bundles.conflict import component_setting_differences, detect_conflicts
from specify_cli.bundles.manifest import BundleManifest, ComponentRef
from specify_cli.bundles.records import InstalledBundleRecord, save_records
from tests.specify_cli.bundles.helpers import valid_manifest_dict


def _manifest(**overrides) -> BundleManifest:
    return BundleManifest.from_dict(valid_manifest_dict(**overrides))


def test_integration_clash_is_blocking():
    manifest = _manifest(integration={"id": "claude"})
    report = detect_conflicts(manifest, active_integration="copilot", installed=[])
    assert report.has_blocking_conflict is True
    assert "claude" in report.integration_clash
    assert "copilot" in report.integration_clash


def test_matching_integration_no_clash():
    manifest = _manifest(integration={"id": "copilot"})
    report = detect_conflicts(manifest, active_integration="copilot", installed=[])
    assert report.has_blocking_conflict is False


def test_components_override_does_not_change_root_integration_clash():
    manifest = _manifest(integration={"id": "claude"})
    report = detect_conflicts(
        manifest,
        active_integration="copilot",
        installed=[],
        components=[ComponentRef(kind="extensions", id="expanded-only")],
    )
    assert report.integration_clash is not None


def test_components_override_still_skips_owner():
    manifest = _manifest()
    component = ComponentRef(kind="extensions", id="expanded-only")
    owner = InstalledBundleRecord.create(
        bundle_id="demo-bundle", version="1.0.0", components=[component]
    )
    report = detect_conflicts(
        manifest, active_integration="copilot", installed=[owner], components=[component]
    )
    assert report.overlaps == []


def test_components_override_is_used_for_overlap_detection():
    manifest = _manifest(
        provides={"extensions": [{"id": "expanded-only", "version": "9.0.0"}]}
    )
    expanded_component = ComponentRef(
        kind="extensions", id="expanded-only", version="1.0.0"
    )
    other = InstalledBundleRecord.create(
        bundle_id="other", version="1.0.0", components=[expanded_component]
    )
    report = detect_conflicts(
        manifest,
        active_integration="copilot",
        installed=[other],
        components=[expanded_component],
    )
    assert report.overlaps == [
        "extension 'expanded-only' is already required by bundle 'other'."
    ]


def test_expanded_component_version_clash_is_reported():
    manifest = _manifest()
    expanded_component = ComponentRef(
        kind="presets", id="expanded-only", version="2.0.0"
    )
    other = InstalledBundleRecord.create(
        bundle_id="other",
        version="1.0.0",
        components=[
            ComponentRef(kind="presets", id="expanded-only", version="3.0.0")
        ],
    )
    report = detect_conflicts(
        manifest,
        active_integration="copilot",
        installed=[other],
        components=[expanded_component],
    )
    assert report.has_blocking_conflict
    assert "expanded-only" in report.version_clashes[0]
    assert "2.0.0" in report.version_clashes[0]
    assert "3.0.0" in report.version_clashes[0]


def test_agnostic_bundle_never_clashes():
    manifest = _manifest()  # no integration
    report = detect_conflicts(manifest, active_integration="copilot", installed=[])
    assert report.has_blocking_conflict is False


def test_overlap_with_other_bundle_is_reported():
    manifest = _manifest()
    other = InstalledBundleRecord.create(
        bundle_id="other",
        version="1.0.0",
        components=[ComponentRef(kind="presets", id="preset-a", version="2.0.0")],
    )
    report = detect_conflicts(manifest, active_integration="copilot", installed=[other])
    assert report.overlaps == [
        "preset 'preset-a' is already required by bundle 'other'."
    ]
    assert report.has_blocking_conflict is False


def test_required_only_overlap_does_not_attribute_component_ownership(tmp_path):
    manifest = _manifest()
    other = InstalledBundleRecord.create(
        bundle_id="other",
        version="1.0.0",
        components=[],
        required_components=[
            ComponentRef(kind="presets", id="preset-a", version="2.0.0")
        ],
    )
    report = detect_conflicts(manifest, active_integration="copilot", installed=[other])

    assert report.overlaps == [
        "preset 'preset-a' is already required by bundle 'other'."
    ]
    assert report.has_blocking_conflict is False
    save_records(tmp_path, [other])
    assert _bundle_overlaps(tmp_path, manifest, offline=True) == report.overlaps


def test_same_bundle_reinstall_is_not_overlap():
    manifest = _manifest()
    same = InstalledBundleRecord.create(
        bundle_id="demo-bundle",
        version="1.2.0",
        components=[ComponentRef(kind="presets", id="preset-a")],
    )
    report = detect_conflicts(manifest, active_integration="copilot", installed=[same])
    assert report.overlaps == []


def test_incompatible_pins_from_multiple_bundles_are_blocking(tmp_path):
    manifest = _manifest()
    records = [
        InstalledBundleRecord.create(
            bundle_id=name, version="1.0.0",
            components=[ComponentRef(kind="presets", id="preset-a", version=version)],
        )
        for name, version in (("compatible", "v2.0.0"), ("incompatible", "3.0.0"))
    ]
    report = detect_conflicts(manifest, "copilot", records)

    assert report.has_blocking_conflict
    assert len(report.version_clashes) == 1
    assert "incompatible" in report.version_clashes[0]
    assert "3.0.0" in report.version_clashes[0]
    assert len(report.overlaps) == 1

    save_records(tmp_path, records)
    assert report.version_clashes[0] in _bundle_overlaps(tmp_path, manifest, offline=True)


def test_unknown_existing_pin_cannot_satisfy_an_exact_pin():
    manifest = _manifest()
    other = InstalledBundleRecord.create(
        bundle_id="other", version="1.0.0",
        components=[ComponentRef(kind="presets", id="preset-a")],
    )
    report = detect_conflicts(manifest, "copilot", [other])

    assert report.has_blocking_conflict
    assert "<unknown>" in report.version_clashes[0]


def test_setting_differences_equal_settings_returns_empty():
    a = ComponentRef(kind="presets", id="p", source="cat", priority=5, strategy="replace")
    b = ComponentRef(kind="presets", id="p", source="cat", priority=5, strategy="replace")
    assert component_setting_differences(a, b) == []


def test_setting_differences_ignores_versions():
    a = ComponentRef(kind="extensions", id="e", version="1.0.0")
    b = ComponentRef(kind="extensions", id="e", version="2.0.0")
    assert component_setting_differences(a, b) == []
    assert component_setting_differences(
        a, ComponentRef(kind="extensions", id="e")
    ) == []


def test_setting_differences_reports_extension_priority_but_ignores_strategy():
    a = ComponentRef(kind="extensions", id="e", priority=1, strategy="append")
    b = ComponentRef(kind="extensions", id="e", priority=2, strategy="replace")
    assert component_setting_differences(a, b) == ["priority"]


def test_setting_differences_reports_source_for_any_kind():
    a = ComponentRef(kind="workflows", id="w", source="one")
    b = ComponentRef(kind="workflows", id="w", source="two")
    assert component_setting_differences(a, b) == ["source"]


def test_setting_differences_unset_source_differs_from_set_source():
    unset = ComponentRef(kind="extensions", id="e")
    pinned = ComponentRef(kind="extensions", id="e", source="cat")
    assert component_setting_differences(unset, pinned) == ["source"]
    assert component_setting_differences(pinned, unset) == ["source"]


def test_setting_differences_preset_fields_in_stable_order():
    a = ComponentRef(kind="presets", id="p", source="one", priority=1, strategy="append")
    b = ComponentRef(kind="presets", id="p", source="two", priority=2, strategy="replace")
    assert component_setting_differences(a, b) == ["source", "priority", "strategy"]
    assert component_setting_differences(
        a, ComponentRef(kind="presets", id="p", source="one", priority=2, strategy="append")
    ) == ["priority"]
    assert component_setting_differences(
        a, ComponentRef(kind="presets", id="p", source="one", priority=1, strategy="replace")
    ) == ["strategy"]
