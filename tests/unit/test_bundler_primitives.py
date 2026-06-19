"""Unit tests for the primitive-dispatch bridge (T044).

Covers routing, offline gating, and the network-aware ``DefaultPrimitiveInstaller``
seam — without touching real catalogs or the network (Constitution Principle II,
offline-first).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundler.models.manifest import ComponentRef
from specify_cli.bundler.services.adapters import DefaultPrimitiveInstaller
from specify_cli.bundler.services.primitives import (
    _ExtensionKindManager,
    _PresetKindManager,
    _StepKindManager,
    _WorkflowKindManager,
    primitive_manager,
)


def _component(kind: str, cid: str = "x") -> ComponentRef:
    return ComponentRef(kind=kind, id=cid)


def test_primitive_manager_routes_each_kind(tmp_path: Path):
    assert isinstance(primitive_manager("presets", tmp_path), _PresetKindManager)
    assert isinstance(primitive_manager("extensions", tmp_path), _ExtensionKindManager)
    assert isinstance(primitive_manager("workflows", tmp_path), _WorkflowKindManager)
    assert isinstance(primitive_manager("steps", tmp_path), _StepKindManager)


def test_primitive_manager_rejects_unknown_kind(tmp_path: Path):
    with pytest.raises(BundlerError, match="Unknown component kind"):
        primitive_manager("bogus", tmp_path)


def test_offline_preset_not_bundled_refuses(tmp_path: Path):
    manager = primitive_manager("presets", tmp_path, allow_network=False)
    with pytest.raises(BundlerError, match="network access is disabled"):
        manager.install(_component("presets", "definitely-not-bundled"))


def test_offline_extension_not_bundled_refuses(tmp_path: Path):
    manager = primitive_manager("extensions", tmp_path, allow_network=False)
    with pytest.raises(BundlerError, match="network access is disabled"):
        manager.install(_component("extensions", "definitely-not-bundled"))


def test_offline_workflow_refuses_without_network(tmp_path: Path):
    manager = primitive_manager("workflows", tmp_path, allow_network=False)
    with pytest.raises(BundlerError, match="network access is disabled"):
        manager.install(_component("workflows"))


def test_offline_step_refuses_without_network(tmp_path: Path):
    manager = primitive_manager("steps", tmp_path, allow_network=False)
    with pytest.raises(BundlerError, match="network access is disabled"):
        manager.install(_component("steps"))


def test_default_installer_threads_allow_network(tmp_path: Path):
    installer = DefaultPrimitiveInstaller(allow_network=False)
    with pytest.raises(BundlerError, match="network access is disabled"):
        installer.install(tmp_path, _component("workflows"))


def test_offline_workflow_allows_bundled(tmp_path: Path, monkeypatch):
    # A workflow that ships with Spec Kit must install even with --offline.
    import specify_cli
    import specify_cli._assets as assets

    monkeypatch.setattr(
        assets, "_locate_bundled_workflow", lambda wid: tmp_path / "wf"
    )
    calls: list[str] = []
    monkeypatch.setattr(specify_cli, "workflow_add", lambda wid: calls.append(wid))

    manager = primitive_manager("workflows", tmp_path, allow_network=False)
    manager.install(_component("workflows", "bundled-wf"))

    assert calls == ["bundled-wf"]
