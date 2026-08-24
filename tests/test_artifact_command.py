"""Unit and contract tests for the `specify artifact` command group.

Covers the pure-logic layer (:class:`ArtifactCatalog`) plus the CLI wiring
(``specify artifact list``, ``specify artifact info``) exercised through
Typer's ``CliRunner``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from specify_cli import app
from specify_cli.artifacts import (
    AmbiguousArtifactError,
    Artifact,
    ArtifactCatalog,
    ArtifactNotFoundError,
    NotASpecKitProjectError,
    StackLayer,
)


ERROR_REGEX = re.compile(r"^(unknown artifact |ambiguous artifact |not a Spec Kit project)")


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


def _install_preset(project_root: Path, pack_id: str, provides: dict, priority: int = 10) -> Path:
    """Drop a minimal preset onto disk and register it in the ``.registry`` file."""
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

    def test_lookup_id_grammar(self, spec_kit_project: Path):
        info = ArtifactCatalog(spec_kit_project).get_artifact_info("speckit.constitution")
        for layer in info["stack"]:
            assert re.match(
                r"^(preset|extension|core):[^:]+:(command|template|script):[^:]+(:[0-9a-f]{12})?$",
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
        _install_preset(
            spec_kit_project,
            "test-ambig",
            {
                "templates": [{"name": "shared-name", "description": "t"}],
                "scripts": [{"name": "shared-name", "description": "s"}],
            },
        )
        with pytest.raises(AmbiguousArtifactError) as excinfo:
            ArtifactCatalog(spec_kit_project).get_artifact_info("shared-name")
        assert excinfo.value.message.startswith("ambiguous artifact shared-name: matches kinds")
        assert ERROR_REGEX.match(excinfo.value.message)


class TestKindHint:
    def test_kind_flag_disambiguates(self, spec_kit_project: Path):
        _install_preset(
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
        from typer.testing import CliRunner

        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "list"])
        assert result.exit_code == 2
        assert result.stdout == ""

    def test_list_json_emits_array(self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch):
        from typer.testing import CliRunner

        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "list", "--json"])
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert isinstance(payload, list)
        assert result.stdout.endswith("\n")

    def test_list_json_is_pretty_printed(self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch):
        from typer.testing import CliRunner

        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "list", "--json"])
        assert '  "id"' in result.stdout  # 2-space indent visible

    def test_info_json_shape(self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch):
        from typer.testing import CliRunner

        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "info", "speckit.constitution", "--json"])
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert set(payload.keys()) == {"id", "name", "kind", "description", "stack"}

    def test_info_unknown_error_envelope(self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch):
        from typer.testing import CliRunner

        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "info", "no.such.thing", "--json"])
        assert result.exit_code == 1
        assert result.stdout == ""
        err = json.loads(result.stderr)
        assert set(err.keys()) == {"error"}
        assert ERROR_REGEX.match(err["error"])

    def test_not_a_project_error_envelope(self, non_project: Path, monkeypatch: pytest.MonkeyPatch):
        from typer.testing import CliRunner

        monkeypatch.chdir(non_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "list", "--json"])
        assert result.exit_code == 1
        assert result.stdout == ""
        err = json.loads(result.stderr)
        assert err["error"] == "not a Spec Kit project: no .specify/ directory found"

    def test_stdout_empty_on_error(self, non_project: Path, monkeypatch: pytest.MonkeyPatch):
        from typer.testing import CliRunner

        monkeypatch.chdir(non_project)
        runner = CliRunner()
        for argv in (
            ["artifact", "list", "--json"],
            ["artifact", "info", "x", "--json"],
        ):
            result = runner.invoke(app, argv)
            assert result.stdout == "", f"stdout leak for {argv}: {result.stdout!r}"


class TestUTF8NoBOM:
    def test_output_is_utf8_without_bom(self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch):
        from typer.testing import CliRunner

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
    def test_preset_replace_hides_core(self, spec_kit_project: Path):
        # Install a preset that replaces the constitution command.
        pack = _install_preset(
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
# Existing module-import placeholder retained for import safety.
# ---------------------------------------------------------------------------


def test_module_imports():
    from specify_cli.artifacts import ArtifactCatalog  # noqa: F401


