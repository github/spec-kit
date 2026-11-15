"""Unit tests for the resolver: version gate and integration compatibility."""
from __future__ import annotations

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundles.expansion import LoadedBundle, expand_manifest
from specify_cli.bundles.manifest import BundleManifest
from specify_cli.bundles.resolver import resolve_install_plan
from tests.specify_cli.bundles.helpers import (
    FakeBundleLoader,
    reference_manifest_dict,
    valid_manifest_dict,
)


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


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_pinned_integration_with_blank_active_fails(blank):
    """A blank active integration is indeterminate, not a match.

    The clash guard is a truthiness test and the indeterminate guard is an
    `is None` test, so `""` satisfied neither and fell through to
    `effective_integration = required` — silently adopting the bundle's pinned
    integration, the exact outcome the docstring says the guard prevents.
    """
    manifest = _manifest(integration={"id": "claude"})
    with pytest.raises(BundlerError, match="could not be determined"):
        resolve_install_plan(
            manifest, speckit_version="0.11.2", active_integration=blank
        )


def test_padded_active_integration_is_not_a_clash_with_itself():
    """A padded value must strip, like the writer's clean_integration_key,
    rather than be reported as clashing with its own unpadded form."""
    manifest = _manifest(integration={"id": "claude"})
    plan = resolve_install_plan(
        manifest, speckit_version="0.11.2", active_integration="  claude  "
    )
    assert plan.effective_integration == "claude"


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


def _expanded_root(
    *,
    root_requires: dict | None = None,
    root_integration: dict | None = None,
    child_requires: dict | None = None,
    child_integration: dict | None = None,
    child_extensions: list[dict] | None = None,
):
    root_data = reference_manifest_dict(
        [{"id": "bugfix", "version": "1.0.0"}], bundle_id="team"
    )
    root_data["requires"] = root_requires or {"speckit_version": ">=0.1.0"}
    root_data["integration"] = root_integration
    root_data["provides"]["extensions"] = [{"id": "root-ext", "version": "1.0.0"}]
    root = BundleManifest.from_dict(root_data)
    child_data = valid_manifest_dict(
        requires=child_requires or {"speckit_version": ">=0.1.0"},
        integration=child_integration,
    )
    child_data["bundle"]["id"] = "bugfix"
    child_data["bundle"]["version"] = "1.0.0"
    child_data["provides"] = {
        "extensions": child_extensions or [{"id": "child-ext", "version": "1.0.0"}]
    }
    child = BundleManifest.from_dict(child_data)
    loader = FakeBundleLoader(
        {("bugfix", "1.0.0"): LoadedBundle(child, "default", True)}
    )
    return root, expand_manifest(root, loader)


def test_plan_from_expanded_manifest_carries_references_and_components():
    root, expanded = _expanded_root()
    plan = resolve_install_plan(
        expanded, speckit_version="0.11.2", active_integration="copilot"
    )
    assert plan.references == expanded.references
    assert [component.id for component in plan.components] == [
        "child-ext",
        "root-ext",
    ]
    assert plan.bundle_id == root.bundle.id


def test_reference_tools_and_mcp_are_union_deduplicated():
    _, expanded = _expanded_root(
        root_requires={
            "speckit_version": ">=0.1.0",
            "tools": ["docker", "git"],
            "mcp": ["shared", "root-only"],
        },
        child_requires={
            "speckit_version": ">=0.1.0",
            "tools": ["git", "node"],
            "mcp": ["shared", "child-only"],
        },
    )
    plan = resolve_install_plan(
        expanded, speckit_version="0.11.2", active_integration="copilot"
    )
    assert plan.warnings[:2] == [
        "Requires external tools: docker, git, node",
        "Requires MCP servers: shared, root-only, child-only",
    ]


def test_reference_matching_integration_has_no_warning():
    _, expanded = _expanded_root(child_integration={"id": "copilot"})
    plan = resolve_install_plan(
        expanded, speckit_version="0.11.2", active_integration="copilot"
    )
    assert not any("targets" in warning for warning in plan.warnings)


def test_unexpanded_manifest_with_references_is_rejected():
    root = BundleManifest.from_dict(
        reference_manifest_dict([{"id": "bugfix", "version": "1.0.0"}])
    )
    with pytest.raises(BundlerError, match="before expansion"):
        resolve_install_plan(
            root, speckit_version="0.11.2", active_integration="copilot"
        )


def test_reference_version_gate_reports_full_chain():
    _, expanded = _expanded_root(
        child_requires={"speckit_version": ">=2.0"}
    )
    with pytest.raises(BundlerError, match=r"Bundle 'bugfix' \(team → bugfix\)"):
        resolve_install_plan(
            expanded, speckit_version="1.3", active_integration="copilot"
        )


def test_reference_version_gate_can_be_disabled():
    _, expanded = _expanded_root(child_requires={"speckit_version": ">=99.0.0"})
    plan = resolve_install_plan(
        expanded,
        speckit_version="0.11.2",
        active_integration="copilot",
        enforce_version=False,
    )
    assert plan.bundle_id == "team"


def test_transitive_reference_version_gate_reports_full_chain():
    root_data = reference_manifest_dict([{"id": "a", "version": "1.0.0"}], bundle_id="team")
    root = BundleManifest.from_dict(root_data)
    a_data = reference_manifest_dict([{"id": "bugfix", "version": "1.0.0"}], bundle_id="a")
    a_data["bundle"]["version"] = "1.0.0"
    a = BundleManifest.from_dict(a_data)
    bugfix_data = valid_manifest_dict(
        requires={"speckit_version": ">=99.0.0"},
    )
    bugfix_data["bundle"]["id"] = "bugfix"
    bugfix_data["bundle"]["version"] = "1.0.0"
    bugfix = BundleManifest.from_dict(bugfix_data)
    loader = FakeBundleLoader({
        ("a", "1.0.0"): LoadedBundle(a, "default", True),
        ("bugfix", "1.0.0"): LoadedBundle(bugfix, "default", True),
    })
    expanded = expand_manifest(root, loader)
    with pytest.raises(
        BundlerError,
        match=r"Bundle 'bugfix' \(team → a → bugfix\)",
    ):
        resolve_install_plan(
            expanded, speckit_version="0.11.2", active_integration="copilot"
        )


def test_reference_integration_mismatch_is_a_warning():
    _, expanded = _expanded_root(child_integration={"id": "copilot"})
    plan = resolve_install_plan(
        expanded, speckit_version="0.11.2", active_integration="claude"
    )
    assert plan.warnings[-1] == (
        "Bundle 'bugfix' (team → bugfix) targets 'copilot'; "
        "this install uses 'claude'."
    )


def test_root_integration_pin_is_used_for_reference_warning():
    _, expanded = _expanded_root(
        root_integration={"id": "copilot"}, child_integration={"id": "claude"}
    )
    plan = resolve_install_plan(
        expanded, speckit_version="0.11.2", active_integration="copilot"
    )
    assert plan.warnings[-1] == (
        "Bundle 'bugfix' (team → bugfix) targets 'claude'; "
        "this install uses 'copilot'."
    )


def test_root_and_reference_matching_integration_has_no_warning():
    _, expanded = _expanded_root(
        root_integration={"id": "copilot"}, child_integration={"id": "copilot"}
    )
    plan = resolve_install_plan(
        expanded, speckit_version="0.11.2", active_integration="copilot"
    )
    assert not any("targets" in warning for warning in plan.warnings)


def test_explicit_integration_override_is_used_for_reference_warning():
    _, expanded = _expanded_root(
        root_integration={"id": "copilot"}, child_integration={"id": "claude"}
    )
    plan = resolve_install_plan(
        expanded,
        speckit_version="0.11.2",
        active_integration=None,
        integration_explicit=True,
    )
    assert "this install uses 'copilot'" in plan.warnings[-1]


def test_reference_integration_unknown_is_a_warning():
    _, expanded = _expanded_root(child_integration={"id": "copilot"})
    plan = resolve_install_plan(
        expanded, speckit_version="0.11.2", active_integration=None
    )
    assert plan.warnings[-1] == (
        "Bundle 'bugfix' (team → bugfix) targets integration 'copilot'; "
        "the project's integration could not be determined."
    )


def test_expansion_warnings_are_appended_after_resolver_warnings():
    _, expanded = _expanded_root(
        root_requires={
            "speckit_version": ">=0.1.0",
            "tools": ["docker"],
            "mcp": ["root-server"],
        },
        child_requires={"speckit_version": ">=0.1.0", "mcp": ["child-server"]},
        child_integration={"id": "claude"},
        child_extensions=[{"id": "root-ext", "version": "2.0.0"}],
    )
    plan = resolve_install_plan(
        expanded, speckit_version="0.11.2", active_integration="copilot"
    )
    assert plan.warnings == [
        "Requires external tools: docker",
        "Requires MCP servers: root-server, child-server",
        "Bundle 'bugfix' (team → bugfix) targets 'claude'; this install uses 'copilot'.",
        expanded.warnings[-1],
    ]


def test_flat_tools_are_not_deduplicated():
    manifest_data = valid_manifest_dict(
        requires={"speckit_version": ">=0.1.0", "tools": ["git", "git"]}
    )
    plan = resolve_install_plan(
        BundleManifest.from_dict(manifest_data),
        speckit_version="0.11.2",
        active_integration="copilot",
    )
    assert plan.warnings == ["Requires external tools: git, git"]
