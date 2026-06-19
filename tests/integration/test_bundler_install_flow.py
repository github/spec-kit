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
