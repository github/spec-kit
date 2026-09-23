"""Tests for ``specify artifact info``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from tests.specify_cli.artifacts.helpers import (
    ERROR_REGEX,
    install_extension_with_hooks,
)


class TestCommandInfo:
    def test_info_json_shape(self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        result = runner.invoke(app, ["artifact", "info", "speckit.constitution", "--json"])
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert set(payload.keys()) == {"id", "name", "kind", "description", "stack"}

    def test_info_accepts_id_form_on_cli(
        self, spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(spec_kit_project)
        runner = CliRunner()
        by_bare = runner.invoke(app, ["artifact", "info", "speckit.plan", "--json"])
        by_id = runner.invoke(app, ["artifact", "info", "command:speckit.plan", "--json"])
        assert by_bare.exit_code == 0, by_bare.stderr
        assert by_id.exit_code == 0, by_id.stderr
        assert json.loads(by_id.stdout) == json.loads(by_bare.stdout)

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
