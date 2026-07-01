"""Unit tests for conflict detection (T034): integration clash and overlap precedence."""
from __future__ import annotations

from specify_cli.bundler.models.manifest import BundleManifest, ComponentRef
from specify_cli.bundler.models.records import InstalledBundleRecord
from specify_cli.bundler.services.conflict import detect_conflicts
from tests.bundler_helpers import valid_manifest_dict


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


def test_agnostic_bundle_never_clashes():
    manifest = _manifest()  # no integration
    report = detect_conflicts(manifest, active_integration="copilot", installed=[])
    assert report.has_blocking_conflict is False


def test_overlap_with_other_bundle_is_reported():
    manifest = _manifest()
    other = InstalledBundleRecord.create(
        bundle_id="other",
        version="1.0.0",
        components=[ComponentRef(kind="presets", id="preset-a")],
    )
    report = detect_conflicts(manifest, active_integration="copilot", installed=[other])
    assert any("preset-a" in o and "other" in o for o in report.overlaps)
    assert report.has_blocking_conflict is False


def test_same_bundle_reinstall_is_not_overlap():
    manifest = _manifest()
    same = InstalledBundleRecord.create(
        bundle_id="demo-bundle",
        version="1.2.0",
        components=[ComponentRef(kind="presets", id="preset-a")],
    )
    report = detect_conflicts(manifest, active_integration="copilot", installed=[same])
    assert report.overlaps == []
