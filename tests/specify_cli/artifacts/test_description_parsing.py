"""Best-effort Python metadata parsing must not disrupt artifact commands."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app


COMMANDS = [
    ["artifact", "list", "--json"],
    ["artifact", "info", "script:deploy", "--json"],
    ["artifact", "info", "command:speckit.plan", "--json"],
]


def _write_python_script(project: Path, source: str) -> None:
    templates = project / ".specify" / "templates"
    scripts = templates / "scripts" / "python"
    scripts.mkdir(parents=True)
    commands = templates / "commands"
    commands.mkdir()
    (commands / "deploy.md").write_text(
        "---\nscripts:\n  py: scripts/python/deploy.py\n---\nDeploy.\n",
        encoding="utf-8",
    )
    (project / ".specify" / "init-options.json").write_text(
        json.dumps({"script": "py"}), encoding="utf-8"
    )
    (scripts / "deploy.py").write_text(source, encoding="utf-8")


def _assert_script_description(payload, command, expected):
    if command[1] == "list":
        assert (
            next(row for row in payload if row["id"] == "script:deploy")["description"]
            == expected
        )
    elif command[2] == "script:deploy":
        assert payload["description"] == expected
    else:
        assert payload["id"] == "command:speckit.plan"


@pytest.mark.parametrize(
    "expression",
    ["1+" * 9999 + "1", "+" * 6000 + "1"],
    ids=["deep-addition", "deep-unary"],
)
@pytest.mark.parametrize("command", COMMANDS)
def test_parser_resource_failures_use_comment_fallback(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    expression: str,
    command: list[str],
):
    _write_python_script(spec_kit_project, "# Deployment helper\n" + expression + "\n")
    monkeypatch.chdir(spec_kit_project)

    result = CliRunner().invoke(app, command)

    assert result.exit_code == 0, result.exception
    assert result.stderr == ""
    _assert_script_description(json.loads(result.stdout), command, "Deployment helper")


@pytest.mark.parametrize("command", COMMANDS)
def test_metadata_parse_suppresses_warnings_without_changing_filters(
    spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch, command: list[str]
):
    _write_python_script(
        spec_kit_project,
        '# Header\n"""Deployment helper."""\nimport re\nre.compile("\\d+")\n'
        'raise RuntimeError("Inventory must never execute this script")\n',
    )
    monkeypatch.chdir(spec_kit_project)
    with warnings.catch_warnings(record=True) as emitted:
        warnings.simplefilter("always")
        filters = warnings.filters.copy()
        result = CliRunner().invoke(app, command)
        assert warnings.filters == filters

    assert result.exit_code == 0, result.exception
    assert result.stderr == ""
    assert emitted == []
    _assert_script_description(json.loads(result.stdout), command, "Deployment helper.")
