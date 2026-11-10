"""Unit tests for the bundle manifest validator service."""
from __future__ import annotations

import pytest

from specify_cli.bundles import validator as validator_mod
from specify_cli.bundles.manifest import BundleManifest, ComponentRef
from specify_cli.bundles.validator import validate_manifest
from tests.specify_cli.bundles.helpers import valid_manifest_dict


def _manifest(**overrides) -> BundleManifest:
    return BundleManifest.from_dict(valid_manifest_dict(**overrides))


def test_invalid_speckit_constraint_reported_as_error():
    manifest = _manifest(requires={"speckit_version": ">>bad"})
    report = validate_manifest(manifest)
    assert not report.ok
    assert any("speckit_version" in e for e in report.errors)


def test_duplicate_component_id_cannot_request_two_versions():
    data = valid_manifest_dict()
    data["provides"]["extensions"].append({"id": "ext-a", "version": "2.0.0"})

    report = validate_manifest(BundleManifest.from_dict(data))

    assert not report.ok
    assert any(
        "ext-a" in error and "duplicate" in error.lower()
        for error in report.errors
    )


def test_components_override_is_checked():
    manifest = _manifest()
    expanded_component = ComponentRef(
        kind="extensions", id="expanded-only", version="1.0.0"
    )

    report = validate_manifest(
        manifest,
        reference_checker=lambda component: "not found",
        components=[expanded_component],
    )

    assert report.errors == [
        "Unresolved reference extension:expanded-only@1.0.0: not found"
    ]


def test_unresolved_expanded_component_is_reported():
    manifest = _manifest()
    expanded_component = ComponentRef(
        kind="extensions", id="expanded-only", version="1.0.0"
    )

    report = validate_manifest(
        manifest,
        reference_checker=lambda component: (
            "missing expanded component" if component.id == "expanded-only" else None
        ),
        components=[*manifest.components, expanded_component],
    )

    assert any("expanded-only" in error for error in report.errors)


def test_non_bundler_error_not_swallowed(monkeypatch):
    # A programming error inside constraint parsing must propagate, not be
    # masked behind an "invalid constraint" validation message.
    def boom(_value):
        raise RuntimeError("unexpected bug")

    monkeypatch.setattr(validator_mod, "parse_constraint", boom)
    manifest = _manifest(requires={"speckit_version": ">=1.0.0"})
    with pytest.raises(RuntimeError, match="unexpected bug"):
        validate_manifest(manifest)
