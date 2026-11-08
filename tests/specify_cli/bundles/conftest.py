from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def project(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / ".specify").mkdir()
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture(params=["extensions", "presets"])
def priority_bundle(project: Path, request):
    from typer.testing import CliRunner

    from specify_cli import app
    from specify_cli.extensions import ExtensionRegistry
    from specify_cli.presets import PresetRegistry
    from tests.specify_cli.bundles.helpers import valid_manifest_dict, write_manifest

    kind = request.param
    cid = "bug" if kind == "extensions" else "lean"
    component = {"id": cid, "version": "1.0.2" if kind == "extensions" else "1.0.0", "priority": 10}
    if kind == "presets":
        component["strategy"] = "replace"
    source = write_manifest(project / "source", valid_manifest_dict(provides={kind: [component]}))
    runner = CliRunner()
    result = runner.invoke(app, ["bundle", "install", str(source), "--offline"])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, [kind[:-1], "set-priority", cid, "3"])
    assert result.exit_code == 0, result.output
    registry_type = ExtensionRegistry if kind == "extensions" else PresetRegistry

    def read_metadata():
        return registry_type(project / ".specify" / kind).get(cid)

    assert read_metadata()["priority"] == 3
    return source, read_metadata
