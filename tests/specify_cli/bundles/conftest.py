from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture()
def project(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / ".specify").mkdir()
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture(params=["extensions", "presets"])
def bundled_component(project: Path, request):
    """Install a bundle whose only component, an extension or a preset, declares priority 10."""
    from typer.testing import CliRunner

    from specify_cli import app
    from specify_cli.extensions import ExtensionRegistry
    from specify_cli.presets import PresetRegistry
    from tests.specify_cli.bundles.helpers import valid_manifest_dict, write_manifest

    kind = request.param
    cid = "bug" if kind == "extensions" else "lean"
    component = {"id": cid, "version": "1.0.2" if kind == "extensions" else "1.0.0"}
    if kind == "presets":
        component["strategy"] = "replace"

    def declare(priority: int) -> Path:
        component["priority"] = priority
        return write_manifest(project / "source", valid_manifest_dict(provides={kind: [component]}))

    source = declare(10)
    result = CliRunner().invoke(app, ["bundle", "install", str(source), "--offline"])
    assert result.exit_code == 0, result.output
    registry_type = ExtensionRegistry if kind == "extensions" else PresetRegistry

    def read_metadata():
        return registry_type(project / ".specify" / kind).get(cid)

    assert read_metadata()["priority"] == 10
    return SimpleNamespace(
        kind=kind, cid=cid, source=source, declare=declare, read_metadata=read_metadata
    )


@pytest.fixture
def priority_bundle(bundled_component):
    """The bundle above, with the component's priority set to 3 by the user."""
    from typer.testing import CliRunner

    from specify_cli import app

    component = bundled_component
    result = CliRunner().invoke(
        app, [component.kind[:-1], "set-priority", component.cid, "3"]
    )
    assert result.exit_code == 0, result.output
    assert component.read_metadata()["priority"] == 3
    return component.source, component.read_metadata
