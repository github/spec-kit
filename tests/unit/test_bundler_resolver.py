"""Unit tests for the resolver: version gate and integration compatibility."""
from __future__ import annotations

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundler.models.manifest import BundleManifest
from specify_cli.bundler.services.resolver import resolve_install_plan
from tests.bundler_helpers import valid_manifest_dict


def _manifest(**overrides) -> BundleManifest:
    return BundleManifest.from_dict(valid_manifest_dict(**overrides))


def test_plan_expands_all_components():
    plan = resolve_install_plan(
        _manifest(), speckit_version="0.11.2", active_integration="copilot"
    )
    assert plan.component_count == 4
    assert plan.bundle_id == "demo-bundle"


def test_version_gate_refuses_incompatible():
    manifest = _manifest(requires={"speckit_version": ">=99.0.0"})
    with pytest.raises(BundlerError, match="requires Spec Kit"):
        resolve_install_plan(
            manifest, speckit_version="0.11.2", active_integration="copilot"
        )


def test_integration_clash_halts():
    manifest = _manifest(integration={"id": "claude"})
    with pytest.raises(BundlerError, match="active integration"):
        resolve_install_plan(
            manifest, speckit_version="0.11.2", active_integration="copilot"
        )


def test_agnostic_inherits_active_integration():
    plan = resolve_install_plan(
        _manifest(), speckit_version="0.11.2", active_integration="copilot"
    )
    assert plan.effective_integration == "copilot"


def test_matching_integration_is_allowed():
    manifest = _manifest(integration={"id": "copilot"})
    plan = resolve_install_plan(
        manifest, speckit_version="0.11.2", active_integration="copilot"
    )
    assert plan.effective_integration == "copilot"


def test_pinned_integration_with_indeterminate_active_fails():
    # FR-019 guard: a bundle that pins an integration must not silently adopt it
    # when the project's active integration cannot be determined.
    manifest = _manifest(integration={"id": "claude"})
    with pytest.raises(BundlerError, match="could not be determined"):
        resolve_install_plan(
            manifest, speckit_version="0.11.2", active_integration=None
        )


def test_pinned_integration_with_indeterminate_active_allows_explicit_override():
    manifest = _manifest(integration={"id": "claude"})
    plan = resolve_install_plan(
        manifest,
        speckit_version="0.11.2",
        active_integration="claude",
        integration_explicit=True,
    )
    assert plan.effective_integration == "claude"


def test_tool_requirements_become_warnings():
    manifest = _manifest(requires={"speckit_version": ">=0.1.0", "tools": ["docker"]})
    plan = resolve_install_plan(
        manifest, speckit_version="0.11.2", active_integration="copilot"
    )
    assert any("docker" in w for w in plan.warnings)
