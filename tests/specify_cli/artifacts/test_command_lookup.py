"""Tests for ``specify artifact lookup``."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import Mock

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.artifacts import ArtifactCatalog, command_lookup
from specify_cli.integrations import installer
from tests.conftest import install_preset


class TestCommandLookup:
    @pytest.mark.parametrize(
        "options",
        [None, {}, {"allow_symlinks": False}, {"allow_symlinks": True}],
        ids=["missing-file", "missing-setting", "deny", "allow"],
    )
    def test_lookup_json_cross_references_manifest_contribution(
        self,
        spec_kit_project: Path,
        monkeypatch: pytest.MonkeyPatch,
        options: dict[str, object] | None,
    ):
        monkeypatch.chdir(spec_kit_project)
        config = spec_kit_project / ".specify" / "init-options.json"
        if options is None:
            config.unlink(missing_ok=True)
        else:
            config.write_text(json.dumps(options), encoding="utf-8")
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

    @pytest.mark.parametrize(
        "case,diagnostic",
        [
            ("malformed", "Invalid JSON"),
            ("invalid-setting", "JSON boolean"),
            ("symlink", "symlink"),
            ("dangling-symlink", "symlink"),
        ],
    )
    def test_lookup_policy_failure_precedes_loader_and_catalog(
        self,
        spec_kit_project: Path,
        monkeypatch: pytest.MonkeyPatch,
        case: str,
        diagnostic: str,
    ):
        monkeypatch.chdir(spec_kit_project)
        config = spec_kit_project / ".specify" / "init-options.json"
        if case == "malformed":
            config.write_text("{", encoding="utf-8")
        elif case == "invalid-setting":
            config.write_text('{"allow_symlinks": "true"}', encoding="utf-8")
        else:
            target = spec_kit_project / "linked-init-options.json"
            if case == "symlink":
                target.write_text('{"allow_symlinks": true}', encoding="utf-8")
            config.unlink(missing_ok=True)
            try:
                config.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                pytest.skip(f"Symlinks unavailable: {exc}")

        loader = Mock(side_effect=AssertionError("installed loader reached"))
        catalog = Mock(side_effect=AssertionError("artifact catalog reached"))
        monkeypatch.setattr(installer, "load_installed_integrations", loader)
        monkeypatch.setattr(command_lookup, "ArtifactCatalog", catalog)

        result = CliRunner().invoke(
            app,
            ["artifact", "lookup", "preset:lookup-pack:template:lookup-template", "--json"],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        error = json.loads(result.stderr)
        assert set(error) == {"error"}
        assert "init-options.json" in error["error"]
        assert diagnostic in error["error"]
        loader.assert_not_called()
        catalog.assert_not_called()

    def test_lookup_symlinked_registry_uses_json_error_envelope(
        self, symlinked_preset_registry: Path, monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.chdir(symlinked_preset_registry)

        result = CliRunner().invoke(
            app,
            ["artifact", "lookup", "preset:example:template:example", "--json"],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert result.stderr == '{"error": "artifact resolution failed"}\n'

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
