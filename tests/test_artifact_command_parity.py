"""Resolver-parity tests for the `specify artifact` command group.

Verifies that the artifact output stays consistent with the underlying
:class:`~specify_cli.presets.PresetResolver`, including for contributions
that only a manifest can surface.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from specify_cli.artifacts import ArtifactCatalog
from specify_cli.presets import PresetResolver
from tests.conftest import install_preset


@pytest.fixture
def spec_kit_project(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    root.mkdir()
    (root / ".specify").mkdir()
    (root / ".specify" / "presets").mkdir()
    (root / ".specify" / "extensions").mkdir()
    (root / ".specify" / "templates").mkdir()
    return root


class TestResolverParity:
    """The ``active: true`` row must be what :meth:`resolve_content` would pick."""

    def test_manifest_declared_artifact_matches_resolver(self, spec_kit_project: Path):
        pack = install_preset(
            spec_kit_project,
            "test-manifest-parity",
            {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.manifest-declared",
                        "file": "commands/differently-named.md",
                        "description": "manifest contribution",
                    }
                ]
            },
        )
        (pack / "commands").mkdir()
        (pack / "commands" / "differently-named.md").write_text(
            "body-from-manifest", encoding="utf-8"
        )

        catalog = ArtifactCatalog(spec_kit_project)
        info = catalog.get_artifact_info("speckit.manifest-declared")
        active = next(layer for layer in info["stack"] if layer["active"])
        winner = PresetResolver(spec_kit_project).resolve_content(
            "speckit.manifest-declared", template_type="command"
        )

        assert winner == "body-from-manifest"
        assert active["layer"] == "preset"
        assert active["lookupId"] == "preset:test-manifest-parity:command:speckit.manifest-declared"

    def test_preset_manifest_id_mismatch_uses_registry_key(self, spec_kit_project: Path):
        pack = install_preset(
            spec_kit_project,
            "renamed-preset",
            {
                "commands": [
                    {
                        "name": "speckit.preset-renamed.hello",
                        "file": "commands/actual.md",
                        "description": "manifest contribution",
                    }
                ]
            },
        )
        manifest_path = pack / "preset.yml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest["preset"]["id"] = "original-preset"
        manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
        (pack / "commands").mkdir()
        (pack / "commands" / "actual.md").write_text(
            "body-from-renamed-preset", encoding="utf-8"
        )

        catalog = ArtifactCatalog(spec_kit_project)
        assert "command:speckit.preset-renamed.hello" in {
            row.id for row in catalog.list_artifacts()
        }
        info = catalog.get_artifact_info("speckit.preset-renamed.hello")
        active = next(layer for layer in info["stack"] if layer["active"])
        winner = PresetResolver(spec_kit_project).resolve_content(
            "speckit.preset-renamed.hello", template_type="command"
        )

        assert winner == "body-from-renamed-preset"
        assert active["lookupId"] == (
            "preset:renamed-preset:command:speckit.preset-renamed.hello"
        )
        assert (
            PresetResolver(spec_kit_project)
            .collect_all_layers("speckit.preset-renamed.hello", "command")[0]["lookupId"]
            == "preset:renamed-preset:command:speckit.preset-renamed.hello"
        )


def test_module_imports():
    _ = ArtifactCatalog
