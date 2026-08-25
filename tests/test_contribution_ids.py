"""Tests for the deterministic contribution-id and stack lookup-id feature.

Every command / template / script / hook contribution surfaced by a preset or
extension manifest exposes a computed ``id`` derived from author-declared data
only, and every layer of a resolved artifact stack exposes a matching
``lookupId``. The scenarios below cover: the identifier grammar across every
``layer x kind`` combination, hook deduplication, cross-process byte-stability,
path/mtime independence, and the additive-only shape guarantee for the
enriched contribution dicts.
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest
import yaml

from specify_cli._identifier import (
    IdentifierComponentError,
    PROJECT_OVERRIDE_LAYER,
    derive_hook_id,
    derive_named_id,
    layer_kind_from_lookup_id,
    validate_component,
)
from specify_cli.extensions import ExtensionManifest, ValidationError
from specify_cli.presets import PresetManifest, PresetResolver


# ---------------------------------------------------------------------------
# Fixture builders (programmatic — no on-disk fixture tree)
# ---------------------------------------------------------------------------


def _preset_data(pack_id: str = "speckit-core") -> dict:
    return {
        "schema_version": "1.0",
        "preset": {
            "id": pack_id,
            "name": pack_id,
            "version": "1.0.0",
            "description": "Fixture preset",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {
            "templates": [
                {"type": "command", "name": "speckit.plan", "file": "commands/plan.md"},
                {"type": "template", "name": "spec-template", "file": "templates/spec.md"},
                {"type": "script", "name": "setup-plan", "file": "scripts/setup-plan.sh"},
            ]
        },
    }


def _extension_data(
    ext_id: str = "speckit-git",
    hooks: dict | None = None,
    with_commands: bool = True,
    with_templates: bool = True,
    with_scripts: bool = True,
) -> dict:
    data = {
        "schema_version": "1.0",
        "extension": {
            "id": ext_id,
            "name": ext_id,
            "version": "1.0.0",
            "description": "Fixture extension",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {},
    }
    if with_commands:
        data["provides"]["commands"] = [
            {
                "name": f"speckit.{ext_id.replace('-', '')}.branch",
                "file": "commands/branch.md",
                "description": "Fixture command",
            }
        ]
    if with_templates:
        data["provides"]["templates"] = [
            {"name": "pr-body", "file": "templates/pr-body.md"}
        ]
    if with_scripts:
        data["provides"]["scripts"] = [
            {"name": "post-commit", "file": "scripts/post-commit.sh"}
        ]
    if hooks is not None:
        data["hooks"] = hooks
    return data


def _write_manifest(tmp_path: Path, data: dict, filename: str) -> Path:
    manifest_path = tmp_path / filename
    with open(manifest_path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False)
    return manifest_path


# ---------------------------------------------------------------------------
# Identifier grammar — layer x kind derivation matrix
# ---------------------------------------------------------------------------


class TestIdentifierDerivation:
    """Every layer x kind combination produces the expected grammar."""

    @pytest.mark.parametrize(
        "layer, source_id, kind, name, expected",
        [
            ("core", "_", "command", "speckit.constitution", "core:_:command:speckit.constitution"),
            ("core", "_", "template", "spec-template", "core:_:template:spec-template"),
            ("core", "_", "script", "setup-plan", "core:_:script:setup-plan"),
            ("preset", "speckit-core", "command", "speckit.plan", "preset:speckit-core:command:speckit.plan"),
            ("preset", "speckit-core", "template", "spec-template", "preset:speckit-core:template:spec-template"),
            ("preset", "speckit-core", "script", "setup-plan", "preset:speckit-core:script:setup-plan"),
            ("extension", "speckit-git", "command", "speckit.git.branch", "extension:speckit-git:command:speckit.git.branch"),
            ("extension", "speckit-git", "template", "pr-body", "extension:speckit-git:template:pr-body"),
            ("extension", "speckit-git", "script", "post-commit", "extension:speckit-git:script:post-commit"),
        ],
    )
    def test_named_id_grammar(self, layer, source_id, kind, name, expected):
        assert derive_named_id(layer, source_id, kind, name) == expected

    @pytest.mark.parametrize(
        "layer, source_id, event, command, expected",
        [
            ("core", "_", "before_specify", "speckit.constitution", "core:_:hook:before_specify:speckit.constitution"),
            ("preset", "speckit-core", "before_plan", "speckit.plan", "preset:speckit-core:hook:before_plan:speckit.plan"),
            ("extension", "speckit-git", "before_specify", "speckit.git.branch", "extension:speckit-git:hook:before_specify:speckit.git.branch"),
        ],
    )
    def test_hook_id_no_discriminator(self, layer, source_id, event, command, expected):
        assert derive_hook_id(layer, source_id, event, command) == expected

    def test_named_id_stable_across_two_derivations(self):
        a = derive_named_id("preset", "speckit-core", "command", "speckit.plan")
        b = derive_named_id("preset", "speckit-core", "command", "speckit.plan")
        assert a == b


class TestLayerKindFromLookupId:
    """``layer_kind_from_lookup_id`` extracts the layer segment of a lookupId."""

    @pytest.mark.parametrize(
        "lookup_id, expected",
        [
            ("core:_:command:speckit.constitution", "core"),
            ("preset:speckit-core:template:spec-template", "preset"),
            ("extension:speckit-git:script:post-commit", "extension"),
            (f"{PROJECT_OVERRIDE_LAYER}:_:template:spec-template", PROJECT_OVERRIDE_LAYER),
        ],
    )
    def test_recognized_layer_prefixes(self, lookup_id, expected):
        assert layer_kind_from_lookup_id(lookup_id) == expected

    @pytest.mark.parametrize(
        "lookup_id",
        [
            "",
            "bogus:_:command:speckit.plan",
            "core",
            ":_:command:speckit.plan",
        ],
    )
    def test_unrecognized_or_malformed_returns_none(self, lookup_id):
        assert layer_kind_from_lookup_id(lookup_id) is None


class TestHookContributions:
    def test_duplicate_commands_are_last_wins_and_move_to_end(self, tmp_path):
        data = _extension_data(
            hooks={
                "before_plan": [
                    {"command": "speckit.speckitgit.branch", "priority": 10},
                    {"command": "speckit.speckitgit.status", "priority": 20},
                    {"command": "speckit.speckitgit.branch", "priority": 30},
                ]
            }
        )
        manifest = ExtensionManifest(_write_manifest(tmp_path, data, "extension.yml"))
        hooks = [c for c in manifest.iter_contributions() if c["kind"] == "hook"]
        assert len(hooks) == 2
        assert [(hook["command"], hook["priority"]) for hook in hooks] == [
            ("speckit.speckitgit.status", 20),
            ("speckit.speckitgit.branch", 30),
        ]
        assert hooks[-1]["id"] == (
            "extension:speckit-git:hook:before_plan:speckit.speckitgit.branch"
        )
        assert manifest.contribution_id(
            "hook", "before_plan:speckit.speckitgit.branch"
        ) == hooks[-1]["id"]


# ---------------------------------------------------------------------------
# Manifest component `:` guard
# ---------------------------------------------------------------------------


class TestComponentGuard:
    def test_validate_component_rejects_colon(self):
        with pytest.raises(IdentifierComponentError) as exc_info:
            validate_component("has:colon", "test field")
        assert "':' is reserved" in str(exc_info.value)

    def test_validate_component_rejects_empty(self):
        with pytest.raises(IdentifierComponentError):
            validate_component("", "test field")

    def test_validate_component_rejects_non_string(self):
        with pytest.raises(IdentifierComponentError):
            validate_component(42, "test field")

    def test_extension_hook_event_name_with_colon_rejected(self, tmp_path):
        data = _extension_data(
            hooks={"before:plan": {"command": "speckit.speckitgit.branch"}}
        )
        with pytest.raises(ValidationError) as exc_info:
            ExtensionManifest(_write_manifest(tmp_path, data, "extension.yml"))
        assert "':' is reserved" in str(exc_info.value)

    def test_extension_hook_command_with_colon_rejected(self, tmp_path):
        data = _extension_data(
            hooks={"before_plan": {"command": "speckit:bad:command"}}
        )
        with pytest.raises(ValidationError) as exc_info:
            ExtensionManifest(_write_manifest(tmp_path, data, "extension.yml"))
        assert "':' is reserved" in str(exc_info.value)


# ---------------------------------------------------------------------------
# `iter_contributions` output surface
# ---------------------------------------------------------------------------


class TestContributionSurface:
    def test_preset_iter_contributions_matrix(self, tmp_path):
        manifest = PresetManifest(_write_manifest(tmp_path, _preset_data(), "preset.yml"))
        entries = manifest.iter_contributions()
        by_kind = {e["kind"]: e for e in entries}
        assert by_kind["command"]["id"] == "preset:speckit-core:command:speckit.plan"
        assert by_kind["template"]["id"] == "preset:speckit-core:template:spec-template"
        assert by_kind["script"]["id"] == "preset:speckit-core:script:setup-plan"
        for entry in entries:
            assert entry["layer"] == "preset"
            assert entry["sourceId"] == "speckit-core"

    def test_extension_iter_contributions_matrix(self, tmp_path):
        data = _extension_data(
            hooks={"before_specify": {"command": "speckit.speckitgit.branch"}}
        )
        manifest = ExtensionManifest(_write_manifest(tmp_path, data, "extension.yml"))
        entries = manifest.iter_contributions()
        kinds = {e["kind"]: e for e in entries}
        assert kinds["command"]["id"] == "extension:speckit-git:command:speckit.speckitgit.branch"
        assert kinds["template"]["id"] == "extension:speckit-git:template:pr-body"
        assert kinds["script"]["id"] == "extension:speckit-git:script:post-commit"
        assert kinds["hook"]["id"] == "extension:speckit-git:hook:before_specify:speckit.speckitgit.branch"
        assert kinds["hook"]["name"] == "before_specify:speckit.speckitgit.branch"

    def test_contribution_id_lookup(self, tmp_path):
        manifest = PresetManifest(_write_manifest(tmp_path, _preset_data(), "preset.yml"))
        assert (
            manifest.contribution_id("command", "speckit.plan")
            == "preset:speckit-core:command:speckit.plan"
        )
        assert manifest.contribution_id("command", "does-not-exist") is None

    def test_representation_shape_is_additive_for_preset(self, tmp_path):
        original = _preset_data()
        manifest = PresetManifest(_write_manifest(tmp_path, original, "preset.yml"))
        derived_keys = {"layer", "sourceId", "kind", "id"}
        for src_entry, out_entry in zip(original["provides"]["templates"], manifest.iter_contributions()):
            assert set(src_entry.keys()).issubset(out_entry.keys())
            assert derived_keys.issubset(out_entry.keys())

    def test_representation_shape_is_additive_for_extension(self, tmp_path):
        original = _extension_data(
            hooks={"before_specify": {"command": "speckit.speckitgit.branch"}}
        )
        manifest = ExtensionManifest(_write_manifest(tmp_path, original, "extension.yml"))
        entries = manifest.iter_contributions()
        derived_named = {"layer", "sourceId", "kind", "id"}

        cmd_entry = original["provides"]["commands"][0]
        cmd_out = next(e for e in entries if e["kind"] == "command")
        assert set(cmd_entry.keys()).issubset(cmd_out.keys())
        assert derived_named.issubset(cmd_out.keys())

        hook_entry = original["hooks"]["before_specify"]
        hook_out = next(e for e in entries if e["kind"] == "hook")
        assert set(hook_entry.keys()).issubset(hook_out.keys())
        assert derived_named.issubset(hook_out.keys())
        assert hook_out["name"] == "before_specify:speckit.speckitgit.branch"

    def test_underlying_data_not_mutated(self, tmp_path):
        original = _preset_data()
        original_snapshot = copy.deepcopy(original)
        manifest = PresetManifest(_write_manifest(tmp_path, original, "preset.yml"))
        _ = manifest.iter_contributions()
        assert manifest.data == original_snapshot


# ---------------------------------------------------------------------------
# `lookupId` round-trip through the resolver
# ---------------------------------------------------------------------------


def _make_project(root: Path) -> Path:
    """Create a minimal project layout the resolver understands."""
    (root / ".specify" / "presets").mkdir(parents=True)
    (root / ".specify" / "extensions").mkdir(parents=True)
    (root / ".specify" / "memory").mkdir(parents=True)
    (root / "templates" / "commands").mkdir(parents=True)
    (root / "templates" / "scripts").mkdir(parents=True)
    return root


class TestLookupIdRoundTrip:
    def test_project_override_layer_carries_sentinel_lookup_id(self, tmp_path):
        project = _make_project(tmp_path)
        overrides_dir = project / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True)
        (overrides_dir / "spec-template.md").write_text("override", encoding="utf-8")
        resolver = PresetResolver(project)
        layers = resolver.collect_all_layers("spec-template", "template")
        override_layer = next(
            layer for layer in layers if layer["source"] == "project override"
        )
        assert override_layer["lookupId"] == derive_named_id(
            PROJECT_OVERRIDE_LAYER, "_", "template", "spec-template"
        )

    def test_core_layer_carries_core_lookup_id(self, tmp_path):
        project = _make_project(tmp_path)
        (project / "templates" / "spec-template.md").write_text("core", encoding="utf-8")
        # PresetResolver reads templates from a bundled/repo path — point the
        # resolver at the fixture project by monkey-patching the templates_dir.
        resolver = PresetResolver(project)
        resolver.templates_dir = project / "templates"
        layers = resolver.collect_all_layers("spec-template", "template")
        core_layer = next(layer for layer in layers if layer["source"] == "core")
        assert core_layer["lookupId"] == derive_named_id(
            "core", "_", "template", "spec-template"
        )

    def test_preset_layer_lookup_id_matches_manifest_contribution_id(self, tmp_path):
        project = _make_project(tmp_path)
        pack_id = "speckit-fixture"
        pack_dir = project / ".specify" / "presets" / pack_id
        (pack_dir / "templates").mkdir(parents=True)
        (pack_dir / "templates" / "spec-template.md").write_text("preset", encoding="utf-8")
        _write_manifest(
            pack_dir,
            {
                "schema_version": "1.0",
                "preset": {
                    "id": pack_id,
                    "name": pack_id,
                    "version": "1.0.0",
                    "description": "Fixture",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "templates": [
                        {
                            "type": "template",
                            "name": "spec-template",
                            "file": "templates/spec-template.md",
                        }
                    ]
                },
            },
            "preset.yml",
        )
        registry = {
            "schema_version": "1.0",
            "presets": {
                pack_id: {"version": "1.0.0", "priority": 10, "enabled": True}
            },
        }
        (project / ".specify" / "presets" / ".registry").write_text(
            json.dumps(registry), encoding="utf-8"
        )
        resolver = PresetResolver(project)
        layers = resolver.collect_all_layers("spec-template", "template")
        preset_layer = next(
            layer for layer in layers if layer["source"].startswith(pack_id)
        )
        manifest = PresetManifest(pack_dir / "preset.yml")
        assert preset_layer["lookupId"] == manifest.contribution_id("template", "spec-template")
        assert preset_layer["lookupId"] == f"preset:{pack_id}:template:spec-template"


# ---------------------------------------------------------------------------
# Determinism across environments
# ---------------------------------------------------------------------------


_SUBPROCESS_SCRIPT = textwrap.dedent(
    """
    import sys, json
    from specify_cli.extensions import ExtensionManifest
    manifest = ExtensionManifest(sys.argv[1])
    ids = [c["id"] for c in manifest.iter_contributions()]
    sys.stdout.write(json.dumps(ids))
    """
)


class TestDeterminism:
    def _fixture_manifest(self, tmp_path: Path) -> Path:
        data = _extension_data(
            hooks={
                "before_specify": {"command": "speckit.speckitgit.branch"},
                "before_plan": [
                    {"command": "speckit.speckitgit.branch", "priority": 10},
                    {"command": "speckit.speckitgit.branch", "priority": 20},
                ],
            }
        )
        return _write_manifest(tmp_path, data, "extension.yml")

    def test_identifiers_match_across_subprocesses(self, tmp_path):
        manifest_path = self._fixture_manifest(tmp_path)
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            [str(Path(__file__).resolve().parent.parent / "src"), env.get("PYTHONPATH", "")]
        )

        def _run() -> str:
            proc = subprocess.run(
                [sys.executable, "-c", _SUBPROCESS_SCRIPT, str(manifest_path)],
                capture_output=True,
                text=True,
                env=env,
                check=True,
            )
            return proc.stdout

        assert _run() == _run()

    def test_ids_independent_of_paths_and_mtimes(self, tmp_path):
        original_dir = tmp_path / "orig"
        copied_dir = tmp_path / "copy"
        original_dir.mkdir()
        manifest_path = self._fixture_manifest(original_dir)
        original_ids = [c["id"] for c in ExtensionManifest(manifest_path).iter_contributions()]

        shutil.copytree(original_dir, copied_dir)
        distant_past = time.time() - 3600
        os.utime(copied_dir / manifest_path.name, (distant_past, distant_past))
        copied_ids = [
            c["id"] for c in ExtensionManifest(copied_dir / manifest_path.name).iter_contributions()
        ]
        assert original_ids == copied_ids


# ---------------------------------------------------------------------------
# Identifiers never persisted
# ---------------------------------------------------------------------------


class TestNoPersistence:
    def test_no_id_written_to_manifest_files(self, tmp_path):
        data = _extension_data(
            hooks={"before_specify": {"command": "speckit.speckitgit.branch"}}
        )
        manifest_path = _write_manifest(tmp_path, data, "extension.yml")
        # Read identifiers to force the derivation code path.
        manifest = ExtensionManifest(manifest_path)
        ids = [c["id"] for c in manifest.iter_contributions()]
        assert ids  # sanity check — feature actually ran
        on_disk = manifest_path.read_text(encoding="utf-8")
        assert ":command:" not in on_disk
        assert ":template:" not in on_disk
        assert ":script:" not in on_disk
        assert ":hook:" not in on_disk

    def test_no_id_written_to_preset_manifest_files(self, tmp_path):
        preset_path = _write_manifest(tmp_path, _preset_data(), "preset.yml")
        manifest = PresetManifest(preset_path)
        _ = [c["id"] for c in manifest.iter_contributions()]
        on_disk = preset_path.read_text(encoding="utf-8")
        assert ":command:" not in on_disk
        assert ":template:" not in on_disk
        assert ":script:" not in on_disk
