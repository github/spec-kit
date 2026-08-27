"""Unit tests for the bundle manifest validator service."""
from __future__ import annotations

import pytest

from specify_cli.bundler.models.manifest import BundleManifest
from specify_cli.bundler.services import validator as validator_mod
from specify_cli.bundler.services.validator import validate_manifest
from tests.bundler_helpers import valid_manifest_dict


def _manifest(**overrides) -> BundleManifest:
    return BundleManifest.from_dict(valid_manifest_dict(**overrides))


def test_invalid_speckit_constraint_reported_as_error():
    manifest = _manifest(requires={"speckit_version": ">>bad"})
    report = validate_manifest(manifest)
    assert not report.ok
    assert any("speckit_version" in e for e in report.errors)


def test_non_bundler_error_not_swallowed(monkeypatch):
    # A programming error inside constraint parsing must propagate, not be
    # masked behind an "invalid constraint" validation message.
    def boom(_value):
        raise RuntimeError("unexpected bug")

    monkeypatch.setattr(validator_mod, "parse_constraint", boom)
    manifest = _manifest(requires={"speckit_version": ">=1.0.0"})
    with pytest.raises(RuntimeError, match="unexpected bug"):
        validate_manifest(manifest)
