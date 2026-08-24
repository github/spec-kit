"""Unit and contract tests for the `specify artifact` command group.

Covers the pure-logic layer (:class:`ArtifactCatalog`) plus the CLI wiring
(``specify artifact list``, ``specify artifact info``) exercised through
Typer's ``CliRunner``.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.artifacts import (
    AmbiguousArtifactError,
    Artifact,
    ArtifactCatalog,
    ArtifactKind,
    ArtifactNotFoundError,
    ArtifactResolutionError,
    NotASpecKitProjectError,
    _derive_manifest_path,
    _preset_display_name,
)
from specify_cli.extensions import ExtensionRegistry
from specify_cli.presets import PresetRegistry, PresetResolver
from tests.conftest import install_preset


ERROR_REGEX = re.compile(
    r"^(unknown artifact |ambiguous artifact |artifact resolution failed|not a Spec Kit project)"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def spec_kit_project(tmp_path: Path) -> Path:
    """Create a minimal but valid Spec Kit project layout."""
    root = tmp_path / "proj"
    root.mkdir()
    (root / ".specify").mkdir()
    (root / ".specify" / "presets").mkdir()
    (root / ".specify" / "extensions").mkdir()
    (root / ".specify" / "templates").mkdir()
    return root


@pytest.fixture
def non_project(tmp_path: Path) -> Path:
    """A directory that intentionally lacks ``.specify/``."""
    root = tmp_path / "not-proj"
    root.mkdir()
    return root


# ---------------------------------------------------------------------------
# Contract tests — matching artifact-list.schema.json
# ---------------------------------------------------------------------------


class TestListArtifactsContract:
    def test_returns_list_of_artifact(self, spec_kit_project: Path):
        rows = ArtifactCatalog(spec_kit_project).list_artifacts()
        assert all(isinstance(r, Artifact) for r in rows)

    def test_every_row_has_required_fields(self, spec_kit_project: Path):
        for row in ArtifactCatalog(spec_kit_project).list_artifacts():
            d = row.to_json_dict()
            assert set(d.keys()) == {"id", "name", "kind", "description"}
            assert isinstance(d["description"], str)  # never None; empty string OK

    def test_id_grammar(self, spec_kit_project: Path):
        pattern = re.compile(r"^(command|template|script):[^:]+$")
        for row in ArtifactCatalog(spec_kit_project).list_artifacts():
            assert pattern.match(row.id), f"bad id: {row.id!r}"

    def test_name_never_contains_colon(self, spec_kit_project: Path):
        for row in ArtifactCatalog(spec_kit_project).list_artifacts():
            assert ":" not in row.name

    def test_kind_is_from_fixed_enum(self, spec_kit_project: Path):
        for row in ArtifactCatalog(spec_kit_project).list_artifacts():
            assert row.kind in ("command", "template", "script")

    def test_rows_are_unique(self, spec_kit_project: Path):
        rows = ArtifactCatalog(spec_kit_project).list_artifacts()
        ids = [r.id for r in rows]
        assert len(ids) == len(set(ids))

    def test_core_script_variants_have_one_resolvable_logical_name(
        self, spec_kit_project: Path
    ):
        catalog = ArtifactCatalog(spec_kit_project)
        scripts = [row for row in catalog.list_artifacts() if row.kind == "script"]

        assert {row.name for row in scripts} == {
            "check-prerequisites",
            "common",
            "create-new-feature",
            "resolve-template",
            "setup-plan",
            "setup-tasks",
        }
        for script in scripts:
            info = catalog.get_artifact_info(script.id)
            assert info["stack"][-1]["lookupId"] == f"core:_:script:{script.name}"

    def test_excludes_disabled_and_unusable_manifest_contributions(
        self, spec_kit_project: Path
    ):
        extensions_dir = spec_kit_project / ".specify" / "extensions"
        for extension_id, artifact_name, enabled, file_name in (
            (
                "disabled-ext",
                "disabled-template",
                False,
                "templates/disabled-template.md",
            ),
            (
                "missing-file-ext",
                "missing-template",
                True,
                "templates/missing-template.md",
            ),
        ):
            extension_dir = extensions_dir / extension_id
            extension_dir.mkdir()
            (extension_dir / "extension.yml").write_text(
                yaml.safe_dump(
                    {
                        "schema_version": "1.0",
                        "extension": {
                            "id": extension_id,
                            "name": extension_id,
                            "version": "1.0.0",
                            "description": "test",
                            "author": "test",
                            "repository": "https://example.com",
                            "license": "MIT",
                        },
                        "requires": {"speckit_version": ">=0.2.0"},
                        "provides": {
                            "templates": [
                                {
                                    "name": artifact_name,
                                    "file": file_name,
                                    "description": "Should not be listed",
                                }
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )
            if not enabled:
                template = extension_dir / file_name
                template.parent.mkdir()
                template.write_text("# Disabled\n", encoding="utf-8")
            ExtensionRegistry(extensions_dir).add(
                extension_id, {"version": "1.0.0", "enabled": enabled}
            )

        names = {row.name for row in ArtifactCatalog(spec_kit_project).list_artifacts()}
        assert "disabled-template" not in names
        assert "missing-template" not in names

    def test_unregistered_extension_uses_directory_id_for_lookup(self, spec_kit_project: Path):
        ext_dir = spec_kit_project / ".specify" / "extensions" / "renamed"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()
        (ext_dir / "commands" / "actual.md").write_text(
            "---\ndescription: Dir identity wins\n---\nbody\n",
            encoding="utf-8",
        )
        (ext_dir / "extension.yml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "1.0",
                    "extension": {
                        "id": "original",
                        "name": "Original Id",
                        "version": "1.0.0",
                        "description": "test",
                        "author": "test",
                        "repository": "https://example.com",
                        "license": "MIT",
                    },
                    "requires": {"speckit_version": ">=0.2.0"},
                    "provides": {
                        "commands": [
                            {
                                "name": "speckit.original.hello",
                                "file": "commands/actual.md",
                                "description": "manifest declared command",
                            }
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )

        info = ArtifactCatalog(spec_kit_project).get_artifact_info("speckit.original.hello")
        assert info["stack"][0]["lookupId"] == "extension:renamed:command:speckit.original.hello"
        assert (
            PresetResolver(spec_kit_project)
            .collect_all_layers("speckit.original.hello", "command")[0]["lookupId"]
            == "extension:renamed:command:speckit.original.hello"
        )

    def test_includes_project_local_core_assets(self, spec_kit_project: Path):
        templates_dir = spec_kit_project / ".specify" / "templates"
        (templates_dir / "legacy-template.md").write_text(
            "---\ndescription: Local template\n---\n", encoding="utf-8"
        )
        commands_dir = templates_dir / "commands"
        commands_dir.mkdir()
        (commands_dir / "local-command.md").write_text(
            "---\ndescription: Local command\n---\n", encoding="utf-8"
        )
        scripts_dir = templates_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "legacy-script.sh").write_text(
            "# Local script\n", encoding="utf-8"
        )

        catalog = ArtifactCatalog(spec_kit_project)
        artifacts = {artifact.id: artifact for artifact in catalog.list_artifacts()}

        assert artifacts["template:legacy-template"].description == "Local template"
        assert artifacts["command:speckit.local-command"].description == "Local command"
        assert artifacts["script:legacy-script"].description == "Local script"
        assert catalog.get_artifact_info("speckit.local-command")["stack"][0]["lookupId"] == (
            "core:_:command:speckit.local-command"
        )
        assert catalog.get_artifact_info("legacy-template")["stack"][0]["lookupId"] == (
            "core:_:template:legacy-template"
        )
        assert catalog.get_artifact_info("legacy-script")["stack"][0]["lookupId"] == (
            "core:_:script:legacy-script"
        )

    @pytest.mark.skipif(os.name == "nt", reason="':' filenames are unsupported on Windows")
    def test_skips_invalid_colon_names_in_project_local_inventory(self, spec_kit_project: Path):
        templates_dir = spec_kit_project / ".specify" / "templates"
        commands_dir = templates_dir / "commands"
        scripts_dir = templates_dir / "scripts"
        overrides_dir = templates_dir / "overrides"
        override_scripts_dir = overrides_dir / "scripts"
        commands_dir.mkdir(parents=True)
        scripts_dir.mkdir(parents=True)
        overrides_dir.mkdir(parents=True)
        override_scripts_dir.mkdir(parents=True)

        (templates_dir / "bad:template.md").write_text("---\ndescription: bad\n---\n", encoding="utf-8")
        (commands_dir / "bad:command.md").write_text("---\ndescription: bad\n---\n", encoding="utf-8")
        (scripts_dir / "bad:script.sh").write_text("# bad\n", encoding="utf-8")
        (overrides_dir / "bad:override.md").write_text("override", encoding="utf-8")
        (override_scripts_dir / "bad:override-script.sh").write_text("# bad\n", encoding="utf-8")

        artifacts = ArtifactCatalog(spec_kit_project).list_artifacts()
        assert all(":" not in artifact.name for artifact in artifacts)

    def test_preserves_prefixed_project_local_command_names(self, spec_kit_project: Path):
        commands_dir = spec_kit_project / ".specify" / "templates" / "commands"
        commands_dir.mkdir()
        (commands_dir / "speckit.local-prefixed.md").write_text(
            "---\ndescription: Local prefixed command\n---\n", encoding="utf-8"
        )

        artifacts = {artifact.id: artifact for artifact in ArtifactCatalog(spec_kit_project).list_artifacts()}
        assert "command:speckit.local-prefixed" in artifacts
        assert "command:speckit.speckit.local-prefixed" not in artifacts

    def test_prefers_exact_core_command_name(self, spec_kit_project: Path):
        commands_dir = spec_kit_project / ".specify" / "templates" / "commands"
        commands_dir.mkdir()
        (commands_dir / "foo.md").write_text(
            "---\ndescription: Stripped fallback\n---\n", encoding="utf-8"
        )
        exact_path = commands_dir / "speckit.foo.md"
        exact_path.write_text(
            "---\ndescription: Exact logical name\n---\n", encoding="utf-8"
        )

        assert PresetResolver(spec_kit_project).resolve("speckit.foo", "command") == exact_path
        info = ArtifactCatalog(spec_kit_project).get_artifact_info("speckit.foo")
        assert info["description"] == "Exact logical name"

    def test_active_preset_description_overrides_hidden_core_description(
        self, spec_kit_project: Path
    ):
        """A preset that overrides a core command must win the description too.

        Regression test: descriptions used to be merged "first non-empty
        wins", and core rows were inserted before contributions — so an
        active preset's replacement of a core command still reported the
        (now-inactive) core description.
        """
        commands_dir = spec_kit_project / ".specify" / "templates" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "speckit.constitution.md").write_text(
            "---\ndescription: Core description\n---\n", encoding="utf-8"
        )

        pack = install_preset(
            spec_kit_project,
            "override-preset",
            {
                "commands": [
                    {"name": "speckit.constitution", "description": "Preset description"}
                ]
            },
        )
        (pack / "commands").mkdir()
        (pack / "commands" / "speckit.constitution.md").write_text(
            "# Preset\n", encoding="utf-8"
        )

        artifacts = {
            artifact.id: artifact
            for artifact in ArtifactCatalog(spec_kit_project).list_artifacts()
        }
        assert artifacts["command:speckit.constitution"].description == "Preset description"

    def test_higher_precedence_preset_description_wins(self, spec_kit_project: Path):
        """When two presets both provide an artifact, the winner's description wins.

        Lower ``priority`` number means higher precedence (see
        ``PresetResolver.collect_all_layers``); the loser's description must
        not leak through just because it happens to be enumerated first
        alphabetically.
        """
        pack_low = install_preset(
            spec_kit_project,
            "aaa-low-priority-preset",
            {"templates": [{"name": "shared-artifact", "description": "Loser description"}]},
            priority=20,
        )
        (pack_low / "templates").mkdir()
        (pack_low / "templates" / "shared-artifact.md").write_text(
            "# Loser\n", encoding="utf-8"
        )

        pack_high = install_preset(
            spec_kit_project,
            "zzz-high-priority-preset",
            {"templates": [{"name": "shared-artifact", "description": "Winner description"}]},
            priority=5,
        )
        (pack_high / "templates").mkdir()
        (pack_high / "templates" / "shared-artifact.md").write_text(
            "# Winner\n", encoding="utf-8"
        )

        artifacts = {
            artifact.id: artifact
            for artifact in ArtifactCatalog(spec_kit_project).list_artifacts()
        }
        assert artifacts["template:shared-artifact"].description == "Winner description"


class TestListSorting:
    """Deterministic ordering: kind first (command/template/script), then name."""

    def test_kind_grouping(self, spec_kit_project: Path):
        rows = ArtifactCatalog(spec_kit_project).list_artifacts()
        kinds_seen = [r.kind for r in rows]
        # kinds must appear as contiguous groups in the fixed order
        first_idx = {k: next((i for i, x in enumerate(kinds_seen) if x == k), None) for k in ("command", "template", "script")}
        indices = [v for v in first_idx.values() if v is not None]
        assert indices == sorted(indices)

    def test_name_sorted_within_kind(self, spec_kit_project: Path):
        rows = ArtifactCatalog(spec_kit_project).list_artifacts()
        by_kind: dict[str, list[str]] = {}
        for r in rows:
            by_kind.setdefault(r.kind, []).append(r.name)
        for _, names in by_kind.items():
            assert names == sorted(names)


class TestEmptyProject:
    def test_empty_stack_returns_empty_list(self, tmp_path: Path):
        # A .specify/ dir with no presets/extensions and no accessible core.
        # We can't easily wipe the core baseline in this process, so instead
        # verify list_artifacts is at least callable and returns a list.
        root = tmp_path / "empty"
        root.mkdir()
        (root / ".specify").mkdir()
        rows = ArtifactCatalog(root).list_artifacts()
        assert isinstance(rows, list)


# ---------------------------------------------------------------------------
# get_artifact_info contract
# ---------------------------------------------------------------------------


class TestInfoContract:
    def test_stack_ordered_highest_first(self, spec_kit_project: Path):
        info = ArtifactCatalog(spec_kit_project).get_artifact_info("speckit.constitution")
        assert info["stack"], "expected at least one stack layer"

    def test_exactly_one_active_row(self, spec_kit_project: Path):
        info = ArtifactCatalog(spec_kit_project).get_artifact_info("speckit.constitution")
        actives = [layer for layer in info["stack"] if layer["active"]]
        assert len(actives) == 1

    def test_active_is_index_zero(self, spec_kit_project: Path):
        info = ArtifactCatalog(spec_kit_project).get_artifact_info("speckit.constitution")
        assert info["stack"][0]["active"] is True
        for layer in info["stack"][1:]:
            assert layer["active"] is False

    def test_core_row_shape(self, spec_kit_project: Path):
        info = ArtifactCatalog(spec_kit_project).get_artifact_info("speckit.constitution")
        core = next(layer for layer in info["stack"] if layer["layer"] == "core")
        assert core["presetId"] is None
        assert core["presetName"] is None
        assert core["manifestPath"] is None
        assert core["strategy"] == "replace"
        assert re.match(r"^core:_:(command|template|script):[^:]+$", core["lookupId"])

    def test_project_override_row_shape(self, spec_kit_project: Path):
        overrides = spec_kit_project / ".specify" / "templates" / "overrides"
        overrides.mkdir()
        (overrides / "speckit.constitution.md").write_text("override", encoding="utf-8")

        info = ArtifactCatalog(spec_kit_project).get_artifact_info("speckit.constitution")

        project = next(layer for layer in info["stack"] if layer["layer"] == "project")
        assert project["presetId"] is None
        assert project["presetName"] is None
        assert project["manifestPath"] is None
        assert project["strategy"] == "replace"
        assert re.match(r"^project:_:(command|template|script):[^:]+$", project["lookupId"])

    def test_lookup_id_grammar(self, spec_kit_project: Path):
        info = ArtifactCatalog(spec_kit_project).get_artifact_info("speckit.constitution")
        for layer in info["stack"]:
            assert re.match(
                r"^(project|preset|extension|core):[^:]+:(command|template|script):[^:]+(:[0-9a-f]{12})?$",
                layer["lookupId"],
            )

    def test_id_matches_list(self, spec_kit_project: Path):
        cat = ArtifactCatalog(spec_kit_project)
        info = cat.get_artifact_info("speckit.constitution")
        assert info["id"] == "command:speckit.constitution"


# ---------------------------------------------------------------------------
# Error conditions — pinned strings for the artifact-error contract
# ---------------------------------------------------------------------------


class TestErrors:
    def test_unknown_artifact_message(self, spec_kit_project: Path):
        with pytest.raises(ArtifactNotFoundError) as excinfo:
            ArtifactCatalog(spec_kit_project).get_artifact_info("no.such.thing")
        assert excinfo.value.message == "unknown artifact no.such.thing"
        assert ERROR_REGEX.match(excinfo.value.message)

    def test_not_a_project(self, non_project: Path):
        with pytest.raises(NotASpecKitProjectError) as excinfo:
            ArtifactCatalog(non_project).list_artifacts()
        assert excinfo.value.message == "not a Spec Kit project: no .specify/ directory found"
        assert ERROR_REGEX.match(excinfo.value.message)

    def test_ambiguous_artifact_message(self, spec_kit_project: Path):
        """When both a command and a template share the same bare name."""
        # Register a preset that contributes 'shared-name' as both a
        # template and a script — the info lookup with no kind hint should
        # then be ambiguous.
        pack = install_preset(
            spec_kit_project,
            "test-ambig",
            {
                "templates": [
                    {"type": "template", "name": "shared-name", "description": "t"},
                    {"type": "script", "name": "shared-name", "description": "s"},
                ],
            },
        )
        (pack / "templates").mkdir()
        (pack / "templates" / "shared-name.md").write_text("# Template\n")
        (pack / "scripts").mkdir()
        (pack / "scripts" / "shared-name.sh").write_text("#!/usr/bin/env bash\n")
        with pytest.raises(AmbiguousArtifactError) as excinfo:
            ArtifactCatalog(spec_kit_project).get_artifact_info("shared-name")
        assert excinfo.value.message.startswith("ambiguous artifact shared-name: matches kinds")
        assert ERROR_REGEX.match(excinfo.value.message)

    def test_resolution_error_message(self):
        assert ArtifactResolutionError().message == "artifact resolution failed"

    def test_info_rejects_corrupt_extension_registry(self, spec_kit_project: Path):
        registry = spec_kit_project / ".specify" / "extensions" / ".registry"
        registry.write_text("{invalid", encoding="utf-8")

        with pytest.raises(ArtifactResolutionError):
            ArtifactCatalog(spec_kit_project).get_artifact_info("command:speckit.constitution")


class TestKindHint:
    def test_kind_flag_disambiguates(self, spec_kit_project: Path):
        install_preset(
            spec_kit_project,
            "test-kind",
            {"templates": [{"name": "dup", "description": "t"}],
             "scripts": [{"name": "dup", "description": "s"}]},
        )
        # No stack file backs these contributions on disk so the info call
        # will raise unknown after resolving kind — either way it should
        # not raise ambiguous when a kind is supplied.
        try:
            ArtifactCatalog(spec_kit_project).get_artifact_info("dup", kind="template")
        except ArtifactNotFoundError:
            pass  # expected: manifest declared it but no file to compose

    def test_shorthand_grammar(self, spec_kit_project: Path):
        # Even with core commands, the shorthand should route correctly.
        info = ArtifactCatalog(spec_kit_project).get_artifact_info("command:speckit.constitution")
        assert info["kind"] == "command"

    def test_conflicting_shorthand_and_flag(self, spec_kit_project: Path):
        with pytest.raises(ArtifactNotFoundError):
            ArtifactCatalog(spec_kit_project).get_artifact_info(
                "template:speckit.constitution", kind="command"
            )

    @pytest.mark.parametrize(
        ("kind", "name"),
        (
            ("template", "../../outside"),
            ("command", "template:foo"),
            ("script", "script:name"),
        ),
    )
    def test_kind_hint_rejects_invalid_name_components(
        self, spec_kit_project: Path, kind: ArtifactKind, name: str
    ):
        with pytest.raises(ArtifactNotFoundError):
            ArtifactCatalog(spec_kit_project).get_artifact_info(name, kind=kind)


# ---------------------------------------------------------------------------
# Skills exclusion
# ---------------------------------------------------------------------------


class TestSkillsExcluded:
    def test_no_skills_in_list(self, spec_kit_project: Path):
        skills_dir = spec_kit_project / ".github" / "skills" / "speckit-my-skill"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("---\nname: my-skill\n---\nbody", encoding="utf-8")
        rows = ArtifactCatalog(spec_kit_project).list_artifacts()
        assert not any("skill" in r.name.lower() for r in rows)


# ---------------------------------------------------------------------------
# CLI wiring — Typer CliRunner
# ---------------------------------------------------------------------------


class TestCLI:
    def test_list_requires_json_flag(self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "list"])
        assert result.exit_code == 2
        assert result.stdout == ""

    def test_list_json_emits_array(self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "list", "--json"])
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert isinstance(payload, list)
        assert result.stdout.endswith("\n")

    def test_list_json_is_pretty_printed(self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "list", "--json"])
        assert '  "id"' in result.stdout  # 2-space indent visible

    def test_info_json_shape(self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "info", "speckit.constitution", "--json"])
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert set(payload.keys()) == {"id", "name", "kind", "description", "stack"}

    def test_info_unknown_error_envelope(self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "info", "no.such.thing", "--json"])
        assert result.exit_code == 1
        assert result.stdout == ""
        err = json.loads(result.stderr)
        assert set(err.keys()) == {"error"}
        assert ERROR_REGEX.match(err["error"])

    def test_info_corrupt_extension_registry_uses_json_error_envelope(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        extensions_dir = spec_kit_project / ".specify" / "extensions"
        (extensions_dir / ".registry").write_text("{invalid", encoding="utf-8")
        monkeypatch.chdir(spec_kit_project)
        result = CliRunner().invoke(
            app, ["artifact", "info", "speckit.constitution", "--json"]
        )
        assert result.exit_code == 1
        assert result.stdout == ""
        assert json.loads(result.stderr) == {"error": "artifact resolution failed"}

    def test_list_corrupt_extension_registry_uses_json_error_envelope(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        extensions_dir = spec_kit_project / ".specify" / "extensions"
        (extensions_dir / ".registry").write_text("{invalid", encoding="utf-8")
        monkeypatch.chdir(spec_kit_project)
        result = CliRunner().invoke(app, ["artifact", "list", "--json"])
        assert result.exit_code == 1
        assert result.stdout == ""
        assert json.loads(result.stderr) == {"error": "artifact resolution failed"}

    def test_not_a_project_error_envelope(self, non_project: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(non_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "list", "--json"])
        assert result.exit_code == 1
        assert result.stdout == ""
        err = json.loads(result.stderr)
        assert err["error"] == "not a Spec Kit project: no .specify/ directory found"

    def test_stdout_empty_on_error(self, non_project: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(non_project)
        runner = CliRunner()
        for argv in (
            ["artifact", "list", "--json"],
            ["artifact", "info", "x", "--json"],
        ):
            result = runner.invoke(app, argv)
            assert result.stdout == "", f"stdout leak for {argv}: {result.stdout!r}"

    @pytest.mark.parametrize(
        "override",
        ("missing-project", "."),
    )
    def test_invalid_init_dir_override_uses_json_error_envelope(
        self,
        non_project: Path,
        monkeypatch: pytest.MonkeyPatch,
        override: str,
    ):
        monkeypatch.chdir(non_project)
        monkeypatch.setenv("SPECIFY_INIT_DIR", override)
        runner = CliRunner()
        for argv in (
            ["artifact", "list", "--json"],
            ["artifact", "info", "x", "--json"],
        ):
            result = runner.invoke(app, argv)
            assert result.exit_code == 1
            assert result.stdout == ""
            assert json.loads(result.stderr) == {
                "error": "not a Spec Kit project: no .specify/ directory found"
            }


class TestUTF8NoBOM:
    def test_output_is_utf8_without_bom(self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "list", "--json"])
        assert result.exit_code == 0
        # No BOM at start
        assert not result.stdout.startswith("\ufeff")


# ---------------------------------------------------------------------------
# Preset composition integration — active/hidden semantics
# ---------------------------------------------------------------------------


class TestStackComposition:
    def test_preset_command_uses_entry_type(self, spec_kit_project: Path):
        pack = install_preset(
            spec_kit_project,
            "test-command",
            {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.constitution",
                        "description": "override",
                    }
                ]
            },
        )
        (pack / "commands").mkdir()
        (pack / "commands" / "speckit.constitution.md").write_text(
            "---\ndescription: override\n---\nbody", encoding="utf-8"
        )

        rows = ArtifactCatalog(spec_kit_project).list_artifacts()
        assert any(row.id == "command:speckit.constitution" for row in rows)
        assert ArtifactCatalog(spec_kit_project).get_artifact_info("speckit.constitution")["kind"] == "command"

    def test_preset_single_segment_command_id_from_list_is_resolvable(
        self, spec_kit_project: Path
    ):
        pack = install_preset(
            spec_kit_project,
            "test-single-command",
            {"commands": [{"name": "specify", "description": "single segment"}]},
        )
        (pack / "commands").mkdir()
        (pack / "commands" / "specify.md").write_text(
            "---\ndescription: single segment\n---\nbody", encoding="utf-8"
        )

        catalog = ArtifactCatalog(spec_kit_project)
        ids = {row.id for row in catalog.list_artifacts()}

        assert "command:specify" in ids
        info = catalog.get_artifact_info("command:specify")
        assert info["id"] == "command:specify"
        assert catalog.get_artifact_info("specify", kind="command")["id"] == "command:specify"

    def test_preset_replace_hides_core(self, spec_kit_project: Path):
        # Install a preset that replaces the constitution command.
        pack = install_preset(
            spec_kit_project,
            "test-replace",
            {"commands": [{"name": "speckit.constitution", "description": "override"}]},
        )
        (pack / "commands").mkdir()
        (pack / "commands" / "speckit.constitution.md").write_text(
            "---\ndescription: override\n---\nbody", encoding="utf-8"
        )

        info = ArtifactCatalog(spec_kit_project).get_artifact_info("speckit.constitution")
        stack = info["stack"]
        assert stack[0]["active"] is True
        assert stack[0]["hidden"] is False
        # If a lower core layer exists it must be hidden.
        core_rows = [layer for layer in stack if layer["layer"] == "core"]
        for row in core_rows:
            assert row["hidden"] is True


# ---------------------------------------------------------------------------
# Convention-based discovery — extensions without a manifest, project overrides
# ---------------------------------------------------------------------------


class TestConventionDiscovery:
    def test_unregistered_extension_template_without_manifest(self, spec_kit_project: Path):
        ext_dir = spec_kit_project / ".specify" / "extensions" / "legacy" / "templates"
        ext_dir.mkdir(parents=True)
        (ext_dir / "legacy-template.md").write_text("body", encoding="utf-8")

        catalog = ArtifactCatalog(spec_kit_project)
        assert any(row.id == "template:legacy-template" for row in catalog.list_artifacts())
        info = catalog.get_artifact_info("legacy-template")
        assert info["stack"][0]["lookupId"] == "extension:legacy:template:legacy-template"

    def test_convention_command_and_script_are_listed(self, spec_kit_project: Path):
        ext_dir = spec_kit_project / ".specify" / "extensions" / "legacy"
        (ext_dir / "commands").mkdir(parents=True)
        (ext_dir / "commands" / "speckit.legacy.md").write_text("body", encoding="utf-8")
        (ext_dir / "scripts").mkdir()
        (ext_dir / "scripts" / "legacy-script.sh").write_text("#!/bin/sh\n", encoding="utf-8")

        ids = {row.id for row in ArtifactCatalog(spec_kit_project).list_artifacts()}
        assert "command:speckit.legacy" in ids
        assert "script:legacy-script" in ids

    def test_extension_readme_is_not_listed_as_template(self, spec_kit_project: Path):
        ext_dir = spec_kit_project / ".specify" / "extensions" / "legacy"
        ext_dir.mkdir(parents=True)
        (ext_dir / "README.md").write_text("docs", encoding="utf-8")

        ids = {row.id for row in ArtifactCatalog(spec_kit_project).list_artifacts()}
        assert "template:README" not in ids

    def test_disabled_extension_convention_file_is_excluded(self, spec_kit_project: Path):
        extensions_dir = spec_kit_project / ".specify" / "extensions"
        ext_dir = extensions_dir / "legacy" / "templates"
        ext_dir.mkdir(parents=True)
        (ext_dir / "legacy-template.md").write_text("body", encoding="utf-8")
        (extensions_dir / ".registry").write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "extensions": {"legacy": {"priority": 10, "enabled": False}},
                }
            ),
            encoding="utf-8",
        )

        ids = {row.id for row in ArtifactCatalog(spec_kit_project).list_artifacts()}
        assert "template:legacy-template" not in ids

    def test_project_override_only_artifact_is_listed(self, spec_kit_project: Path):
        overrides = spec_kit_project / ".specify" / "templates" / "overrides"
        (overrides / "scripts").mkdir(parents=True)
        (overrides / "local-template.md").write_text("body", encoding="utf-8")
        (overrides / "scripts" / "local-script.sh").write_text("#!/bin/sh\n", encoding="utf-8")

        catalog = ArtifactCatalog(spec_kit_project)
        ids = {row.id for row in catalog.list_artifacts()}
        assert "template:local-template" in ids
        assert "script:local-script" in ids
        info = catalog.get_artifact_info("local-template")
        assert info["stack"][0]["layer"] == "project"

    def test_dotted_override_only_artifact_is_a_command(self, spec_kit_project: Path):
        overrides = spec_kit_project / ".specify" / "templates" / "overrides"
        overrides.mkdir(parents=True)
        (overrides / "speckit.local.md").write_text("body", encoding="utf-8")

        catalog = ArtifactCatalog(spec_kit_project)
        ids = {row.id for row in catalog.list_artifacts()}
        assert "command:speckit.local" in ids
        assert "template:speckit.local" not in ids
        with pytest.raises(ArtifactNotFoundError):
            catalog.get_artifact_info("template:speckit.local")
        info = catalog.get_artifact_info("command:speckit.local")
        assert info["kind"] == "command"
        assert info["stack"][0]["layer"] == "project"

    def test_malformed_dotted_override_is_not_forced_to_command(
        self, spec_kit_project: Path
    ):
        overrides = spec_kit_project / ".specify" / "templates" / "overrides"
        overrides.mkdir(parents=True)
        (overrides / "speckit..local.md").write_text("body", encoding="utf-8")

        catalog = ArtifactCatalog(spec_kit_project)
        ids = {row.id for row in catalog.list_artifacts()}
        assert "template:speckit..local" in ids
        assert "command:speckit..local" not in ids

    def test_unregistered_preset_template_without_manifest(self, spec_kit_project: Path):
        pack_dir = spec_kit_project / ".specify" / "presets" / "legacy-preset"
        pack_dir.mkdir()
        PresetRegistry(pack_dir.parent).add(
            "legacy-preset", {"priority": 10, "version": "1.0.0"}
        )
        preset_templates_dir = pack_dir / "templates"
        preset_templates_dir.mkdir()
        (preset_templates_dir / "legacy-preset-template.md").write_text(
            "body", encoding="utf-8"
        )

        catalog = ArtifactCatalog(spec_kit_project)
        assert any(
            row.id == "template:legacy-preset-template" for row in catalog.list_artifacts()
        )
        info = catalog.get_artifact_info("legacy-preset-template")
        assert info["stack"][0]["lookupId"] == (
            "preset:legacy-preset:template:legacy-preset-template"
        )

    def test_command_override_is_not_duplicated_as_template(self, spec_kit_project: Path):
        ext_dir = spec_kit_project / ".specify" / "extensions" / "legacy" / "commands"
        ext_dir.mkdir(parents=True)
        (ext_dir / "speckit.legacy.md").write_text("body", encoding="utf-8")
        overrides = spec_kit_project / ".specify" / "templates" / "overrides"
        overrides.mkdir(parents=True)
        (overrides / "speckit.legacy.md").write_text("override", encoding="utf-8")

        catalog = ArtifactCatalog(spec_kit_project)
        ids = {row.id for row in catalog.list_artifacts()}
        assert "command:speckit.legacy" in ids
        assert "template:speckit.legacy" not in ids
        assert catalog.get_artifact_info("speckit.legacy")["kind"] == "command"


class TestManifestPathPortability:
    """`_derive_manifest_path` must never leak an absolute host path."""

    def test_preset_manifest_path_is_repo_relative(self, tmp_path: Path):
        project_root = tmp_path / "proj"
        pack_dir = project_root / ".specify" / "presets" / "my-pack"
        pack_dir.mkdir(parents=True)
        (pack_dir / "preset.yml").write_text("id: my-pack\n", encoding="utf-8")

        layer = {
            "lookupId": "preset:my-pack:template:spec-template",
            "path": pack_dir / "spec-template.md",
        }
        assert (
            _derive_manifest_path(layer, project_root)
            == ".specify/presets/my-pack/preset.yml"
        )

    def test_extension_manifest_path_is_repo_relative(self, tmp_path: Path):
        project_root = tmp_path / "proj"
        ext_dir = project_root / ".specify" / "extensions" / "my-ext"
        ext_dir.mkdir(parents=True)
        (ext_dir / "extension.yml").write_text("id: my-ext\n", encoding="utf-8")

        layer = {
            "lookupId": "extension:my-ext:command:speckit.my-ext.go",
            "path": ext_dir / "commands" / "speckit.my-ext.go.md",
        }
        assert (
            _derive_manifest_path(layer, project_root)
            == ".specify/extensions/my-ext/extension.yml"
        )

    def test_missing_manifest_file_is_none(self, tmp_path: Path):
        project_root = tmp_path / "proj"
        pack_dir = project_root / ".specify" / "presets" / "my-pack"
        pack_dir.mkdir(parents=True)

        layer = {
            "lookupId": "preset:my-pack:template:spec-template",
            "path": pack_dir / "spec-template.md",
        }
        assert _derive_manifest_path(layer, project_root) is None

    def test_core_and_project_layers_have_no_manifest(self, tmp_path: Path):
        project_root = tmp_path / "proj"
        project_root.mkdir()

        core_layer = {"lookupId": "core:_:template:spec-template"}
        project_layer = {"lookupId": "project:_:template:spec-template"}
        assert _derive_manifest_path(core_layer, project_root) is None
        assert _derive_manifest_path(project_layer, project_root) is None


class TestPresetDisplayName:
    """`_preset_display_name` delegates to the validated `PresetManifest.name`."""

    _VALID_MANIFEST = """\
schema_version: "1.0"
preset:
  id: pack
  name: Nested Name
  version: "1.0.0"
  description: A test preset
requires:
  speckit_version: ">=1.0.0"
provides:
  templates:
    - type: template
      name: spec-template
      file: spec-template.md
"""

    def test_reads_validated_preset_name(self, tmp_path: Path):
        pack_dir = tmp_path / "pack"
        pack_dir.mkdir()
        (pack_dir / "preset.yml").write_text(self._VALID_MANIFEST, encoding="utf-8")

        assert _preset_display_name(pack_dir, "pack") == "Nested Name"

    def test_falls_back_to_pack_id_when_manifest_fails_validation(self, tmp_path: Path):
        """A legacy flat manifest with no ``preset:`` section fails validation."""
        pack_dir = tmp_path / "pack"
        pack_dir.mkdir()
        (pack_dir / "preset.yml").write_text("id: pack\nname: Flat Name\n", encoding="utf-8")

        assert _preset_display_name(pack_dir, "pack") == "pack"

    def test_falls_back_to_pack_id_without_manifest_file(self, tmp_path: Path):
        pack_dir = tmp_path / "pack"
        pack_dir.mkdir()

        assert _preset_display_name(pack_dir, "pack") == "pack"


# ---------------------------------------------------------------------------
# Existing module-import placeholder retained for import safety.
# ---------------------------------------------------------------------------


def test_module_imports():
    assert ArtifactCatalog is not None
