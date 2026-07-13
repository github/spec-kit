"""Integration tests for the install → record → remove lifecycle (offline, fake installer).

Uses :class:`FakeInstaller` so no network or real primitive machinery is touched
(Constitution Principle II network-mocking, Principle IV offline-first).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundler.models.manifest import BundleManifest
from specify_cli.bundler.models.records import load_records
from specify_cli.bundler.services.installer import install_bundle, remove_bundle
from specify_cli.bundler.services.resolver import resolve_install_plan
from tests.bundler_helpers import FakeInstaller, make_project, valid_manifest_dict


def _plan(manifest):
    return resolve_install_plan(
        manifest, speckit_version="0.11.2", active_integration="copilot"
    )


def test_install_records_and_invokes_primitives(tmp_path: Path):
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()

    result = install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    assert len(result.installed) == 4
    assert len(installer.install_calls) == 4
    records = load_records(tmp_path)
    assert len(records) == 1
    assert records[0].bundle_id == "demo-bundle"


def test_install_is_idempotent(tmp_path: Path):
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()

    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)
    second = install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    # Second install adds nothing and does not duplicate the record.
    assert second.installed == []
    assert len(second.skipped) == 4
    assert len(load_records(tmp_path)) == 1


def test_partial_failure_rolls_back_and_records_nothing(tmp_path: Path):
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller(fail_on="preset-a")

    with pytest.raises(BundlerError):
        install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    # ext-a was installed first, then rolled back; no record persisted.
    assert installer.installed == set()
    assert load_records(tmp_path) == []


def test_remove_is_non_collateral(tmp_path: Path):
    make_project(tmp_path)
    installer = FakeInstaller()

    # Bundle A provides a shared preset; Bundle B also provides it.
    data_a = valid_manifest_dict()
    data_a["bundle"]["id"] = "a"
    data_b = valid_manifest_dict()
    data_b["bundle"]["id"] = "b"
    data_b["provides"] = {"presets": [
        {"id": "preset-a", "version": "2.0.0", "priority": 10, "strategy": "append"}
    ]}

    man_a = BundleManifest.from_dict(data_a)
    man_b = BundleManifest.from_dict(data_b)
    install_bundle(tmp_path, _plan(man_a), installer, manifest=man_a)
    install_bundle(tmp_path, _plan(man_b), installer, manifest=man_b)

    # Removing B must NOT uninstall preset-a (still needed by A).
    result = remove_bundle(tmp_path, "b", installer)
    assert ("presets", "preset-a") in {(c.kind, c.id) for c in result.skipped}
    assert installer.is_installed(tmp_path, man_a.presets[0]) is True

    remaining = {r.bundle_id for r in load_records(tmp_path)}
    assert remaining == {"a"}


def test_remove_unknown_bundle_errors(tmp_path: Path):
    make_project(tmp_path)
    with pytest.raises(BundlerError, match="not installed"):
        remove_bundle(tmp_path, "ghost", FakeInstaller())


def test_remove_reports_uninstalled_not_installed(tmp_path: Path):
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    result = remove_bundle(tmp_path, "demo-bundle", installer)

    # Removal flows populate the dedicated ``uninstalled`` list; ``installed``
    # stays empty so the result type is never ambiguous for callers.
    assert result.installed == []
    assert len(result.uninstalled) == 4
    assert installer.installed == set()


def test_remove_counts_only_components_actually_removed(tmp_path: Path):
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    # Simulate one contributed component already gone from disk (e.g. removed
    # out of band). It must not be reported as uninstalled and remove() must
    # not be called for it.
    gone = manifest.components[0]
    installer.installed.discard((gone.kind, gone.id))

    result = remove_bundle(tmp_path, "demo-bundle", installer)

    assert len(result.uninstalled) == 3
    assert (gone.kind, gone.id) not in installer.remove_calls
    assert gone in result.skipped
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()

    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)
    result = install_bundle(
        tmp_path, _plan(manifest), installer, manifest=manifest, refresh=True
    )

    # With refresh, already-installed components are re-applied, not skipped.
    assert result.skipped == []
    assert len(result.refreshed) == 4
    assert len(installer.refresh_calls) == 4
    assert result.changed is True


def test_refresh_falls_back_to_install_without_hook(tmp_path: Path):
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())

    class NoRefreshInstaller(FakeInstaller):
        refresh = None  # type: ignore[assignment]

    installer = NoRefreshInstaller()
    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)
    before = len(installer.install_calls)
    result = install_bundle(
        tmp_path, _plan(manifest), installer, manifest=manifest, refresh=True
    )

    # No refresh hook → re-install path keeps components current.
    assert len(result.refreshed) == 4
    assert len(installer.install_calls) == before + 4


def test_update_preserves_original_installed_at(tmp_path: Path):
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    original = load_records(tmp_path)[0].installed_at

    # A refresh (bundle update) must not rewrite the original install timestamp.
    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest, refresh=True)

    assert load_records(tmp_path)[0].installed_at == original


def test_refresh_does_not_touch_independently_installed_component(tmp_path: Path):
    # bundle update (refresh) must not re-apply a component installed
    # independently and tracked by no bundle — refreshing it would be a
    # collateral change to something the bundle does not own (FR-022).
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    installer.installed.add(("extensions", "ext-a"))

    result = install_bundle(
        tmp_path, _plan(manifest), installer, manifest=manifest, refresh=True
    )

    # ext-a is skipped (not refreshed) and never attributed to the bundle.
    assert ("extensions", "ext-a") not in installer.refresh_calls
    assert ("extensions", "ext-a") in {(c.kind, c.id) for c in result.skipped}
    assert ("extensions", "ext-a") not in {(c.kind, c.id) for c in result.refreshed}
    contributed = {
        (c.kind, c.id) for c in load_records(tmp_path)[0].contributed_components
    }
    assert ("extensions", "ext-a") not in contributed


def test_pre_existing_component_is_not_attributed_or_removed(tmp_path: Path):
    # A component installed independently (before any bundle) must not be
    # attributed to the bundle, so removing the bundle never uninstalls it
    # (FR-022, no collateral removal).
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    # Pre-install ext-a independently — no bundle record references it yet.
    installer.installed.add(("extensions", "ext-a"))

    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    contributed = {
        (c.kind, c.id) for c in load_records(tmp_path)[0].contributed_components
    }
    assert ("extensions", "ext-a") not in contributed

    remove_bundle(tmp_path, "demo-bundle", installer)
    assert ("extensions", "ext-a") in installer.installed


def _bundle(manifest_id, ext_ids, *, version="1.0.0"):
    data = valid_manifest_dict()
    data["bundle"]["id"] = manifest_id
    data["bundle"]["version"] = version
    data["provides"] = {
        "extensions": [{"id": e, "version": version} for e in ext_ids]
    }
    return BundleManifest.from_dict(data)


def test_update_uninstalls_components_dropped_by_new_version(tmp_path: Path):
    """`bundle update` must uninstall components the new version no longer
    ships, instead of orphaning them (installed on disk, tracked by nothing)."""
    make_project(tmp_path)
    installer = FakeInstaller()

    man_v1 = _bundle("demo", ["ext-a", "ext-b"])
    install_bundle(tmp_path, _plan(man_v1), installer, manifest=man_v1)
    assert ("extensions", "ext-b") in installer.installed

    man_v2 = _bundle("demo", ["ext-a"], version="2.0.0")
    result = install_bundle(
        tmp_path, _plan(man_v2), installer, manifest=man_v2, refresh=True
    )

    # ext-b was dropped by v2 -> uninstalled and reported.
    assert ("extensions", "ext-b") in installer.remove_calls
    assert ("extensions", "ext-b") in {(c.kind, c.id) for c in result.uninstalled}
    assert ("extensions", "ext-b") not in installer.installed
    assert ("extensions", "ext-a") in installer.installed

    # The saved record lists only ext-a.
    rec = next(r for r in load_records(tmp_path) if r.bundle_id == "demo")
    keys = {(c.kind, c.id) for c in rec.contributed_components}
    assert ("extensions", "ext-a") in keys
    assert ("extensions", "ext-b") not in keys


def test_update_keeps_component_still_needed_by_sibling_bundle(tmp_path: Path):
    """A dropped component still owned by another bundle stays installed."""
    make_project(tmp_path)
    installer = FakeInstaller()

    man_sib = _bundle("sibling", ["ext-b"])
    install_bundle(tmp_path, _plan(man_sib), installer, manifest=man_sib)

    man_v1 = _bundle("demo", ["ext-a", "ext-b"])
    install_bundle(tmp_path, _plan(man_v1), installer, manifest=man_v1)

    man_v2 = _bundle("demo", ["ext-a"], version="2.0.0")
    install_bundle(
        tmp_path, _plan(man_v2), installer, manifest=man_v2, refresh=True
    )

    # ext-b is still needed by 'sibling' -> not removed, stays installed.
    assert ("extensions", "ext-b") not in installer.remove_calls
    assert ("extensions", "ext-b") in installer.installed

    # But demo's record no longer attributes it.
    rec = next(r for r in load_records(tmp_path) if r.bundle_id == "demo")
    assert ("extensions", "ext-b") not in {
        (c.kind, c.id) for c in rec.contributed_components
    }
