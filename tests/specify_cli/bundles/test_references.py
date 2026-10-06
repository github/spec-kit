"""Unit tests for the bundle reference checker (T047 / FR-005 / SC-007).

Resolution is offline-first: bundled and installed components resolve without a
network; unknown ids fail online and downgrade to warnings offline.
"""
from __future__ import annotations

from pathlib import Path

from specify_cli.bundles.manifest import ComponentRef
from specify_cli.bundles.references import make_reference_checker
from tests.specify_cli.bundles.helpers import bundled_extension_version, make_project


def _ref(kind: str, id_: str, version: str | None = "1.0.0") -> ComponentRef:
    return ComponentRef(kind=kind, id=id_, version=version)


def test_bundled_extension_resolves(tmp_path: Path):
    root = make_project(tmp_path)
    warnings: list[str] = []
    check = make_reference_checker(root, allow_network=True, warnings=warnings)
    assert check(
        _ref("extensions", "agent-context", bundled_extension_version("agent-context"))
    ) is None
    assert warnings == []


def test_builtin_step_type_resolves(tmp_path: Path):
    """A built-in step type must resolve, like a bundled extension.

    Spec Kit ships 12 step types as built-ins registered in ``STEP_REGISTRY``
    rather than as on-disk asset directories, so there is no
    ``_locate_bundled_step``. The ``steps`` branch of ``_resolved_locally`` only
    asked ``StepRegistry(root).is_installed()``, which tracks *community* step
    types installed under ``.specify/workflows/steps/`` — so every built-in step
    type was reported as an unresolved reference.
    """
    from specify_cli.workflows import BUILTIN_STEP_TYPES

    root = make_project(tmp_path)
    warnings: list[str] = []
    check = make_reference_checker(root, allow_network=True, warnings=warnings)

    for step_id in ("shell", "gate", "command", "if", "slot"):
        assert step_id in BUILTIN_STEP_TYPES, step_id
        assert check(_ref("steps", step_id, None)) is None, step_id
    assert warnings == []


def test_community_step_is_not_treated_as_bundled(tmp_path: Path):
    """A community step loaded for one project must not resolve for another.

    `load_custom_steps` adds project-installed ids to the process-global
    `STEP_REGISTRY` and never removes them, so checking `STEP_REGISTRY` here
    would accept project A's community step as "bundled" while validating
    project B. `BUILTIN_STEP_TYPES` is snapshotted before any custom step can
    load, which is why the check uses it instead.
    """
    from specify_cli.workflows import (
        BUILTIN_STEP_TYPES,
        STEP_REGISTRY,
        _register_step,
    )
    from specify_cli.workflows.base import StepBase, StepResult, StepStatus

    class _CommunityStep(StepBase):
        type_key = "community-only-step"

        def execute(self, config, context):  # pragma: no cover - never run
            return StepResult(status=StepStatus.COMPLETED)

    # Simulate project A having loaded a community step into the global registry.
    _register_step(_CommunityStep())
    try:
        assert "community-only-step" in STEP_REGISTRY
        assert "community-only-step" not in BUILTIN_STEP_TYPES

        # Project B does not have it installed, so it must NOT resolve locally.
        root = make_project(tmp_path)
        warnings: list[str] = []
        check = make_reference_checker(root, allow_network=True, warnings=warnings)
        problem = check(_ref("steps", "community-only-step"))
        assert problem is not None, "leaked community step resolved as bundled"
        assert "community-only-step" in problem
    finally:
        STEP_REGISTRY.pop("community-only-step", None)


def test_unknown_step_type_still_errors_online(tmp_path: Path):
    """The guard must not make every step id resolve."""
    root = make_project(tmp_path)
    warnings: list[str] = []
    check = make_reference_checker(root, allow_network=True, warnings=warnings)
    problem = check(_ref("steps", "no-such-step-type"))
    assert problem is not None
    assert "no-such-step-type" in problem


def test_unknown_reference_errors_online(tmp_path: Path):
    root = make_project(tmp_path)
    warnings: list[str] = []
    check = make_reference_checker(root, allow_network=True, warnings=warnings)
    problem = check(_ref("presets", "does-not-exist"))
    assert problem is not None
    assert "does-not-exist" in problem


def test_unknown_reference_warns_offline(tmp_path: Path):
    root = make_project(tmp_path)
    warnings: list[str] = []
    check = make_reference_checker(root, allow_network=False, warnings=warnings)
    assert check(_ref("presets", "does-not-exist")) is None
    assert any("does-not-exist" in w for w in warnings)


def test_wrong_bundled_pin_does_not_resolve_locally(tmp_path):
    root = make_project(tmp_path)
    warnings = []
    check = make_reference_checker(root, allow_network=False, warnings=warnings)

    assert check(_ref("extensions", "agent-context", "999.0.0")) is None
    assert any("agent-context" in message for message in warnings)


def test_online_validation_checks_winning_exact_release_and_source(tmp_path, monkeypatch):
    import specify_cli._assets as assets
    from specify_cli.workflows.catalog import WorkflowCatalog

    monkeypatch.setattr(assets, "_locate_bundled_workflow", lambda _id: None)
    lookups = []

    def lookup(_self, _id, version=None):
        lookups.append(version)
        if version == "1.0.0":
            return {
                "version": "1.0.0", "_catalog_name": "winning",
                "_install_allowed": True,
            }
        if version is None:
            return {
                "version": "2.0.0", "_catalog_name": "winning",
                "_install_allowed": True,
            }
        return None

    monkeypatch.setattr(WorkflowCatalog, "get_workflow_info", lookup)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)
    requested = ComponentRef(
        kind="workflows", id="catalog-workflow", version="1.0.0", source="winning"
    )

    assert check(requested) is None
    assert lookups == [None, "1.0.0"]
    assert check(ComponentRef(kind="workflows", id=requested.id, version="3.0.0"))
    assert check(ComponentRef(
        kind="workflows", id=requested.id, version="1.0.0", source="lower"
    ))
    assert warnings == []


def test_online_validation_rejects_discovery_only_exact_release(tmp_path, monkeypatch):
    from specify_cli.workflows.catalog import StepCatalog

    monkeypatch.setattr(
        StepCatalog, "get_step_info",
        lambda _self, _id, version=None: {
            "version": version or "2.0.0", "_catalog_name": "winning",
            "_install_allowed": version is None,
        },
    )
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert check(_ref("steps", "catalog-step", "1.0.0"))
    assert warnings == []


def test_online_validation_reports_invalid_release_metadata(tmp_path, monkeypatch):
    from specify_cli.workflows.catalog import StepCatalog, StepCatalogError

    def invalid_release(_self, _id, version=None):
        raise StepCatalogError("Step release needs a SHA-256 digest.")

    monkeypatch.setattr(StepCatalog, "get_step_info", invalid_release)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert "SHA-256" in check(_ref("steps", "invalid-release"))
    assert warnings == []


def test_online_validation_warns_when_catalogs_are_unreachable(tmp_path, monkeypatch):
    from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowCatalogError

    def unavailable(_self, _id, version=None):
        raise WorkflowCatalogError("All configured catalogs failed to fetch.")

    monkeypatch.setattr(WorkflowCatalog, "get_workflow_info", unavailable)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert check(_ref("workflows", "unreachable")) is None
    assert len(warnings) == 1
    assert "unreachable" in warnings[0]
