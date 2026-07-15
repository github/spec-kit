"""Integration tests for the install → record → remove lifecycle (offline, fake installer).

Uses :class:`FakeInstaller` so no network or real primitive machinery is touched
(Constitution Principle II network-mocking, Principle IV offline-first).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundler.models.manifest import BundleManifest
from specify_cli.bundler.models.records import load_records, records_path
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
            "specify_cli.bundler.lib.yamlio.json.dump",
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
            "specify_cli.bundler.services.installer.save_records",
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
