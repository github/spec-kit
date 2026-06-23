"""Contract tests for the bundle manifest schema (bundle.yml).

Mirrors contracts/bundle-manifest.schema.md: required identity/metadata fields,
semver pinning of components, preset priority+strategy, integration optionality.
"""
from __future__ import annotations

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundler.models.manifest import BundleManifest
from tests.bundler_helpers import valid_manifest_dict


def test_valid_manifest_has_no_structural_errors():
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    assert manifest.structural_errors() == []
    assert manifest.bundle.id == "demo-bundle"
    assert manifest.is_agnostic() is True


def test_missing_required_field_is_reported_by_name():
    data = valid_manifest_dict()
    del data["bundle"]["license"]
    errors = BundleManifest.from_dict(data).structural_errors()
    assert any("bundle.license" in e for e in errors)


def test_unsupported_schema_version_is_rejected():
    data = valid_manifest_dict(schema_version="9.9")
    errors = BundleManifest.from_dict(data).structural_errors()
    assert any("schema_version" in e for e in errors)


def test_non_semver_bundle_version_is_rejected():
    data = valid_manifest_dict()
    data["bundle"]["version"] = "not-a-version"
    errors = BundleManifest.from_dict(data).structural_errors()
    assert any("semver" in e for e in errors)


def test_preset_requires_priority_and_strategy():
    data = valid_manifest_dict()
    data["provides"]["presets"] = [{"id": "p", "version": "1.0.0"}]
    errors = BundleManifest.from_dict(data).structural_errors()
    assert any("priority" in e for e in errors)
    assert any("strategy" in e for e in errors)


def test_invalid_preset_strategy_is_rejected():
    data = valid_manifest_dict()
    data["provides"]["presets"][0]["strategy"] = "merge"
    errors = BundleManifest.from_dict(data).structural_errors()
    assert any("strategy" in e for e in errors)


def test_non_integer_priority_raises_actionable_error():
    data = valid_manifest_dict()
    data["provides"]["presets"][0]["priority"] = "high"
    with pytest.raises(BundlerError, match="priority must be an integer"):
        BundleManifest.from_dict(data)


def test_non_step_components_must_be_pinned():
    data = valid_manifest_dict()
    data["provides"]["extensions"] = [{"id": "ext-unpinned"}]
    errors = BundleManifest.from_dict(data).structural_errors()
    assert any("must be pinned" in e for e in errors)


def test_steps_may_be_unpinned():
    data = valid_manifest_dict()
    data["provides"]["steps"] = [{"id": "step-x"}]
    manifest = BundleManifest.from_dict(data)
    assert manifest.structural_errors() == []


def test_integration_makes_bundle_non_agnostic():
    data = valid_manifest_dict(integration={"id": "copilot"})
    manifest = BundleManifest.from_dict(data)
    assert manifest.is_agnostic() is False
    assert manifest.integration.id == "copilot"


def test_components_property_orders_by_kind():
    manifest = BundleManifest.from_dict(valid_manifest_dict())
    kinds = [c.kind for c in manifest.components]
    assert kinds == ["extensions", "presets", "steps", "workflows"]


def test_string_tags_rejected_not_split_per_character():
    # A bare string would otherwise be iterated character-by-character; the
    # schema requires a list of strings.
    data = valid_manifest_dict()
    data["tags"] = "security"
    with pytest.raises(BundlerError, match="'tags' must be a list of strings"):
        BundleManifest.from_dict(data)


def test_unsafe_bundle_id_flagged_by_structural_validation():
    data = valid_manifest_dict()
    data["bundle"]["id"] = "../evil"
    manifest = BundleManifest.from_dict(data)
    errors = manifest.structural_errors()
    assert any("bundle.id" in e and "slug" in e for e in errors)


def test_valid_slug_bundle_id_passes():
    data = valid_manifest_dict()
    data["bundle"]["id"] = "team-a.bundle_1"
    manifest = BundleManifest.from_dict(data)
    assert not any("bundle.id" in e for e in manifest.structural_errors())


def test_string_tools_rejected_not_split_per_character():
    data = valid_manifest_dict()
    data["requires"]["tools"] = "docker"
    with pytest.raises(BundlerError, match="'requires.tools' must be a list of strings"):
        BundleManifest.from_dict(data)


def test_string_mcp_rejected_not_split_per_character():
    data = valid_manifest_dict()
    data["requires"]["mcp"] = "github"
    with pytest.raises(BundlerError, match="'requires.mcp' must be a list of strings"):
        BundleManifest.from_dict(data)
