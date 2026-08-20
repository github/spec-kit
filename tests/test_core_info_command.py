"""CLI-level tests for ``specify core info --json`` via Typer's CliRunner."""
from __future__ import annotations

import importlib
import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from tests.conftest import strip_ansi


def _invoke(args: list[str]):
    runner = CliRunner()
    return runner.invoke(app, args)


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


def test_core_info_json_returns_zero_and_valid_json() -> None:
    result = _invoke(["core", "info", "--json"])
    assert result.exit_code == 0, result.output
    parsed = json.loads(result.output)
    assert list(parsed.keys()) == ["commands", "templates", "scripts"]


def test_core_info_without_json_exits_nonzero() -> None:
    result = _invoke(["core", "info"])
    assert result.exit_code != 0
    # Message points at the flag; user knows what to do.
    assert "--json" in strip_ansi(result.output)


def test_core_info_help_lists_json_flag() -> None:
    result = _invoke(["core", "info", "--help"])
    assert result.exit_code == 0
    assert "--json" in strip_ansi(result.output)


def test_specify_root_help_shows_core_group() -> None:
    result = _invoke(["--help"])
    assert result.exit_code == 0
    assert "core" in strip_ansi(result.output).lower()


# ---------------------------------------------------------------------------
# Schema-conformance (hand-rolled shape check)
# ---------------------------------------------------------------------------


_STABLE_ID = re.compile(r"^core:_:(command|template|script):[A-Za-z0-9._-]+$")
_PACKAGE_REL = re.compile(r"^(?!/)[^\\]+$")
_ALLOWED_RUNTIMES = {"bash", "powershell", "python"}


def _validate_command(entry: dict) -> None:
    required = {"id", "name", "description", "sourcePath", "artifact", "optional", "handoffs"}
    assert set(entry.keys()) == required, entry
    assert _STABLE_ID.match(entry["id"])
    assert isinstance(entry["name"], str) and entry["name"]
    assert isinstance(entry["description"], str) and entry["description"]
    assert _PACKAGE_REL.match(entry["sourcePath"])
    assert entry["artifact"] is None or isinstance(entry["artifact"], str)
    assert isinstance(entry["optional"], bool)
    assert isinstance(entry["handoffs"], list)
    for h in entry["handoffs"]:
        assert isinstance(h, str) and h


def _validate_template(entry: dict) -> None:
    required = {"id", "name", "description", "sourcePath"}
    assert set(entry.keys()) == required, entry
    assert _STABLE_ID.match(entry["id"])
    assert isinstance(entry["name"], str) and entry["name"]
    assert isinstance(entry["description"], str) and entry["description"]
    assert _PACKAGE_REL.match(entry["sourcePath"])


def _validate_script(entry: dict) -> None:
    required = {"id", "name", "description", "sourcePath", "runtimes"}
    assert set(entry.keys()) == required, entry
    assert _STABLE_ID.match(entry["id"])
    assert isinstance(entry["name"], str) and entry["name"]
    assert isinstance(entry["description"], str) and entry["description"]
    assert _PACKAGE_REL.match(entry["sourcePath"])
    assert isinstance(entry["runtimes"], list) and entry["runtimes"]
    assert set(entry["runtimes"]) <= _ALLOWED_RUNTIMES
    assert entry["runtimes"] == sorted(set(entry["runtimes"]))


def test_core_info_output_validates_against_contract_schema() -> None:
    result = _invoke(["core", "info", "--json"])
    parsed = json.loads(result.output)
    for entry in parsed["commands"]:
        _validate_command(entry)
    for entry in parsed["templates"]:
        _validate_template(entry)
    for entry in parsed["scripts"]:
        _validate_script(entry)


# ---------------------------------------------------------------------------
# Determinism gate
# ---------------------------------------------------------------------------


def test_core_info_output_is_byte_identical_across_two_runs() -> None:
    a = _invoke(["core", "info", "--json"])
    b = _invoke(["core", "info", "--json"])
    assert a.exit_code == 0 and b.exit_code == 0
    assert a.output == b.output, "output not byte-identical across two runs"


# ---------------------------------------------------------------------------
# Path-shape invariant
# ---------------------------------------------------------------------------


def test_core_info_source_paths_are_package_relative() -> None:
    parsed = json.loads(_invoke(["core", "info", "--json"]).output)
    for section in ("commands", "templates", "scripts"):
        for entry in parsed[section]:
            assert _PACKAGE_REL.match(entry["sourcePath"]), entry["sourcePath"]


# ---------------------------------------------------------------------------
# Project-isolation guarantees
# ---------------------------------------------------------------------------


def test_core_info_runs_outside_specify_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The command must succeed even when cwd is not a Spec Kit project."""
    monkeypatch.chdir(tmp_path)
    result = _invoke(["core", "info", "--json"])
    assert result.exit_code == 0, result.output


def test_core_info_ignores_presets_and_extensions_in_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Even a project with a fake .specify + preset dir must not change output."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".specify").mkdir()
    (tmp_path / ".specify" / "presets").mkdir()
    (tmp_path / ".specify" / "presets" / "fake.yml").write_text(
        "preset:\n  id: fake\n  name: fake\n", encoding="utf-8"
    )
    inside = _invoke(["core", "info", "--json"]).output

    monkeypatch.chdir(tmp_path.parent)
    outside = _invoke(["core", "info", "--json"]).output

    assert inside == outside


# ---------------------------------------------------------------------------
# Fail-fast on packaging errors → non-zero exit + JSON envelope on stderr
# ---------------------------------------------------------------------------


def test_core_info_missing_command_file_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    importlib.import_module("specify_cli.core")

    # Redirect the discovery helpers to a name that has no shipped file.
    monkeypatch.setattr(
        "specify_cli.extensions.CORE_COMMAND_NAMES",
        frozenset({"nonexistent-command"}),
    )
    result = _invoke(["core", "info", "--json"])
    assert result.exit_code == 1
    # CliRunner mixes streams by default; parse the envelope out of the output.
    # Look for the JSON envelope keys — that's enough to confirm the shape.
    assert "core_inventory.missing_file" in strip_ansi(result.output)
