from __future__ import annotations

import io  # noqa: F401
import json  # noqa: F401
from pathlib import Path
from unittest.mock import patch  # noqa: F401

import pytest
import yaml  # noqa: F401
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundles.packager import build_bundle  # noqa: F401
from tests.conftest import strip_ansi  # noqa: F401

runner = CliRunner()


def test_bundle_help_lists_all_commands():
    result = runner.invoke(app, ["bundle", "--help"])
    assert result.exit_code == 0
    for cmd in (
        "search",
        "info",
        "list",
        "install",
        "add",
        "update",
        "remove",
        "validate",
        "build",
        "init",
        "catalog",
    ):
        assert cmd in result.output


def test_fail_writes_error_to_stderr_not_stdout(capsys):
    """_fail must write to stderr, not stdout: every bundle command routes errors
    through it, and under --json the error would otherwise corrupt the JSON payload
    that consumers read from stdout."""
    import typer

    from specify_cli.bundles._commands import _fail

    with pytest.raises(typer.Exit):
        _fail("something broke")
    captured = capsys.readouterr()
    assert "something broke" in captured.err
    assert "something broke" not in captured.out


@pytest.mark.parametrize(
    "argv, expected",
    [
        (
            ["bundle", "catalog", "add", "ssh://ex[/red]ample.com/c.json"],
            "ssh://ex[/red]ample.com/c.json",
        ),
        (["bundle", "catalog", "remove", "no[/red]such"], "no[/red]such"),
        (["bundle", "update", "no[/red]such"], "no[/red]such"),
        (["bundle", "remove", "no[/red]such"], "no[/red]such"),
    ],
)
def test_error_paths_escape_rich_markup(project: Path, argv: list, expected: str):
    result = runner.invoke(app, argv)

    assert result.exit_code == 1
    # A MarkupError would surface here as an exception rather than a clean exit.
    assert isinstance(result.exception, SystemExit)
    assert expected in strip_ansi(result.output)
