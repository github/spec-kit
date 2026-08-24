"""Cross-OS and resolver-parity tests for the `specify artifact` command group.

Focuses on invariants that either directly guard against OS-specific
regressions (POSIX-vs-Windows path separators, UTF-8 encoding) or verify
that the artifact output stays consistent with the underlying
:class:`~specify_cli.presets.PresetResolver`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from specify_cli.artifacts import ArtifactCatalog


def _install_preset(project_root: Path, pack_id: str, provides: dict, priority: int = 10) -> Path:
    pack_dir = project_root / ".specify" / "presets" / pack_id
    pack_dir.mkdir(parents=True)
    manifest = {
        "id": pack_id,
        "version": "1.0.0",
        "metadata": {"name": f"Test preset {pack_id}"},
        "provides": provides,
    }
    (pack_dir / "preset.yml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    registry_path = project_root / ".specify" / "presets" / ".registry"
    if registry_path.is_file():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    else:
        registry = {"schema_version": "1.0.0", "presets": {}}
    registry["presets"][pack_id] = {"priority": priority, "version": "1.0.0"}
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    return pack_dir


@pytest.fixture
def spec_kit_project(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    root.mkdir()
    (root / ".specify").mkdir()
    (root / ".specify" / "presets").mkdir()
    (root / ".specify" / "extensions").mkdir()
    (root / ".specify" / "templates").mkdir()
    return root


class TestManifestPathIsPosix:
    """The ``manifestPath`` field MUST use forward slashes on every OS."""

    def test_no_backslashes(self, spec_kit_project: Path):
        pack = _install_preset(
            spec_kit_project,
            "test-posix",
            {"commands": [{"name": "speckit.constitution", "description": "d"}]},
        )
        (pack / "commands").mkdir()
        (pack / "commands" / "speckit.constitution.md").write_text(
            "---\ndescription: d\n---\nbody", encoding="utf-8"
        )
        info = ArtifactCatalog(spec_kit_project).get_artifact_info("speckit.constitution")
        for layer in info["stack"]:
            path = layer["manifestPath"]
            if path is None:
                continue
            assert "\\" not in path, f"backslash leak: {path!r}"

    def test_never_absolute(self, spec_kit_project: Path):
        pack = _install_preset(
            spec_kit_project,
            "test-rel",
            {"commands": [{"name": "speckit.constitution", "description": "d"}]},
        )
        (pack / "commands").mkdir()
        (pack / "commands" / "speckit.constitution.md").write_text(
            "---\ndescription: d\n---\nbody", encoding="utf-8"
        )
        info = ArtifactCatalog(spec_kit_project).get_artifact_info("speckit.constitution")
        for layer in info["stack"]:
            path = layer["manifestPath"]
            if path is None:
                continue
            assert not path.startswith("/"), f"leading slash: {path!r}"
            # Windows drive letter check.
            assert not (len(path) >= 2 and path[1] == ":"), f"drive letter: {path!r}"


class TestResolverParity:
    """The ``active: true`` row must be what :meth:`resolve_content` would pick."""

    def test_active_layer_matches_resolver(self, spec_kit_project: Path):
        from specify_cli.presets import PresetResolver

        pack = _install_preset(
            spec_kit_project,
            "test-parity",
            {"commands": [{"name": "speckit.constitution", "description": "override"}]},
        )
        (pack / "commands").mkdir()
        (pack / "commands" / "speckit.constitution.md").write_text(
            "---\ndescription: override\n---\nbody-from-preset", encoding="utf-8"
        )

        info = ArtifactCatalog(spec_kit_project).get_artifact_info("speckit.constitution")
        active = next(layer for layer in info["stack"] if layer["active"])

        resolver = PresetResolver(spec_kit_project)
        winner = resolver.resolve_content("speckit.constitution", template_type="command")
        assert winner is not None
        # The active row's layer classification must correspond to a real
        # winning layer — if a preset override was installed and picked up
        # by the resolver, active.layer must not be "core".
        assert "body-from-preset" in winner
        assert active["layer"] == "preset"


class TestJSONShape:
    """Reasserts JSON-envelope invariants at the whole-payload level."""

    def test_no_trailing_whitespace(self, spec_kit_project: Path):
        catalog = ArtifactCatalog(spec_kit_project)
        rows = [a.to_json_dict() for a in catalog.list_artifacts()]
        payload = json.dumps(rows, indent=2, sort_keys=True) + "\n"
        for line in payload.splitlines():
            assert line == line.rstrip(), f"trailing ws: {line!r}"

    def test_terminated_by_single_newline(self, spec_kit_project: Path):
        catalog = ArtifactCatalog(spec_kit_project)
        rows = [a.to_json_dict() for a in catalog.list_artifacts()]
        payload = json.dumps(rows, indent=2, sort_keys=True) + "\n"
        assert payload.endswith("\n")
        assert not payload.endswith("\n\n")


def test_module_imports():
    _ = ArtifactCatalog

