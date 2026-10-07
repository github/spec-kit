"""Integration tests for the install → record → remove lifecycle (offline, fake installer).

Uses :class:`FakeInstaller` so no network or real primitive machinery is touched
(Constitution Principle II network-mocking, Principle IV offline-first).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundles.installer import install_bundle, remove_bundle
from specify_cli.bundles.manifest import BundleManifest, ComponentRef
from specify_cli.bundles.records import (
    InstalledBundleRecord,
    load_records,
    records_path,
    save_records,
)
from specify_cli.bundles.resolver import resolve_install_plan
from tests.specify_cli.bundles.helpers import (
    FakeInstaller,
    make_project,
    valid_manifest_dict,
)


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


def test_second_bundle_cannot_claim_different_pin_before_mutation(tmp_path: Path):
    make_project(tmp_path)
    installer = FakeInstaller()
    first = _bundle("first", ["ext-a"], version="1.0.0")
    install_bundle(tmp_path, _plan(first), installer, manifest=first)
    other = _bundle("other", ["ext-a", "ext-b"], version="2.0.0")

    with pytest.raises(BundlerError, match="Only one version"):
        install_bundle(tmp_path, _plan(other), installer, manifest=other)

    assert [r.bundle_id for r in load_records(tmp_path)] == ["first"]
    assert installer.install_calls == [("extensions", "ext-a")]


def test_independent_requirement_blocks_conflicting_bundle_after_removal(
    tmp_path: Path,
):
    make_project(tmp_path)
    installer = FakeInstaller()
    key = ("extensions", "ext-a")
    installer.installed.add(key)
    installer.versions[key] = "1.0.0"
    first = _bundle("first", ["ext-a"], version="1.0.0")
    install_bundle(tmp_path, _plan(first), installer, manifest=first)

    record = load_records(tmp_path)[0]
    assert record.contributed_components == ()
    assert record.required_components == tuple(first.components)

    installer.installed.remove(key)
    installer.versions.pop(key)
    second = _bundle("second", ["ext-a"], version="2.0.0")
    with pytest.raises(BundlerError, match="bundle 'first' already requires version 1.0.0"):
        install_bundle(tmp_path, _plan(second), installer, manifest=second)

    assert installer.install_calls == []
    assert [r.bundle_id for r in load_records(tmp_path)] == ["first"]


def test_removal_preserves_component_required_but_not_owned_by_other_bundle(
    tmp_path: Path,
):
    make_project(tmp_path)
    installer = FakeInstaller()
    key = ("extensions", "ext-a")
    installer.installed.add(key)
    installer.versions[key] = "1.0.0"
    first = _bundle("first", ["ext-a"])
    install_bundle(tmp_path, _plan(first), installer, manifest=first)

    installer.installed.remove(key)
    installer.versions.pop(key)
    second = _bundle("second", ["ext-a"])
    install_bundle(tmp_path, _plan(second), installer, manifest=second)

    assert load_records(tmp_path)[1].contributed_components == tuple(second.components)
    result = remove_bundle(tmp_path, "second", installer)
    assert key in {(c.kind, c.id) for c in result.skipped}
    assert key in installer.installed
    assert installer.remove_calls == []

    remaining = load_records(tmp_path)
    assert remaining[0].bundle_id == "first"
    assert remaining[0].contributed_components == tuple(first.components)
    remove_bundle(tmp_path, "first", installer)
    assert key not in installer.installed
    assert installer.remove_calls == [key]


def test_update_transfers_dropped_contribution_to_requiring_bundle(tmp_path: Path):
    make_project(tmp_path)
    installer = FakeInstaller()
    first = _bundle("first", ["ext-a"])
    install_bundle(tmp_path, _plan(first), installer, manifest=first)
    save_records(
        tmp_path,
        [
            *load_records(tmp_path),
            InstalledBundleRecord.create(
                "other", "1.0.0", [], required_components=first.components
            ),
        ],
    )
    reduced = _bundle("first", [])
    result = install_bundle(
        tmp_path, _plan(reduced), installer, manifest=reduced, refresh=True
    )

    assert result.uninstalled == []
    assert ("extensions", "ext-a") in installer.installed
    remaining = {record.bundle_id: record for record in load_records(tmp_path)}
    assert remaining["first"].contributed_components == ()
    assert remaining["other"].contributed_components == tuple(first.components)

    remove_bundle(tmp_path, "other", installer)
    assert installer.remove_calls == [("extensions", "ext-a")]


@pytest.mark.parametrize("actual", [None, "2.0.0"])
def test_unpinned_install_cannot_bypass_unowned_bundle_pin(
    tmp_path: Path, actual: str | None,
):
    make_project(tmp_path)
    installer = FakeInstaller()
    key = ("steps", "shared")
    installer.installed.add(key)
    installer.versions[key] = "1.0.0"
    pinned = _step_bundle("pinned", "1.0.0")
    install_bundle(tmp_path, _plan(pinned), installer, manifest=pinned)
    assert load_records(tmp_path)[0].contributed_components == ()

    if actual is None:
        installer.installed.remove(key)
        installer.versions.pop(key)
    else:
        installer.versions[key] = actual
    unpinned = _step_bundle("unpinned")
    with pytest.raises(BundlerError, match="unpinned.*shared.*requires"):
        install_bundle(tmp_path, _plan(unpinned), installer, manifest=unpinned)

    assert installer.install_calls == []
    assert [r.bundle_id for r in load_records(tmp_path)] == ["pinned"]


def test_unpinned_install_can_share_matching_unowned_requirement(tmp_path: Path):
    make_project(tmp_path)
    installer = FakeInstaller()
    key = ("steps", "shared")
    installer.installed.add(key)
    installer.versions[key] = "1.0.0"
    pinned = _step_bundle("pinned", "1.0.0")
    install_bundle(tmp_path, _plan(pinned), installer, manifest=pinned)

    unpinned = _step_bundle("unpinned")
    result = install_bundle(tmp_path, _plan(unpinned), installer, manifest=unpinned)

    assert result.skipped == unpinned.components
    assert installer.install_calls == []
    assert load_records(tmp_path)[1].contributed_components == ()
    refreshed = install_bundle(
        tmp_path, _plan(unpinned), installer, manifest=unpinned, refresh=True
    )
    assert refreshed.skipped == unpinned.components
    assert installer.refresh_calls == []


def test_unpinned_refresh_cannot_change_unowned_bundle_pin(tmp_path: Path):
    make_project(tmp_path)
    installer = FakeInstaller()
    key = ("steps", "shared")
    installer.installed.add(key)
    installer.versions[key] = "1.0.0"
    pinned = _step_bundle("pinned", "1.0.0")
    install_bundle(tmp_path, _plan(pinned), installer, manifest=pinned)
    installer.installed.remove(key)
    installer.versions.pop(key)

    owned = _step_bundle("owned", "1.0.0")
    install_bundle(tmp_path, _plan(owned), installer, manifest=owned)
    original_record = records_path(tmp_path).read_bytes()
    unpinned = _step_bundle("owned")
    with pytest.raises(BundlerError, match="unpinned.*shared.*requires"):
        install_bundle(
            tmp_path, _plan(unpinned), installer, manifest=unpinned, refresh=True
        )

    assert installer.refresh_calls == []
    assert records_path(tmp_path).read_bytes() == original_record


def test_owned_component_drift_is_rejected_without_refresh(tmp_path: Path):
    make_project(tmp_path)
    installer = FakeInstaller()
    manifest = _bundle("first", ["ext-a"], version="1.0.0")
    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)
    installer.versions[("extensions", "ext-a")] = "0.9.0"

    with pytest.raises(BundlerError, match="0.9.0"):
        install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)
    assert installer.refresh_calls == []

    result = install_bundle(
        tmp_path, _plan(manifest), installer, manifest=manifest, refresh=True
    )
    assert result.refreshed == manifest.components


def test_shared_component_drift_cannot_be_refreshed(tmp_path: Path):
    make_project(tmp_path)
    installer = FakeInstaller()
    first = _bundle("first", ["ext-a"], version="1.0.0")
    second = _bundle("second", ["ext-a"], version="1.0.0")
    install_bundle(tmp_path, _plan(first), installer, manifest=first)
    install_bundle(tmp_path, _plan(second), installer, manifest=second)
    installer.versions[("extensions", "ext-a")] = "0.9.0"

    with pytest.raises(BundlerError, match="0.9.0"):
        install_bundle(tmp_path, _plan(first), installer, manifest=first, refresh=True)
    assert installer.refresh_calls == []


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"priority": 20}, "priority"),
        ({"strategy": "replace"}, "strategy"),
        ({"source": "trusted"}, "source"),
    ],
)
@pytest.mark.parametrize("required_only", [False, True])
def test_shared_refresh_preserves_other_bundles_install_requirements(
    tmp_path: Path, change: dict, field: str, required_only: bool,
):
    make_project(tmp_path)
    installer = FakeInstaller()
    first = _preset_bundle("first")
    other = _preset_bundle("other")
    install_bundle(tmp_path, _plan(first), installer, manifest=first)
    if required_only:
        save_records(
            tmp_path,
            [
                *load_records(tmp_path),
                InstalledBundleRecord.create(
                    "other", "1.0.0", [], required_components=other.components
                ),
            ],
        )
    else:
        install_bundle(tmp_path, _plan(other), installer, manifest=other)
    before = records_path(tmp_path).read_bytes()

    changed = _preset_bundle("first", **change)
    with pytest.raises(BundlerError, match=rf"shared preset.*{field}"):
        install_bundle(
            tmp_path, _plan(changed), installer, manifest=changed, refresh=True
        )

    assert installer.refresh_calls == []
    assert records_path(tmp_path).read_bytes() == before


def test_shared_install_rejects_conflicting_preset_priority(tmp_path: Path):
    make_project(tmp_path)
    installer = FakeInstaller()
    first = _preset_bundle("first")
    install_bundle(tmp_path, _plan(first), installer, manifest=first)
    before = records_path(tmp_path).read_bytes()
    second = _preset_bundle("second", priority=20)
    second.extensions.append(
        ComponentRef(kind="extensions", id="ext-new", version="1.0.0")
    )

    with pytest.raises(BundlerError, match="shared preset.*priority"):
        install_bundle(tmp_path, _plan(second), installer, manifest=second)

    assert installer.install_calls == [("presets", "preset-a")]
    assert ("extensions", "ext-new") not in installer.installed
    assert installer.refresh_calls == []
    assert records_path(tmp_path).read_bytes() == before


def test_shared_refresh_allows_matching_install_requirements(tmp_path: Path):
    make_project(tmp_path)
    installer = FakeInstaller()
    first = _preset_bundle("first")
    second = _preset_bundle("second")
    install_bundle(tmp_path, _plan(first), installer, manifest=first)
    install_bundle(tmp_path, _plan(second), installer, manifest=second)

    result = install_bundle(
        tmp_path, _plan(second), installer, manifest=second, refresh=True
    )

    assert result.refreshed == second.components
    assert installer.refresh_calls == [("presets", "preset-a")]
    assert len(load_records(tmp_path)) == 2


def test_unpinned_shared_step_cannot_refresh_another_bundles_pin(tmp_path: Path):
    make_project(tmp_path)
    installer = FakeInstaller()
    pinned_data = valid_manifest_dict()
    pinned_data["bundle"]["id"] = "pinned"
    pinned_data["provides"] = {"steps": [{"id": "shared", "version": "1.0.0"}]}
    pinned = BundleManifest.from_dict(pinned_data)
    unpinned_data = valid_manifest_dict()
    unpinned_data["bundle"]["id"] = "unpinned"
    unpinned_data["provides"] = {"steps": [{"id": "shared"}]}
    unpinned = BundleManifest.from_dict(unpinned_data)
    install_bundle(tmp_path, _plan(pinned), installer, manifest=pinned)
    install_bundle(tmp_path, _plan(unpinned), installer, manifest=unpinned)

    with pytest.raises(BundlerError, match="unpinned shared"):
        install_bundle(
            tmp_path, _plan(unpinned), installer, manifest=unpinned, refresh=True
        )
    assert installer.refresh_calls == []


@pytest.mark.parametrize("winning,accepted", [("expected", True), ("other", False)])
def test_source_is_checked_even_when_component_is_already_installed(
    tmp_path: Path, monkeypatch, winning: str, accepted: bool,
):
    from specify_cli.bundles.adapters import DefaultPrimitiveInstaller
    from specify_cli.extensions import ExtensionCatalog, ExtensionRegistry

    make_project(tmp_path)
    ExtensionRegistry(tmp_path / ".specify" / "extensions").add(
        "ext-a", {"version": "1.0.0"}
    )
    fetches = []

    def fetch(self, source, force_refresh=False):
        fetches.append(source.name)
        return {
            "schema_version": "1.0",
            "extensions": {"ext-a": {"version": "1.0.0"}},
        }

    from specify_cli.extensions import CatalogEntry

    monkeypatch.setattr(
        ExtensionCatalog, "get_active_catalogs",
        lambda self: [
            CatalogEntry("https://example.com/catalog.json", winning, 1, True)
        ],
    )
    monkeypatch.setattr(ExtensionCatalog, "_fetch_single_catalog", fetch)
    data = valid_manifest_dict()
    data["provides"] = {
        "extensions": [
            {"id": "ext-a", "version": "1.0.0", "source": "expected"}
        ]
    }
    manifest = BundleManifest.from_dict(data)

    if accepted:
        result = install_bundle(
            tmp_path, _plan(manifest), DefaultPrimitiveInstaller(), manifest=manifest
        )
        assert result.skipped == manifest.components
        assert fetches == [winning]
    else:
        with pytest.raises(BundlerError, match="expected"):
            install_bundle(
                tmp_path, _plan(manifest), DefaultPrimitiveInstaller(), manifest=manifest
            )
        assert not records_path(tmp_path).exists()


def test_install_rejects_version_change_without_refresh(tmp_path: Path):
    """A normal install must not advance a record past stale components.

    ``bundle install`` is intentionally idempotent.  When the same bundle ID
    resolves to a different version, callers must use ``bundle update`` so the
    owned primitives are refreshed before the record is changed.
    """
    make_project(tmp_path)
    installer = FakeInstaller()

    version_one = _bundle("demo", ["ext-a"], version="1.0.0")
    install_bundle(tmp_path, _plan(version_one), installer, manifest=version_one)

    version_two = _bundle("demo", ["ext-a"], version="2.0.0")
    with pytest.raises(BundlerError, match="bundle update"):
        install_bundle(tmp_path, _plan(version_two), installer, manifest=version_two)

    record = load_records(tmp_path)[0]
    assert record.version == "1.0.0"
    assert len(installer.install_calls) == 1


@pytest.mark.parametrize("kind,updates", [
    ("extensions", {"version": "2.0.0"}),
    ("presets", {"version": "3.0.0"}),
    ("steps", {"version": "1.0.0"}),
    ("workflows", {"version": "0.4.0"}),
    ("extensions", {"source": "https://example.com/catalog.json"}),
    ("presets", {"priority": 20}),
    ("presets", {"strategy": "prepend"}),
    ("extensions", None),
    ("presets", None),
    ("steps", None),
    ("workflows", None),
])
def test_install_requires_refresh_for_owned_component_changes(
    tmp_path: Path, kind: str, updates: dict | None,
):
    make_project(tmp_path)
    data = valid_manifest_dict()
    original = BundleManifest.from_dict(data)
    installer = FakeInstaller()
    install_bundle(tmp_path, _plan(original), installer, manifest=original)
    original_record = records_path(tmp_path).read_bytes()
    original_installed = set(installer.installed)
    installer.install_calls.clear()

    component_id = data["provides"][kind][0]["id"]
    if updates is None:
        data["provides"][kind] = []
    else:
        data["provides"][kind][0].update(updates)
    # Even a new component ordered before the changed one must not be installed.
    data["provides"]["extensions"].insert(0, {"id": "ext-new", "version": "1.0.0"})
    changed = BundleManifest.from_dict(data)
    plan = _plan(changed)

    with pytest.raises(BundlerError, match="--refresh"):
        install_bundle(tmp_path, plan, installer, manifest=changed)

    assert records_path(tmp_path).read_bytes() == original_record
    assert installer.installed == original_installed
    assert installer.install_calls == []
    assert installer.refresh_calls == []
    assert installer.remove_calls == []

    result = install_bundle(tmp_path, plan, installer, manifest=changed, refresh=True)
    record = load_records(tmp_path)[0]
    assert record.version == original.bundle.version
    assert record.contributed_components == tuple(plan.components)
    assert {(c.kind, c.id) for c in result.installed} == {("extensions", "ext-new")}
    if updates is None:
        assert installer.remove_calls == [(kind, component_id)]
        assert (kind, component_id) not in installer.installed
    else:
        assert (kind, component_id) in installer.refresh_calls
        assert installer.remove_calls == []


def test_install_allows_reordered_components_and_additions(tmp_path: Path):
    make_project(tmp_path)
    data = valid_manifest_dict()
    data["provides"]["extensions"].append({"id": "ext-b", "version": "1.0.0"})
    original = BundleManifest.from_dict(data)
    installer = FakeInstaller()
    install_bundle(tmp_path, _plan(original), installer, manifest=original)

    data["provides"]["extensions"].reverse()
    # Identity includes kind: a step can have the same ID as an extension.
    data["provides"]["steps"].append({"id": "ext-a"})
    changed = BundleManifest.from_dict(data)
    plan = _plan(changed)
    result = install_bundle(tmp_path, plan, installer, manifest=changed)

    assert {(c.kind, c.id) for c in result.installed} == {("steps", "ext-a")}
    assert len(result.skipped) == 5
    assert installer.refresh_calls == []
    assert load_records(tmp_path)[0].contributed_components == tuple(plan.components)


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


def test_remove_converts_raw_installer_exception_to_bundler_error(tmp_path: Path):
    """A raw exception from a primitive installer (e.g. an OSError from an
    unreadable workflow registry surfacing through _WorkflowKindManager's
    fail-closed construction) must not propagate uncaught out of
    remove_bundle: install_bundle already converts any non-BundlerError
    exception into a clean BundlerError, but remove_bundle had no such
    conversion, so the CLI's `bundle remove` (which only catches
    BundlerError) would let a raw exception through with no clean message
    and no removal side effects should occur either."""
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    def boom(project_root, component):
        raise OSError("workflow registry unreadable")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(installer, "is_installed", boom)
        with pytest.raises(BundlerError):
            remove_bundle(tmp_path, "demo-bundle", installer)

    # No removal side effects: the bundle record must still be present.
    assert {r.bundle_id for r in load_records(tmp_path)} == {"demo-bundle"}


def test_remove_partial_failure_message_reflects_partial_state(tmp_path: Path):
    """A failure can occur after earlier components in the same bundle have
    already been removed from disk. The bundle record is left unchanged
    (save_records never runs on this path), so it still claims the bundle
    fully installed -- but the message must not claim "No changes were
    recorded" when components were, in fact, already removed."""
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    real_remove = installer.remove
    calls = {"n": 0}

    def remove_then_fail(project_root, component):
        calls["n"] += 1
        if calls["n"] == 1:
            return real_remove(project_root, component)
        raise OSError("disk full")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(installer, "remove", remove_then_fail)
        with pytest.raises(BundlerError) as exc_info:
            remove_bundle(tmp_path, "demo-bundle", installer)

    message = str(exc_info.value)
    assert "no changes were recorded" not in message.lower()
    assert {r.bundle_id for r in load_records(tmp_path)} == {"demo-bundle"}


def test_remove_bundler_error_from_installer_after_partial_removal_reports_partial_state(
    tmp_path: Path,
):
    """If the primitive installer itself raises BundlerError (not a raw/
    unexpected exception) after an earlier component in the same bundle was
    already removed, the surfaced message must still carry the same
    partial-removal detail as the generic-exception path -- a bare
    ``except BundlerError: raise`` would re-raise the installer's original
    message verbatim with no mention that the project may now be partially
    uninstalled."""
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    real_remove = installer.remove
    calls = {"n": 0}

    def remove_then_raise_bundler_error(project_root, component):
        calls["n"] += 1
        if calls["n"] == 1:
            return real_remove(project_root, component)
        raise BundlerError("kind manager refused removal")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(installer, "remove", remove_then_raise_bundler_error)
        with pytest.raises(BundlerError) as exc_info:
            remove_bundle(tmp_path, "demo-bundle", installer)

    message = str(exc_info.value)
    assert "no changes were recorded" not in message.lower()
    assert "kind manager refused removal" in message
    assert "partially uninstalled" in message.lower()
    assert {r.bundle_id for r in load_records(tmp_path)} == {"demo-bundle"}


def test_remove_bundler_error_from_installer_with_zero_removed_reports_no_changes(
    tmp_path: Path,
):
    """When the installer raises BundlerError before anything was actually
    removed, the message should not misleadingly claim partial state."""
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    def boom(project_root, component):
        raise BundlerError("kind manager unavailable")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(installer, "is_installed", boom)
        with pytest.raises(BundlerError) as exc_info:
            remove_bundle(tmp_path, "demo-bundle", installer)

    message = str(exc_info.value)
    assert "no components were removed" in message.lower()
    assert "no removal was attempted" in message.lower()
    assert "partially uninstalled" not in message.lower()
    assert "kind manager unavailable" in message
    assert {r.bundle_id for r in load_records(tmp_path)} == {"demo-bundle"}


def test_remove_zero_completed_removals_still_cautions_about_partial_changes(
    tmp_path: Path,
):
    """`result.uninstalled` only records a component after its `remove()`
    call returns successfully. If the very first `remove()` call itself
    raises after already deleting some files, zero completed removals are
    recorded even though the project may already be partially uninstalled --
    the zero-count message must not claim "No components were removed" as
    an unqualified fact; it must caution that the failing component may
    have made partial changes before raising."""
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    def boom(project_root, component):
        # Simulates a remove() that deletes some files before raising --
        # from the caller's perspective this component was never recorded
        # as completed, but disk state may already be partially changed.
        raise OSError("disk full partway through removal")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(installer, "remove", boom)
        with pytest.raises(BundlerError) as exc_info:
            remove_bundle(tmp_path, "demo-bundle", installer)

    message = str(exc_info.value)
    assert "no components were removed" in message.lower()
    assert "partial" in message.lower()
    assert "partially uninstalled" in message.lower()
    assert {r.bundle_id for r in load_records(tmp_path)} == {"demo-bundle"}


def test_remove_record_save_failure_reports_partial_state(tmp_path: Path):
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)
    record_file = records_path(tmp_path)
    original_record = record_file.read_bytes()

    def fail_dump(_data, handle, *_args, **_kwargs):
        handle.write('{"partial":')
        handle.flush()
        raise OSError("disk full")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "specify_cli.bundles.yamlio.json.dump",
            fail_dump,
        )
        with pytest.raises(BundlerError) as exc_info:
            remove_bundle(tmp_path, "demo-bundle", installer)

    message = str(exc_info.value)
    assert "disk full" in message
    assert "partially uninstalled" in message.lower()
    assert installer.installed == set()
    assert record_file.read_bytes() == original_record
    assert {r.bundle_id for r in load_records(tmp_path)} == {"demo-bundle"}


def test_remove_record_save_failure_without_remove_attempt_is_not_partial(
    tmp_path: Path,
):
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)
    installer.installed.clear()

    def fail_save(*_args, **_kwargs):
        raise OSError("disk full")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "specify_cli.bundles.installer.save_records",
            fail_save,
        )
        with pytest.raises(BundlerError) as exc_info:
            remove_bundle(tmp_path, "demo-bundle", installer)

    message = str(exc_info.value)
    assert "no removal was attempted" in message.lower()
    assert "partially uninstalled" not in message.lower()
    assert {r.bundle_id for r in load_records(tmp_path)} == {"demo-bundle"}


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
    assert gone not in result.skipped
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
    installer.versions[("extensions", "ext-a")] = "1.0.0"

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
    installer.versions[("extensions", "ext-a")] = "1.0.0"

    install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    contributed = {
        (c.kind, c.id) for c in load_records(tmp_path)[0].contributed_components
    }
    assert ("extensions", "ext-a") not in contributed

    remove_bundle(tmp_path, "demo-bundle", installer)
    assert ("extensions", "ext-a") in installer.installed


def test_install_rejects_independently_installed_component_at_other_version(
    tmp_path: Path,
):
    # An independently installed component is skipped and never refreshed, so
    # recording the bundle over a different version would leave the project
    # running the old one under a record that says otherwise (#4434).
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    installer.installed.add(("extensions", "ext-a"))
    installer.versions[("extensions", "ext-a")] = "0.9.0"

    with pytest.raises(
        BundlerError, match=r"extension 'ext-a' to 1\.0\.0, but 0\.9\.0 is installed"
    ):
        install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    assert installer.install_calls == []
    assert not records_path(tmp_path).exists()


def test_refresh_rejects_independently_installed_component_at_other_version(
    tmp_path: Path,
):
    # bundle update never refreshes an unowned component, so a new pin it does
    # not meet must fail instead of advancing the record past it.
    make_project(tmp_path)
    installer = FakeInstaller()
    installer.installed.add(("extensions", "ext-a"))
    installer.versions[("extensions", "ext-a")] = "1.0.0"
    man_v1 = _bundle("demo", ["ext-a"])
    install_bundle(tmp_path, _plan(man_v1), installer, manifest=man_v1)
    original_record = records_path(tmp_path).read_bytes()

    man_v2 = _bundle("demo", ["ext-a"], version="2.0.0")
    with pytest.raises(BundlerError, match=r"to 2\.0\.0, but 1\.0\.0 is installed"):
        install_bundle(
            tmp_path, _plan(man_v2), installer, manifest=man_v2, refresh=True
        )

    assert installer.refresh_calls == []
    assert records_path(tmp_path).read_bytes() == original_record


def test_install_rejects_independently_installed_component_of_unknown_version(
    tmp_path: Path,
):
    # A registry entry without a readable version can't be shown to meet the
    # pin, and skipping it would recreate the #4434 mismatch.
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    installer.installed.add(("extensions", "ext-a"))

    with pytest.raises(
        BundlerError, match=r"ext-a' to 1\.0\.0, but its installed version is unknown"
    ):
        install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    assert installer.install_calls == []
    assert not records_path(tmp_path).exists()


def test_install_converts_raw_pin_check_exception_to_bundler_error(
    tmp_path: Path,
):
    # The pin check runs before anything is installed, but an unreadable
    # registry (e.g. _WorkflowKindManager failing closed at construction) must
    # still surface as the clean BundlerError the CLI catches.
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    installer.installed.add(("extensions", "ext-a"))

    def boom(project_root, component):
        raise OSError("workflow registry unreadable")

    installer.installed_version = boom
    with pytest.raises(BundlerError, match="workflow registry unreadable"):
        install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    assert installer.install_calls == []
    assert not records_path(tmp_path).exists()


def test_independently_installed_component_at_pinned_version_stays_unowned(
    tmp_path: Path,
):
    make_project(tmp_path)
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    installer = FakeInstaller()
    installer.installed.add(("extensions", "ext-a"))
    installer.versions[("extensions", "ext-a")] = "v1.0.0"

    result = install_bundle(tmp_path, _plan(manifest), installer, manifest=manifest)

    assert ("extensions", "ext-a") in {(c.kind, c.id) for c in result.skipped}
    contributed = {
        (c.kind, c.id) for c in load_records(tmp_path)[0].contributed_components
    }
    assert ("extensions", "ext-a") not in contributed


def _bundle(manifest_id, ext_ids, *, version="1.0.0"):
    data = valid_manifest_dict()
    data["bundle"]["id"] = manifest_id
    data["bundle"]["version"] = version
    data["provides"] = {
        "extensions": [{"id": e, "version": version} for e in ext_ids]
    }
    return BundleManifest.from_dict(data)


def _step_bundle(bundle_id: str, version: str | None = None) -> BundleManifest:
    data = valid_manifest_dict()
    data["bundle"]["id"] = bundle_id
    step = {"id": "shared"}
    if version is not None:
        step["version"] = version
    data["provides"] = {"steps": [step]}
    return BundleManifest.from_dict(data)


def _preset_bundle(
    bundle_id: str, *, priority: int = 10, strategy: str = "append",
    source: str | None = None,
) -> BundleManifest:
    data = valid_manifest_dict()
    data["bundle"]["id"] = bundle_id
    preset = {
        "id": "preset-a", "version": "2.0.0",
        "priority": priority, "strategy": strategy,
    }
    if source is not None:
        preset["source"] = source
    data["provides"] = {"presets": [preset]}
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


def test_install_result_changed_reports_uninstalled():
    # A `bundle update` that only DROPS components (new manifest reduces
    # provides) populates uninstalled with nothing installed/refreshed; that is
    # still a mutating change, so `changed` must be True — not a false no-op.
    from specify_cli.bundles.installer import InstallResult
    from specify_cli.bundles.manifest import ComponentRef

    result = InstallResult(bundle_id="x")
    assert result.changed is False  # empty == no change
    result.uninstalled.append(ComponentRef(kind="presets", id="p1"))
    assert result.changed is True
