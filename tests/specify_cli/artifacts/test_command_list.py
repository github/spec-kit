"""Tests for ``specify artifact list``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import ExtensionRegistry
from specify_cli.presets import PresetRegistry
from tests.conftest import install_preset


class TestCommandList:
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

    def test_list_json_rows_include_stack(self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "list", "--json"])
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload, "expected at least one artifact"

        row = payload[0]
        assert set(row.keys()) == {"id", "name", "kind", "description", "stack"}
        assert isinstance(row["stack"], list)

        info_result = runner.invoke(app, ["artifact", "info", row["id"], "--json"])
        assert info_result.exit_code == 0, info_result.stderr
        info = json.loads(info_result.stdout)
        assert row["stack"] == info["stack"]

    def test_list_json_stack_source_path_contract(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        preset_pack = install_preset(
            spec_kit_project,
            "compliance",
            {
                "commands": [
                    {
                        "name": "speckit.compliance.plan",
                        "file": "commands/speckit.compliance.plan.md",
                        "description": "Compliance plan",
                    }
                ]
            },
        )
        (preset_pack / "commands").mkdir()
        (preset_pack / "commands" / "speckit.compliance.plan.md").write_text(
            "---\ndescription: Compliance plan\n---\nbody\n", encoding="utf-8"
        )
        PresetRegistry(spec_kit_project / ".specify" / "presets").update(
            "compliance",
            {
                "registered_skills": {
                    "copilot": ["speckit-compliance-plan"],
                }
            },
        )
        skill_file = (
            spec_kit_project
            / ".github"
            / "skills"
            / "speckit-compliance-plan"
            / "SKILL.md"
        )
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: speckit-compliance-plan\n---\n", encoding="utf-8")

        extension_dir = spec_kit_project / ".specify" / "extensions" / "quality"
        (extension_dir / "templates").mkdir(parents=True)
        (extension_dir / "templates" / "checklist.md").write_text(
            "---\ndescription: Extension checklist\n---\n", encoding="utf-8"
        )
        (extension_dir / "extension.yml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "1.0",
                    "extension": {
                        "id": "quality",
                        "name": "Quality",
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
                                "name": "checklist",
                                "file": "templates/checklist.md",
                                "description": "Extension checklist",
                            }
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )
        ExtensionRegistry(spec_kit_project / ".specify" / "extensions").add(
            "quality", {"version": "1.0.0", "enabled": True}
        )

        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "list", "--json"])
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)

        non_null_source_paths: set[str] = set()
        for row in payload:
            for layer in row["stack"]:
                assert "sourcePath" in layer
                source_path = layer["sourcePath"]
                if source_path is None:
                    continue
                assert isinstance(source_path, str)
                assert (spec_kit_project / source_path).is_file()
                non_null_source_paths.add(source_path)

        assert ".github/skills/speckit-compliance-plan/SKILL.md" in non_null_source_paths
        assert ".specify/extensions/quality/templates/checklist.md" in non_null_source_paths

    def test_list_json_is_pretty_printed(self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "list", "--json"])
        assert '  "id"' in result.stdout  # 2-space indent visible

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

    def test_output_is_utf8_without_bom(self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "list", "--json"])
        assert result.exit_code == 0
        # No BOM at start
        assert not result.stdout.startswith("\ufeff")
