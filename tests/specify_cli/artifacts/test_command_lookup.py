"""Tests for ``specify artifact lookup``."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.artifacts import ArtifactCatalog
from tests.conftest import install_preset


class TestCommandLookup:
    def test_lookup_json_cross_references_manifest_contribution(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(spec_kit_project)
        pack = install_preset(
            spec_kit_project,
            "lookup-pack",
            {
                "templates": [
                    {
                        "type": "template",
                        "name": "lookup-template",
                        "file": "templates/lookup.md",
                        "description": "Lookup target",
                    }
                ]
            },
        )
        (pack / "templates").mkdir()
        (pack / "templates" / "lookup.md").write_text("body", encoding="utf-8")

        lookup_id = ArtifactCatalog(spec_kit_project).get_artifact_info(
            "template:lookup-template"
        )["stack"][0]["lookupId"]
        result = CliRunner().invoke(
            app, ["artifact", "lookup", lookup_id, "--json"]
        )

        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["id"] == lookup_id
        assert payload["contribution"]["description"] == "Lookup target"
        assert payload["sourcePath"] == (
            ".specify/presets/lookup-pack/templates/lookup.md"
        )

    def test_lookup_json_rejects_unknown_contribution(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(spec_kit_project)
        lookup_id = "extension:missing:command:speckit.missing.command"

        result = CliRunner().invoke(
            app, ["artifact", "lookup", lookup_id, "--json"]
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert json.loads(result.stderr) == {
            "error": f"unknown contribution {lookup_id}"
        }

    @pytest.mark.parametrize(
        "manifest_value",
        [
            date(2026, 1, 1),
            float("nan"),
            float("inf"),
            float("-inf"),
            "\ud800",
        ],
        ids=[
            "date",
            "nan",
            "positive-infinity",
            "negative-infinity",
            "unpaired-surrogate",
        ],
    )
    def test_lookup_json_rejects_non_json_manifest_value(
        self,
        spec_kit_project: Path,
        monkeypatch: pytest.MonkeyPatch,
        manifest_value: object,
    ):
        monkeypatch.chdir(spec_kit_project)
        install_preset(
            spec_kit_project,
            "non-json-contribution",
            {
                "templates": [
                    {
                        "type": "template",
                        "name": "non-json-contribution",
                        "extra": manifest_value,
                    }
                ]
            },
        )

        result = CliRunner().invoke(
            app,
            [
                "artifact",
                "lookup",
                "preset:non-json-contribution:template:non-json-contribution",
                "--json",
            ],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert json.loads(result.stderr) == {
            "error": "artifact resolution failed"
        }

    @pytest.mark.parametrize(
        "lookup_id",
        [
            "invalid:source:command:name",
            "extension:source:invalid:name",
            "extension:source:hook:%FF:command",
            "extension:source:hook:event:%ZZ",
        ],
    )
    def test_lookup_json_rejects_malformed_lookup_id(
        self,
        spec_kit_project: Path,
        monkeypatch: pytest.MonkeyPatch,
        lookup_id: str,
    ):
        monkeypatch.chdir(spec_kit_project)

        result = CliRunner().invoke(
            app, ["artifact", "lookup", lookup_id, "--json"]
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert json.loads(result.stderr) == {
            "error": f"unknown contribution {lookup_id}"
        }

    def test_lookup_requires_json_flag(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(spec_kit_project)
        result = CliRunner().invoke(
            app,
            [
                "artifact",
                "lookup",
                "extension:missing:command:speckit.missing.command",
            ],
        )

        assert result.exit_code == 2
        assert result.stdout == ""

    def test_lookup_validates_project_before_lookup_id(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(tmp_path)
        result = CliRunner().invoke(
            app,
            ["artifact", "lookup", "project:_:command:local", "--json"],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert json.loads(result.stderr) == {
            "error": "not a Spec Kit project: no .specify/ directory found"
        }
