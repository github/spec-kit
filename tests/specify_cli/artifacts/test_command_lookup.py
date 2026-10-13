"""Tests for ``specify artifact lookup``."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import Mock

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli._project_policy import (
    ProjectResolutionError,
    preflight_project_policy,
)
from specify_cli.artifacts import (
    ArtifactCatalog,
    _operation_lookup,
    command_lookup,
)
from specify_cli.artifacts._operation_lookup import (
    ArtifactLookupJsonObject,
    ArtifactLookupNotFoundError,
    ArtifactLookupResult,
)
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
        result = CliRunner().invoke(app, ["artifact", "lookup", lookup_id, "--json"])

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
        monkeypatch.setattr(_operation_lookup, "ArtifactCatalog", catalog)

        result = CliRunner().invoke(
            app,
            [
                "artifact",
                "lookup",
                "preset:lookup-pack:template:lookup-template",
                "--json",
            ],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        error = json.loads(result.stderr)
        assert set(error) == {"error"}
        assert "init-options.json" in error["error"]
        assert diagnostic in error["error"]
        loader.assert_not_called()
        catalog.assert_not_called()

    @pytest.mark.parametrize("marker_kind", ["symlink", "file"])
    def test_lookup_preserves_structural_project_policy_json_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        marker_kind: str,
    ):
        project_directory = tmp_path / "project"
        project_directory.mkdir()
        marker = project_directory / ".specify"
        if marker_kind == "symlink":
            target = tmp_path / "real-specify"
            target.mkdir()
            try:
                marker.symlink_to(target, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                pytest.skip(f"Symlinks unavailable: {exc}")
        else:
            marker.write_text("not a directory", encoding="utf-8")

        with pytest.raises(ProjectResolutionError) as preflight_exc:
            preflight_project_policy(project_directory)

        monkeypatch.chdir(project_directory)
        result = CliRunner().invoke(
            app,
            [
                "artifact",
                "lookup",
                "malformed",
                "--json",
            ],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert json.loads(result.stderr) == {"error": str(preflight_exc.value)}
        assert result.stderr.count("\n") == 1
        assert "Traceback" not in result.stderr

    def test_lookup_json_rejects_unknown_contribution(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(spec_kit_project)
        lookup_id = "extension:missing:command:speckit.missing.command"

        result = CliRunner().invoke(app, ["artifact", "lookup", lookup_id, "--json"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert json.loads(result.stderr) == {
            "error": f"unknown contribution {lookup_id}"
        }

    def test_lookup_dispatches_directly_to_shared_operation(
        self,
        spec_kit_project: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        expected = ArtifactLookupResult(
            id="extension:quality:template:réview",
            layer="extension",
            sourceId="quality",
            kind="template",
            name="réview",
            manifestPath=".specify/extensions/quality/extension.yml",
            sourcePath=".specify/extensions/quality/templates/réview.md",
            contribution=ArtifactLookupJsonObject(
                (
                    ("name", "réview"),
                    ("description", "Réview ✓"),
                )
            ),
        )
        operation = Mock(return_value=expected)
        monkeypatch.setattr(command_lookup, "lookup_artifact", operation)
        monkeypatch.chdir(spec_kit_project)

        result = CliRunner().invoke(
            app,
            [
                "artifact",
                "lookup",
                "extension:quality:template:réview",
                "--json",
            ],
        )

        assert result.exit_code == 0, result.stderr
        assert json.loads(result.stdout) == expected.to_json_dict()
        request = operation.call_args.args[0]
        assert request.project_directory == spec_kit_project
        assert request.lookup_id == "extension:quality:template:réview"
        assert "ArtifactCatalog" not in command_lookup.__dict__

    def test_lookup_json_matches_shared_operation_result(
        self,
        spec_kit_project: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        pack = install_preset(
            spec_kit_project,
            "parity",
            {
                "templates": [
                    {
                        "type": "template",
                        "name": "parity",
                        "file": "templates/parity.md",
                        "description": "Parity ✓",
                    }
                ]
            },
        )
        (pack / "templates").mkdir()
        (pack / "templates" / "parity.md").write_text(
            "body",
            encoding="utf-8",
        )
        lookup_id = "preset:parity:template:parity"
        expected = command_lookup.lookup_artifact(
            command_lookup.ArtifactLookupRequest(
                spec_kit_project,
                lookup_id,
            )
        )
        monkeypatch.chdir(spec_kit_project)

        result = CliRunner().invoke(
            app,
            ["artifact", "lookup", lookup_id, "--json"],
        )

        assert result.exit_code == 0, result.stderr
        assert json.loads(result.stdout) == expected.to_json_dict()

    def test_lookup_success_stream_is_exact_legacy_json(
        self,
        spec_kit_project: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        expected = ArtifactLookupResult(
            id="preset:quality:template:réview",
            layer="preset",
            sourceId="quality",
            kind="template",
            name="réview",
            manifestPath=".specify/presets/quality/preset.yml",
            sourcePath=None,
            contribution=ArtifactLookupJsonObject(
                (
                    ("zeta", (1, 2)),
                    ("alpha", "Réview ✓"),
                )
            ),
        )
        monkeypatch.setattr(
            command_lookup,
            "lookup_artifact",
            Mock(return_value=expected),
        )
        monkeypatch.chdir(spec_kit_project)

        result = CliRunner().invoke(
            app,
            ["artifact", "lookup", expected.id, "--json"],
        )

        assert result.exit_code == 0
        payload = expected.to_json_dict()
        assert result.stdout == (
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        )
        result.stdout.encode("utf-8")
        assert json.loads(result.stdout) == payload
        assert result.stderr == ""
        assert "\x1b[" not in result.stdout

    def test_lookup_expected_operation_failure_is_one_legacy_json_error(
        self,
        spec_kit_project: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        lookup_id = "extension:missing:command:speckit.missing"
        monkeypatch.setattr(
            command_lookup,
            "lookup_artifact",
            Mock(side_effect=ArtifactLookupNotFoundError(lookup_id)),
        )
        monkeypatch.chdir(spec_kit_project)

        result = CliRunner().invoke(
            app,
            ["artifact", "lookup", lookup_id, "--json"],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert result.stderr == (
            '{"error": "unknown contribution '
            'extension:missing:command:speckit.missing"}\n'
        )
        assert result.stderr.count("\n") == 1
        assert "\x1b[" not in result.stderr
        assert "Traceback" not in result.stderr

    def test_lookup_cli_context_filesystem_failure_is_json_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.setattr(
            command_lookup,
            "_project_directory_from_cli_context",
            Mock(side_effect=OSError("unreadable cwd")),
        )

        result = CliRunner().invoke(
            app,
            [
                "artifact",
                "lookup",
                "preset:sample:template:sample",
                "--json",
            ],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert json.loads(result.stderr) == {"error": "artifact resolution failed"}

    def test_lookup_cli_context_path_resolution_runtime_error_is_json_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("SPECIFY_INIT_DIR", "cyclic-project")
        monkeypatch.setattr(
            Path,
            "resolve",
            Mock(side_effect=RuntimeError("Symlink loop from path resolution")),
        )

        result = CliRunner().invoke(
            app,
            [
                "artifact",
                "lookup",
                "preset:sample:template:sample",
                "--json",
            ],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert json.loads(result.stderr) == {"error": "artifact resolution failed"}
        assert "Traceback" not in result.stderr

    def test_lookup_unexpected_operation_filesystem_failure_is_json_error(
        self,
        spec_kit_project: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.setattr(
            command_lookup,
            "lookup_artifact",
            Mock(side_effect=OSError("unreadable catalog")),
        )
        monkeypatch.chdir(spec_kit_project)

        result = CliRunner().invoke(
            app,
            [
                "artifact",
                "lookup",
                "preset:sample:template:sample",
                "--json",
            ],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert json.loads(result.stderr) == {"error": "artifact resolution failed"}
        assert "Traceback" not in result.stderr

    def test_lookup_cli_context_resolves_init_dir_override(
        self,
        spec_kit_project: Path,
        non_project: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        operation = Mock(
            side_effect=ArtifactLookupNotFoundError("preset:missing:template:missing")
        )
        monkeypatch.setattr(command_lookup, "lookup_artifact", operation)
        monkeypatch.chdir(non_project)
        monkeypatch.setenv("SPECIFY_INIT_DIR", str(spec_kit_project))

        result = CliRunner().invoke(
            app,
            [
                "artifact",
                "lookup",
                "preset:missing:template:missing",
                "--json",
            ],
        )

        assert result.exit_code == 1
        request = operation.call_args.args[0]
        assert request.project_directory == spec_kit_project.resolve()

    def test_lookup_rendering_failure_is_json_error(
        self,
        spec_kit_project: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        result_object = Mock()
        result_object.to_json_dict.return_value = {"value": date(2026, 1, 1)}
        monkeypatch.setattr(
            command_lookup,
            "lookup_artifact",
            Mock(return_value=result_object),
        )
        monkeypatch.chdir(spec_kit_project)

        result = CliRunner().invoke(
            app,
            [
                "artifact",
                "lookup",
                "preset:sample:template:sample",
                "--json",
            ],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert json.loads(result.stderr) == {"error": "artifact resolution failed"}

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
        assert json.loads(result.stderr) == {"error": "artifact resolution failed"}

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

        result = CliRunner().invoke(app, ["artifact", "lookup", lookup_id, "--json"])

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

    def test_lookup_validates_project_before_unknown_lookup_id(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.chdir(tmp_path)
        result = CliRunner().invoke(
            app,
            [
                "artifact",
                "lookup",
                "extension:missing:command:speckit.missing",
                "--json",
            ],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert json.loads(result.stderr) == {
            "error": "not a Spec Kit project: no .specify/ directory found"
        }
