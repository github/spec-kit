"""Tests for ``specify artifact info``."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.artifacts import command_info
from specify_cli.artifacts._operation_info import (
    ArtifactInfoNamedArtifact,
    ArtifactInfoNotFoundError,
    ArtifactInfoResult,
)
from specify_cli.artifacts.models import StackLayer
from tests.specify_cli.artifacts.helpers import (
    ERROR_REGEX,
    install_extension_with_hooks,
)


class TestCommandInfo:
    def test_info_requires_json_flag(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(spec_kit_project)

        result = CliRunner().invoke(
            app,
            ["artifact", "info", "speckit.plan"],
        )

        assert result.exit_code == 2
        assert result.stdout == ""
        assert result.stderr == (
            "specify artifact requires --json for now; "
            "text output is not yet implemented.\n"
        )

    def test_info_rejects_invalid_cli_kind_before_dispatch(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        operation = Mock(side_effect=AssertionError("operation reached"))
        monkeypatch.setattr(command_info, "get_artifact_info", operation)
        monkeypatch.chdir(spec_kit_project)

        result = CliRunner().invoke(
            app,
            [
                "artifact",
                "info",
                "speckit.plan",
                "--json",
                "--kind",
                "invalid",
            ],
        )

        assert result.exit_code == 2
        assert result.stdout == ""
        assert result.stderr == (
            "invalid --kind 'invalid': expected one of "
            "command, template, script, hook\n"
        )
        operation.assert_not_called()

    def test_info_dispatches_directly_to_shared_operation(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        expected = ArtifactInfoResult(
            artifact=ArtifactInfoNamedArtifact(
                id="template:réview",
                name="réview",
                kind="template",
                description="Réview ✓",
                stack=(
                    StackLayer(
                        id="template:réview",
                        layer="extension",
                        sourceId="quality",
                        presetId=None,
                        presetName=None,
                        strategy="replace",
                        active=True,
                        hidden=False,
                        manifestPath=".specify/extensions/quality/extension.yml",
                        lookupId="extension:quality:template:réview",
                        sourcePath=(".specify/extensions/quality/templates/réview.md"),
                    ),
                ),
            )
        )
        operation = Mock(return_value=expected)
        monkeypatch.setattr(command_info, "get_artifact_info", operation)
        monkeypatch.chdir(spec_kit_project)

        result = CliRunner().invoke(
            app,
            [
                "artifact",
                "info",
                "réview",
                "--json",
                "--kind",
                "template",
            ],
        )

        assert result.exit_code == 0, result.stderr
        assert json.loads(result.stdout) == expected.to_json_dict()
        request = operation.call_args.args[0]
        assert request.project_directory == spec_kit_project
        assert request.identifier == "réview"
        assert request.kind == "template"

    def test_info_json_matches_shared_operation_result(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(spec_kit_project)
        expected = command_info.get_artifact_info(
            command_info.ArtifactInfoRequest(
                spec_kit_project,
                "command:speckit.plan",
            )
        )

        result = CliRunner().invoke(
            app,
            ["artifact", "info", "command:speckit.plan", "--json"],
        )

        assert result.exit_code == 0, result.stderr
        assert json.loads(result.stdout) == expected.to_json_dict()

    def test_info_json_shape(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(
            app, ["artifact", "info", "speckit.constitution", "--json"]
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert set(payload.keys()) == {"id", "name", "kind", "description", "stack"}
        assert result.stdout == (
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n"
        )
        assert result.stderr == ""
        assert "\x1b[" not in result.stdout

    def test_info_accepts_id_form_on_cli(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        by_bare = runner.invoke(app, ["artifact", "info", "speckit.plan", "--json"])
        by_id = runner.invoke(
            app, ["artifact", "info", "command:speckit.plan", "--json"]
        )
        assert by_bare.exit_code == 0, by_bare.stderr
        assert by_id.exit_code == 0, by_id.stderr
        assert json.loads(by_id.stdout) == json.loads(by_bare.stdout)

    def test_info_unknown_error_envelope(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "info", "no.such.thing", "--json"])
        assert result.exit_code == 1
        assert result.stdout == ""
        err = json.loads(result.stderr)
        assert set(err.keys()) == {"error"}
        assert ERROR_REGEX.match(err["error"])
        assert result.stderr.count("\n") == 1
        assert "\x1b[" not in result.stderr

    def test_info_expected_operation_failure_is_one_legacy_json_error(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(
            command_info,
            "get_artifact_info",
            Mock(side_effect=ArtifactInfoNotFoundError("missing")),
        )
        monkeypatch.chdir(spec_kit_project)

        result = CliRunner().invoke(
            app,
            ["artifact", "info", "missing", "--json"],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert result.stderr == '{"error": "unknown artifact missing"}\n'
        assert "Traceback" not in result.stderr

    def test_info_cli_context_filesystem_failure_is_json_error(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(
            command_info,
            "_project_directory_from_cli_context",
            Mock(side_effect=OSError("unreadable cwd")),
        )

        result = CliRunner().invoke(
            app,
            ["artifact", "info", "speckit.plan", "--json"],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert json.loads(result.stderr) == {"error": "artifact resolution failed"}

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

    def test_stdout_empty_on_error(
        self, non_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
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

    def test_list_and_info_json(self, spec_kit_project: Path, monkeypatch):
        install_extension_with_hooks(
            spec_kit_project,
            "compliance",
            hooks={"before_specify": [{"command": "speckit.compliance.pre-check"}]},
        )
        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()

        list_result = runner.invoke(app, ["artifact", "list", "--json"])
        info_result = runner.invoke(
            app,
            [
                "artifact",
                "info",
                "hook:before_specify:speckit.compliance.pre-check",
                "--json",
            ],
        )

        assert list_result.exit_code == 0, list_result.output
        assert info_result.exit_code == 0, info_result.output
        assert any(row["kind"] == "hook" for row in json.loads(list_result.stdout))
        assert json.loads(info_result.stdout)["kind"] == "hook"

    def test_unknown_hook_json_error_envelope(
        self, spec_kit_project: Path, monkeypatch
    ):
        monkeypatch.chdir(spec_kit_project)

        result = CliRunner().invoke(
            app,
            ["artifact", "info", "hook:nope:missing.cmd", "--json"],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert ERROR_REGEX.match(json.loads(result.stderr)["error"])

    @pytest.mark.parametrize(
        "identifier",
        ["hook:event:bad%escape", "hook:event:%FF"],
    )
    def test_malformed_hook_id_json_error_envelope(
        self, spec_kit_project: Path, monkeypatch, identifier: str
    ):
        monkeypatch.chdir(spec_kit_project)

        result = CliRunner().invoke(
            app,
            ["artifact", "info", identifier, "--json"],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert ERROR_REGEX.match(json.loads(result.stderr)["error"])
