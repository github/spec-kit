"""Unit tests for the bundle reference checker (T047 / FR-005 / SC-007).

Resolution is offline-first: bundled and installed components resolve without a
network; unknown ids fail online and downgrade to warnings offline.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from specify_cli.bundles.manifest import ComponentRef
from specify_cli.bundles.references import make_reference_checker
from tests.specify_cli.bundles.helpers import make_project


def _ref(kind: str, id_: str) -> ComponentRef:
    return ComponentRef(kind=kind, id=id_, version="1.0.0")


def test_bundled_extension_resolves(tmp_path: Path):
    root = make_project(tmp_path)
    warnings: list[str] = []
    check = make_reference_checker(root, allow_network=True, warnings=warnings)
    assert check(_ref("extensions", "agent-context")) is None
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
        assert check(_ref("steps", step_id)) is None, step_id
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


def _release_entry(kind: str, cid: str) -> dict:
    """A catalog entry advertising 0.5.1 that keeps 0.4.12 under ``releases``."""
    if kind == "steps":
        digests = {"step.yml": "a" * 64, "__init__.py": "b" * 64}
        current = {
            "url": f"https://example.com/{cid}/v0.5.1/step.yml",
            "init_url": f"https://example.com/{cid}/v0.5.1/__init__.py",
            "sha256": digests,
        }
        release = {
            "url": f"https://example.com/{cid}/v0.4.12/step.yml",
            "init_url": f"https://example.com/{cid}/v0.4.12/__init__.py",
            "sha256": digests,
        }
    else:
        url_key = "url" if kind == "workflows" else "download_url"
        current = {url_key: f"https://example.com/{cid}/v0.5.1.zip", "sha256": "a" * 64}
        release = {url_key: f"https://example.com/{cid}/v0.4.12.zip", "sha256": "b" * 64}
    return {
        "id": cid,
        "name": cid,
        "version": "0.5.1",
        **current,
        "releases": {"0.4.12": release},
        "_install_allowed": True,
    }


def _patch_catalog(monkeypatch, kind: str, entry: dict | None) -> None:
    from specify_cli.extensions import ExtensionCatalog
    from specify_cli.presets import PresetCatalog
    from specify_cli.workflows.catalog import StepCatalog, WorkflowCatalog

    target = {
        "presets": (PresetCatalog, "get_pack_info"),
        "extensions": (ExtensionCatalog, "get_extension_info"),
        "workflows": (WorkflowCatalog, "get_workflow_info"),
        "steps": (StepCatalog, "get_step_info"),
    }[kind]
    monkeypatch.setattr(*target, lambda _self, _id, version=None: entry)


_KINDS = ["presets", "extensions", "workflows", "steps"]


@pytest.mark.parametrize("kind", _KINDS)
def test_online_validate_accepts_pinned_historical_release(
    tmp_path: Path, monkeypatch, kind: str
):
    root = make_project(tmp_path)
    _patch_catalog(monkeypatch, kind, _release_entry(kind, "pinned-thing"))
    warnings: list[str] = []
    check = make_reference_checker(root, allow_network=True, warnings=warnings)

    ref = ComponentRef(kind=kind, id="pinned-thing", version="0.4.12")
    assert check(ref) is None
    assert warnings == []


@pytest.mark.parametrize("kind", _KINDS)
def test_online_validate_rejects_pin_missing_from_catalog(
    tmp_path: Path, monkeypatch, kind: str
):
    """Online validation checks the exact pinned version, not just the ID."""
    root = make_project(tmp_path)
    _patch_catalog(monkeypatch, kind, _release_entry(kind, "pinned-thing"))
    warnings: list[str] = []
    check = make_reference_checker(root, allow_network=True, warnings=warnings)

    problem = check(ComponentRef(kind=kind, id="pinned-thing", version="0.3.0"))
    assert problem is not None
    assert "pinned to version 0.3.0" in problem
    assert "advertises 0.5.1" in problem


@pytest.mark.parametrize("kind", _KINDS)
def test_online_validate_entry_without_version_cannot_check_pin(
    tmp_path: Path, monkeypatch, kind: str
):
    root = make_project(tmp_path)
    _patch_catalog(monkeypatch, kind, {"id": "pinned-thing", "name": "pinned-thing"})
    warnings: list[str] = []
    check = make_reference_checker(root, allow_network=True, warnings=warnings)

    assert check(ComponentRef(kind=kind, id="pinned-thing", version="0.3.0")) is None
