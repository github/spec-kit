"""Tests for the experimental ``specify mcp`` command adapter."""

from unittest.mock import patch

from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()


def test_mcp_command_registered_in_root_help():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "mcp" in result.output


def test_mcp_help_marks_server_experimental_and_stdio_only():
    result = runner.invoke(app, ["mcp", "--help"])

    assert result.exit_code == 0
    assert "experimental" in result.output.lower()
    assert "stdio" in result.output.lower()
    assert "--transport" not in result.output


def test_mcp_command_starts_server_without_cli_output():
    with patch("specify_cli.mcp_server.run_stdio_server") as run_stdio_server:
        result = runner.invoke(app, ["mcp"])

    assert result.exit_code == 0
    assert result.stdout == ""
    assert result.stderr == ""
    run_stdio_server.assert_called_once_with()
