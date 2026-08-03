"""Install-time initialization and integration precedence (T049, T050).

``specify bundle install`` into an uninitialized directory must scaffold a Spec
Kit project first (FR-012), choosing the integration by precedence (FR-013):
explicit ``--integration`` override → bundle-declared integration → default.
The end-to-end test runs fully offline against bundled assets.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundler.models.manifest import BundleManifest
from specify_cli.commands.bundle import _resolve_init_integration
from specify_cli.bundler.services.packager import build_bundle
from tests.bundler_helpers import valid_manifest_dict

runner = CliRunner()


def _manifest(**overrides):
    data = valid_manifest_dict(**overrides)
    return BundleManifest.from_dict(data)


def test_precedence_override_wins():
    manifest = _manifest(integration={"id": "claude"})
    assert _resolve_init_integration("gemini", manifest) == "gemini"


def test_precedence_bundle_declared_when_no_override():
    manifest = _manifest(integration={"id": "claude"})
    assert _resolve_init_integration(None, manifest) == "claude"


def test_precedence_default_when_unspecified():
    manifest = _manifest()
    assert _resolve_init_integration(None, manifest) == "copilot"
    assert _resolve_init_integration(None, None) == "copilot"


def _build_mini(tmp_path: Path) -> Path:
    bundle = tmp_path / "mini"
    bundle.mkdir()
    (bundle / "bundle.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "bundle": {
                    "id": "mini",
                    "name": "Mini",
                    "version": "1.0.0",
                    "role": "developer",
                    "description": "minimal",
                    "author": "tests",
                    "license": "MIT",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {"extensions": [{"id": "agent-context", "version": "1.0.0"}]},
            }
        ),
        encoding="utf-8",
    )
    (bundle / "README.md").write_text("# Mini\n", encoding="utf-8")
    return build_bundle(bundle).artifact_path


def test_install_initializes_uninitialized_project(tmp_path: Path):
    project = tmp_path / "proj"
    project.mkdir()
    artifact = _build_mini(tmp_path)

    previous = Path.cwd()
    os.chdir(project)
    try:
        result = runner.invoke(
            app, ["bundle", "install", str(artifact), "--offline"]
        )
        assert result.exit_code == 0, result.output
    finally:
        os.chdir(previous)

    assert (project / ".specify").is_dir()
    marker = project / ".specify" / "integration.json"
    assert marker.exists()
    data = json.loads(marker.read_text(encoding="utf-8"))
    assert "copilot" in json.dumps(data)
