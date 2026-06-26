"""Unit tests for the bundle reference checker (T047 / FR-005 / SC-007).

Resolution is offline-first: bundled and installed components resolve without a
network; unknown ids fail online and downgrade to warnings offline.
"""
from __future__ import annotations

from pathlib import Path

from specify_cli.bundler.models.manifest import ComponentRef
from specify_cli.bundler.services.references import make_reference_checker
from tests.bundler_helpers import make_project


def _ref(kind: str, id_: str) -> ComponentRef:
    return ComponentRef(kind=kind, id=id_, version="1.0.0")


def test_bundled_extension_resolves(tmp_path: Path):
    root = make_project(tmp_path)
    warnings: list[str] = []
    check = make_reference_checker(root, allow_network=True, warnings=warnings)
    assert check(_ref("extensions", "agent-context")) is None
    assert warnings == []


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
